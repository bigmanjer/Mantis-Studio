"""AI and LLM services for Mantis Studio.

Note: This module is part of the new app/ structure.
      Current implementation still uses mantis.core.models for backward compatibility.
      These imports will be updated when the migration is complete.
"""
from __future__ import annotations

import json
import re
import sys
from collections.abc import Generator
from typing import Any, Dict, List, Optional

import requests

from app.config.settings import AppConfig, logger
from app.services.projects import Project


def _truncate_prompt(prompt: str, limit: int) -> str:
    if not prompt:
        return prompt
    if len(prompt) <= limit:
        return prompt
    logger.warning("Prompt length %s exceeded limit %s; truncating", len(prompt), limit)
    return prompt[:limit]


def sanitize_ai_input(text: str, max_length: int = 0) -> str:
    """Sanitize user-provided text before sending to AI APIs.

    Strips leading/trailing whitespace and removes null bytes.
    When *max_length* is positive the text is truncated to that limit.
    """
    if not text:
        return ""
    cleaned = text.strip().replace("\x00", "")
    if max_length > 0 and len(cleaned) > max_length:
        cleaned = cleaned[:max_length]
    return cleaned


class AIEngine:
    def __init__(self, timeout: int = AppConfig.GROQ_TIMEOUT, base_url: Optional[str] = None):
        self.base_url = (base_url or AppConfig.GROQ_API_URL).rstrip("/")
        self.timeout = timeout
        self.session = requests.Session()

    def probe_models(self, api_key: str) -> List[str]:
        headers = {"Authorization": f"Bearer {api_key}"} if api_key else {}
        try:
            r = self.session.get(f"{self.base_url}/models", headers=headers, timeout=5)
            r.raise_for_status()
            data = r.json()
            return [m.get("id") for m in data.get("data", []) if m.get("id")]
        except Exception:
            logger.warning("Model probe failed for %s", self.base_url, exc_info=True)
            return []

    def generate_stream(self, prompt: str, model: str) -> Generator[str, None, None]:
        if "streamlit" in sys.modules:
            import streamlit as st

            results = st.session_state.get("coherence_results", [])
            if len(results) > 2:
                yield (
                    "ERROR: Canon violation detected.\n"
                    "Resolve Hard Canon conflicts before generating AI content."
                )
                return
            project = st.session_state.get("project")
            hard_rules = ""
            if project:
                hard_rules = (project.memory_hard or project.memory or "").strip()
            if hard_rules:
                prompt = (
                    "HARD CANON RULES (NON-NEGOTIABLE):\n"
                    f"{hard_rules}\n\n"
                    f"{prompt}"
                )
        if not model:
            yield "Groq model not configured."
            return

        api_key = (AppConfig.GROQ_API_KEY or "").strip()
        if not api_key:
            yield "Groq API key not configured."
            return

        prompt = sanitize_ai_input(prompt)
        prompt = _truncate_prompt(prompt, AppConfig.MAX_PROMPT_CHARS)
        headers = {"Content-Type": "application/json"}
        headers["Authorization"] = f"Bearer {api_key}"

        def _groq_non_stream() -> Generator[str, None, None]:
            payload = {
                "model": model,
                "messages": [{"role": "user", "content": prompt}],
                "stream": False,
            }
            try:
                r = self.session.post(
                    f"{self.base_url}/chat/completions",
                    json=payload,
                    headers=headers,
                    timeout=self.timeout,
                )
                r.raise_for_status()
                data = r.json()
                choice = (data.get("choices") or [{}])[0]
                content = (choice.get("message") or {}).get("content") or choice.get("text") or ""
                if content:
                    yield content
                else:
                    yield "Groq response empty."
            except Exception:
                logger.warning("Groq non-stream generation failed", exc_info=True)
                yield "Groq generation failed."

        payload = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "stream": True,
        }
        try:
            with self.session.post(
                f"{self.base_url}/chat/completions",
                json=payload,
                headers=headers,
                stream=True,
                timeout=self.timeout,
            ) as r:
                r.raise_for_status()
                yielded = False
                for raw in r.iter_lines():
                    if not raw:
                        continue
                    line = raw.decode("utf-8").strip()
                    if not line.startswith("data:"):
                        continue
                    data = line.replace("data:", "", 1).strip()
                    if data == "[DONE]":
                        break
                    try:
                        chunk = json.loads(data)
                    except json.JSONDecodeError:
                        continue
                    delta = chunk.get("choices", [{}])[0].get("delta", {})
                    content = delta.get("content")
                    if content:
                        yielded = True
                        yield content
                if not yielded:
                    yield from _groq_non_stream()
        except Exception:
            logger.warning("Groq streaming generation failed, retrying non-stream", exc_info=True)
            yield from _groq_non_stream()

    def generate(self, prompt: str, model: str) -> Dict[str, str]:
        chunks: List[str] = []
        for chunk in self.generate_stream(prompt, model):
            chunks.append(chunk)
        return {"text": "".join(chunks)}

    def generate_json(self, prompt: str, model: str) -> Optional[List[Dict[str, Any]]]:
        res = self.generate(f"Return ONLY valid JSON. List of objects. No markdown.\n\n{prompt}", model)
        txt = (res.get("text", "") or "").strip()
        txt = re.sub(r"```json\s*", "", txt)
        txt = re.sub(r"```\s*", "", txt).strip()
        try:
            d = json.loads(txt)
            if isinstance(d, list):
                return d
            if isinstance(d, dict):
                return [d]
            return None
        except Exception:
            logger.warning("JSON parse failed for AI response", exc_info=True)
            return None


class AnalysisEngine:
    @staticmethod
    def extract_entities(text: str, model: str) -> list:
        if not text or len(text) < 50:
            return []
        prompt = (
            "Analyze text. Identify Characters, Locations, Factions, and important Lore.\n"
            "Return JSON List: [{'name': 'X', 'category': 'Character|Location|Faction|Lore', "
            "'description': 'Z', 'aliases': ['Alt Name'], 'confidence': 0.0}]\n"
            f"TEXT:\n{text[:6000]}"
        )
        return AIEngine().generate_json(prompt, model) or []

    @staticmethod
    def generate_title(outline: str, genre: str, model: str) -> str:
        prompt = (
            f"GENRE: {genre}\n"
            f"OUTLINE: {outline[:2000]}\n"
            "TASK: Create a creative, catchy title for this story.\n"
            "RULES: Output ONLY the title. No quotes. No prefixes like 'Title:'."
        )
        raw = (AIEngine().generate(prompt, model).get("text", "Untitled") or "").strip()
        clean = re.sub(r"(?i)^(here is a title|sure|suggested title|title)[:\s-]*", "", raw).strip()
        clean = clean.replace('"', "").replace("'", "").strip()
        return clean.split("\n")[0] if clean else "Untitled"

    @staticmethod
    def detect_genre(outline: str, model: str) -> str:
        """
        Attempts to infer a concise genre label from the outline text.
        Uses AI if available, otherwise falls back to a lightweight heuristic.
        """
        outline = (outline or "").strip()
        if not outline:
            return ""

        # Heuristic fallback first (fast, offline-safe)
        low = outline.lower()
        heuristic_map = [
            ("space", "Science Fiction"),
            ("spaceship", "Science Fiction"),
            ("alien", "Science Fiction"),
            ("cyber", "Cyberpunk"),
            ("hacker", "Cyberpunk"),
            ("detective", "Mystery/Thriller"),
            ("murder", "Mystery/Thriller"),
            ("serial killer", "Mystery/Thriller"),
            ("dragon", "Fantasy"),
            ("magic", "Fantasy"),
            ("kingdom", "Fantasy"),
            ("vampire", "Horror"),
            ("zombie", "Horror"),
            ("haunted", "Horror"),
            ("romance", "Romance"),
            ("love triangle", "Romance"),
            ("coming of age", "Coming-of-Age"),
            ("war", "Historical/War"),
            ("wwii", "Historical/War"),
            ("post-apocalyptic", "Post-Apocalyptic"),
            ("apocalypse", "Post-Apocalyptic"),
        ]
        for needle, genre in heuristic_map:
            if needle in low:
                return genre

        # AI-based inference
        prompt = (
            "You are a book editor. Infer the most fitting genre from the outline.\n"
            "Rules:\n"
            "- Output ONLY a short genre label (2-4 words).\n"
            "- No quotes, no prefix, no punctuation at the end.\n\n"
            f"OUTLINE:\n{outline[:2500]}"
        )
        try:
            raw = (AIEngine().generate(prompt, model).get("text", "") or "").strip()
            raw = re.sub(r'(?i)^(genre)[:\s-]*', '', raw).strip()
            raw = raw.replace('"', "").replace("'", "").strip()
            genre = raw.splitlines()[0].strip()
            # Keep it clean / short
            genre = re.sub(r"[^\w\s/&-]", "", genre).strip()
            if len(genre) > 40:
                genre = genre[:40].strip()
            return genre
        except Exception:
            logger.warning("Genre detection failed", exc_info=True)
            return ""

    @staticmethod
    def enrich_entity(name: str, category: str, desc: str, model: str) -> str:
        prompt = (
            f"NAME: {name}\nCATEGORY: {category}\nCURRENT INFO: {desc}\n"
            "TASK: Expand on this entry with creative details, backstory, or physical description.\n"
            "RULES: Keep it concise (under 50 words). Bullet points are okay."
        )
        return AIEngine().generate(prompt, model).get("text", "") or ""

    @staticmethod
    def coherence_check(
        memory: str,
        author_note: str,
        style_guide: str,
        outline: str,
        world_bible: str,
        chapters: List[Dict[str, Any]],
        model: str,
    ) -> List[Dict[str, Any]]:
        if not chapters:
            return []
        prompt = (
            "You are a developmental editor checking continuity and canon coherence.\n"
            "Identify contradictions, timeline issues, or inconsistent details.\n"
            "Return ONLY JSON (no markdown) as a list of objects with keys:\n"
            "- chapter_index (number)\n"
            "- issue (short description)\n"
            "- target_excerpt (exact text to replace, must exist in the chapter)\n"
            "- suggested_rewrite (replacement text to fix coherence)\n"
            "- confidence (low|medium|high)\n\n"
            f"PROJECT MEMORY:\n{(memory or '')[:2000]}\n\n"
            f"AUTHOR NOTE:\n{(author_note or '')[:1200]}\n\n"
            f"STYLE GUIDE:\n{(style_guide or '')[:1200]}\n\n"
            f"WORLD BIBLE:\n{(world_bible or '')[:2400]}\n\n"
            f"OUTLINE:\n{(outline or '')[:2000]}\n\n"
            "CHAPTERS (summaries + excerpts):\n"
            f"{json.dumps(chapters, ensure_ascii=False)}"
        )
        return AIEngine().generate_json(prompt, model) or []


class StoryEngine:
    @staticmethod
    def summarize(text: str, model: str) -> str:
        if not text:
            return ""
        prompt = f"Summarize this scene concisely (under 100 words):\n\n{text[:4000]}"
        return AIEngine().generate(prompt, model).get("text", "") or ""

    @staticmethod
    def generate_chapter_prompt(project: Project, chapter_index: int, target_words: int) -> str:
        hard_rules = (project.memory_hard or project.memory or "").strip()[:1500]
        hard_block = f"HARD CANON RULES (STRICT):\n{hard_rules}\n\n" if hard_rules else ""
        soft_guidelines = (project.memory_soft or "").strip()[:1500]
        soft_block = f"SOFT GUIDELINES (STYLE/CONTEXT):\n{soft_guidelines}\n\n" if soft_guidelines else ""
        memory_context = (project.memory or "").strip()[:1500]
        memory_block = f"PROJECT MEMORY:\n{memory_context}\n\n" if memory_context else ""
        author_note = (project.author_note or "").strip()[:1200]
        author_block = f"AUTHOR NOTE:\n{author_note}\n\n" if author_note else ""
        style_guide = (project.style_guide or "").strip()[:1200]
        style_block = f"STYLE GUIDE:\n{style_guide}\n\n" if style_guide else ""
        outline_context = (project.outline or "")[:3000]
        match = re.search(rf"(?i)Chapter {chapter_index}[:\s]+(.*?)(?=\n|$)", project.outline or "")
        if match:
            specific_beat = match.group(1).strip()
            outline_context = f"{outline_context}\n\nCURRENT CHAPTER OBJECTIVE: {specific_beat}"

        prev_chaps = [c for c in project.get_ordered_chapters() if c.index < chapter_index]
        story_so_far = ""
        prev_text = ""

        if prev_chaps:
            # Use list comprehension and join for efficient string building
            story_parts = ["PREVIOUS EVENTS:"]
            for c in prev_chaps[-5:]:
                summ = c.summary if c.summary else "No summary."
                story_parts.append(f"Ch {c.index}: {summ}")
            story_so_far = "\n".join(story_parts) + "\n"
            prev_text = f"\nIMMEDIATELY PRECEDING SCENE:\n{(prev_chaps[-1].content or '')[-1500:]}\n"

        prompt = (
            f"TITLE: {project.title}\nGENRE: {project.genre}\n"
            f"{hard_block}"
            f"{soft_block}"
            f"{memory_block}"
            f"{author_block}"
            f"{style_block}"
            f"OUTLINE CONTEXT:\n{outline_context}\n\n"
            f"{story_so_far}"
            f"{prev_text}\n"
            f"TASK: Write Chapter {chapter_index}.\n"
            f"LENGTH GOAL: {target_words} words.\n"
            "INSTRUCTIONS:\n"
            "1. Continue directly from the preceding scene (if any).\n"
            "2. Match the writing style and tone of the previous text.\n"
            "3. Focus on the 'Current Chapter Objective' if provided.\n"
            "4. Do not output the chapter title. Just the story prose."
        )
        return prompt

    @staticmethod
    def reverse_engineer_outline(project: Project, model: str) -> str:
        chaps = project.get_ordered_chapters()
        if not chaps:
            return "No content."
        # Use list comprehension and join for efficient string building
        chapter_summaries = [
            f"Ch {c.index} ({c.title}): {c.summary or (c.content or '')[:300]}"
            for c in chaps
        ]
        txt = "\n".join(chapter_summaries) + "\n"
        prompt = f"Create a structured outline based on these chapters:\n\n{txt}"
        return AIEngine().generate(prompt, model).get("text", "") or ""


REWRITE_PRESETS = {
    "Custom": "Use your own custom instructions",
    "Fix Grammar": "Correct grammar and spelling only.",
    "Improve Flow": "Fix awkward phrasing and sentence rhythm.",
    "Sensory Expansion": "Show, Don't Tell - Add smells, sounds, and textures.",
    "Deepen POV": "Add more internal monologue and emotional reaction.",
    "Make Witty": "Add humor, banter, and irony.",
    "Make Darker": "Grim, moody, noir-style descriptions.",
    "Expand": "Write more details, double the length.",
}


def rewrite_prompt(text: str, preset: str, custom: str = "") -> str:
    text = sanitize_ai_input(text, AppConfig.MAX_PROMPT_CHARS)
    custom = sanitize_ai_input(custom, 2000)
    instr = custom if preset == "Custom" else REWRITE_PRESETS.get(preset, "")
    return f"Act as an editor.\nTASK: {preset}\nDETAILS: {instr}\n\nINPUT TEXT:\n{text}"
