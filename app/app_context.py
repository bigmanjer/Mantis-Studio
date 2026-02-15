#!/usr/bin/env python3
"""
MANTIS Studio - Application Entry

This file contains an alternative implementation of the MANTIS Studio UI.
It is NOT the active entry point - see ../app/main.py instead.

This implementation is preserved for reference and potential future consolidation
as described in README.md Section 9A (Repository Organization Recommendation).

If you're looking to understand how the app works, refer to:
    - ../app/main.py (active entry point)
    - mantis/router.py (navigation)
    - mantis/ui/pages/* (view implementations)
"""
# app/main.py — MANTIS Studio
#
# Run:
#   python -m streamlit run app/main.py
#
# Requirements:
#   streamlit>=1.42.0
#   requests
#   python-dotenv (optional)
#   pandas
#   plotly
#
# Notes:
# - This preserves ALL current features from your v47 generator build:
#   Projects (create/load/delete), Outline generation/title generation/reverse engineer,
#   Entity scanning & enrich, World Bible categories, Chapters w/ AI autowrite,
#   Summaries, Rewrite presets, Export markdown, Import story text, Auto-save, Ghost text flow.
#
# - This is a UI/first-time appearance upgrade:
#   First-run welcome, clearer home, cleaner sidebar, better empty states, safer buttons/layout.

import datetime
import difflib
import json
import os
from pathlib import Path
import random
import re
import shutil
import sys
import time
import uuid
from types import SimpleNamespace
from collections.abc import Generator
from typing import Any, Callable, Dict, List, Optional

import requests
# (UI-only imports are loaded inside _run_ui() so selftests can run without Streamlit installed.)

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.config.settings import AppConfig, ensure_storage_dirs, load_app_config, logger, save_app_config
from app.services.export import project_to_markdown
from app.services.projects import Chapter, Entity, Project, sanitize_chapter_title
# Local-first architecture: projects stored in default directory
from app.services.world_bible import queue_world_bible_suggestion
from app.services.ai import AIEngine, AnalysisEngine, REWRITE_PRESETS, StoryEngine, rewrite_prompt
from app.state import initialize_session_state, install_key_helpers, ui_key

# NOTE: Streamlit-dependent utilities are imported inside _run_ui() so
# `python app/main.py --selftest` can run without Streamlit installed.


# ===== v45 BRANDING (SAFE, ORIGINAL TEMPLATE) =====
import base64
# ==================================================

SELFTEST_MODE = "--selftest" in sys.argv
REPAIR_MODE = "--repair" in sys.argv


# ============================================================
# 1) CONFIG
# ============================================================
# ============================================================
# 2) MODELS
# ============================================================
# ============================================================
# 3) AI ENGINE
# ============================================================
# ============================================================
# 4) UTILS
# ============================================================
# ============================================================
# 5) STREAMLIT UI (Appearance + First-time Onboarding)
# ============================================================



def _run_ui():
    import streamlit as st
    from app import router
    from app.components.ui import action_card, card, primary_button, section_header, stat_tile
    from app.layout.layout import apply_theme, get_theme_tokens, render_footer, render_header

    key_scope, _ = install_key_helpers(st)

    ASSETS_DIR = Path(__file__).resolve().parents[1] / "assets"

    @st.cache_data(show_spinner=False)
    def load_asset_bytes(filename: str) -> Optional[bytes]:
        path = ASSETS_DIR / filename
        if not path.exists():
            return None
        try:
            return path.read_bytes()
        except Exception:
            logger.warning("Failed to load asset %s", path, exc_info=True)
            return None

    def asset_base64(filename: str) -> str:
        payload = load_asset_bytes(filename)
        if not payload:
            return ""
        return base64.b64encode(payload).decode("utf-8")

    def get_canon_health() -> tuple[str, str]:
        results = st.session_state.get("coherence_results", [])
        issue_count = len(results)
        if issue_count == 0:
            return "🟢", "Canon Stable"
        if issue_count <= 2:
            return "🟡", "Minor Canon Drift"
        return "🔴", "High Canon Risk"

    def detect_hard_canon_violation(project: Project, chapter_index: int, new_text: str) -> List[Dict[str, Any]]:
        hard_rules = (project.memory_hard or project.memory or "").strip()
        if not hard_rules or not (new_text or "").strip():
            return []
        if not AppConfig.GROQ_API_KEY or not get_ai_model():
            return []
        compiled_world_bible = "\n".join(
            f"{e.name} ({e.category}): {e.description}"
            for e in project.world_db.values()
        )
        chapters_payload = [
            {
                "chapter_index": chapter_index,
                "summary": "",
                "excerpt": (new_text or "")[:800],
            }
        ]
        results = AnalysisEngine.coherence_check(
            memory=hard_rules,
            author_note="",
            style_guide="",
            outline=project.outline or "",
            world_bible=compiled_world_bible,
            chapters=chapters_payload,
            model=get_ai_model(),
        )
        return results or []

    def render_privacy():
        st.markdown("## Privacy Policy\n\nLocal-only storage. No analytics.")

    def render_terms():
        st.markdown("## Terms of Service\n\nProvided as-is for creative use.")

    def render_copyright():
        st.markdown("## Copyright\n\n© MANTIS Studio")

    def render_help():
        st.markdown("## Help\n\nVisit our [GitHub](https://github.com/bigmanjer/Mantis-Studio/issues) for support.")

    icon_path = ASSETS_DIR / "mantis_logo_trans.png"
    page_icon = str(icon_path) if icon_path.exists() else "🪲"
    st.set_page_config(page_title=AppConfig.APP_NAME, page_icon=page_icon, layout="wide")

    config_data = load_app_config()

    initialize_session_state(st, config_data)

    theme = st.session_state.ui_theme if st.session_state.ui_theme in ("Dark", "Light") else "Dark"
    tokens = get_theme_tokens(theme)[theme]
    apply_theme(tokens)

    header_logo_b64 = asset_base64("mantis_logo_trans.png")
    render_header(AppConfig.VERSION, header_logo_b64)

    
    def open_legal_page() -> None:
        st.session_state.page = "legal"
        st.rerun()

    def persist_project(
        project: "Project",
        *,
        action: str = "save",
    ) -> bool:
        path = project.save()
        if not path:
            logger.error("persist_project failed for '%s' (action=%s)", project.title, action)
            try:
                st.toast("⚠️ Save failed — check file permissions and disk space.", icon="⚠️")
            except Exception as e:
                st.error(f"Save failed for '{project.title}': {e}")
            return False
        return True

    def render_app_footer() -> None:
        render_footer(AppConfig.VERSION)


    if not st.session_state.projects_dir:
        st.session_state.projects_dir = AppConfig.PROJECTS_DIR

    # Reliable navigation rerun (avoids Streamlit edge cases when returning early)
    if st.session_state.get("_force_nav"):
        st.session_state._force_nav = False
        st.rerun()

    def get_ai_model() -> str:
        return st.session_state.get("groq_model", AppConfig.DEFAULT_MODEL)

    def _resolve_ai_key(provider: str) -> str:
        session_key = (st.session_state.get("ai_keys") or {}).get(provider, "")
        if session_key:
            return session_key
        return config_data.get(f"{provider}_api_key", "") or ""

    def _display_ai_key(provider: str) -> str:
        session_key = (st.session_state.get("ai_keys") or {}).get(provider, "")
        if session_key:
            return session_key
        return config_data.get(f"{provider}_api_key", "") or ""

    def _set_ai_key(provider: str, value: str) -> None:
        cleaned = (value or "").strip()
        ai_keys = st.session_state.get("ai_keys") or {}
        if cleaned:
            ai_keys[provider] = cleaned
        else:
            ai_keys.pop(provider, None)
        st.session_state.ai_keys = ai_keys
        resolved = _resolve_ai_key(provider)
        if provider == "groq":
            st.session_state.groq_api_key = resolved
            AppConfig.GROQ_API_KEY = resolved
        elif provider == "openai":
            st.session_state.openai_api_key = resolved
            AppConfig.OPENAI_API_KEY = resolved

    def save_p():
        if st.session_state.project and st.session_state.auto_save:
            persist_project(st.session_state.project)

    def get_active_projects_dir() -> Optional[str]:
        return st.session_state.get("projects_dir") or AppConfig.PROJECTS_DIR

    def resume_pending_action() -> None:
        pending = st.session_state.get("pending_action")
        if not pending:
            return
        action = pending.get("action")
        payload = pending.get("payload") or {}
        return_to = pending.get("return_to") or "home"
        st.session_state.pending_action = None

        if action == "create_project":
            p = Project.create(
                payload.get("title") or "Untitled Project",
                author=payload.get("author", ""),
                genre=payload.get("genre", ""),
                storage_dir=get_active_projects_dir() or AppConfig.PROJECTS_DIR,
            )
            p.save()
            st.session_state.project = p
        elif action == "import_project":
            text = payload.get("text") or ""
            p = Project.create("Imported Project", storage_dir=get_active_projects_dir() or AppConfig.PROJECTS_DIR)
            p.import_text_file(text)
            if AppConfig.GROQ_API_KEY and get_ai_model():
                p.outline = StoryEngine.reverse_engineer_outline(p, get_ai_model())
            p.save()
            st.session_state.project = p
        elif action == "save_project":
            if st.session_state.project:
                st.session_state.project.save()
                st.toast("Project saved.")
        elif action == "save_outline":
            if st.session_state.project:
                st.session_state.project.save()
                st.toast("Outline saved.")
        elif action == "save_chapter":
            if st.session_state.project:
                st.session_state.project.save()
                st.toast("Chapter saved.")
        elif action == "export_project":
            if st.session_state.project:
                st.session_state.project.save()
                st.session_state.export_project_path = st.session_state.project.filepath
        elif action == "save_app_settings":
            save_app_settings()
        elif action == "delete_project":
            delete_path = payload.get("path")
            if delete_path:
                Project.delete_file(delete_path)
                _bump_projects_refresh()

        st.session_state.page = return_to
        st.rerun()

    if st.session_state.get("pending_action"):
        resume_pending_action()


    def load_project_safe(path: str, context: str = "project") -> Optional["Project"]:
        try:
            return Project.load(path)
        except Exception:
            logger.warning("Failed to load %s: %s", context, path, exc_info=True)
            st.error("We couldn't open that project file. It may be missing or corrupted.")
            return None

    def render_page_header(
        title: str,
        subtitle: str,
        primary_label: Optional[str] = None,
        primary_action: Optional[Callable[[], None]] = None,
        secondary_label: Optional[str] = None,
        secondary_action: Optional[Callable[[], None]] = None,
        tag: Optional[str] = None,
        key_prefix: str = "page_header",
    ) -> None:
        with st.container(border=True):
            left, right = st.columns([2.4, 1])
            with left:
                tag_html = f"<span class='mantis-tag'>{tag}</span>" if tag else ""
                st.html(
                    f"""
                    <div class="mantis-page-header">
                        <div>
                            <div class="mantis-page-title">{title} {tag_html}</div>
                            <div class="mantis-page-sub">{subtitle}</div>
                        </div>
                    </div>
                    """,
                )
            with right:
                if primary_label and primary_action:
                    if st.button(primary_label, type="primary", use_container_width=True, key=f"{key_prefix}__primary"):
                        primary_action()
                if secondary_label and secondary_action:
                    if st.button(secondary_label, use_container_width=True, key=f"{key_prefix}__secondary"):
                        secondary_action()

    @st.cache_data(show_spinner=False)
    def _cached_models(base_url: str, api_key: str) -> List[str]:
        return AIEngine(base_url=base_url).probe_models(api_key)

    def refresh_models():
        st.session_state.groq_model_list = _cached_models(
            st.session_state.groq_base_url,
            st.session_state.groq_api_key,
        ) or []

    def refresh_openai_models():
        st.session_state.openai_model_list = _cached_models(
            st.session_state.openai_base_url,
            st.session_state.openai_api_key,
        ) or []

    def save_app_settings():
        # Merge with existing config to preserve saved data
        data = load_app_config()
        data.update({
            "groq_base_url": st.session_state.groq_base_url,
            "groq_model": st.session_state.groq_model,
            "openai_base_url": st.session_state.openai_base_url,
            "openai_model": st.session_state.openai_model,
            "ui_theme": st.session_state.ui_theme,
            "daily_word_goal": int(st.session_state.daily_word_goal),
            "weekly_sessions_goal": int(st.session_state.weekly_sessions_goal),
            "focus_minutes": int(st.session_state.focus_minutes),
            "activity_log": list(st.session_state.activity_log),
        })
        # Only overwrite API keys when they have a value to avoid
        # clearing previously saved keys.
        for provider, attr in (("groq", "groq_api_key"), ("openai", "openai_api_key")):
            val = (getattr(st.session_state, attr, "") or "").strip()
            if val:
                data[f"{provider}_api_key"] = val
        # Persist connection-tested flags so the warning stays dismissed
        # after a page refresh.
        for flag in ("groq_connection_tested", "openai_connection_tested"):
            data[flag] = bool(st.session_state.get(flag))
        save_app_config(data)
        st.toast("Settings saved.")

    def _today_str() -> str:
        return datetime.date.today().isoformat()

    def _parse_day(day: str) -> Optional[datetime.date]:
        try:
            return datetime.date.fromisoformat(day)
        except ValueError:
            return None

    def _log_activity():
        today = _today_str()
        log = set(st.session_state.activity_log)
        log.add(today)
        st.session_state.activity_log = sorted(log)
        save_app_settings()

    def _weekly_activity_count() -> int:
        today = datetime.date.today()
        cutoff = today - datetime.timedelta(days=6)
        count = 0
        for day in st.session_state.activity_log:
            parsed = _parse_day(day)
            if parsed and parsed >= cutoff:
                count += 1
        return count

    def _activity_streak() -> int:
        if not st.session_state.activity_log:
            return 0
        days = sorted(
            {d for d in (_parse_day(day) for day in st.session_state.activity_log) if d}
        )
        if not days:
            return 0
        streak = 0
        cursor = datetime.date.today()
        day_set = set(days)
        while cursor in day_set:
            streak += 1
            cursor -= datetime.timedelta(days=1)
        return streak

    def _activity_series() -> List[Dict[str, Any]]:
        today = datetime.date.today()
        labels = []
        counts = []
        log_set = set(st.session_state.activity_log)
        for offset in range(6, -1, -1):
            day = today - datetime.timedelta(days=offset)
            labels.append(day.strftime("%a"))
            counts.append(1 if day.isoformat() in log_set else 0)
        return [{"day": label, "sessions": count} for label, count in zip(labels, counts)]

    @st.cache_data(show_spinner=False)
    def _load_recent_projects(active_dir: Optional[str], refresh_token: int) -> List[Dict[str, Any]]:
        if not active_dir or not os.path.exists(active_dir):
            return []
        files = sorted(
            [f for f in os.listdir(active_dir) if f.endswith(".json")],
            key=lambda x: os.path.getmtime(os.path.join(active_dir, x)),
            reverse=True,
        )
        projects = []
        for filename in files:
            full_path = os.path.join(active_dir, filename)
            try:
                with open(full_path, "r", encoding="utf-8") as fh:
                    meta = json.load(fh)
                projects.append({"path": full_path, "meta": meta})
            except Exception:
                logger.warning("Failed to load project metadata: %s", full_path, exc_info=True)
        return projects

    def _bump_projects_refresh() -> None:
        st.session_state.projects_refresh_token += 1

    def _project_snapshot(meta: Dict[str, Any]) -> Dict[str, Any]:
        chapters = meta.get("chapters", {}) or {}
        chapter_list = list(chapters.values())
        word_count = sum(int(c.get("word_count") or 0) for c in chapter_list)
        return {
            "title": meta.get("title") or "Untitled Project",
            "genre": meta.get("genre") or "General Fiction",
            "chapters": len(chapter_list),
            "words": word_count,
            "modified_at": meta.get("last_modified") or meta.get("modified_at"),
        }

    def _random_project_title() -> str:
        adjectives = [
            "Ashen",
            "Verdant",
            "Crimson",
            "Celestial",
            "Obsidian",
            "Luminous",
            "Forgotten",
            "Gilded",
            "Veiled",
            "Hollow",
            "Radiant",
            "Stormbound",
            "Ivory",
            "Eclipsed",
            "Thorned",
            "Mythic",
        ]
        nouns = [
            "Crown",
            "Archive",
            "Sanctum",
            "Labyrinth",
            "Harbor",
            "Citadel",
            "Oath",
            "Chronicle",
            "Constellation",
            "Axiom",
            "Ember",
            "Signal",
            "Throne",
            "Vesper",
            "Pulse",
            "Emissary",
        ]
        suffixes = [
            "of Hollowlight",
            "of the Verdant Sea",
            "of the Last Meridian",
            "of Emberglass",
            "of the Drowned Sky",
            "of Ironfall",
            "of the Crystal District",
            "of Midnight Bloom",
            "of the Sunken Choir",
            "of Starward",
        ]
        return f"The {random.choice(adjectives)} {random.choice(nouns)} {random.choice(suffixes)}"

    def _random_project_genres() -> str:
        genres = [
            "Solarpunk",
            "Mythic Fantasy",
            "Cosmic Horror",
            "Techno-Thriller",
            "Romantic Suspense",
            "Gaslamp Adventure",
            "Urban Fantasy",
            "Dark Academia",
            "Political Intrigue",
            "Epic Fantasy",
            "Noir Mystery",
            "Found Family",
            "Post-Apocalyptic",
            "Speculative Romance",
            "Spy Drama",
            "Weird Western",
        ]
        genre_count = min(4, len(genres))
        picks = random.sample(genres, k=genre_count)
        return " · ".join(picks)

    def test_groq_connection(base_url: str, api_key: str) -> bool:
        headers = {}
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"
        try:
            r = requests.get(
                f"{base_url.rstrip('/')}/models",
                headers=headers,
                timeout=5,
            )
            r.raise_for_status()
            return True
        except Exception:
            return False

    def test_openai_connection(base_url: str, api_key: str) -> bool:
        headers = {}
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"
        try:
            r = requests.get(
                f"{base_url.rstrip('/')}/models",
                headers=headers,
                timeout=5,
            )
            r.raise_for_status()
            return True
        except Exception:
            return False

    def fetch_groq_models(base_url: str, api_key: str) -> tuple[List[str], str]:
        headers = {}
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"
        try:
            r = requests.get(
                f"{base_url.rstrip('/')}/models",
                headers=headers,
                timeout=10,
            )
            r.raise_for_status()
            data = r.json()
            models = [m.get("id") for m in data.get("data", []) if m.get("id")]
            return models, ""
        except Exception as exc:
            return [], str(exc)

    def fetch_openai_models(base_url: str, api_key: str) -> tuple[List[str], str]:
        headers = {}
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"
        try:
            r = requests.get(
                f"{base_url.rstrip('/')}/models",
                headers=headers,
                timeout=10,
            )
            r.raise_for_status()
            data = r.json()
            models = [m.get("id") for m in data.get("data", []) if m.get("id")]
            return models, ""
        except Exception as exc:
            return [], str(exc)

    def test_groq_model(base_url: str, api_key: str, model: str) -> tuple[bool, str]:
        headers = {"Content-Type": "application/json"}
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"
        payload = {
            "model": model,
            "messages": [{"role": "user", "content": "ping"}],
            "max_tokens": 1,
            "temperature": 0,
        }
        try:
            r = requests.post(
                f"{base_url.rstrip('/')}/chat/completions",
                headers=headers,
                json=payload,
                timeout=15,
            )
            r.raise_for_status()
            return True, ""
        except Exception as exc:
            return False, str(exc)

    def test_openai_model(base_url: str, api_key: str, model: str) -> tuple[bool, str]:
        headers = {"Content-Type": "application/json"}
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"
        payload = {
            "model": model,
            "messages": [{"role": "user", "content": "ping"}],
            "max_tokens": 1,
            "temperature": 0,
        }
        try:
            r = requests.post(
                f"{base_url.rstrip('/')}/chat/completions",
                headers=headers,
                json=payload,
                timeout=15,
            )
            r.raise_for_status()
            return True, ""
        except Exception as exc:
            return False, str(exc)

    def extract_entities_ui(text: str, label: str):
        """Scan text for entities and update the World Bible.

        Uses Project.upsert_entity fuzzy matching so that abbreviations, nicknames,
        or slightly different spellings merge into existing entries instead of
        creating duplicates.
        """
        model = get_ai_model()
        raw_text = text or ""
        p = st.session_state.project

        try:
            ents = AnalysisEngine.extract_entities(raw_text, model)
        except Exception:
            logger.warning("Entity extraction failed for %s", label, exc_info=True)
            st.error("Entity scan failed. Please check your AI settings and try again.")
            return
        total_detected = len(ents)
        added = 0
        matched = 0
        flagged = 0
        suggested = 0

        for e in ents:
            name = (e.get("name") or "").strip()
            category = (e.get("category") or "").strip()
            if not name or not category:
                continue

            desc = (e.get("description") or "").strip()
            aliases = e.get("aliases") or []
            try:
                confidence = float(e.get("confidence")) if e.get("confidence") is not None else 0.0
            except (TypeError, ValueError):
                confidence = 0.0

            if confidence < AppConfig.WORLD_BIBLE_CONFIDENCE:
                existing = p.find_entity_match(
                    name,
                    category,
                    aliases=aliases if isinstance(aliases, list) else None,
                )
                if existing and desc:
                    queue_world_bible_suggestion(
                        {
                            "type": "update",
                            "entity_id": existing.id,
                            "name": existing.name,
                            "category": existing.category,
                            "description": desc,
                            "aliases": aliases,
                            "confidence": confidence,
                            "source": label,
                        },
                        project=p,
                    )
                else:
                    queue_world_bible_suggestion(
                        {
                            "type": "new",
                            "name": name,
                            "category": Project._normalize_category(category),
                            "description": desc,
                            "aliases": aliases,
                            "confidence": confidence,
                            "source": label,
                        },
                        project=p,
                    )
                flagged += 1
                continue

            ent, status = p.upsert_entity(
                name,
                category,
                desc,
                aliases=aliases if isinstance(aliases, list) else None,
                allow_merge=False,
                allow_alias=True,
            )
            if ent is None:
                continue

            if status == "created":
                added += 1
            else:
                matched += 1
                if desc:
                    queue_world_bible_suggestion(
                        {
                            "type": "update",
                            "entity_id": ent.id,
                            "name": ent.name,
                            "category": ent.category,
                            "description": desc,
                            "aliases": aliases,
                            "confidence": confidence,
                            "source": label,
                        },
                        project=p,
                    )
                    suggested += 1

        persist_project(p)
        st.session_state["last_entity_scan"] = time.time()

        if added > 0 or matched > 0 or flagged > 0:
            summary = [f"{added} new", f"{matched} existing", f"{flagged} flagged"]
            if suggested:
                summary.append(f"{suggested} suggested updates")
            st.toast(f"World Bible updated ✓ ({', '.join(summary)})", icon="🌍")
        else:
            if total_detected > 0:
                st.toast("Detected entities, but they all matched existing entries.", icon="🤷")
            else:
                st.toast("No entities detected in this text.", icon="🤷")

    query = st.query_params.get("page")
    if query == "privacy":
        render_privacy()
        render_app_footer()
        return
    if query == "terms":
        render_terms()
        render_app_footer()
        return
    if query == "copyright":
        render_copyright()
        render_app_footer()
        return
    if query == "help":
        render_help()
        render_app_footer()
        return

    def render_ai_settings():
        def refresh_all_models() -> None:
            st.cache_data.clear()
            refresh_models()
            refresh_openai_models()
            st.toast("Model list refreshed")

        def save_settings_action() -> None:
            save_app_settings()

        render_page_header(
            "AI Tools",
            "Connect providers, choose models, and validate access.",
            primary_label="💾 Save settings",
            primary_action=save_settings_action,
            secondary_label="↻ Refresh models",
            secondary_action=refresh_all_models,
            tag="Settings",
            key_prefix="ai_header",
        )
        if st.session_state.pop("ai_settings__flash", False):
            st.success("AI Settings opened. Update providers and models below.")

        status_cols = st.columns(3)
        with status_cols[0]:
            st.metric("Groq", "Connected" if st.session_state.groq_api_key else "Missing key")
        with status_cols[1]:
            st.metric("OpenAI", "Connected" if st.session_state.openai_api_key else "Missing key")
        with status_cols[2]:
            st.metric("Active model", st.session_state.groq_model or "Not set")

        provider_cols = st.columns(2)
        with provider_cols[0]:
            with st.container(border=True):
                st.markdown("### 🤖 Groq")
                groq_url = st.text_input("Groq Base URL", value=st.session_state.groq_base_url)
                if groq_url != st.session_state.groq_base_url:
                    st.session_state.groq_base_url = groq_url
                    AppConfig.GROQ_API_URL = groq_url

                groq_key = st.text_input(
                    "Groq API Key",
                    value=_display_ai_key("groq"),
                    type="password",
                    help="Required for Groq cloud models.",
                )
                if groq_key != _display_ai_key("groq"):
                    _set_ai_key("groq", groq_key)

                if st.button("↻ Fetch Groq Models", use_container_width=True):
                    models, error_message = fetch_groq_models(
                        st.session_state.groq_base_url,
                        st.session_state.groq_api_key,
                    )
                    if models:
                        st.session_state.groq_model_list = models
                        st.session_state.groq_model_tests = {}
                        st.toast(f"Loaded {len(models)} models.")
                    else:
                        st.session_state.groq_model_list = []
                        st.session_state.groq_model_tests = {}
                        st.error(f"Model fetch failed. {error_message or 'Check the base URL and key.'}")

                if st.session_state.groq_model_list:
                    models = st.session_state.groq_model_list
                    idx = 0
                    if st.session_state.groq_model in models:
                        idx = models.index(st.session_state.groq_model)
                    groq_model = st.selectbox("Groq Model", models, index=idx)

                    if st.button("🧪 Test All Groq Models", use_container_width=True):
                        results = {}
                        total = len(models)
                        progress = st.progress(0)
                        for i, model_name in enumerate(models, start=1):
                            ok, error_message = test_groq_model(
                                st.session_state.groq_base_url,
                                st.session_state.groq_api_key,
                                model_name,
                            )
                            results[model_name] = "" if ok else error_message
                            progress.progress(i / total)
                        st.session_state.groq_model_tests = results
                        failures = [m for m, err in results.items() if err]
                        if failures:
                            st.warning(f"{len(failures)} models failed. Expand results for details.")
                        else:
                            st.success("All models responded successfully.")

                    if st.session_state.groq_model_tests:
                        with st.expander("Groq model test results", expanded=False):
                            for model_name, error_message in sorted(
                                st.session_state.groq_model_tests.items()
                            ):
                                if error_message:
                                    st.error(f"{model_name}: {error_message}")
                                else:
                                    st.success(f"{model_name}: OK")
                else:
                    groq_model = st.text_input("Groq Model", value=st.session_state.groq_model)

                if groq_model != st.session_state.groq_model:
                    st.session_state.groq_model = groq_model
                    AppConfig.DEFAULT_MODEL = groq_model

                st.markdown(
                    "[Get a free Groq API key](https://console.groq.com/keys) to enable cloud models."
                )
                if not st.session_state.groq_api_key:
                    st.info("No Groq API key yet. Create one above and paste it here to unlock Groq models.")
                if st.button("🔌 Test Groq Connection", use_container_width=True):
                    ok = test_groq_connection(
                        st.session_state.groq_base_url,
                        st.session_state.groq_api_key,
                    )
                    if ok:
                        st.session_state.groq_connection_tested = True
                        st.success("Groq connection OK.")
                    else:
                        st.error("Groq connection failed. Check your base URL and key.")

        with provider_cols[1]:
            with st.container(border=True):
                st.markdown("### ✨ OpenAI")
                openai_url = st.text_input("OpenAI Base URL", value=st.session_state.openai_base_url)
                if openai_url != st.session_state.openai_base_url:
                    st.session_state.openai_base_url = openai_url
                    AppConfig.OPENAI_API_URL = openai_url

                openai_key = st.text_input(
                    "OpenAI API Key",
                    value=_display_ai_key("openai"),
                    type="password",
                    help="Required for OpenAI cloud models.",
                )
                if openai_key != _display_ai_key("openai"):
                    _set_ai_key("openai", openai_key)
                if not st.session_state.openai_api_key:
                    st.info("No OpenAI API key yet. Create one and paste it here to unlock OpenAI models.")

                if st.button("↻ Fetch OpenAI Models", use_container_width=True):
                    models, error_message = fetch_openai_models(
                        st.session_state.openai_base_url,
                        st.session_state.openai_api_key,
                    )
                    if models:
                        st.session_state.openai_model_list = models
                        st.session_state.openai_model_tests = {}
                        st.toast(f"Loaded {len(models)} models.")
                    else:
                        st.session_state.openai_model_list = []
                        st.session_state.openai_model_tests = {}
                        st.error(f"Model fetch failed. {error_message or 'Check the base URL and key.'}")

                if st.session_state.openai_model_list:
                    models = st.session_state.openai_model_list
                    idx = 0
                    if st.session_state.openai_model in models:
                        idx = models.index(st.session_state.openai_model)
                    openai_model = st.selectbox("OpenAI Model", models, index=idx)

                    if st.button("🧪 Test All OpenAI Models", use_container_width=True):
                        results = {}
                        total = len(models)
                        progress = st.progress(0)
                        for i, model_name in enumerate(models, start=1):
                            ok, error_message = test_openai_model(
                                st.session_state.openai_base_url,
                                st.session_state.openai_api_key,
                                model_name,
                            )
                            results[model_name] = "" if ok else error_message
                            progress.progress(i / total)
                        st.session_state.openai_model_tests = results
                        failures = [m for m, err in results.items() if err]
                        if failures:
                            st.warning(f"{len(failures)} models failed. Expand results for details.")
                        else:
                            st.success("All models responded successfully.")

                    if st.session_state.openai_model_tests:
                        with st.expander("OpenAI model test results", expanded=False):
                            for model_name, error_message in sorted(
                                st.session_state.openai_model_tests.items()
                            ):
                                if error_message:
                                    st.error(f"{model_name}: {error_message}")
                                else:
                                    st.success(f"{model_name}: OK")
                else:
                    openai_model = st.text_input("OpenAI Model", value=st.session_state.openai_model)

                if openai_model != st.session_state.openai_model:
                    st.session_state.openai_model = openai_model
                    AppConfig.OPENAI_MODEL = openai_model

                st.markdown(
                    "[Create an OpenAI account](https://platform.openai.com/api-keys) to get an API key."
                )
                if st.button("🔌 Test OpenAI Connection", use_container_width=True):
                    ok = test_openai_connection(
                        st.session_state.openai_base_url,
                        st.session_state.openai_api_key,
                    )
                    if ok:
                        st.session_state.openai_connection_tested = True
                        st.success("OpenAI connection OK.")
                    else:
                        st.error("OpenAI connection failed. Check your base URL and key.")

        with st.container(border=True):
            st.markdown("### ✅ Actions")
            action_cols = st.columns(4)
            with action_cols[0]:
                st.checkbox("Auto-save", key="auto_save")
            with action_cols[1]:
                if st.button("↻ Refresh Groq Models", use_container_width=True):
                    st.cache_data.clear()
                    refresh_models()
                    st.toast("Model list refreshed")
            with action_cols[2]:
                if st.button("↻ Refresh OpenAI Models", use_container_width=True):
                    st.cache_data.clear()
                    refresh_openai_models()
                    st.toast("OpenAI model list refreshed")
            with action_cols[3]:
                if st.button("💾 Save AI Settings", use_container_width=True):
                    save_app_settings()

    def render_legal_redirect():
        render_page_header(
            "Legal",
            "Review policies, IP guidance, and acceptable use.",
            tag="Policies",
            key_prefix="legal_header",
        )
        st.info("Open the Legal Hub for full policies and documentation.")
        if st.button("Open Legal Hub", use_container_width=True):
            st.session_state.page = "legal"
            st.rerun()

    with st.sidebar:
        with key_scope("sidebar"):
            sidebar_logo_b64 = asset_base64("mantis_logo_trans.png")
            sidebar_logo_html = (
                f'<img src="data:image/png;base64,{sidebar_logo_b64}" alt="MANTIS logo" />'
                if sidebar_logo_b64
                else '<span class="mantis-logo-fallback">MANTIS</span>'
            )
            st.html(
                f"""
            <div class="mantis-sidebar-brand">
                <div class="mantis-sidebar-logo">
                    {sidebar_logo_html}
                </div>
                <div>
                    <div class="mantis-sidebar-title">MANTIS Studio — v{AppConfig.VERSION}</div>
                    <div class="mantis-sidebar-sub">Modular AI Narrative Text Intelligence System</div>
                </div>
            </div>
            """,
            )

            st.markdown("---")

            st.markdown("### 🎨 Appearance")
            st.selectbox("Theme", ["Dark", "Light"], key="ui_theme")
            st.divider()

            if st.session_state.project:
                p = st.session_state.project
                st.markdown("### 📖 Project")
                st.caption(p.title)
                projects_dir = get_active_projects_dir()
                if projects_dir:
                    st.caption(f"🗂 Projects folder: `{projects_dir}`")
                st.caption(f"📚 Total words: {p.get_total_word_count()}")

            st.divider()
            st.markdown("### 🧭 Navigation")
            st.caption("Dashboard • Projects • Editor • World Bible • Memory • Insights • Export")

            nav_labels, pmap = router.get_nav_config(bool(st.session_state.project))
            current_page = st.session_state.page
            reverse_map = {v: k for k, v in pmap.items()}
            current_label = reverse_map.get(current_page, "Dashboard")
            try:
                current_index = nav_labels.index(current_label)
            except ValueError:
                current_index = 0
            nav = st.radio(
                "Navigation",
                nav_labels,
                index=current_index,
                label_visibility="collapsed",
            )
            next_page = pmap[nav]
            if next_page != st.session_state.page:
                if next_page == "memory":
                    st.session_state.world_focus_tab = "Memory"
                    st.session_state.page = "world"
                elif next_page == "insights":
                    st.session_state.world_focus_tab = "Insights"
                    st.session_state.page = "world"
                elif next_page == "export":
                    st.session_state.page = "export"
                elif next_page == "legal":
                    st.session_state.page = "legal"
                else:
                    st.session_state.page = next_page
                st.rerun()

            if st.session_state.project:
                st.divider()

                cA, cB = st.columns(2)
                with cA:
                    if st.button("💾 Save", type="primary", use_container_width=True):
                        if persist_project(p, action="save"):
                            st.toast("Saved")
                with cB:
                    if st.button("✖ Close", use_container_width=True):
                        save_p()
                        st.session_state.project = None
                        st.session_state.page = "home"
                        st.rerun()
            else:
                st.info("No project loaded.")

    def render_home():
        active_dir = get_active_projects_dir()
        recent_projects = _load_recent_projects(active_dir, st.session_state.projects_refresh_token)
        has_project = bool(recent_projects)


        banner_bytes = load_asset_bytes("mantis_banner_dark.png")
        st.html('<div class="mantis-banner">')
        if banner_bytes:
            st.image(banner_bytes, use_container_width=True)
        else:
            st.markdown("## MANTIS Studio")
        st.html("</div>")

        has_outline = any((p["meta"].get("outline") or "").strip() for p in recent_projects)
        has_chapter = any(
            (c.get("word_count") or 0) > 0
            for p in recent_projects
            for c in (p["meta"].get("chapters") or {}).values()
        )

        active_project = st.session_state.project
        recent_snapshot = _project_snapshot(recent_projects[0]["meta"]) if recent_projects else None

        project_title = (
            (active_project.title if active_project else None)
            or (recent_snapshot or {}).get("title")
            or "Your next story"
        )
        weekly_goal = max(1, int(st.session_state.weekly_sessions_goal))
        weekly_count = _weekly_activity_count()
        canon_icon, canon_label = get_canon_health()
        latest_chapter_label = "You last worked on Chapter — · recently"
        latest_chapter_index = None
        latest_chapter_id = None
        latest_ts = None

        if active_project and getattr(active_project, "chapters", None):
            ch = max(
                active_project.chapters.values(),
                key=lambda c: (c.modified_at or c.created_at or 0),
            )
            latest_ts = ch.modified_at or ch.created_at
            latest_chapter_index = ch.index
            latest_chapter_id = ch.id
            latest_chapter_label = f"Latest: Chapter {ch.index} — {ch.title}"

        primary_label = "✨ Start your story"
        primary_target = "projects"
        if canon_icon == "🔴":
            primary_label = "🛠 Fix story issues"
            primary_target = "world"
        elif has_chapter and latest_chapter_index:
            primary_label = f"▶ Continue Chapter {latest_chapter_index}"
            primary_target = "chapters"
        elif has_outline:
            primary_label = "📝 Build your outline"
            primary_target = "outline"

        def open_recent_project(target: str, focus_tab: Optional[str] = None) -> None:
            if not recent_projects and not st.session_state.project:
                st.session_state.page = "projects"
                st.toast("Create or import a project to unlock this module.")
                st.rerun()
            if recent_projects and not st.session_state.project:
                loaded = load_project_safe(recent_projects[0]["path"], context="recent project")
                if not loaded:
                    st.session_state.page = "projects"
                    st.toast("Select a project to continue.")
                    st.rerun()
                st.session_state.project = loaded
            if focus_tab:
                st.session_state.world_focus_tab = focus_tab
            st.session_state.page = target
            st.rerun()

        def open_export() -> None:
            export_path = None
            if st.session_state.project and st.session_state.project.filepath:
                export_path = st.session_state.project.filepath
            elif recent_projects:
                export_path = recent_projects[0]["path"]
            if export_path:
                st.session_state.export_project_path = export_path
                st.session_state.page = "export"
                st.rerun()
            else:
                st.session_state.page = "export"
                st.toast("Select a project to export.")
                st.rerun()

        def open_ai_settings() -> None:
            st.session_state.ai_settings__flash = True
            st.session_state.page = "ai"
            st.rerun()

        def open_primary_cta() -> None:
            if primary_target == "chapters" and latest_chapter_id:
                st.session_state.curr_chap_id = latest_chapter_id
            open_recent_project(primary_target)

        def open_new_project() -> None:
            st.session_state.page = "projects"
            st.rerun()

        render_page_header(
            "Dashboard",
            "Your studio cockpit for progress, projects, and next steps.",
            primary_label=primary_label,
            primary_action=open_primary_cta,
            secondary_label="➕ New project",
            secondary_action=open_new_project,
            tag="Workspace",
            key_prefix="dashboard_header",
        )

        hero_logo_bytes = load_asset_bytes("mantis_logo_trans.png")
        with st.container(border=True):
            hero_cols = st.columns([2.4, 1])
            with hero_cols[0]:
                logo_col, text_col = st.columns([0.18, 0.82])
                with logo_col:
                    if hero_logo_bytes:
                        st.image(hero_logo_bytes, width=64)
                    else:
                        st.markdown("### M")
                with text_col:
                    st.markdown("### MANTIS Studio")
                    st.markdown("#### About MANTIS")
                    st.markdown("**A premium command deck for storytellers.**")
                    st.markdown(
                        """
                        - AI-assisted drafting, summaries, and rewrite presets
                        - World Bible to keep canon, characters, and lore aligned
                        - Memory + insights to track momentum and continuity
                        - Clean markdown exports for editors and collaborators
                        """
                    )
                    st.caption("Built for writers who want clarity, speed, and control.")
                    if st.button("Learn more", key="dashboard__about_learn_more"):
                        open_legal_page()
            with hero_cols[1]:
                st.html(
                    f"""
                    <div style="display:flex; gap:8px; justify-content:flex-end; flex-wrap:wrap;">
                        <span class="mantis-pill">Workspace</span>
                        <span class="mantis-pill">v{AppConfig.VERSION}</span>
                    </div>
                    """,
                )

        header_cols = st.columns([2.2, 1])
        with header_cols[0]:
            with card("Current focus", "Suggested next step based on your latest activity."):
                st.markdown(f"## {project_title}")
                st.caption(latest_chapter_label)
                if st.button(primary_label, type="primary", use_container_width=True):
                    if primary_target == "chapters" and latest_chapter_id:
                        st.session_state.curr_chap_id = latest_chapter_id
                    open_recent_project(primary_target)
                action_row = st.columns(2)
                with action_row[0]:
                    if st.button("📂 Resume project", use_container_width=True, disabled=not recent_projects):
                        open_recent_project("chapters")
                with action_row[1]:
                    if st.button("🧭 New project", use_container_width=True):
                        st.session_state.page = "projects"
                        st.rerun()

        with header_cols[1]:
            with card("Workspace snapshot"):
                st.markdown("#### Project status")
                k1, k2 = st.columns(2)
                with k1:
                    stat_tile("Active projects", str(len(recent_projects)), icon="📁")
                with k2:
                    stat_tile("Latest genre", (recent_snapshot or {}).get("genre", "—"), icon="🏷️")
                k3, k4 = st.columns(2)
                with k3:
                    stat_tile("Weekly sessions", f"{weekly_count}/{weekly_goal}", icon="🗓️")
                with k4:
                    stat_tile("Writing streak", f"{_activity_streak()} days", icon="🔥")
                st.caption(f"Canon health: {canon_icon} {canon_label}.")

        section_header("Quick actions", "Jump straight into your most-used tools.")
        quick_row_one = st.columns(3)
        with quick_row_one[0]:
            if action_card(
                "✍️ Editor",
                "Draft chapters and summaries.",
                help_text="Open the chapter editor.",
                button_type="secondary",
            ):
                open_recent_project("chapters")
        with quick_row_one[1]:
            if action_card(
                "📝 Outline",
                "Plan beats, arcs, and chapter flow.",
                button_type="secondary",
            ):
                open_recent_project("outline")
        with quick_row_one[2]:
            if action_card(
                "🌍 World Bible",
                "Characters, places, factions, lore.",
                button_type="secondary",
            ):
                open_recent_project("world")

        quick_row_two = st.columns(3)
        with quick_row_two[0]:
            if action_card(
                "🧠 Memory",
                "Hard canon rules and guidelines.",
                button_type="secondary",
            ):
                open_recent_project("world", focus_tab="Memory")
        with quick_row_two[1]:
            if action_card(
                "📊 Insights",
                "Canon health and analytics.",
                button_type="secondary",
            ):
                open_recent_project("world", focus_tab="Insights")
        with quick_row_two[2]:
            if action_card(
                "⬇️ Export",
                "Download your project as markdown.",
                button_label="Export",
                button_type="secondary",
            ):
                open_export()

        with st.container(border=True):
            st.markdown("#### My projects")
            st.caption("Select a project to open and pick up where you left off.")
            if not recent_projects:
                st.info("📭 No projects yet. Create one to get started.")
            else:
                for project_entry in recent_projects[:5]:
                    meta = project_entry.get("meta", {})
                    title = meta.get("title") or os.path.basename(project_entry.get("path", "Untitled"))
                    genre = meta.get("genre") or "—"
                    row = st.columns([2.2, 1, 1])
                    with row[0]:
                        if st.button(f"📂 {title}", use_container_width=True, key=f"dash_proj_{project_entry.get('path', '')}"):
                            loaded = load_project_safe(project_entry["path"], context="project")
                            if loaded:
                                st.session_state.project = loaded
                                st.session_state.page = "chapters"
                                st.rerun()
                    with row[1]:
                        st.caption(genre)
                    with row[2]:
                        if st.button("Open", use_container_width=True, key=f"dash_open_{project_entry.get('path', '')}"):
                            loaded = load_project_safe(project_entry["path"], context="project")
                            if loaded:
                                st.session_state.project = loaded
                                st.session_state.page = "chapters"
                                st.rerun()

        with st.container(border=True):
            st.markdown("#### Utilities")
            st.caption("Compact shortcuts to settings, docs, and policies.")
            s1, s2 = st.columns(2)
            with s1:
                st.markdown("**AI Settings**")
                st.caption("Manage providers, models, and API access.")
                if st.button(
                    "⚙️ AI Settings",
                    key="dashboard__utilities_ai_settings",
                    use_container_width=True,
                    help="Jump to AI Tools to configure Groq/OpenAI.",
                ):
                    open_ai_settings()
            with s2:
                st.markdown("**Help Docs**")
                st.caption("Guides, README notes, and updates.")
                st.link_button(
                    "📖 Help Docs",
                    "https://github.com/bigmanjer/Mantis-Studio",
                    use_container_width=True,
                    help="Open the project documentation in a new tab.",
                )

        if not st.session_state.groq_api_key or not st.session_state.openai_api_key:
            with card("🔑 Connect your AI providers", "Unlock generation, summaries, and entity tools with API access."):
                cta_left, cta_right = st.columns(2)
                with cta_left:
                    st.link_button("Create Groq Account", "https://console.groq.com/keys", use_container_width=True)
                with cta_right:
                    st.link_button(
                        "Create OpenAI Account",
                        "https://platform.openai.com/api-keys",
                        use_container_width=True,
                    )
        else:
            with card("✅ AI providers connected", "Your AI providers are configured and ready to use."):
                cta_left, cta_right = st.columns(2)
                with cta_left:
                    if st.button("⚙️ Manage AI Settings", use_container_width=True, key="dashboard__ai_connected_settings"):
                        open_ai_settings()
                with cta_right:
                    st.caption("Groq and OpenAI are active.")


    def render_projects():
        active_dir = get_active_projects_dir()
        recent_projects = _load_recent_projects(active_dir, st.session_state.projects_refresh_token)

        def open_latest_project() -> None:
            if not recent_projects:
                st.toast("Complete the form below to create your first project.")
                return
            loaded = load_project_safe(recent_projects[0]["path"], context="recent project")
            if not loaded:
                return
            st.session_state.project = loaded
            st.session_state.page = "chapters"
            st.session_state.first_run = False
            st.rerun()

        primary_label = "Open latest project" if recent_projects else "Create your first project"
        render_page_header(
            "Projects",
            "Create, import, and manage your story worlds.",
            primary_label=primary_label,
            primary_action=open_latest_project,
            secondary_label="⬇️ Import draft",
            secondary_action=lambda: st.toast("Use the importer below to bring in .txt or .md files."),
            tag="Workspace",
            key_prefix="projects_header",
        )

        from app.utils.helpers import ai_connection_warning
        ai_connection_warning(st)

        section_header(
            "Start a new project",
            "Set a title, genre, and author details to build your base.",
        )
        with st.container(border=True):
            with st.form("new_project_form", clear_on_submit=False):
                c1, c2 = st.columns([2, 1])
                with c1:
                    t = st.text_input("Title", placeholder="e.g., The Chronicle of Ash")
                with c2:
                    g = st.text_input("Genre", placeholder="e.g., Dark Fantasy, Sci-Fi Noir")
                a = st.text_input("Author (optional)", placeholder="Your name")
                submitted = st.form_submit_button("🚀 Initialize Project", type="primary", use_container_width=True)
                if submitted:
                    if not t:
                        t = _random_project_title()
                    if not g:
                        g = _random_project_genres()
                    p = Project.create(
                        t,
                        author=a,
                        genre=g,
                        storage_dir=get_active_projects_dir(),
                    )
                    persist_project(p, action="create_project")
                    _bump_projects_refresh()
                    st.session_state.project = p
                    st.session_state.page = "outline"
                    st.session_state.first_run = False
                    st.rerun()

        section_header(
            "Import an existing draft",
            "Upload a .txt or .md file to split into chapters.",
        )
        with st.container(border=True):
            uf = st.file_uploader("Upload file", type=["txt", "md"])
            if uf:
                max_bytes = AppConfig.MAX_UPLOAD_MB * 1024 * 1024
                uf_size = getattr(uf, "size", None)
                if uf_size and uf_size > max_bytes:
                    st.error(
                        f"File too large. Max size is {AppConfig.MAX_UPLOAD_MB} MB."
                    )
                else:
                    txt = uf.read().decode("utf-8", errors="replace")
                    if st.button("Import & Analyze", use_container_width=True):
                        try:
                            p = Project.create("Imported Project", storage_dir=get_active_projects_dir())
                            p.import_text_file(txt)
                            if AppConfig.GROQ_API_KEY and get_ai_model():
                                with st.spinner("Reviewing document and generating outline..."):
                                    p.outline = StoryEngine.reverse_engineer_outline(p, get_ai_model())
                            else:
                                st.warning("Add a Groq API key and model to auto-generate an outline.")
                            persist_project(p, action="create_project")
                        except Exception:
                            logger.warning("Import failed for uploaded draft", exc_info=True)
                            st.error("Import failed. Please check the file and try again.")
                            return
                        _bump_projects_refresh()
                        st.session_state.project = p
                        st.session_state.page = "outline"
                        st.session_state.first_run = False
                        st.rerun()

        section_header(
            "Your projects",
            "Open, export, or clean up older drafts.",
        )
        with st.container(border=True):
            if not recent_projects:
                st.info("📭 No projects yet. Start a new project above to get going.")
            else:
                for project_entry in recent_projects[:30]:
                    full = project_entry["path"]
                    try:
                        meta = project_entry["meta"]
                        filename = os.path.basename(full)
                        title = meta.get("title") or filename
                        genre = meta.get("genre") or ""
                        row1, row2, row3, row4 = st.columns([5, 2, 1.5, 1])
                        with row1:
                            if st.button(f"📂 {title}", key=f"open_{full}", use_container_width=True):
                                loaded = load_project_safe(full, context="project")
                                if loaded:
                                    st.session_state.project = loaded
                                    st.session_state.page = "chapters"
                                    st.session_state.first_run = False
                                    st.rerun()
                        with row2:
                            st.caption(genre)
                        with row3:
                            if st.button("⬇️ Export", key=f"export_{full}", use_container_width=True):
                                st.session_state.export_project_path = full
                                st.rerun()
                        with row4:
                            if st.button("🗑", key=f"del_{full}", use_container_width=True):
                                st.session_state.delete_project_path = full
                                st.session_state.delete_project_title = title
                    except Exception:
                        logger.warning("Failed to load project metadata: %s", full, exc_info=True)

        if st.session_state.delete_project_path:
            with st.container(border=True):
                title = st.session_state.delete_project_title or "this project"
                st.warning(f"Delete **{title}**? This cannot be undone.")
                d1, d2 = st.columns(2)
                with d1:
                    if st.button("🗑 Confirm delete", type="primary", use_container_width=True):
                        Project.delete_file(st.session_state.delete_project_path)
                        if (
                            st.session_state.project
                            and st.session_state.project.filepath == st.session_state.delete_project_path
                        ):
                            st.session_state.project = None
                            st.session_state.page = "projects"
                        st.session_state.delete_project_path = None
                        st.session_state.delete_project_title = None
                        _bump_projects_refresh()
                        st.toast("Project deleted.")
                        st.rerun()
                with d2:
                    if st.button("Cancel", use_container_width=True):
                        st.session_state.delete_project_path = None
                        st.session_state.delete_project_title = None
                        st.rerun()

        export_path = st.session_state.get("export_project_path")
        if export_path:
            with st.container(border=True):
                try:
                    export_project = Project.load(export_path)
                except Exception:
                    st.error("Export failed. Unable to load project.")
                    st.session_state.export_project_path = None
                else:
                    st.markdown("### Export Project")
                    st.caption("Download a single markdown file containing outline, world bible, and chapters.")
                    st.download_button(
                        "⬇️ Download .md",
                        project_to_markdown(export_project),
                        file_name=f"{export_project.title}.md",
                        use_container_width=True,
                    )
                    if st.button("Close export", use_container_width=True):
                        st.session_state.export_project_path = None
                        st.rerun()


    def render_export():
        render_page_header(
            "Export",
            "Export your project as markdown for editors or collaborators.",
            tag="Export",
            key_prefix="export_header",
        )

        export_project = None
        export_path = st.session_state.get("export_project_path")
        if export_path:
            try:
                export_project = Project.load(export_path)
            except Exception:
                st.error("Export failed. Unable to load project.")
                st.session_state.export_project_path = None
                return
        elif st.session_state.project:
            export_project = st.session_state.project
            if not export_project.filepath:
                export_project.save()

        if not export_project:
            st.info("No project selected for export yet.")
            return

        with st.container(border=True):
            st.markdown(f"### {export_project.title}")
            st.caption("Download a single markdown file containing outline, world bible, and chapters.")
            st.download_button(
                "⬇️ Download .md",
                project_to_markdown(export_project),
                file_name=f"{export_project.title}.md",
                use_container_width=True,
            )

    def render_outline():
        p = st.session_state.project
        if not p:
            with st.container(border=True):
                st.info("📭 No project loaded. Create or open a project to edit an outline.")
                if st.button("Go to Projects", use_container_width=True):
                    st.session_state.page = "projects"
                    st.rerun()
            return
        def save_outline_action() -> None:
            if persist_project(p, action="save"):
                st.toast("Outline saved.")

        def scan_outline_action() -> None:
            extract_entities_ui(p.outline or "", "Outline")

        render_page_header(
            "Outline",
            "Your blueprint. Generate structure, scan entities, and keep the story plan here.",
            primary_label="💾 Save outline",
            primary_action=save_outline_action,
            secondary_label="🔍 Scan entities",
            secondary_action=scan_outline_action,
            tag="Project",
            key_prefix="outline_header",
        )

        # Keep the outline editor widget in sync when switching projects/pages
        if st.session_state.get("out_txt_project_id") != p.id:
            st.session_state["out_txt_project_id"] = p.id
            st.session_state["_outline_sync"] = p.outline or ""  # apply on next rerun before widget renders

        # If AI updated the outline this run, apply it BEFORE the text_area is created.
        if st.session_state.get("_outline_sync") is not None:
            st.session_state["out_txt"] = st.session_state.pop("_outline_sync")

        with st.container(border=True):
            top1, top2, top3 = st.columns([2.2, 1.1, 1])
            with top1:
                new_title = st.text_input("Project Title", p.title)
                if new_title != p.title:
                    p.title = new_title
                    save_p()
            with top2:
                new_genre = st.text_input("Genre", p.genre, placeholder="e.g., Dark Fantasy")
                if new_genre != p.genre:
                    p.genre = new_genre
                    save_p()
            with top3:
                if st.button("💾 Save Project", type="primary", use_container_width=True):
                    if persist_project(p, action="save"):
                        st.toast("Saved")

        left, right = st.columns([2.1, 1])

        # Placeholder for streaming AI-generated outline; lives below the editor, like chapters.
        outline_stream_ph = st.empty()

        with left:
            with st.container(border=True):
                st.markdown("### 🧩 Blueprint")
                val = st.text_area("Plot Outline", p.outline, height=560, key="out_txt", label_visibility="collapsed")
                if val != p.outline:
                    p.outline = val
                    save_p()

                if st.button("💾 Save Outline", use_container_width=True):
                    if persist_project(p, action="save"):
                        # Automatically scan entities on save so World Bible stays in sync.
                        extract_entities_ui(p.outline or "", "Outline")
                        st.toast("Outline Saved & Entities Scanned")

        with right:
            with st.container(border=True):
                st.markdown("### 🏗️ Architect (AI)")
                st.caption("Generate a chapter-by-chapter outline and append it to your blueprint.")

                chaps = st.number_input("Chapters", 1, 50, 12)
                if st.button("✨ Generate Structure", type="primary", use_container_width=True):
                    # use outline_stream_ph defined above
                    full = ""
                    prompt = (
                        f"Write a detailed {chaps}-chapter outline for a {p.genre} novel: {p.title}. "
                        "Use structure: Chapter X: [Title] - [Summary]."
                    )
                    for chunk in AIEngine().generate_stream(prompt, get_ai_model()):
                        full += chunk
                        outline_stream_ph.markdown(full)

                    if full.strip():
                        new_outline = (((p.outline or "").rstrip() + "\n\n" + full.strip()).strip())
                        p.outline = new_outline
                        st.session_state["_outline_sync"] = new_outline  # apply on next rerun before widget renders
                        save_p()
                        st.rerun()

    def build_expander_label(base: str, suffix: Optional[str] = None) -> str:
        if suffix:
            return f"{base} · {suffix}"
        return base

    def render_world():
        p = st.session_state.project
        if not p:
            with st.container(border=True):
                st.info("📭 No project loaded. Open or create a project to access the World Bible.")
                if st.button("Go to Projects", use_container_width=True):
                    st.session_state.page = "projects"
                    st.rerun()
            return
        def open_add_entity() -> None:
            tab_label = st.session_state.get("world_tabs") or "Characters"
            category_map = {
                "Characters": "Character",
                "Locations": "Location",
                "Factions": "Faction",
                "Lore": "Lore",
            }
            category = category_map.get(tab_label, "Character")
            st.session_state[f"add_open_{category}"] = True
            st.rerun()

        render_page_header(
            "World Bible",
            "Track canonical characters, locations, factions, and lore.",
            primary_label="➕ Add entity",
            primary_action=open_add_entity,
            secondary_label="🔍 Run scan",
            secondary_action=lambda: extract_entities_ui(p.outline or "", "Outline"),
            tag="Canon",
            key_prefix="world_header",
        )

        st.html(
            """
            <style>
            .world-overview-card {
                padding: 14px 18px;
                border-radius: 18px;
                background: var(--mantis-surface);
                border: 1px solid var(--mantis-card-border);
            }
            .world-pill {
                display: inline-flex;
                align-items: center;
                gap: 6px;
                padding: 6px 12px;
                border-radius: 999px;
                font-size: 0.85rem;
                font-weight: 600;
                border: 1px solid var(--mantis-primary-border);
                background: var(--mantis-accent-soft);
            }
            .world-pill.good {
                border-color: rgba(34,197,94,0.45);
                background: rgba(34,197,94,0.16);
            }
            .world-pill.warn {
                border-color: rgba(245,158,11,0.4);
                background: rgba(245,158,11,0.16);
            }
            .world-pill.risk {
                border-color: rgba(239,68,68,0.45);
                background: rgba(239,68,68,0.16);
            }
            .world-card {
                padding: 14px 18px;
                border-radius: 18px;
                background: var(--mantis-surface);
                border: 1px solid var(--mantis-card-border);
                box-shadow: 0 10px 22px rgba(15, 23, 42, 0.06);
            }
            .world-card.highlight {
                border-color: rgba(245,158,11,0.6);
                box-shadow: 0 12px 24px rgba(245,158,11,0.18);
            }
            .world-card-header {
                display: flex;
                align-items: center;
                justify-content: space-between;
                gap: 14px;
            }
            .world-card-title {
                display: flex;
                align-items: center;
                gap: 10px;
                font-size: 1.05rem;
                font-weight: 600;
            }
            .world-card-meta {
                display: flex;
                align-items: center;
                gap: 10px;
                font-size: 0.85rem;
                color: var(--mantis-muted);
            }
            .world-badge {
                padding: 4px 10px;
                border-radius: 999px;
                background: var(--mantis-accent-soft);
                border: 1px solid var(--mantis-primary-border);
                color: var(--mantis-text);
                font-weight: 600;
                text-transform: uppercase;
                letter-spacing: 0.06em;
                font-size: 0.65rem;
            }
            .world-card-actions {
                display: flex;
                align-items: center;
                gap: 10px;
            }
            .world-card-metric {
                font-weight: 600;
                color: var(--mantis-text);
            }
            </style>
            """,
        )

        entries = list(p.world_db.values())
        chapters = p.get_ordered_chapters()
        chapter_texts = [(c, (c.content or "")) for c in chapters]
        chapter_texts_lower = [(c, text.lower()) for c, text in chapter_texts]

        def _count_mentions(aliases: List[str], text: str) -> int:
            total = 0
            for alias in aliases:
                alias_clean = (alias or "").strip()
                if not alias_clean:
                    continue
                pattern = rf"\\b{re.escape(alias_clean.lower())}\\b"
                total += len(re.findall(pattern, text))
            return total

        mention_counts: Dict[str, int] = {}
        mention_refs: Dict[str, List[Chapter]] = {}
        for ent in entries:
            aliases = [ent.name] + (ent.aliases or [])
            total_hits = 0
            hit_chapters = []
            for chap, lower_text in chapter_texts_lower:
                hits = _count_mentions(aliases, lower_text)
                if hits:
                    hit_chapters.append(chap)
                total_hits += hits
            mention_counts[ent.id] = total_hits
            mention_refs[ent.id] = hit_chapters

        orphaned_ids = {eid for eid, count in mention_counts.items() if count == 0}
        under_described_ids = {
            e.id for e in entries if len((e.description or "").strip()) < 30
        }
        normalized_name_map: Dict[str, List[str]] = {}
        for ent in entries:
            normalized = Project._normalize_entity_name(ent.name)
            if not normalized:
                continue
            normalized_name_map.setdefault(normalized, []).append(ent.id)
        collision_ids = {
            ent_id
            for ent_ids in normalized_name_map.values()
            if len(ent_ids) > 1
            for ent_id in ent_ids
        }
        flagged_entity_ids = orphaned_ids | under_described_ids | collision_ids

        locked_entities = [
            e for e in entries if "locked" in (e.tags or "").lower()
        ]
        last_scan_ts = st.session_state.get("last_entity_scan") or p.last_modified
        canon_icon, canon_label = get_canon_health()
        canon_class = "good"
        if canon_icon == "🟡":
            canon_class = "warn"
        elif canon_icon == "🔴":
            canon_class = "risk"

        with card("World overview", "Live status of your canon database."):
            top_cols = st.columns([1, 1, 1, 1, 1.2])
            with top_cols[0]:
                stat_tile("Total entities", str(len(entries)), icon="📘")
            with top_cols[1]:
                stat_tile("Orphaned", str(len(orphaned_ids)), icon="🛰️")
            with top_cols[2]:
                stat_tile("Locked", str(len(locked_entities)), icon="🔒")
            with top_cols[3]:
                stat_tile(
                    "Last scan",
                    time.strftime("%Y-%m-%d %H:%M", time.localtime(last_scan_ts)),
                    icon="🕒",
                )
            with top_cols[4]:
                stat_tile("Canon health", f"{canon_icon} {canon_label}", icon="✅")

        with card("Search & filters", "Refine by status, recency, or canon risk."):
            f1, f2, f3, f4 = st.columns([2.2, 1, 1, 1])
            with f1:
                if st.session_state.get("world_search_pending"):
                    st.session_state["world_search"] = st.session_state.pop("world_search_pending")
                query = st.text_input(
                    "Search",
                    placeholder="Type a name or alias to filter...",
                    key="world_search",
                )
            with f2:
                show_orphaned = st.checkbox("Orphaned only", key="world_filter_orphaned")
            with f3:
                show_canon_risk = st.checkbox("Canon risk only", key="world_filter_risk")
            with f4:
                show_recent = st.checkbox("Recently added", key="world_filter_recent")

        tab_options = ["Characters", "Locations", "Factions", "Lore", "Memory", "Insights"]
        focus_tab = st.session_state.pop("world_focus_tab", None)
        if focus_tab not in tab_options:
            focus_tab = None
        default_tab = focus_tab or st.session_state.get("world_tabs", tab_options[0])
        if default_tab not in tab_options:
            default_tab = tab_options[0]
        selected_tab = st.radio(
            "World Bible sections",
            tab_options,
            index=tab_options.index(default_tab),
            horizontal=True,
            key="world_tabs",
        )

        review_queue = st.session_state.get("world_bible_review", [])
        if review_queue:
            with card("🔍 Review AI Suggestions", "AI suggestions are queued for review. Apply to update canon."):
                for idx, item in enumerate(list(review_queue)):
                    stype = item.get("type", "new")
                    label = f"{item.get('name', 'Unnamed')} • {item.get('category', 'Lore')}"
                    if stype == "update":
                        label = f"🔄 {label}"
                    elif stype == "alias_only":
                        label = f"🏷️ {label}"
                    else:
                        label = f"🆕 {label}"
                    expander_label = build_expander_label(label, str(idx))
                    with st.expander(expander_label):
                        type_labels = {"update": "Update Existing", "alias_only": "Add Aliases", "new": "New Entry"}
                        st.markdown(f"**Action:** {type_labels.get(stype, stype.title())}")
                        if item.get("match_name"):
                            st.markdown(f"**Matches:** {item['match_name']}")
                        confidence = item.get("confidence")
                        if confidence is not None:
                            st.markdown(f"**Confidence:** {confidence:.2f}")
                        source = item.get("source")
                        if source:
                            st.markdown(f"**Source:** {source}")
                        if item.get("reason"):
                            st.info(item["reason"])
                        novel_bullets = item.get("novel_bullets") or []
                        if novel_bullets:
                            st.markdown("**New details to add:**")
                            for b in novel_bullets:
                                st.markdown(f"- {b}")
                        elif item.get("description"):
                            st.markdown("**Suggested Notes**")
                            st.write(item.get("description"))
                        novel_aliases = item.get("novel_aliases") or []
                        if novel_aliases:
                            st.markdown(f"**New aliases:** {', '.join(novel_aliases)}")
                        elif item.get("aliases"):
                            st.markdown(f"**Aliases:** {', '.join(item.get('aliases') or [])}")

                        c1, c2 = st.columns(2)
                        with c1:
                            if st.button("✅ Apply", key=f"apply_suggestion_{idx}", use_container_width=True):
                                from app.services.world_bible_merge import apply_suggestion as _apply_suggestion
                                applied_ent, _action = _apply_suggestion(p, item)
                                # Clear cached widget values so the UI
                                # reflects the updated description/aliases
                                # on the next rerun.
                                if applied_ent is not None:
                                    st.session_state.pop(f"desc_{applied_ent.id}", None)
                                    st.session_state.pop(f"aliases_{applied_ent.id}", None)
                                review_queue.pop(idx)
                                st.session_state["world_bible_review"] = review_queue
                                persist_project(p)
                                st.toast("World Bible updated.")
                                st.rerun()
                        with c2:
                            if st.button("🗑 Ignore", key=f"ignore_suggestion_{idx}", use_container_width=True):
                                review_queue.pop(idx)
                                st.session_state["world_bible_review"] = review_queue
                                st.toast("Suggestion removed.")
                                st.rerun()

        focus_entity = st.session_state.get("world_focus_entity")
        recent_cutoff = time.time() - (7 * 86400)

        def render_cat(category: str):
            with card():
                top = st.columns([1, 1.2, 1])
                with top[0]:
                    st.markdown(f"### {category}")
                with top[2]:
                    if st.button(f"➕ Add {category}", use_container_width=True):
                        st.session_state[f"add_open_{category}"] = True

                if st.session_state.get(f"add_open_{category}", False):
                    with st.form(f"add_{category}"):
                        cat_slug = re.sub(r"[^a-z0-9]+", "_", category.lower()).strip("_")
                        n = st.text_input("Name", key=f"add_{cat_slug}_name")
                        d = st.text_area("Description", key=f"add_{cat_slug}_desc")
                        a = st.text_input("Aliases (comma-separated)", key=f"add_{cat_slug}_aliases")
                        s1, s2 = st.columns(2)
                        with s1:
                            ok = st.form_submit_button("Save", type="primary", use_container_width=True)
                        with s2:
                            cancel = st.form_submit_button("Cancel", use_container_width=True)
                        if ok:
                            aliases = [alias.strip() for alias in (a or "").split(",") if alias.strip()]
                            p.upsert_entity(n, category, d, aliases=aliases, allow_merge=True, allow_alias=True)
                            persist_project(p)
                            st.session_state[f"add_open_{category}"] = False
                            st.rerun()
                        if cancel:
                            st.session_state[f"add_open_{category}"] = False
                            st.rerun()

                ents = [
                    e
                    for e in p.world_db.values()
                    if Project._normalize_category(e.category)
                    == Project._normalize_category(category)
                ]
                if query:
                    q = query.lower()
                    ents = [
                        e
                        for e in ents
                        if q in (e.name or "").lower()
                        or any(q in alias.lower() for alias in (e.aliases or []))
                    ]
                if show_orphaned:
                    ents = [e for e in ents if e.id in orphaned_ids]
                if show_canon_risk:
                    ents = [e for e in ents if e.id in flagged_entity_ids]
                if show_recent:
                    ents = [e for e in ents if e.created_at >= recent_cutoff]

                if not ents:
                    st.info(f"📭 No {category} entries yet. Add one above or scan entities from your outline/chapters.")
                    return

                ents = sorted(ents, key=lambda ent: (ent.name or "").lower())

                for idx, e in enumerate(ents):
                    mention_count = mention_counts.get(e.id, 0)
                    is_orphaned = e.id in orphaned_ids
                    is_under_described = e.id in under_described_ids
                    is_collision = e.id in collision_ids
                    if is_orphaned:
                        status_icon = "💤"
                    elif is_collision:
                        status_icon = "🔴"
                    elif is_under_described:
                        status_icon = "🟡"
                    else:
                        status_icon = "🟢"

                    highlight = "highlight" if e.id in flagged_entity_ids or e.id == focus_entity else ""

                    with st.container(border=True):
                        st.html(
                            f"""
                            <div class="world-card {highlight}">
                                <div class="world-card-header">
                                    <div class="world-card-title">{status_icon} {e.name}</div>
                                    <div class="world-card-meta">
                                        <span class="world-badge">{e.category}</span>
                                        <span class="world-card-metric">📌 {mention_count} mentions</span>
                                    </div>
                                </div>
                            </div>
                            """,
                        )

                        issues = []
                        if is_orphaned:
                            issues.append("Orphaned")
                        if is_under_described:
                            issues.append("Needs detail")
                        if is_collision:
                            issues.append("Name collision")
                        if issues:
                            st.caption(f"⚠️ {' • '.join(issues)}")

                        detail_suffix = f"{e.name} ({e.id})" if e.id else e.name
                        detail_label = build_expander_label("Details", detail_suffix)
                        with st.expander(detail_label, expanded=e.id == focus_entity):
                            new_desc = st.text_area("Notes", e.description, key=f"desc_{e.id}", height=140)
                            if new_desc != e.description:
                                e.description = new_desc
                                persist_project(p)

                            alias_text = st.text_input(
                                "Aliases (comma-separated)",
                                value=", ".join(e.aliases or []),
                                key=f"aliases_{e.id}",
                            )
                            if alias_text != ", ".join(e.aliases or []):
                                e.aliases = [a.strip() for a in alias_text.split(",") if a.strip()]
                                persist_project(p)

                            st.caption("Enrichment is currently unavailable.")

                            refs = mention_refs.get(e.id, [])
                            if refs:
                                options = {
                                    f"Chapter {chap.index}: {chap.title}": chap.id for chap in refs
                                }
                                sel = st.selectbox(
                                    "Jump to chapter",
                                    list(options.keys()),
                                    key=f"jump_select_{e.id}",
                                )
                                if st.button("📖 Jump to Chapter", key=f"jump_{e.id}", use_container_width=True):
                                    st.session_state.page = "chapters"
                                    st.session_state.curr_chap_id = options[sel]
                                    st.session_state._force_nav = True
                                    st.rerun()
                            else:
                                st.caption("No chapter references yet.")

                            d1, d2 = st.columns([1, 1])
                            with d1:
                                if st.session_state.delete_entity_id == e.id:
                                    st.warning(f"Delete **{st.session_state.delete_entity_name or e.name}**?")
                                    cdel1, cdel2 = st.columns(2)
                                    with cdel1:
                                        if st.button("Confirm", type="primary", use_container_width=True):
                                            p.delete_entity(e.id)
                                            persist_project(p)
                                            st.session_state.delete_entity_id = None
                                            st.session_state.delete_entity_name = None
                                            st.toast("Entity deleted.")
                                            st.rerun()
                                    with cdel2:
                                        if st.button("Cancel", use_container_width=True):
                                            st.session_state.delete_entity_id = None
                                            st.session_state.delete_entity_name = None
                                            st.rerun()
                                elif st.button("🗑 Delete", key=f"del_{e.id}", use_container_width=True):
                                    st.session_state.delete_entity_id = e.id
                                    st.session_state.delete_entity_name = e.name
                            with d2:
                                st.caption(f"Created: {time.strftime('%Y-%m-%d', time.localtime(e.created_at))}")

        if selected_tab == "Characters":
            render_cat("Character")
        elif selected_tab == "Locations":
            render_cat("Location")
        elif selected_tab == "Factions":
            render_cat("Faction")
        elif selected_tab == "Lore":
            render_cat("Lore")
        elif selected_tab == "Memory":
            st.markdown("### 🧠 World Memory")
            st.caption("Keep canon notes, timelines, and facts the AI should always know.")
            st.markdown("#### 🔒 Hard Canon Rules")
            hard_key = f"world_memory_hard_{p.id}"
            hard_default = p.memory_hard or p.memory
            hard_val = st.text_area("Hard Canon Rules", hard_default, height=160, key=hard_key)
            if hard_val != p.memory_hard:
                p.memory_hard = hard_val
                save_p()

            st.markdown("#### 🧭 Soft Guidelines")
            soft_key = f"world_memory_soft_{p.id}"
            soft_val = st.text_area("Soft Guidelines", p.memory_soft, height=160, key=soft_key)
            if soft_val != p.memory_soft:
                p.memory_soft = soft_val
                save_p()

            st.markdown("#### 🧠 Project Memory")
            memory_key = f"world_memory_{p.id}"
            memory_val = st.text_area("Memory", p.memory, height=320, key=memory_key)
            if memory_val != p.memory:
                p.memory = memory_val
                save_p()
            if st.button("💾 Save Memory", use_container_width=True):
                if persist_project(p, action="save"):
                    st.toast("Memory saved")

            st.divider()
            st.markdown("#### 🔍 Coherence Check")
            scope_cols = st.columns(3)
            with scope_cols[0]:
                scope_outline = st.checkbox("Outline", value=True, key=f"coh_outline_{p.id}")
            with scope_cols[1]:
                scope_world = st.checkbox("World Bible", value=True, key=f"coh_world_{p.id}")
            with scope_cols[2]:
                scope_chapters = st.checkbox("Chapters", value=True, key=f"coh_chapters_{p.id}")

            if st.button("🔍 Run Coherence Check", use_container_width=True):
                compiled_world_bible = "\n".join(
                    f"{e.name} ({e.category}): {e.description}"
                    for e in p.world_db.values()
                )
                chapter_payload = [
                    {
                        "chapter_index": c.index,
                        "summary": c.summary,
                        "excerpt": (c.content or "")[:800],
                    }
                    for c in p.get_ordered_chapters()
                ]
                outline_payload = p.outline if scope_outline else ""
                world_payload = compiled_world_bible if scope_world else ""
                chapters_payload = chapter_payload if scope_chapters else []
                with st.spinner("Running coherence check..."):
                    results = AnalysisEngine.coherence_check(
                        memory=p.memory,
                        author_note=p.author_note,
                        style_guide=p.style_guide,
                        outline=outline_payload,
                        world_bible=world_payload,
                        chapters=chapters_payload,
                        model=get_ai_model(),
                    )
                st.session_state["coherence_results"] = results or []
                canon_icon, canon_label = get_canon_health()
                st.session_state.setdefault("canon_health_log", [])
                st.session_state["canon_health_log"].append(
                    {
                        "timestamp": time.time(),
                        "status": canon_icon,
                        "issue_count": len(st.session_state.get("coherence_results", [])),
                    }
                )
                st.session_state["canon_health_log"] = st.session_state["canon_health_log"][-30:]
                if results:
                    st.toast("Coherence issues found.")
                else:
                    st.toast("No coherence issues detected.")

            results = st.session_state.get("coherence_results", [])
            if results:
                st.markdown("#### 🧩 Coherence Issues")
                for idx, issue in enumerate(list(results)):
                    with st.container(border=True):
                        chapter_idx = issue.get("chapter_index", "?")
                        st.markdown(f"**Chapter #{chapter_idx}**")
                        st.markdown(f"**Issue:** {issue.get('issue', 'Unspecified issue')}")
                        st.markdown(f"**Confidence:** {issue.get('confidence', 'unknown')}")
                        st.markdown("**Suggested Rewrite:**")
                        st.write(issue.get("suggested_rewrite", ""))

                        a1, a2 = st.columns(2)
                        with a1:
                            if st.button("✅ Apply Fix", key=f"coh_apply_{idx}", use_container_width=True):
                                target_excerpt = issue.get("target_excerpt", "")
                                try:
                                    chapter_num = int(chapter_idx)
                                except (TypeError, ValueError):
                                    chapter_num = None
                                target_chapter = None
                                if chapter_num is not None:
                                    for c in p.get_ordered_chapters():
                                        if c.index == chapter_num:
                                            target_chapter = c
                                            break
                                if not target_chapter:
                                    st.warning("Chapter not found for this issue.")
                                elif target_excerpt and target_excerpt in (target_chapter.content or ""):
                                    updated = (target_chapter.content or "").replace(
                                        target_excerpt,
                                        issue.get("suggested_rewrite", ""),
                                        1,
                                    )
                                    target_chapter.update_content(updated, "Coherence Fix")
                                    persist_project(p)
                                    results.pop(idx)
                                    st.session_state["coherence_results"] = results
                                    update_locked_chapters()
                                    st.toast("Applied fix.")
                                    st.rerun()
                                elif issue.get("suggested_rewrite"):
                                    insertion = issue.get("suggested_rewrite", "").strip()
                                    if insertion:
                                        spacer = "\n\n" if (target_chapter.content or "").strip() else ""
                                        updated = f"{(target_chapter.content or '').rstrip()}{spacer}{insertion}"
                                        target_chapter.update_content(updated, "Coherence Fix (Appended)")
                                        persist_project(p)
                                        results.pop(idx)
                                        st.session_state["coherence_results"] = results
                                        update_locked_chapters()
                                        st.toast("Applied fix (appended).")
                                        st.rerun()
                                else:
                                    st.warning("Target excerpt not found in chapter content.")
                        with a2:
                            if st.button("🗑 Ignore", key=f"coh_ignore_{idx}", use_container_width=True):
                                results.pop(idx)
                                st.session_state["coherence_results"] = results
                                update_locked_chapters()
                                st.toast("Issue ignored.")
                                st.rerun()
        elif selected_tab == "Insights":
            st.markdown("### 📊 World Bible Insights")
            st.caption("Quick stats on your current canon database.")
            entries = list(p.world_db.values())
            total_entries = len(entries)
            counts = {"Character": 0, "Location": 0, "Faction": 0, "Lore": 0}
            for ent in entries:
                category = Project._normalize_category(ent.category)
                counts[category] = counts.get(category, 0) + 1

            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Total Entries", total_entries)
            c2.metric("Characters", counts.get("Character", 0))
            c3.metric("Locations", counts.get("Location", 0))
            c4.metric("Factions", counts.get("Faction", 0))

            c5, c6 = st.columns(2)
            c5.metric("Lore", counts.get("Lore", 0))
            c6.metric(
                "Last Updated",
                time.strftime("%Y-%m-%d", time.localtime(p.last_modified)),
            )

            st.divider()
            if not st.session_state.get("is_premium", False):
                st.info("🔒 Canon history is a Premium feature.")
            else:
                st.markdown("### 🧠 Canon Health History")
                for entry in st.session_state.get("canon_health_log", []):
                    st.caption(
                        f"{time.strftime('%Y-%m-%d %H:%M', time.localtime(entry['timestamp']))} "
                        f"{entry['status']} ({entry['issue_count']} issues)"
                    )

            st.divider()
            st.markdown("### ⏱ Timeline Heatmap")
            for chap in p.get_ordered_chapters():
                intensity = min(1.0, chap.word_count / 2000)
                st.progress(intensity, text=f"Chapter {chap.index}: {chap.word_count} words")

            st.divider()
            st.markdown("#### 📌 Entity Utilization")
            utilization_rows = []
            for ent in entries:
                aliases = [ent.name] + (ent.aliases or [])
                total_hits = mention_counts.get(ent.id, 0)
                utilization_rows.append(
                    {
                        "Name": ent.name,
                        "Category": ent.category,
                        "Appearances": total_hits,
                        "Orphaned": ent.id in orphaned_ids,
                        "Under-described": ent.id in under_described_ids,
                    }
                )
            if utilization_rows:
                st.dataframe(utilization_rows, use_container_width=True, hide_index=True)
            else:
                st.info("No entities yet to analyze.")

            st.divider()
            st.markdown("#### 🚩 Flagged Entities")
            flagged_entities = [ent for ent in entries if ent.id in flagged_entity_ids]
            if flagged_entities:
                for ent in flagged_entities:
                    reasons = []
                    if ent.id in orphaned_ids:
                        reasons.append("Orphaned")
                    if ent.id in under_described_ids:
                        reasons.append("Needs detail")
                    if ent.id in collision_ids:
                        reasons.append("Name collision")
                    with st.container(border=True):
                        r1, r2 = st.columns([3, 1])
                        with r1:
                            st.markdown(f"**{ent.name}** • {ent.category}")
                            st.caption(" • ".join(reasons))
                        with r2:
                            if st.button("Jump to Entity", key=f"jump_entity_{ent.id}", use_container_width=True):
                                st.session_state["world_focus_entity"] = ent.id
                                st.session_state["world_search_pending"] = ent.name
                                st.toast("Entity highlighted in World Bible.")
            else:
                st.success("No flagged entities right now.")

            st.divider()
            st.markdown("#### ⚠️ Canon Risk Flags")
            coherence_results = st.session_state.get("coherence_results", [])
            high_canon_drift = len(coherence_results) > 0
            alias_collision = any(len(names) > 1 for names in normalized_name_map.values())

            timeline_dense = False
            dense_chapters = []
            for chap in chapters:
                summary_text = (chap.summary or "").strip()
                base_text = summary_text if summary_text else (chap.content or "")[:800]
                sentence_count = len([s for s in re.split(r"[.!?]+", base_text) if s.strip()])
                if sentence_count > 3:
                    timeline_dense = True
                    dense_chapters.append(chap.index)

            if high_canon_drift:
                st.warning("High Canon Drift: coherence issues detected.")
            if alias_collision:
                st.warning("Alias Collision: multiple entities share normalized names.")
            if timeline_dense:
                chap_list = ", ".join(str(idx) for idx in dense_chapters)
                st.warning(f"Timeline Density: >3 major events in chapters {chap_list}.")
            if not any([high_canon_drift, alias_collision, timeline_dense]):
                st.success("No canon risk flags detected.")

            st.divider()
            st.markdown("#### ✅ AI Readiness Score")
            readiness = 0
            if (p.memory or "").strip():
                readiness += 20
            if len(entries) > 10:
                readiness += 20
            if (p.outline or "").strip():
                readiness += 20
            if chapters:
                readiness += 20
            if not coherence_results:
                readiness += 20
            st.metric("AI Readiness", f"{readiness}%")

    def render_chapters():
        p = st.session_state.project
        if not p:
            with st.container(border=True):
                st.info("📭 No project loaded. Create or open a project to start writing.")
                if st.button("Go to Projects", use_container_width=True):
                    st.session_state.page = "projects"
                    st.rerun()
            return

        def _persist_chapter_update() -> None:
            st.session_state.project = p
            persist_project(p)
            _bump_projects_refresh()
            st.rerun()

        chaps = p.get_ordered_chapters()

        def create_next_chapter() -> None:
            next_idx = len(chaps) + 1 if chaps else 1
            title = f"Chapter {next_idx}"
            if p.outline:
                pat = re.compile(rf"Chapter {next_idx}[:\\s]+(.*?)(?=\\n|$)", re.IGNORECASE)
                match = pat.search(p.outline or "")
                if match:
                    raw = match.group(1).strip()
                    title = sanitize_chapter_title(re.split(r" [-–:] ", raw, 1)[0].strip()) or title
            p.add_chapter(title)
            _persist_chapter_update()

        render_page_header(
            "Editor",
            "Write chapters, update summaries, and apply AI improvements.",
            tag="Drafting",
            key_prefix="editor_header",
        )

        if not chaps:
            with st.container(border=True):
                st.info("📭 No chapters yet.\n\nCreate your first chapter — or let MANTIS write one from your outline.")
                if st.button(
                    "➕ Create Chapter 1",
                    type="primary",
                    use_container_width=True,
                    key="editor_create_chapter_1"
                ):
                    p.add_chapter("Chapter 1")
                    _persist_chapter_update()
            return

        if "curr_chap_id" not in st.session_state or st.session_state.curr_chap_id not in p.chapters:
            st.session_state.curr_chap_id = chaps[0].id

        curr = p.chapters[st.session_state.curr_chap_id]
        locked_chapters = st.session_state.get("locked_chapters", set())
        # --- SAFELY sync programmatic chapter updates into the editor widget (before widget exists)
        ed_key = f"ed_{curr.id}"
        if (
            st.session_state.get("_chapter_sync_id") == curr.id
            and ed_key in st.session_state
        ):
            st.session_state[ed_key] = st.session_state.get("_chapter_sync_text", "") or ""
            st.session_state._chapter_sync_id = None
            st.session_state._chapter_sync_text = None

        if p.outline and "Untitled" in (curr.title or ""):
            pat = re.compile(rf"Chapter {curr.index}[:\s]+(.*?)(?=\n|$)", re.IGNORECASE)
            match = pat.search(p.outline or "")
            if match:
                raw = match.group(1).strip()
                clean = re.split(r" [-–:] ", raw, 1)[0].strip()
                if len(clean) > 2:
                    curr.title = sanitize_chapter_title(clean)
                    persist_project(p)

        col_nav, col_editor, col_ai = st.columns([1.05, 3.2, 1.25])

        with col_nav:
            with st.container(border=True):
                st.markdown("### 📍 Chapters")
                for c in chaps:
                    lbl = f"{c.index}. {(c.title or 'Untitled')[:18]}"
                    if st.button(
                        lbl,
                        key=f"n_{c.id}",
                        type="primary" if c.id == curr.id else "secondary",
                        use_container_width=True,
                        help=c.title or "Untitled",
                    ):
                        st.session_state.curr_chap_id = c.id
                        st.rerun()

                st.divider()
                if st.button(
                    "➕ New Chapter",
                    use_container_width=True,
                    help="Create a new chapter in this project.",
                    key="editor_new_chapter"
                ):
                    next_idx = len(chaps) + 1
                    pat = re.compile(rf"Chapter {next_idx}[:\s]+(.*?)(?=\n|$)", re.IGNORECASE)
                    match = pat.search(p.outline or "")
                    if match:
                        raw = match.group(1).strip()
                        title = sanitize_chapter_title(re.split(r" [-–:] ", raw, 1)[0].strip())
                    else:
                        title = f"Chapter {next_idx}"
                    p.add_chapter(sanitize_chapter_title(title))
                    _persist_chapter_update()

                if chaps:
                    if st.session_state.get("delete_chapter_id") == curr.id:
                        st.warning(f"Delete **{st.session_state.get('delete_chapter_title') or curr.title}**?")
                        cdel1, cdel2 = st.columns(2)
                        with cdel1:
                            if st.button("Yes", type="primary", use_container_width=True, key="editor_del_ch_confirm"):
                                p.delete_chapter(curr.id)
                                chaps = p.get_ordered_chapters()
                                st.session_state.curr_chap_id = chaps[0].id if chaps else None
                                st.session_state.delete_chapter_id = None
                                st.session_state.delete_chapter_title = None
                                persist_project(p)
                                st.toast("Chapter deleted.")
                                st.rerun()
                        with cdel2:
                            if st.button("No", use_container_width=True, key="editor_del_ch_cancel"):
                                st.session_state.delete_chapter_id = None
                                st.session_state.delete_chapter_title = None
                                st.rerun()
                    elif st.button("🗑 Delete Chapter", use_container_width=True, key=f"editor_del_{curr.id}"):
                        st.session_state.delete_chapter_id = curr.id
                        st.session_state.delete_chapter_title = curr.title

        stream_ph = st.empty()

        with col_editor:
            with st.container(border=True):
                st.markdown("#### Drafting")
                st.caption("Edit chapter title, target length, and content.")
                h1, h2 = st.columns([3, 1])
                with h1:
                    curr.title = st.text_input(
                        "Chapter title",
                        curr.title,
                        label_visibility="collapsed",
                        help="Rename this chapter.",
                        placeholder="Chapter title",
                    )
                with h2:
                    curr.target_words = st.number_input(
                        "Target words",
                        100,
                        10000,
                        int(curr.target_words),
                        label_visibility="collapsed",
                        help="Target word count for this chapter.",
                    )

                val = st.text_area(
                    "Manuscript",
                    curr.content,
                    height=680,
                    label_visibility="collapsed",
                    key=f"ed_{curr.id}",
                    help="Write your chapter content here. Auto-save captures changes when enabled.",
                )
                if val != curr.content:
                    curr.update_content(val, "manual")
                    save_p()

                # -- World Bible awareness: lightweight reference scan --
                from app.services.world_bible_db import scan_editor_for_world_bible_references
                wb_refs = scan_editor_for_world_bible_references(
                    val or "", session_state=st.session_state
                )
                if wb_refs:
                    names = ", ".join(r["name"] for r in wb_refs[:5])
                    suffix = f" (+{len(wb_refs) - 5} more)" if len(wb_refs) > 5 else ""
                    st.info(f"📖 World Bible references detected: {names}{suffix}")

                autosave_state = "On" if st.session_state.auto_save else "Manual"
                try:
                    last_edit = datetime.datetime.fromtimestamp(curr.modified_at).strftime("%b %d, %H:%M")
                except (TypeError, ValueError, OSError):
                    last_edit = "Unknown"
                st.caption(f"🕒 Last edited: {last_edit} • 💾 Auto-save: {autosave_state}")
                st.caption(f"📝 Chapter: {curr.word_count} words • 📚 Total: {p.get_total_word_count()} words")

                c1, c2 = st.columns([1, 1])
                with c1:
                    if st.button(
                        "💾 Save & Scan Entities",
                        type="primary",
                        use_container_width=True,
                        help="Save this chapter and scan for new World Bible entities.",
                    ):
                        curr.update_content(val, "manual")
                        if persist_project(p, action="save"):
                            # Automatically scan entities from this chapter when the user explicitly saves it.
                            extract_entities_ui(curr.content or "", f"Ch {curr.index}")
                            st.toast("Chapter Saved & Entities Scanned")
                with c2:
                    if st.button(
                        "📝 Generate Summary",
                        use_container_width=True,
                        help="Create or refresh the chapter summary.",
                    ):
                        summary = StoryEngine.summarize(curr.content or "", get_ai_model())
                        if summary.strip().startswith("ERROR: Canon violation detected."):
                            st.error("Canon violation detected. Resolve issues before generating AI content.")
                        else:
                            curr.summary = summary
                            persist_project(p)
                            st.rerun()

                def generate_improvement(style_choice, custom_instructions):
                    prompt = rewrite_prompt(curr.content or "", style_choice, custom_instructions)
                    full = ""
                    for chunk in AIEngine().generate_stream(prompt, get_ai_model()):
                        full += chunk
                        stream_ph.markdown(f"**IMPROVING:**\n\n{full}")
                    if full.strip().startswith("ERROR: Canon violation detected."):
                        st.error("Canon violation detected. Resolve issues before generating AI content.")
                        return ""
                    violations = detect_hard_canon_violation(p, curr.index, full)
                    if violations:
                        results = st.session_state.get("coherence_results", [])
                        results.extend(violations)
                        st.session_state["coherence_results"] = results
                        update_locked_chapters()
                        st.warning("Hard Canon conflict detected. AI output was not applied.")
                        return ""
                    return full

                with st.expander("✨ Improve Draft"):
                    rewrite_locked = curr.index in locked_chapters
                    style = st.selectbox(
                        "How to improve?",
                        list(REWRITE_PRESETS.keys()),
                        disabled=rewrite_locked,
                        key=f"editor_improve__style_{curr.id}",
                    )
                    cust = ""
                    if style == "Custom":
                        cust = st.text_input(
                            "Instructions",
                            disabled=rewrite_locked,
                            key=f"editor_improve__instructions_{curr.id}",
                        )
                    if rewrite_locked:
                        st.caption("🔒 Rewrite tools are disabled for locked chapters.")
                    if st.button(
                        "Generate Improvement",
                        use_container_width=True,
                        disabled=rewrite_locked,
                        key=f"editor_improve__generate_{curr.id}",
                    ):
                        full = generate_improvement(style, cust)
                        if full:
                            st.session_state.pending_improvement_text = full
                            st.session_state.pending_improvement_meta = {
                                "mode": style,
                                "custom": cust,
                                "timestamp": time.time(),
                                "chapter_id": curr.id,
                            }
                            st.rerun()

                if st.button(
                    "↩️ Undo last AI apply",
                    use_container_width=True,
                    key=f"editor_improve__undo_{curr.id}",
                    help="Restore the previous chapter text, if available.",
                ):
                    prev = st.session_state.get("chapter_text_prev", {})
                    if prev.get("chapter_id") == curr.id and prev.get("text") is not None:
                        curr.update_content(prev.get("text") or "", "Undo Apply")
                        persist_project(p)
                        st.session_state._chapter_sync_id = curr.id
                        st.session_state._chapter_sync_text = prev.get("text") or ""
                        st.toast("Previous chapter text restored.")
                        st.rerun()
                    else:
                        st.info("No previous chapter text available to restore.")

                chapter_drafts = [
                    draft for draft in st.session_state.get("chapter_drafts", [])
                    if draft.get("chapter_id") == curr.id
                ]
                if chapter_drafts:
                    st.markdown("#### Draft Versions")
                    for idx, draft in enumerate(chapter_drafts, start=1):
                        label = f"Draft {idx} • {draft.get('mode', 'Improved')} • {time.strftime('%Y-%m-%d %H:%M', time.localtime(draft.get('timestamp', 0)))}"
                        with st.expander(label):
                            st.text_area(
                                "Draft Text",
                                draft.get("text", ""),
                                height=200,
                                disabled=True,
                                key=f"editor_improve__draft_text_{curr.id}_{idx}",
                            )
                            if st.button(
                                "Set as active",
                                type="primary",
                                use_container_width=True,
                                key=f"editor_improve__set_active_{curr.id}_{idx}",
                            ):
                                st.session_state.chapter_text_prev = {
                                    "chapter_id": curr.id,
                                    "text": curr.content or "",
                                }
                                curr.update_content(draft.get("text", ""), "Draft Applied")
                                persist_project(p)
                                st.session_state._chapter_sync_id = curr.id
                                st.session_state._chapter_sync_text = draft.get("text", "")
                                st.toast("Draft set as active.")
                                st.rerun()

        with col_ai:
            with st.container(border=True):
                st.markdown("### 🤖 Assistant")
                st.caption("Generate new prose from your outline + previous context.")

                canon_icon, canon_label = get_canon_health()
                st.caption(
                    "Canon status: "
                    f"{canon_icon} {canon_label} • Legend: Canon Stable / Minor Canon Drift / High Canon Risk"
                )
                canon_blocked = canon_icon == "🔴"
                if canon_blocked:
                    st.button(
                        "🚫 Auto-Write Disabled (Canon Risk)",
                        disabled=True,
                        use_container_width=True,
                        help="Resolve canon issues in World Bible → Memory before generating.",
                    )
                elif st.button(
                    "✨ Auto-Write Chapter",
                    type="primary",
                    use_container_width=True,
                    help="Generate a new draft using your outline and chapter context.",
                ):
                    prompt = StoryEngine.generate_chapter_prompt(p, curr.index, int(curr.target_words))
                    full = ""
                    for chunk in AIEngine().generate_stream(prompt, get_ai_model()):
                        full += chunk
                        stream_ph.markdown(f"**GENERATING:**\n\n{full}")

                    if full.strip():
                        if full.strip().startswith("ERROR: Canon violation detected."):
                            st.error("Canon violation detected. Resolve issues before generating AI content.")
                            return
                        violations = detect_hard_canon_violation(p, curr.index, full)
                        if violations:
                            results = st.session_state.get("coherence_results", [])
                            results.extend(violations)
                            st.session_state["coherence_results"] = results
                            update_locked_chapters()
                            st.warning("Hard Canon conflict detected. AI output was not applied.")
                            return
                        new_text = ((curr.content or "") + "\n" + full.strip()).strip()
                        curr.update_content(new_text, "AI Auto-Write")
                        persist_project(p)

                        # Queue sync into editor widget on next run (do NOT set ed_key here!)
                        st.session_state._chapter_sync_id = curr.id
                        st.session_state._chapter_sync_text = new_text

                        st.toast("Chapter Updated")
                        time.sleep(0.3)
                        st.rerun()

                st.divider()
                st.markdown("#### Summary")
                if curr.summary:
                    st.info(curr.summary)
                else:
                    st.info("No summary yet. Click **Generate Summary** to create one.")

        pending_text = st.session_state.get("pending_improvement_text") or ""
        pending_meta = st.session_state.get("pending_improvement_meta") or {}
        pending_for_chapter = pending_text and pending_meta.get("chapter_id") == curr.id
        if pending_for_chapter:
            with st.container(border=True):
                st.markdown("### ✨ Review Changes")
                diff_toggle = st.toggle(
                    "Diff view",
                    value=False,
                    key=f"editor_improve__diff_toggle_{curr.id}",
                    help="Show a unified diff instead of the full texts.",
                )
                col_left, col_right = st.columns(2)
                if diff_toggle:
                    diff_lines = difflib.unified_diff(
                        (curr.content or "").splitlines(),
                        (pending_text or "").splitlines(),
                        fromfile="Original",
                        tofile="Improved",
                        lineterm="",
                    )
                    diff_text = "\n".join(diff_lines).strip() or "No differences found."
                    with col_left:
                        st.text_area(
                            "Original",
                            curr.content or "",
                            height=260,
                            disabled=True,
                            key=f"editor_improve__original_{curr.id}",
                        )
                    with col_right:
                        st.code(diff_text, language="diff")
                else:
                    with col_left:
                        st.text_area(
                            "Original",
                            curr.content or "",
                            height=260,
                            disabled=True,
                            key=f"editor_improve__original_{curr.id}",
                        )
                    with col_right:
                        st.text_area(
                            "Improved",
                            pending_text or "",
                            height=260,
                            disabled=True,
                            key=f"editor_improve__improved_{curr.id}",
                        )

                apply_mode = st.selectbox(
                    "Apply improved text as",
                    [
                        "Replace chapter",
                        "Save as new draft/version",
                        "Append to end (advanced)",
                    ],
                    key=f"editor_improve__apply_mode_{curr.id}",
                )

                b1, b2, b3, b4 = st.columns([1, 1, 1, 1])
                with b1:
                    if st.button(
                        "Apply Changes",
                        type="primary",
                        use_container_width=True,
                        key=f"editor_improve__apply_{curr.id}",
                    ):
                        if apply_mode == "Replace chapter":
                            st.session_state.chapter_text_prev = {
                                "chapter_id": curr.id,
                                "text": curr.content or "",
                            }
                            new_text = pending_text or ""
                            curr.update_content(new_text, "AI Improve")
                            persist_project(p)
                            st.session_state._chapter_sync_id = curr.id
                            st.session_state._chapter_sync_text = new_text
                            st.toast("Chapter replaced with improved text.")
                        elif apply_mode == "Save as new draft/version":
                            draft_entry = {
                                "chapter_id": curr.id,
                                "text": pending_text or "",
                                "mode": pending_meta.get("mode", "Improve"),
                                "timestamp": time.time(),
                            }
                            st.session_state.chapter_drafts = (
                                st.session_state.get("chapter_drafts", []) + [draft_entry]
                            )
                            st.toast("Saved as a new draft version.")
                        else:
                            st.session_state.chapter_text_prev = {
                                "chapter_id": curr.id,
                                "text": curr.content or "",
                            }
                            new_text = ((curr.content or "") + "\n" + (pending_text or "")).strip()
                            curr.update_content(new_text, "AI Improve Append")
                            persist_project(p)
                            st.session_state._chapter_sync_id = curr.id
                            st.session_state._chapter_sync_text = new_text
                            st.toast("Improved text appended to chapter.")

                        st.session_state.pending_improvement_text = ""
                        st.session_state.pending_improvement_meta = {}
                        st.rerun()
                with b2:
                    if st.button(
                        "Copy Improved",
                        use_container_width=True,
                        key=f"editor_improve__copy_{curr.id}",
                    ):
                        st.session_state.editor_improve__copy_buffer = pending_text or ""
                        st.toast("Improved text ready to copy (Ctrl/Cmd+C).")
                with b3:
                    if st.button(
                        "Regenerate",
                        use_container_width=True,
                        key=f"editor_improve__regenerate_{curr.id}",
                    ):
                        regen_style = pending_meta.get("mode", "Improve Flow")
                        regen_custom = pending_meta.get("custom", "")
                        full = generate_improvement(regen_style, regen_custom)
                        if full:
                            st.session_state.pending_improvement_text = full
                            st.session_state.pending_improvement_meta = {
                                "mode": regen_style,
                                "custom": regen_custom,
                                "timestamp": time.time(),
                                "chapter_id": curr.id,
                            }
                            st.rerun()
                with b4:
                    if st.button(
                        "Discard",
                        use_container_width=True,
                        key=f"editor_improve__discard_{curr.id}",
                    ):
                        st.session_state.pending_improvement_text = ""
                        st.session_state.pending_improvement_meta = {}
                        st.rerun()

    ctx = SimpleNamespace(
        st=st,
        AppConfig=AppConfig,
        Project=Project,
        Chapter=Chapter,
        Entity=Entity,
        AIEngine=AIEngine,
        AnalysisEngine=AnalysisEngine,
        StoryEngine=StoryEngine,
        REWRITE_PRESETS=REWRITE_PRESETS,
        rewrite_prompt=rewrite_prompt,
        project_to_markdown=project_to_markdown,
        queue_world_bible_suggestion=queue_world_bible_suggestion,
        action_card=action_card,
        card=card,
        primary_button=primary_button,
        section_header=section_header,
        stat_tile=stat_tile,
        render_page_header=render_page_header,
        render_app_footer=render_app_footer,
        persist_project=persist_project,
        get_ai_model=get_ai_model,
        save_p=save_p,
        get_active_projects_dir=get_active_projects_dir,
        resume_pending_action=resume_pending_action,
        open_legal_page=open_legal_page,
        render_privacy=render_privacy,
        render_terms=render_terms,
        render_copyright=render_copyright,
        config_data=config_data,
        key_scope=key_scope,
        ui_key=ui_key,
        render_home=render_home,
        render_projects=render_projects,
        render_outline=render_outline,
        render_world=render_world,
        render_chapters=render_chapters,
        render_export=render_export,
        render_ai_settings=render_ai_settings,
        render_legal_redirect=render_legal_redirect,
    )

    scope_map = {
        "home": "dashboard",
        "projects": "projects",
        "ai": "settings",
        "legal": "legal",
        "export": "export",
        "outline": "outline",
        "world": "world",
        "chapters": "editor",
    }
    page = st.session_state.page
    renderer = router.resolve_route(page)
    scope = scope_map.get(page)
    if scope:
        with key_scope(scope):
            renderer(ctx)
        render_app_footer()
    else:
        st.session_state.page = "home"
        st.rerun()


def run_selftest() -> int:
    """
    Quick non-UI integrity test. Intended to be called by the launcher.
    Creates a temporary project, exercises save/load, chapters/entities/export, then cleans up.
    """
    print("[MANTIS SELFTEST]")
    try:
        os.makedirs(AppConfig.PROJECTS_DIR, exist_ok=True)
        # Local-first architecture: all projects stored in default directory
        selftest_dir = os.path.join(AppConfig.PROJECTS_DIR, f"selftest_{uuid.uuid4().hex[:8]}")
        os.makedirs(selftest_dir, exist_ok=True)

        p = Project.create("SELFTEST_PROJECT", author="MANTIS", genre="Test", storage_dir=selftest_dir)
        p.outline = "Chapter 1: Test - This is a test outline."
        path = p.save()
        if not os.path.exists(path):
            raise RuntimeError("Save failed: project file not found on disk.")

        p2 = Project.load(path)
        if p2.title != "SELFTEST_PROJECT":
            raise RuntimeError("Load failed: project title mismatch.")

        ch = p2.add_chapter("Test Chapter", "Hello world")
        if ch.word_count != 2:
            raise RuntimeError(f"Chapter word_count incorrect: expected 2, got {ch.word_count}")

        ent = p2.add_entity("Tester", "Character", "A test entity.")
        if ent is None:
            raise RuntimeError("Entity add failed: returned None.")

        md = project_to_markdown(p2)
        if "# SELFTEST_PROJECT" not in md:
            raise RuntimeError("Export markdown failed: missing title header.")

        # Cleanup
        try:
            os.remove(path)
        except OSError:
            logger.warning("Selftest cleanup failed for %s", path, exc_info=True)
        try:
            if os.path.isdir(selftest_dir):
                shutil.rmtree(selftest_dir)
        except OSError:
            logger.warning("Selftest cleanup failed for %s", selftest_dir, exc_info=True)
        print("SELFTEST RESULT: PASS")
        return 0
    except Exception as e:
        logger.error("Selftest failed", exc_info=True)
        print("SELFTEST RESULT: FAIL")
        print(str(e))
        return 1



def run_repair() -> int:
    """
    Repairs/normalizes project JSON files in the projects folder.
    - Creates a timestamped backup copy into projects/.backups
    - Attempts to load via Project.load (validates schema)
    - Rewrites JSON in a normalized format (indent=2, ensure_ascii=False)
    Returns 0 on success, 1 if any file failed.
    """
    projects_dir = AppConfig.PROJECTS_DIR
    backups_dir = AppConfig.BACKUPS_DIR
    os.makedirs(projects_dir, exist_ok=True)
    os.makedirs(backups_dir, exist_ok=True)

    files = [f for f in os.listdir(projects_dir) if f.lower().endswith(".json")]
    if not files:
        print("[REPAIR] No project files found.")
        return 0

    stamp = time.strftime("%Y%m%d_%H%M%S")
    failures = 0

    def _atomic_write(path: str, data: dict) -> None:
        tmp = path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as fh:
            json.dump(data, fh, indent=2, ensure_ascii=False)
        os.replace(tmp, path)

    print(f"[REPAIR] Found {len(files)} project file(s). Backups -> {backups_dir}")
    for fn in files:
        full = os.path.join(projects_dir, fn)
        try:
            # Backup first
            backup_name = f"{stamp}__{fn}"
            backup_path = os.path.join(backups_dir, backup_name)
            try:
                with open(full, "rb") as src, open(backup_path, "wb") as dst:
                    dst.write(src.read())
            except Exception:
                # Backup failure shouldn't block repair attempt, but count it
                print(f"[REPAIR][WARN] Could not backup: {fn}")
                logger.warning("Repair backup failed for %s", full, exc_info=True)

            # Validate/normalize via Project model
            proj = Project.load(full)
            data = proj.to_dict()
            _atomic_write(full, data)
            print(f"[REPAIR][OK] {fn}")
        except Exception as e:
            failures += 1
            print(f"[REPAIR][FAIL] {fn} :: {e}")
            logger.error("Repair failed for %s", full, exc_info=True)

    if failures:
        print(f"[REPAIR] Completed with failures: {failures}")
        return 1

    print("[REPAIR] Completed successfully.")
    return 0


def run_app() -> int:
    ensure_storage_dirs()
    if SELFTEST_MODE:
        return run_selftest()
    if REPAIR_MODE:
        return run_repair()
    _run_ui()
    return 0


if __name__ == "__main__":
    raise SystemExit(run_app())
