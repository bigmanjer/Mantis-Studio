from __future__ import annotations

from contextlib import nullcontext

import app.layout.enhanced_sidebar as sidebar


class _SessionState(dict):
    def __getattr__(self, item):
        try:
            return self[item]
        except KeyError as exc:
            raise AttributeError(item) from exc

    def __setattr__(self, key, value):
        self[key] = value


class _FakeStreamlit:
    def __init__(self, *, button_returns: bool = False):
        self.session_state = _SessionState()
        self._button_returns = button_returns
        self.rerun_called = False

    @property
    def sidebar(self):
        return nullcontext()

    def html(self, *_args, **_kwargs):
        return None

    def image(self, *_args, **_kwargs):
        return None

    def markdown(self, *_args, **_kwargs):
        return None

    def selectbox(self, _label, options, index=0, **_kwargs):
        return options[index]

    def expander(self, *_args, **_kwargs):
        return nullcontext()

    def checkbox(self, _label, value=False, **_kwargs):
        return value

    def button(self, *_args, **_kwargs):
        return self._button_returns

    def divider(self):
        return None

    def caption(self, *_args, **_kwargs):
        return None

    def columns(self, count):
        return tuple(nullcontext() for _ in range(count))

    def toast(self, *_args, **_kwargs):
        return None

    def rerun(self):
        self.rerun_called = True


def test_render_enhanced_sidebar_tolerates_missing_key_scope(monkeypatch):
    fake_st = _FakeStreamlit()
    monkeypatch.setattr(sidebar, "st", fake_st)

    sidebar.render_enhanced_sidebar(
        version="1.0.0",
        project=None,
        current_page="home",
        world_focus="",
        debug_enabled=False,
        key_scope=None,
        slugify=lambda value: value.lower().replace(" ", "_"),
        save_project_callback=lambda: None,
        close_project_callback=lambda: None,
    )

    assert "debug" in fake_st.session_state


def test_render_navigation_section_routes_and_reruns(monkeypatch):
    fake_st = _FakeStreamlit(button_returns=True)
    monkeypatch.setattr(sidebar, "st", fake_st)

    fake_st.session_state["page"] = "home"

    sidebar.render_navigation_section(
        section_name="Test",
        nav_items=[("Memory", "memory", "🧠")],
        current_page="home",
        world_focus="",
        expanded=True,
        slugify=lambda value: value.lower(),
        scope=lambda _name: nullcontext(),
    )

    assert fake_st.session_state["world_focus_tab"] == "Memory"
    assert fake_st.session_state["page"] == "world"
    assert fake_st.rerun_called is True
