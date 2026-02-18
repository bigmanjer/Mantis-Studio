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
    # Note: Both 'current_page' and 'page' are used for compatibility
    # 'page' is the main router key, 'current_page' is for navigation tracking
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
    # TODO: Calculate actual chapter count from loaded projects
    c2.metric("Chapters", "—")
    # TODO: Calculate total word count across all projects
    c3.metric("Word Count", "—")
    
    st.divider()
    
    # Recent Projects list
    st.subheader("Recent Projects")
    
    if not st.session_state.projects:
        st.info("No projects yet. Create one to begin.")
    else:
        # Show up to 5 most recent projects with clickable buttons
        for idx, project in enumerate(st.session_state.projects[:5]):
            # Handle different project data structures
            if isinstance(project, dict):
                project_name = project.get("title") or project.get("name") or "Untitled"
                project_path = project.get("path") or project.get("filepath")
            elif hasattr(project, "title"):
                project_name = project.title
                project_path = getattr(project, "filepath", None)
            else:
                project_name = str(project)
                project_path = None
            
            # Create clickable button for each project
            col1, col2 = st.columns([4, 1])
            with col1:
                st.write(f"📁 {project_name}")
            with col2:
                if st.button("Open", key=f"open_project_{idx}", use_container_width=True):
                    # Load and switch to the project
                    if project_path:
                        try:
                            from app.services.projects import Project
                            loaded = Project.load(project_path)
                            if loaded:
                                st.session_state.project = loaded
                                st.toast(f"Loaded project: {project_name}")
                        except (FileNotFoundError, PermissionError):
                            st.error(f"Failed to load project '{project_name}'. The project file may be missing or inaccessible.")
                        except Exception as e:
                            st.error(f"Failed to load project '{project_name}'. The project file may be corrupted.")
                    navigate("chapters")
    
    st.divider()
    
    # Project Progress widget
    st.subheader("Project Progress")
    # TODO: Calculate actual progress based on active project completion
    st.progress(0.0)


# Legacy compatibility - keep render_home for existing code
def render_home(ctx: Any) -> None:
    """Legacy render function for compatibility.
    
    This maintains backward compatibility with the router that calls render_home(ctx).
    """
    render(ctx)
