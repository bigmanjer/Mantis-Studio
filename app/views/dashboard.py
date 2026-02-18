"""Dashboard view - main application home screen."""

from __future__ import annotations

from typing import Any


def render(ctx: Any = None) -> None:
    """Render the modern dashboard home screen.
    
    This is the main landing page with quick actions, workspace summary,
    recent projects, and progress tracking.
    
    Args:
        ctx: UI context object (optional, uses streamlit directly if not provided)
    """
    import streamlit as st
    from app.core.navigation import navigate
    
    # Ensure session state safety
    if "current_page" not in st.session_state:
        st.session_state.current_page = "home"
    
    if "page" not in st.session_state:
        st.session_state.page = "home"
    
    # Initialize projects list if not present
    if "projects" not in st.session_state:
        st.session_state.projects = []
    
    # Header section
    st.title("Mantis Studio")
    st.caption("Your AI writing workspace")
    
    st.divider()
    
    # Quick Actions row
    st.subheader("Quick Actions")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🆕 New Project", use_container_width=True):
            navigate("projects")
    
    with col2:
        if st.button("✍️ Continue Writing", use_container_width=True):
            navigate("chapters")
    
    with col3:
        if st.button("🌍 World Bible", use_container_width=True):
            navigate("world")
    
    st.divider()
    
    # Workspace Summary metrics
    st.subheader("Workspace Summary")
    
    c1, c2, c3 = st.columns(3)
    
    # Count projects
    project_count = len(st.session_state.projects)
    c1.metric("Projects", project_count)
    c2.metric("Chapters", "—")
    c3.metric("Word Count", "—")
    
    st.divider()
    
    # Recent Projects list
    st.subheader("Recent Projects")
    
    if not st.session_state.projects:
        st.info("No projects yet. Create one to begin.")
    else:
        # Show up to 5 most recent projects
        for project in st.session_state.projects[:5]:
            # Handle different project data structures
            if isinstance(project, dict):
                project_name = project.get("title") or project.get("name") or "Untitled"
                st.write(f"📁 {project_name}")
            elif hasattr(project, "title"):
                st.write(f"📁 {project.title}")
            else:
                st.write(f"📁 {project}")
    
    st.divider()
    
    # Project Progress widget
    st.subheader("Project Progress")
    st.progress(0.0)


# Legacy compatibility - keep render_home for existing code
def render_home(ctx: Any) -> None:
    """Legacy render function for compatibility.
    
    This maintains backward compatibility with the router that calls render_home(ctx).
    """
    render(ctx)
