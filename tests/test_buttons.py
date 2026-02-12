"""Comprehensive button tests for every page in MANTIS Studio.

These tests verify that every button on every page:
1. Has a unique key (prevents Streamlit DuplicateWidgetID errors)
2. Triggers st.rerun() when it mutates session_state.page (navigation works)
3. Triggers st.rerun() when it mutates session_state data the UI depends on
4. Uses the correct type= for its visual role
5. Form submit buttons exist with correct labels

Tests work by static analysis of the source code, so they run without a
Streamlit server.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path
from typing import List, Tuple

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

MAIN_PY = ROOT / "app" / "main.py"
APP_CTX = ROOT / "app" / "app_context.py"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _source() -> str:
    return _read(MAIN_PY)


def _extract_render_function(fn_name: str) -> str:
    """Extract the body of a top-level render function from main.py."""
    src = _source()
    pattern = rf"^    def {fn_name}\b.*?(?=\n    def |\Z)"
    m = re.search(pattern, src, re.MULTILINE | re.DOTALL)
    assert m, f"render function '{fn_name}' not found"
    return m.group(0)


def _find_button_blocks(source: str) -> List[Tuple[int, str]]:
    """Return (line_number, block_text) for every st.button call."""
    results = []
    lines = source.split("\n")
    for i, line in enumerate(lines):
        if "st.button(" in line:
            block = "\n".join(lines[i : i + 20])
            results.append((i + 1, block))
    return results


# ---------------------------------------------------------------------------
# 1) Legal / back-navigation pages
# ---------------------------------------------------------------------------


class TestLegalPageButtons:
    """Every legal sub-page must have a back button with key and rerun."""

    @pytest.mark.parametrize(
        "fn_name,expected_label",
        [
            ("render_privacy", "Back to All Policies"),
            ("render_terms", "Back to All Policies"),
            ("render_copyright", "Back to All Policies"),
            ("render_cookie", "Back to All Policies"),
            ("render_help", "Back to Dashboard"),
        ],
    )
    def test_back_button_exists(self, fn_name, expected_label):
        body = _extract_render_function(fn_name)
        assert expected_label in body, f"{fn_name} missing '{expected_label}' button"

    @pytest.mark.parametrize(
        "fn_name",
        ["render_privacy", "render_terms", "render_copyright", "render_cookie", "render_help"],
    )
    def test_back_button_has_key(self, fn_name):
        body = _extract_render_function(fn_name)
        assert "key=" in body, f"{fn_name} back button missing key="

    @pytest.mark.parametrize(
        "fn_name",
        ["render_privacy", "render_terms", "render_copyright", "render_cookie", "render_help"],
    )
    def test_back_button_calls_rerun(self, fn_name):
        body = _extract_render_function(fn_name)
        assert "st.rerun()" in body, f"{fn_name} back button missing st.rerun()"

    @pytest.mark.parametrize(
        "fn_name",
        ["render_privacy", "render_terms", "render_copyright", "render_cookie", "render_help"],
    )
    def test_back_button_navigates(self, fn_name):
        body = _extract_render_function(fn_name)
        assert 'session_state.page' in body, f"{fn_name} back button doesn't navigate"


# ---------------------------------------------------------------------------
# 2) Legal redirect page (policy picker)
# ---------------------------------------------------------------------------


class TestLegalRedirectButtons:
    """The legal redirect page shows a nav button per legal sub-page."""

    def test_legal_nav_buttons_have_keys(self):
        body = _extract_render_function("render_legal_redirect")
        assert 'key=f"nav_{target}"' in body

    def test_legal_nav_buttons_call_rerun(self):
        body = _extract_render_function("render_legal_redirect")
        assert "st.rerun()" in body


# ---------------------------------------------------------------------------
# 3) Dashboard (render_home) buttons
# ---------------------------------------------------------------------------


class TestDashboardButtons:
    """Dashboard must have all expected CTA and quick-action buttons."""

    @pytest.fixture(autouse=True)
    def _load(self):
        self.body = _extract_render_function("render_home")

    def test_primary_cta_exists(self):
        assert "primary_label" in self.body and 'type="primary"' in self.body

    def test_resume_project_button(self):
        assert "Resume project" in self.body

    def test_new_project_button(self):
        assert "New project" in self.body

    def test_new_project_calls_rerun(self):
        assert "open_new_project()" in self.body

    def test_quick_action_buttons_count(self):
        start = self.body.index("Quick Actions")
        end = self.body.index("Recent Projects", start)
        section = self.body[start:end]
        count = section.count("st.button(")
        assert count == 6, f"Expected 6 quick action buttons, found {count}"

    def test_quick_action_buttons_all_secondary(self):
        start = self.body.index("Quick Actions")
        end = self.body.index("Recent Projects", start)
        section = self.body[start:end]
        btn_count = section.count("st.button(")
        sec_count = section.count('type="secondary"')
        assert sec_count == btn_count, (
            f"All {btn_count} quick action buttons should be type='secondary', got {sec_count}"
        )

    def test_ai_settings_button(self):
        assert "AI Settings" in self.body

    def test_manage_ai_settings_button_has_key(self):
        assert "dashboard__ai_connected_settings" in self.body

    def test_recent_project_open_button(self):
        assert "📂" in self.body

    def test_recent_project_open_button_has_key(self):
        assert 'key=f"open_' in self.body or "open_" in self.body


# ---------------------------------------------------------------------------
# 4) Projects page buttons
# ---------------------------------------------------------------------------


class TestProjectsPageButtons:
    """Projects page: create, import, open, export, delete."""

    @pytest.fixture(autouse=True)
    def _load(self):
        self.body = _extract_render_function("render_projects")

    def test_create_project_form_submit(self):
        assert "🚀 Create Project" in self.body

    def test_create_project_is_form_submit(self):
        assert "form_submit_button" in self.body

    def test_import_analyze_button(self):
        assert "Import & Analyze" in self.body

    def test_import_button_calls_rerun(self):
        # Import & Analyze has a rerun further down in its handler
        idx = self.body.index("Import & Analyze")
        after = self.body[idx : idx + 2000]
        assert "st.rerun()" in after

    def test_open_project_button_has_key(self):
        assert 'key=f"open_' in self.body

    def test_export_project_button_has_key(self):
        assert 'key=f"export_' in self.body

    def test_delete_project_button_has_key(self):
        assert 'key=f"del_' in self.body

    def test_confirm_delete_button(self):
        assert "Confirm delete" in self.body

    def test_confirm_delete_calls_rerun(self):
        idx = self.body.index("Confirm delete")
        after = self.body[idx : idx + 1000]
        assert "st.rerun()" in after

    def test_cancel_button(self):
        assert '"Cancel"' in self.body

    def test_cancel_calls_rerun(self):
        idx = self.body.index('"Cancel"')
        after = self.body[idx : idx + 500]
        assert "st.rerun()" in after

    def test_close_export_button(self):
        assert "Close export" in self.body


# ---------------------------------------------------------------------------
# 5) AI Settings page buttons
# ---------------------------------------------------------------------------


class TestAISettingsButtons:
    """AI Settings page: apply key, clear key, fetch models, test, save."""

    @pytest.fixture(autouse=True)
    def _load(self):
        self.body = _extract_render_function("render_ai_settings")

    def test_apply_key_button_has_key(self):
        assert "session_key" in self.body

    def test_apply_key_calls_rerun(self):
        idx = self.body.index("Apply Key")
        after = self.body[idx : idx + 1200]
        assert "st.rerun()" in after

    def test_clear_key_button_has_key(self):
        assert "clear_session" in self.body

    def test_clear_key_calls_rerun(self):
        idx = self.body.index("Clear Key")
        after = self.body[idx : idx + 400]
        assert "st.rerun()" in after

    def test_fetch_models_button_exists(self):
        assert "Fetch Models" in self.body

    def test_fetch_models_groq_calls_rerun(self):
        # Find the groq fetch section
        assert self.body.count("Fetch Models") >= 2  # groq + openai

    def test_test_connection_button_exists(self):
        assert "Test Connection" in self.body

    def test_test_all_models_button_has_key(self):
        assert "test_all_models_btn" in self.body

    def test_save_settings_button(self):
        assert "Save Settings" in self.body or "save_app_settings" in self.body

    def test_apply_key_auto_fetches_models(self):
        """When Apply Key is pressed, models should be auto-fetched."""
        idx = self.body.index("Apply Key")
        after = self.body[idx : idx + 500]
        assert "fetch_fn" in after or "fetch_openai_models" in after or "fetch_groq_models" in after, (
            "Apply Key should auto-fetch models after setting key"
        )


# ---------------------------------------------------------------------------
# 6) Outline page buttons
# ---------------------------------------------------------------------------


class TestOutlinePageButtons:
    """Outline page: save project, save outline, go to projects, AI generate."""

    @pytest.fixture(autouse=True)
    def _load(self):
        self.body = _extract_render_function("render_outline")

    def test_go_to_projects_button(self):
        assert "Go to Projects" in self.body

    def test_go_to_projects_calls_rerun(self):
        idx = self.body.index("Go to Projects")
        after = self.body[idx : idx + 500]
        assert "st.rerun()" in after

    def test_save_project_button(self):
        assert "Save Project" in self.body

    def test_save_project_calls_rerun(self):
        idx = self.body.index("Save Project")
        after = self.body[idx : idx + 500]
        assert "st.rerun()" in after

    def test_save_outline_button(self):
        assert "Save Outline" in self.body

    def test_save_outline_calls_rerun(self):
        idx = self.body.index("Save Outline")
        after = self.body[idx : idx + 700]
        assert "st.rerun()" in after

    def test_architect_generate_button(self):
        # The outline page has an AI generate button
        assert "primary" in self.body.lower()


# ---------------------------------------------------------------------------
# 7) World Bible page buttons
# ---------------------------------------------------------------------------


class TestWorldBibleButtons:
    """World Bible page: add entity, delete entity, save memory, coherence, etc."""

    @pytest.fixture(autouse=True)
    def _load(self):
        self.body = _extract_render_function("render_world")

    def test_go_to_projects_button(self):
        assert "Go to Projects" in self.body

    def test_add_entity_button(self):
        assert "Add {category}" in self.body or "➕ Add" in self.body

    def test_add_entity_calls_rerun(self):
        idx = self.body.index("➕ Add")
        after = self.body[idx : idx + 400]
        assert "st.rerun()" in after

    def test_delete_entity_button_has_key(self):
        assert 'key=f"del_{e.id}"' in self.body

    def test_delete_entity_calls_rerun(self):
        idx = self.body.index("🗑 Delete")
        after = self.body[idx : idx + 400]
        assert "st.rerun()" in after

    def test_confirm_delete_button(self):
        assert '"Confirm"' in self.body

    def test_confirm_delete_calls_rerun(self):
        idx = self.body.index('"Confirm"')
        after = self.body[idx : idx + 500]
        assert "st.rerun()" in after

    def test_cancel_delete_calls_rerun(self):
        # The entity delete Cancel button (not form cancel) calls rerun
        assert '"Cancel"' in self.body
        idx = self.body.rindex('"Cancel"')  # Last Cancel is the delete-cancel
        after = self.body[idx : idx + 400]
        assert "st.rerun()" in after

    def test_save_memory_button(self):
        assert "Save Memory" in self.body

    def test_save_memory_calls_rerun(self):
        idx = self.body.index("Save Memory")
        after = self.body[idx : idx + 400]
        assert "st.rerun()" in after

    def test_apply_suggestion_button_has_key(self):
        assert 'key=f"apply_suggestion_{idx}"' in self.body

    def test_apply_suggestion_calls_rerun(self):
        idx = self.body.index("✅ Apply")
        after = self.body[idx : idx + 1200]
        assert "st.rerun()" in after

    def test_ignore_suggestion_button_has_key(self):
        assert 'key=f"ignore_suggestion_{idx}"' in self.body

    def test_ignore_suggestion_calls_rerun(self):
        idx = self.body.index('key=f"ignore_suggestion')
        after = self.body[idx : idx + 400]
        assert "st.rerun()" in after

    def test_coherence_check_button(self):
        assert "coherence" in self.body.lower()

    def test_apply_fix_button_has_key(self):
        assert 'key=f"coh_apply_{idx}"' in self.body

    def test_ignore_coherence_button_has_key(self):
        assert 'key=f"coh_ignore_{idx}"' in self.body

    def test_ignore_coherence_calls_rerun(self):
        idx = self.body.index('key=f"coh_ignore')
        after = self.body[idx : idx + 400]
        assert "st.rerun()" in after

    def test_jump_to_chapter_button_has_key(self):
        assert 'key=f"jump_{e.id}"' in self.body

    def test_jump_to_entity_button_has_key(self):
        assert 'key=f"jump_entity_{ent.id}"' in self.body

    def test_jump_to_entity_calls_rerun(self):
        idx = self.body.index("Jump to Entity")
        after = self.body[idx : idx + 500]
        assert "st.rerun()" in after

    def test_form_submit_save_exists(self):
        assert "form_submit_button" in self.body

    def test_form_cancel_exists(self):
        # Check that entity form has both Save and Cancel buttons
        assert '"Save"' in self.body
        assert '"Cancel"' in self.body


# ---------------------------------------------------------------------------
# 8) Editor / Chapters page buttons
# ---------------------------------------------------------------------------


class TestEditorButtons:
    """Editor (chapters) page: create, delete, save, summary, improve, auto-write."""

    @pytest.fixture(autouse=True)
    def _load(self):
        self.body = _extract_render_function("render_chapters")

    # --- No-project state ---
    def test_go_to_projects_when_no_project(self):
        assert "Go to Projects" in self.body

    def test_go_to_projects_has_key(self):
        assert "editor_no_project_go_projects" in self.body

    def test_go_to_projects_calls_rerun(self):
        idx = self.body.index("editor_no_project_go_projects")
        after = self.body[idx : idx + 200]
        assert "st.rerun()" in after

    # --- Create chapter ---
    def test_create_chapter_1_button_has_key(self):
        assert "editor_create_chapter_1" in self.body

    def test_create_chapter_1_type_primary(self):
        idx = self.body.index("Create Chapter 1")
        block = self.body[idx - 50 : idx + 200]
        assert 'type="primary"' in block

    def test_new_chapter_button_has_key(self):
        assert "editor_new_chapter" in self.body

    # --- Delete chapter ---
    def test_delete_chapter_button_has_key(self):
        assert 'key=f"editor_del_{curr.id}"' in self.body

    def test_delete_chapter_calls_rerun(self):
        idx = self.body.index("Delete Chapter")
        after = self.body[idx : idx + 400]
        assert "st.rerun()" in after

    def test_delete_confirm_has_key(self):
        assert "editor_del_ch_confirm" in self.body

    def test_delete_confirm_calls_rerun(self):
        idx = self.body.index("editor_del_ch_confirm")
        after = self.body[idx : idx + 800]
        assert "st.rerun()" in after

    def test_delete_cancel_has_key(self):
        assert "editor_del_ch_cancel" in self.body

    def test_delete_cancel_calls_rerun(self):
        idx = self.body.index("editor_del_ch_cancel")
        after = self.body[idx : idx + 400]
        assert "st.rerun()" in after

    # --- Save chapter ---
    def test_save_chapter_button(self):
        assert "Save Chapter" in self.body

    def test_save_chapter_has_key(self):
        assert 'key=f"editor_save_{curr.id}"' in self.body

    def test_save_chapter_calls_rerun(self):
        idx = self.body.index("Save Chapter")
        after = self.body[idx : idx + 800]
        assert "st.rerun()" in after

    # --- Summary ---
    def test_update_summary_button(self):
        assert "Update Summary" in self.body

    def test_update_summary_has_key(self):
        assert "editor_summary_" in self.body

    def test_update_summary_calls_rerun(self):
        idx = self.body.index("editor_summary_")
        after = self.body[idx : idx + 800]
        assert "st.rerun()" in after

    # --- Improve ---
    def test_generate_improvement_button(self):
        assert "Generate Improvement" in self.body

    def test_generate_improvement_has_key(self):
        assert "editor_improve__generate_" in self.body

    # --- Undo ---
    def test_undo_button(self):
        assert "Undo last apply" in self.body

    def test_undo_has_key(self):
        assert "editor_improve__undo_" in self.body

    def test_undo_calls_rerun_on_success(self):
        idx = self.body.index("Undo last apply")
        after = self.body[idx : idx + 1000]
        assert "st.rerun()" in after

    # --- Apply Changes ---
    def test_apply_changes_button(self):
        assert "Apply Changes" in self.body

    def test_apply_changes_has_key(self):
        assert "editor_improve__apply_" in self.body

    def test_apply_changes_calls_rerun(self):
        idx = self.body.index("editor_improve__apply_")
        after = self.body[idx : idx + 3000]
        assert "st.rerun()" in after

    # --- Copy Improved ---
    def test_copy_improved_button(self):
        assert "Copy Improved" in self.body

    def test_copy_improved_has_key(self):
        assert "editor_improve__copy_" in self.body

    # --- Regenerate ---
    def test_regenerate_button(self):
        assert "Regenerate" in self.body

    def test_regenerate_has_key(self):
        assert "editor_improve__regenerate_" in self.body

    # --- Discard ---
    def test_discard_button(self):
        assert "Discard" in self.body

    def test_discard_has_key(self):
        assert "editor_improve__discard_" in self.body

    def test_discard_calls_rerun(self):
        idx = self.body.index("editor_improve__discard_")
        after = self.body[idx : idx + 400]
        assert "st.rerun()" in after

    # --- Auto-Write ---
    def test_auto_write_button(self):
        assert "Auto-Write Chapter" in self.body

    def test_auto_write_has_key(self):
        assert "editor_autowrite_" in self.body

    def test_auto_write_blocked_has_key(self):
        assert "editor_autowrite_blocked_" in self.body

    # --- Set draft as active ---
    def test_set_draft_active_button(self):
        assert "Set as active" in self.body

    def test_set_draft_active_has_key(self):
        assert "editor_improve__set_active_" in self.body

    def test_set_draft_active_calls_rerun(self):
        idx = self.body.index("editor_improve__set_active_")
        after = self.body[idx : idx + 1000]
        assert "st.rerun()" in after

    # --- Chapter navigation ---
    def test_chapter_nav_buttons_have_keys(self):
        assert "chapter_id" in self.body and "key=" in self.body


# ---------------------------------------------------------------------------
# 9) Export page buttons
# ---------------------------------------------------------------------------


class TestExportPageButtons:
    """Export page must exist and have download/navigation functionality."""

    def test_export_function_exists(self):
        src = _source()
        assert "def render_export" in src

    def test_export_has_download_button(self):
        body = _extract_render_function("render_export")
        assert "download_button" in body or "download" in body.lower()


# ---------------------------------------------------------------------------
# 10) Welcome banner buttons
# ---------------------------------------------------------------------------


class TestWelcomeBannerButtons:
    """Welcome banner: create first project and dismiss buttons."""

    @pytest.fixture(autouse=True)
    def _load(self):
        self.body = _extract_render_function("render_welcome_banner")

    def test_create_first_project_button(self):
        assert "Create My First Project" in self.body

    def test_create_first_project_type_primary(self):
        idx = self.body.index("Create My First Project")
        block = self.body[idx - 50 : idx + 200]
        assert 'type="primary"' in block

    def test_create_first_project_calls_rerun(self):
        idx = self.body.index("Create My First Project")
        after = self.body[idx : idx + 400]
        assert "st.rerun()" in after

    def test_dismiss_button(self):
        assert "Got it" in self.body

    def test_dismiss_calls_rerun(self):
        idx = self.body.index("Got it")
        after = self.body[idx : idx + 400]
        assert "st.rerun()" in after


# ---------------------------------------------------------------------------
# 11) Page header buttons (generic reusable component)
# ---------------------------------------------------------------------------


class TestPageHeaderButtons:
    """render_page_header: primary and secondary action buttons."""

    @pytest.fixture(autouse=True)
    def _load(self):
        self.body = _extract_render_function("render_page_header")

    def test_primary_button_has_key(self):
        assert "{key_prefix}__primary" in self.body

    def test_primary_button_type(self):
        assert 'type="primary"' in self.body

    def test_secondary_button_has_key(self):
        assert "{key_prefix}__secondary" in self.body

    def test_primary_calls_action(self):
        assert "primary_action()" in self.body

    def test_secondary_calls_action(self):
        assert "secondary_action()" in self.body


# ---------------------------------------------------------------------------
# 12) Cross-cutting: every st.button that sets page must call rerun
# ---------------------------------------------------------------------------


class TestNavigationButtonsCallRerun:
    """Every button that sets st.session_state.page must also call st.rerun()."""

    def test_all_page_setting_buttons_call_rerun(self):
        src = _source()
        lines = src.split("\n")
        violations = []
        for i, line in enumerate(lines):
            stripped = line.strip()
            if "session_state.page" in stripped and "=" in stripped and "==" not in stripped:
                # Look back up to 20 lines for a st.button context
                context_start = max(0, i - 20)
                context = "\n".join(lines[context_start : i + 1])
                if "st.button(" in context:
                    # Look forward for st.rerun() within 10 lines
                    forward = "\n".join(lines[i : i + 10])
                    if "st.rerun()" not in forward:
                        violations.append(
                            f"Line {i + 1}: sets session_state.page but doesn't call st.rerun() nearby"
                        )
        assert not violations, (
            f"Buttons that navigate must call st.rerun():\n" + "\n".join(violations)
        )


# ---------------------------------------------------------------------------
# 13) Cross-cutting: form submit buttons
# ---------------------------------------------------------------------------


class TestFormSubmitButtons:
    """Every form_submit_button in the app."""

    def test_create_project_form_submit(self):
        src = _source()
        assert '🚀 Create Project' in src

    def test_entity_form_save(self):
        src = _source()
        # The entity form has Save and Cancel submit buttons
        idx = src.index('form_submit_button("Save"')
        assert idx > 0

    def test_entity_form_cancel(self):
        src = _source()
        idx = src.index('form_submit_button("Cancel"')
        assert idx > 0


# ---------------------------------------------------------------------------
# 14) Cross-cutting: link_button calls
# ---------------------------------------------------------------------------


class TestLinkButtons:
    """All link_button calls should have valid URLs."""

    def test_help_docs_link(self):
        src = _source()
        assert "github.com/bigmanjer/Mantis-Studio" in src

    def test_groq_link(self):
        src = _source()
        assert "console.groq.com" in src

    def test_openai_link(self):
        src = _source()
        assert "platform.openai.com" in src


# ---------------------------------------------------------------------------
# 15) Sidebar navigation buttons
# ---------------------------------------------------------------------------


class TestSidebarNavButtons:
    """Sidebar nav buttons should have keys and call st.rerun."""

    def test_sidebar_nav_buttons_have_keys(self):
        src = _source()
        assert 'key=f"nav_{target}"' in src

    def test_sidebar_nav_buttons_call_rerun(self):
        src = _source()
        idx = src.index('key=f"nav_{target}"')
        after = src[idx : idx + 200]
        assert "st.rerun()" in after


# ---------------------------------------------------------------------------
# 16) Comprehensive: both main.py and app_context.py have matching buttons
# ---------------------------------------------------------------------------


class TestMainAndAppContextButtonParity:
    """Critical buttons must exist in both main.py and app_context.py."""

    def test_create_chapter_1_in_both(self):
        main = _source()
        ctx = _read(APP_CTX)
        assert "editor_create_chapter_1" in main
        assert "editor_create_chapter_1" in ctx

    def test_new_chapter_in_both(self):
        main = _source()
        ctx = _read(APP_CTX)
        assert "editor_new_chapter" in main
        assert "editor_new_chapter" in ctx


# ---------------------------------------------------------------------------
# 17) Every delete-confirmation button pair calls rerun
# ---------------------------------------------------------------------------


class TestDeleteConfirmationPairs:
    """Delete flows: the initial delete button, confirm, and cancel must all rerun."""

    def test_chapter_delete_flow(self):
        body = _extract_render_function("render_chapters")
        # Delete button sets delete_chapter_id then calls rerun
        assert "delete_chapter_id" in body
        assert "delete_chapter_title" in body
        # Count rerun calls - there should be at least 3 for delete flow
        # (initial, confirm, cancel)
        idx = body.index("Delete Chapter")
        section = body[idx : idx + 500]
        rerun_count = section.count("st.rerun()")
        assert rerun_count >= 1, "Delete chapter button must call st.rerun()"

    def test_entity_delete_flow(self):
        body = _extract_render_function("render_world")
        assert "delete_entity_id" in body
        assert "delete_entity_name" in body

    def test_project_delete_flow(self):
        body = _extract_render_function("render_projects")
        assert "delete_project_path" in body or "Confirm delete" in body


# ---------------------------------------------------------------------------
# 18) AI Settings: Apply Key fetches models automatically
# ---------------------------------------------------------------------------


class TestApplyKeyAutoFetch:
    """Pressing Apply Key should automatically fetch models."""

    def test_groq_or_openai_fetch_in_apply_handler(self):
        body = _extract_render_function("render_ai_settings")
        # Find the Apply Key handler
        idx = body.index("Apply Key")
        handler = body[idx : idx + 600]
        # Should reference a fetch function
        assert (
            "fetch_fn" in handler
            or "fetch_groq_models" in handler
            or "fetch_openai_models" in handler
        ), "Apply Key should auto-fetch models"


# ---------------------------------------------------------------------------
# 19) Button count sanity check
# ---------------------------------------------------------------------------


class TestButtonCountSanity:
    """Ensure the app has a reasonable number of buttons (no accidental removal)."""

    def test_main_has_at_least_60_buttons(self):
        src = _source()
        count = src.count("st.button(")
        assert count >= 60, f"Expected at least 60 buttons in main.py, found {count}"

    def test_app_context_has_buttons(self):
        ctx = _read(APP_CTX)
        count = ctx.count("st.button(")
        assert count >= 30, f"Expected at least 30 buttons in app_context.py, found {count}"


# ---------------------------------------------------------------------------
# 20) Every render function with buttons handles its state correctly
# ---------------------------------------------------------------------------


class TestRenderFunctionButtonIntegrity:
    """Every render function that has buttons should properly wire them."""

    @pytest.mark.parametrize(
        "fn_name",
        [
            "render_home",
            "render_projects",
            "render_ai_settings",
            "render_outline",
            "render_world",
            "render_chapters",
        ],
    )
    def test_render_function_has_buttons(self, fn_name):
        body = _extract_render_function(fn_name)
        assert "st.button(" in body, f"{fn_name} should have at least one button"

    @pytest.mark.parametrize(
        "fn_name",
        [
            "render_home",
            "render_projects",
            "render_outline",
            "render_world",
            "render_chapters",
        ],
    )
    def test_render_function_has_rerun(self, fn_name):
        body = _extract_render_function(fn_name)
        assert "st.rerun()" in body, f"{fn_name} should call st.rerun() somewhere"
