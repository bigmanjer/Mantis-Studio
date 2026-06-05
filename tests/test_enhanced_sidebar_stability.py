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
        self.button_keys = []

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

    def button(self, *_args, **kwargs):
        self.button_keys.append(kwargs.get("key"))
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

    assert fake_st.rerun_called is False
    assert "sidebar_theme_dark" in fake_st.button_keys
    assert all("_sidebar_render_suffix" not in str(key) for key in fake_st.button_keys)


def test_render_enhanced_sidebar_keeps_widget_keys_stable(monkeypatch):
    fake_st = _FakeStreamlit()
    monkeypatch.setattr(sidebar, "st", fake_st)

    render_args = dict(
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
    sidebar.render_enhanced_sidebar(**render_args)
    first_keys = list(fake_st.button_keys)
    fake_st.button_keys.clear()

    sidebar.render_enhanced_sidebar(**render_args)

    assert fake_st.button_keys == first_keys


def test_render_navigation_section_routes_and_reruns(monkeypatch):
    fake_st = _FakeStreamlit(button_returns=True)
    monkeypatch.setattr(sidebar, "st", fake_st)

    fake_st.session_state["page"] = "home"

    sidebar.render_navigation_section(
        section_name="Test",
        nav_items=[("Memory", "memory", "")],
        current_page="home",
        world_focus="",
        expanded=True,
        slugify=lambda value: value.lower(),
        key_scope=lambda _name: nullcontext(),
    )

    assert fake_st.session_state["page"] == "memory"
    assert fake_st.rerun_called is True


def test_render_navigation_section_prefers_navigation_callback(monkeypatch):
    fake_st = _FakeStreamlit(button_returns=True)
    monkeypatch.setattr(sidebar, "st", fake_st)
    calls = []

    fake_st.session_state["page"] = "home"

    sidebar.render_navigation_section(
        section_name="Test",
        nav_items=[("Projects", "projects", "")],
        current_page="home",
        world_focus="",
        expanded=True,
        slugify=lambda value: value.lower(),
        key_scope=lambda _name: nullcontext(),
        on_navigate=calls.append,
    )

    assert calls == ["projects"]
    assert fake_st.session_state["page"] == "home"
    assert fake_st.rerun_called is False
