# Mantis Studio: Competitive Analysis & Feature Roadmap
**Implementation-Ready Design Document**

**Version:** 1.0  
**Date:** February 2026  
**Status:** Design Specification  
**Target Audience:** Product Architects, Engineering Teams, Stakeholders

---

## Executive Summary

This document provides a comprehensive competitive analysis of Mantis Studio against leading AI writing platforms (Sudowrite, NovelAI, Jasper AI, and Squibler) and presents an implementation-ready roadmap for feature additions that will close the competitive gap while preserving Mantis Studio's core identity as a modular, narrative-focused AI writing system.

**Current Strengths:**
- Local-first workflow with privacy focus
- Structured World Bible system for canonical worldbuilding
- Single-entry, state-driven architecture
- AI-assisted drafting with context awareness
- Clean separation of concerns (services, views, components)

**Identified Gaps:**
- No cloud storage or multi-user support
- Limited collaboration capabilities
- Missing advanced AI narrative workflows (Describe, Expand, Rewrite)
- No export to professional formats (EPUB, DOCX, PDF)
- Minimal analytics and progress tracking
- Lack of project templates and guided workflows

This document outlines a phased implementation plan to address these gaps while maintaining code quality, modularity, and user experience.

---

## Table of Contents

1. [Competitive Feature Analysis](#1-competitive-feature-analysis)
2. [Must-Have Features](#2-must-have-features)
3. [Nice-to-Have Features](#3-nice-to-have-features)
4. [Technical Design Specifications](#4-technical-design-specifications)
5. [Implementation Roadmap](#5-implementation-roadmap)
6. [Risk Assessment](#6-risk-assessment)
7. [Success Metrics](#7-success-metrics)

---

## 1. Competitive Feature Analysis

### 1.1 Sudowrite

**Platform Focus:** Narrative-focused AI tools for creative writers  
**Target Audience:** Novelists, short story writers, creative fiction authors

#### Core Features
- **Describe**: Sensory expansion that adds vivid details to scenes
  - Expands descriptions with sight, sound, smell, taste, touch
  - Maintains narrative voice and style
  - Context-aware sensory enrichment
- **Expand**: Scene continuation and development
  - Generates next paragraphs/scenes based on context
  - Maintains plot continuity and character consistency
  - Offers multiple expansion options
- **Rewrite**: Tone, style, and pacing adjustments
  - Changes POV (1st person ↔ 3rd person)
  - Adjusts pacing (faster/slower)
  - Modifies tone (darker, lighter, more humorous)
- **Story Continuity & Context Awareness**
  - Story Bible integration
  - Character tracking across scenes
  - Automatic context injection

#### What Mantis Studio Currently Lacks
- ❌ **Dedicated "Describe" tool** for sensory expansion
- ❌ **Structured "Expand" workflow** with multiple generation options
- ❌ **Advanced "Rewrite" engine** with granular controls (POV, tone, pacing)
- ❌ **Automatic context injection** from World Bible into AI prompts
- ⚠️  **Story continuity tracking** (partially implemented via World Bible)

#### Competitive Gap Priority
**High Priority** - These are core narrative tools that directly compete with Mantis Studio's mission.

---

### 1.2 NovelAI

**Platform Focus:** Long-form fiction generation with deep customization  
**Target Audience:** Novel writers, worldbuilders, fanfiction authors

#### Core Features
- **Lorebook / Canon Memory System**
  - Hierarchical worldbuilding entries
  - Automatic context injection based on keywords
  - Entry activation rules and priorities
  - Category-based organization (characters, locations, lore)
- **Long-term Story Context**
  - Memory tokens for persistent narrative elements
  - Automatic summarization of previous chapters
  - Context budget management
- **Style and Voice Customization**
  - Author voice mimicry
  - Genre-specific presets
  - Fine-tuned model selection

#### What Mantis Studio Currently Lacks
- ✅ **World Bible** (similar to Lorebook, already implemented)
- ❌ **Automatic keyword-based context injection**
- ❌ **Context budget visualization** (how much context is being used)
- ❌ **Chapter summarization** for long-term memory
- ❌ **Style presets** (genre-specific, author voice)

#### Competitive Gap Priority
**Medium Priority** - Mantis Studio has a strong foundation (World Bible), but needs automation and UX improvements.

---

### 1.3 Jasper AI

**Platform Focus:** Business and marketing content generation  
**Target Audience:** Marketing teams, content creators, business writers

#### Core Features
- **Guided Templates**
  - SEO blog posts
  - Marketing copy (ads, landing pages, emails)
  - Social media content
  - Product descriptions
  - Business documents
- **Brand Voice Management**
  - Define and save brand voice profiles
  - Consistent tone across all content
  - Team-wide voice library
- **Team Collaboration**
  - Shared workspaces
  - Role-based permissions (Owner, Editor, Viewer)
  - Real-time collaboration
  - Version history and comments

#### What Mantis Studio Currently Lacks
- ❌ **Template library** for guided workflows
- ❌ **Brand voice / style profiles**
- ❌ **Multi-user collaboration** (no cloud backend)
- ❌ **Team workspaces** with permissions
- ❌ **Real-time collaboration** features

#### Competitive Gap Priority
**Low-Medium Priority** - Jasper AI targets a different market (business/marketing). However, collaboration and templates are valuable for Mantis Studio's evolution to multi-user SaaS.

---

### 1.4 Squibler

**Platform Focus:** Manuscript-level project organization  
**Target Audience:** Authors, screenwriters, manuscript-focused writers

#### Core Features
- **Manuscript-Level Organization**
  - Project → Book → Chapter → Scene hierarchy
  - Drag-and-drop scene reordering
  - Chapter and scene templates
- **Chapter Workflows**
  - Chapter status tracking (Draft, Revision, Final)
  - Chapter-level notes and metadata
  - Chapter goals and word count targets
- **Collaboration & Cloud Sync**
  - Real-time cloud sync across devices
  - Share manuscripts with beta readers or editors
  - Commenting and feedback system
  - Version history

#### What Mantis Studio Currently Lacks
- ⚠️  **Scene-level organization** (chapters exist, but no scene granularity)
- ❌ **Drag-and-drop scene reordering**
- ❌ **Chapter status workflow** (Draft → Revision → Final)
- ❌ **Cloud sync** (local-only storage)
- ❌ **Collaboration and sharing** features
- ⚠️  **Version history** (chapters have basic history, needs improvement)

#### Competitive Gap Priority
**High Priority** - Manuscript organization and collaboration are essential for competing in the AI writing platform market.

---

### 1.5 Summary of Competitive Gaps

| Feature Category | Sudowrite | NovelAI | Jasper AI | Squibler | Mantis Gap | Priority |
|-----------------|-----------|---------|-----------|----------|------------|----------|
| AI Narrative Tools (Describe, Expand, Rewrite) | ✅ | ⚠️ | ❌ | ❌ | ❌ | **High** |
| World Bible / Lorebook | ⚠️ | ✅ | ❌ | ⚠️ | ✅ | Low |
| Automatic Context Injection | ✅ | ✅ | ⚠️ | ❌ | ❌ | **High** |
| Scene-Level Organization | ⚠️ | ⚠️ | ❌ | ✅ | ❌ | **High** |
| Cloud Storage & Sync | ✅ | ✅ | ✅ | ✅ | ❌ | **High** |
| Multi-User Collaboration | ❌ | ❌ | ✅ | ✅ | ❌ | **Medium** |
| Team Workspaces & Permissions | ❌ | ❌ | ✅ | ⚠️ | ❌ | **Medium** |
| Template Library | ⚠️ | ⚠️ | ✅ | ✅ | ❌ | **Medium** |
| Export to EPUB/DOCX/PDF | ⚠️ | ⚠️ | ⚠️ | ✅ | ⚠️ | **High** |
| Writing Analytics | ⚠️ | ⚠️ | ⚠️ | ✅ | ⚠️ | **Medium** |
| Version History | ⚠️ | ❌ | ⚠️ | ✅ | ⚠️ | **Medium** |

**Legend:**  
✅ = Fully implemented  
⚠️ = Partially implemented  
❌ = Not implemented

---

## 2. Must-Have Features

These features are critical for Mantis Studio to compete effectively with leading AI writing platforms. They should be prioritized for implementation in the next 6-12 months.

---

### 2.1 Cloud Database with User Accounts

**Business Value:** Enable cloud storage, multi-device access, and data persistence across sessions.

#### 2.1.1 Current State
- **Storage:** Local JSON files in `storage/` directory
- **Authentication:** Optional OIDC (Google, Microsoft, Apple) via Supabase
- **Multi-tenancy:** Not supported
- **Session management:** Streamlit session state (ephemeral)

#### 2.1.2 Proposed Architecture

**Database:** PostgreSQL (via Supabase or self-hosted)

**Schema Overview:**

```sql
-- Core tables
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    username VARCHAR(100) UNIQUE,
    display_name VARCHAR(255),
    auth_provider VARCHAR(50), -- google, microsoft, apple, email
    auth_provider_id VARCHAR(255),
    created_at TIMESTAMP DEFAULT NOW(),
    last_login TIMESTAMP,
    subscription_tier VARCHAR(50) DEFAULT 'free', -- free, pro, team
    settings JSONB DEFAULT '{}'::jsonb
);

CREATE TABLE projects (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    owner_id UUID REFERENCES users(id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    project_type VARCHAR(50), -- novel, screenplay, worldbuilding, marketing
    created_at TIMESTAMP DEFAULT NOW(),
    modified_at TIMESTAMP DEFAULT NOW(),
    archived BOOLEAN DEFAULT FALSE,
    settings JSONB DEFAULT '{}'::jsonb,
    metadata JSONB DEFAULT '{}'::jsonb
);

CREATE TABLE manuscripts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    modified_at TIMESTAMP DEFAULT NOW(),
    status VARCHAR(50) DEFAULT 'draft', -- draft, revision, final
    order_index INTEGER DEFAULT 0
);

CREATE TABLE chapters (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    manuscript_id UUID REFERENCES manuscripts(id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL,
    content TEXT,
    summary TEXT,
    order_index INTEGER NOT NULL,
    word_count INTEGER DEFAULT 0,
    target_words INTEGER DEFAULT 1000,
    status VARCHAR(50) DEFAULT 'draft',
    created_at TIMESTAMP DEFAULT NOW(),
    modified_at TIMESTAMP DEFAULT NOW(),
    metadata JSONB DEFAULT '{}'::jsonb
);

CREATE TABLE scenes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    chapter_id UUID REFERENCES chapters(id) ON DELETE CASCADE,
    title VARCHAR(255),
    content TEXT,
    summary TEXT,
    order_index INTEGER NOT NULL,
    word_count INTEGER DEFAULT 0,
    status VARCHAR(50) DEFAULT 'draft',
    created_at TIMESTAMP DEFAULT NOW(),
    modified_at TIMESTAMP DEFAULT NOW(),
    metadata JSONB DEFAULT '{}'::jsonb
);

CREATE TABLE world_bible_entries (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    category VARCHAR(100), -- character, location, organization, lore, item
    description TEXT,
    aliases TEXT[], -- array of alternate names
    tags TEXT[],
    activation_keywords TEXT[], -- for auto-injection
    priority INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW(),
    modified_at TIMESTAMP DEFAULT NOW(),
    metadata JSONB DEFAULT '{}'::jsonb
);

CREATE TABLE revisions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    entity_type VARCHAR(50) NOT NULL, -- chapter, scene, manuscript
    entity_id UUID NOT NULL,
    content TEXT,
    revision_note TEXT,
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE project_collaborators (
    project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    role VARCHAR(50) NOT NULL, -- owner, editor, viewer
    invited_at TIMESTAMP DEFAULT NOW(),
    PRIMARY KEY (project_id, user_id)
);

CREATE TABLE team_workspaces (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    owner_id UUID REFERENCES users(id) ON DELETE CASCADE,
    created_at TIMESTAMP DEFAULT NOW(),
    settings JSONB DEFAULT '{}'::jsonb
);

CREATE TABLE workspace_members (
    workspace_id UUID REFERENCES team_workspaces(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    role VARCHAR(50) NOT NULL, -- admin, member, viewer
    joined_at TIMESTAMP DEFAULT NOW(),
    PRIMARY KEY (workspace_id, user_id)
);

-- Indexes for performance
CREATE INDEX idx_projects_owner ON projects(owner_id);
CREATE INDEX idx_manuscripts_project ON manuscripts(project_id);
CREATE INDEX idx_chapters_manuscript ON chapters(manuscript_id);
CREATE INDEX idx_scenes_chapter ON scenes(chapter_id);
CREATE INDEX idx_world_bible_project ON world_bible_entries(project_id);
CREATE INDEX idx_revisions_entity ON revisions(entity_type, entity_id);
CREATE INDEX idx_collaborators_project ON project_collaborators(project_id);
CREATE INDEX idx_collaborators_user ON project_collaborators(user_id);
```

#### 2.1.3 Backend Changes Required

**New Modules:**
```
app/
├── services/
│   ├── database.py           # Database connection and query utilities
│   ├── user_service.py       # User management (CRUD, authentication)
│   ├── project_service.py    # Project management (enhanced with DB)
│   ├── collaboration_service.py  # Sharing, permissions, invitations
│   └── sync_service.py       # Sync local ↔ cloud state
```

**Key Implementations:**

**`app/services/database.py`**
```python
"""Database connection and utilities for Mantis Studio."""
import os
from typing import Any, Dict, List, Optional
from contextlib import contextmanager
import psycopg2
from psycopg2.extras import RealDictCursor
from app.config.settings import AppConfig, logger

class Database:
    """PostgreSQL database connection manager."""
    
    def __init__(self):
        self.connection_string = os.getenv(
            "DATABASE_URL",
            AppConfig.DATABASE_URL
        )
        self._connection = None
    
    @contextmanager
    def get_connection(self):
        """Context manager for database connections."""
        conn = psycopg2.connect(
            self.connection_string,
            cursor_factory=RealDictCursor
        )
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            logger.error(f"Database error: {e}")
            raise
        finally:
            conn.close()
    
    def execute_query(
        self,
        query: str,
        params: Optional[tuple] = None,
        fetch: str = "all"
    ) -> Optional[List[Dict[str, Any]]]:
        """Execute a query and return results."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            
            if fetch == "all":
                return cursor.fetchall()
            elif fetch == "one":
                return cursor.fetchone()
            else:
                return None

# Global database instance
db = Database()
```

**`app/services/user_service.py`**
```python
"""User management service."""
from typing import Optional, Dict, Any
from uuid import UUID
from app.services.database import db
from app.config.settings import logger

class UserService:
    """Manage user accounts and authentication."""
    
    @staticmethod
    def create_user(
        email: str,
        auth_provider: str,
        auth_provider_id: str,
        display_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create a new user account."""
        query = """
            INSERT INTO users (email, auth_provider, auth_provider_id, display_name)
            VALUES (%s, %s, %s, %s)
            RETURNING id, email, display_name, subscription_tier, created_at
        """
        result = db.execute_query(
            query,
            (email, auth_provider, auth_provider_id, display_name),
            fetch="one"
        )
        logger.info(f"Created user: {email}")
        return result
    
    @staticmethod
    def get_user_by_email(email: str) -> Optional[Dict[str, Any]]:
        """Retrieve user by email."""
        query = "SELECT * FROM users WHERE email = %s"
        return db.execute_query(query, (email,), fetch="one")
    
    @staticmethod
    def get_user_by_id(user_id: UUID) -> Optional[Dict[str, Any]]:
        """Retrieve user by ID."""
        query = "SELECT * FROM users WHERE id = %s"
        return db.execute_query(query, (str(user_id),), fetch="one")
    
    @staticmethod
    def update_last_login(user_id: UUID) -> None:
        """Update user's last login timestamp."""
        query = "UPDATE users SET last_login = NOW() WHERE id = %s"
        db.execute_query(query, (str(user_id),), fetch=None)

user_service = UserService()
```

**`app/services/collaboration_service.py`**
```python
"""Project collaboration service."""
from typing import List, Dict, Any
from uuid import UUID
from app.services.database import db
from app.config.settings import logger

class CollaborationService:
    """Manage project sharing and permissions."""
    
    @staticmethod
    def add_collaborator(
        project_id: UUID,
        user_id: UUID,
        role: str = "viewer"
    ) -> Dict[str, Any]:
        """Add a collaborator to a project."""
        query = """
            INSERT INTO project_collaborators (project_id, user_id, role)
            VALUES (%s, %s, %s)
            ON CONFLICT (project_id, user_id)
            DO UPDATE SET role = EXCLUDED.role
            RETURNING *
        """
        result = db.execute_query(
            query,
            (str(project_id), str(user_id), role),
            fetch="one"
        )
        logger.info(f"Added collaborator {user_id} to project {project_id} as {role}")
        return result
    
    @staticmethod
    def get_project_collaborators(project_id: UUID) -> List[Dict[str, Any]]:
        """Get all collaborators for a project."""
        query = """
            SELECT u.id, u.email, u.display_name, pc.role, pc.invited_at
            FROM project_collaborators pc
            JOIN users u ON pc.user_id = u.id
            WHERE pc.project_id = %s
        """
        return db.execute_query(query, (str(project_id),))
    
    @staticmethod
    def check_permission(
        project_id: UUID,
        user_id: UUID,
        required_role: str = "viewer"
    ) -> bool:
        """Check if user has required permission level."""
        role_hierarchy = {"owner": 3, "editor": 2, "viewer": 1}
        
        query = """
            SELECT role FROM project_collaborators
            WHERE project_id = %s AND user_id = %s
        """
        result = db.execute_query(
            query,
            (str(project_id), str(user_id)),
            fetch="one"
        )
        
        if not result:
            return False
        
        user_level = role_hierarchy.get(result["role"], 0)
        required_level = role_hierarchy.get(required_role, 1)
        
        return user_level >= required_level

collaboration_service = CollaborationService()
```

#### 2.1.4 Frontend/UI Changes

**Authentication Flow:**
1. Add login/signup page with OIDC providers
2. Store user session in `st.session_state.user`
3. Gate all routes with authentication check
4. Display user info in sidebar header

**New UI Components:**
```
app/views/
├── auth.py              # Login, signup, password reset
├── account.py           # User profile, settings, subscription
└── collaborators.py     # Manage project sharing
```

**Updated Navigation:**
```python
# app/utils/navigation.py
NAV_ITEMS = [
    {"id": "dashboard", "label": "🏠 Dashboard", "icon": "🏠"},
    {"id": "projects", "label": "📁 Projects", "icon": "📁"},
    {"id": "write", "label": "✍️ Write", "icon": "✍️"},
    {"id": "editor", "label": "🧩 Editor", "icon": "🧩"},
    {"id": "world_bible", "label": "🌍 World Bible", "icon": "🌍"},
    {"id": "export", "label": "⬇️ Export", "icon": "⬇️"},
    {"id": "collaborators", "label": "👥 Collaborators", "icon": "👥"},  # NEW
    {"id": "account", "label": "⚙️ Account", "icon": "⚙️"},  # NEW
]
```

#### 2.1.5 Migration Strategy

**Phase 1: Database Setup**
- Deploy PostgreSQL instance (Supabase recommended)
- Run schema migrations
- Set up connection pooling

**Phase 2: Dual-Mode Operation**
- Keep local JSON storage as fallback
- Add `--cloud` flag to enable cloud mode
- Implement sync service for local ↔ cloud

**Phase 3: Full Migration**
- Add migration tool to import local projects to cloud
- Deprecate local-only mode
- Enable cloud-first workflow

---

### 2.2 Multi-Tenant Hosting & Session Management

**Business Value:** Support multiple users on a single deployment with isolated data.

#### 2.2.1 Architecture Pattern

**Row-Level Security (RLS) in PostgreSQL:**
```sql
-- Enable RLS on all user-scoped tables
ALTER TABLE projects ENABLE ROW LEVEL SECURITY;
ALTER TABLE manuscripts ENABLE ROW LEVEL SECURITY;
ALTER TABLE chapters ENABLE ROW LEVEL SECURITY;
ALTER TABLE scenes ENABLE ROW LEVEL SECURITY;
ALTER TABLE world_bible_entries ENABLE ROW LEVEL SECURITY;

-- Policy: Users can only see their own projects or shared projects
CREATE POLICY user_projects_policy ON projects
    FOR SELECT
    USING (
        owner_id = current_setting('app.user_id')::uuid
        OR id IN (
            SELECT project_id FROM project_collaborators
            WHERE user_id = current_setting('app.user_id')::uuid
        )
    );

-- Policy: Users can only modify projects they own or have editor access
CREATE POLICY user_projects_modify_policy ON projects
    FOR UPDATE
    USING (
        owner_id = current_setting('app.user_id')::uuid
        OR id IN (
            SELECT project_id FROM project_collaborators
            WHERE user_id = current_setting('app.user_id')::uuid
            AND role IN ('owner', 'editor')
        )
    );
```

**Session Management:**
```python
# app/utils/session.py
"""Session management for multi-tenant Mantis Studio."""
import streamlit as st
from typing import Optional, Dict, Any
from uuid import UUID

def init_user_session(user: Dict[str, Any]) -> None:
    """Initialize session state for authenticated user."""
    st.session_state.user = user
    st.session_state.user_id = user["id"]
    st.session_state.user_email = user["email"]
    st.session_state.subscription_tier = user.get("subscription_tier", "free")

def get_current_user() -> Optional[Dict[str, Any]]:
    """Get currently authenticated user."""
    return st.session_state.get("user")

def get_current_user_id() -> Optional[UUID]:
    """Get current user ID."""
    user = get_current_user()
    return UUID(user["id"]) if user else None

def require_auth(func):
    """Decorator to require authentication for a view."""
    def wrapper(*args, **kwargs):
        if not get_current_user():
            st.warning("Please log in to access this feature.")
            st.session_state.page = "auth"
            st.rerun()
        return func(*args, **kwargs)
    return wrapper
```

#### 2.2.2 Deployment Considerations

**Environment Configuration:**
```bash
# .env.production
DATABASE_URL=postgresql://user:pass@host:5432/mantis_studio
REDIS_URL=redis://localhost:6379/0
SESSION_SECRET=<random-secret-key>
ENABLE_CLOUD_MODE=true
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=<your-anon-key>
```

**Docker Compose Setup:**
```yaml
# docker-compose.yml
version: '3.8'

services:
  app:
    build: .
    ports:
      - "8501:8501"
    environment:
      - DATABASE_URL=postgresql://postgres:postgres@db:5432/mantis_studio
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - db
      - redis
  
  db:
    image: postgres:15
    environment:
      - POSTGRES_DB=mantis_studio
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=postgres
    volumes:
      - postgres_data:/var/lib/postgresql/data
  
  redis:
    image: redis:7-alpine
    volumes:
      - redis_data:/data

volumes:
  postgres_data:
  redis_data:
```

---

### 2.3 Secure User Authentication

**Business Value:** Protect user data and enable personalized experiences.

#### 2.3.1 Authentication Methods

**Supported Providers:**
1. **Email + Password** (Supabase Auth)
2. **Google OAuth** (existing)
3. **Microsoft OAuth** (existing)
4. **Apple Sign-In** (existing)
5. **GitHub OAuth** (new)

#### 2.3.2 Implementation

**`app/views/auth.py`**
```python
"""Authentication views for Mantis Studio."""
import streamlit as st
from app.services.user_service import user_service
from app.utils.session import init_user_session
from supabase import create_client

def render_auth_page():
    """Render login/signup page."""
    st.title("🐜 Welcome to Mantis Studio")
    
    tab1, tab2 = st.tabs(["Log In", "Sign Up"])
    
    with tab1:
        render_login_form()
    
    with tab2:
        render_signup_form()

def render_login_form():
    """Render login form."""
    st.subheader("Log In")
    
    # OAuth Providers
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🔐 Google", use_container_width=True):
            initiate_oauth_flow("google")
    
    with col2:
        if st.button("🔐 Microsoft", use_container_width=True):
            initiate_oauth_flow("microsoft")
    
    with col3:
        if st.button("🔐 GitHub", use_container_width=True):
            initiate_oauth_flow("github")
    
    st.divider()
    
    # Email/Password Login
    with st.form("login_form"):
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Log In")
        
        if submitted:
            try:
                user = authenticate_user(email, password)
                if user:
                    init_user_session(user)
                    st.success("Logged in successfully!")
                    st.session_state.page = "dashboard"
                    st.rerun()
                else:
                    st.error("Invalid credentials")
            except Exception as e:
                st.error(f"Login failed: {e}")

def authenticate_user(email: str, password: str):
    """Authenticate user with email/password."""
    # Use Supabase Auth or custom implementation
    supabase = create_client(
        st.secrets["SUPABASE_URL"],
        st.secrets["SUPABASE_ANON_KEY"]
    )
    
    response = supabase.auth.sign_in_with_password({
        "email": email,
        "password": password
    })
    
    if response.user:
        # Get or create user in local database
        user = user_service.get_user_by_email(email)
        if not user:
            user = user_service.create_user(
                email=email,
                auth_provider="email",
                auth_provider_id=response.user.id
            )
        return user
    return None
```

#### 2.3.3 Security Best Practices

1. **Password Requirements:**
   - Minimum 8 characters
   - At least one uppercase letter
   - At least one number
   - At least one special character

2. **Session Security:**
   - HTTP-only cookies for session tokens
   - CSRF protection
   - Session expiration after 30 days of inactivity

3. **Data Encryption:**
   - All API communication over HTTPS
   - Database encryption at rest
   - Sensitive data hashed (passwords, API keys)

4. **Rate Limiting:**
   - Max 5 login attempts per 15 minutes
   - Max 100 API requests per hour per user
   - Exponential backoff on failed attempts

---

### 2.4 Collaboration Features

**Business Value:** Enable teams and beta readers to work together on manuscripts.

#### 2.4.1 Project Sharing

**User Flow:**
1. Project owner clicks "Share Project" button
2. Enters collaborator email address
3. Selects permission level (Owner, Editor, Viewer)
4. System sends invitation email
5. Collaborator accepts invitation
6. Project appears in collaborator's project list

**Permission Levels:**

| Permission | Can View | Can Edit | Can Delete | Can Share | Can Export |
|-----------|----------|----------|------------|-----------|------------|
| **Owner** | ✅ | ✅ | ✅ | ✅ | ✅ |
| **Editor** | ✅ | ✅ | ❌ | ❌ | ✅ |
| **Viewer** | ✅ | ❌ | ❌ | ❌ | ✅ |

**Implementation:**

**`app/views/collaborators.py`**
```python
"""Collaborator management view."""
import streamlit as st
from app.services.collaboration_service import collaboration_service
from app.utils.session import get_current_user_id, require_auth

@require_auth
def render_collaborators_page():
    """Render project collaborators management."""
    st.title("👥 Project Collaborators")
    
    project = st.session_state.get("project")
    if not project:
        st.warning("Please select a project first.")
        return
    
    st.subheader(f"Sharing: {project.title}")
    
    # Current collaborators
    st.write("### Current Collaborators")
    collaborators = collaboration_service.get_project_collaborators(project.id)
    
    if collaborators:
        for collab in collaborators:
            col1, col2, col3 = st.columns([3, 2, 1])
            with col1:
                st.write(f"**{collab['display_name'] or collab['email']}**")
            with col2:
                st.write(f"Role: {collab['role'].capitalize()}")
            with col3:
                if st.button("Remove", key=f"remove_{collab['id']}"):
                    remove_collaborator(project.id, collab['id'])
    else:
        st.info("No collaborators yet. Invite someone below!")
    
    # Add new collaborator
    st.write("### Add Collaborator")
    with st.form("add_collaborator_form"):
        email = st.text_input("Email Address")
        role = st.selectbox("Permission Level", ["viewer", "editor", "owner"])
        submitted = st.form_submit_button("Send Invitation")
        
        if submitted and email:
            invite_collaborator(project.id, email, role)

def invite_collaborator(project_id, email, role):
    """Send collaboration invitation."""
    from app.services.user_service import user_service
    
    # Find user by email
    user = user_service.get_user_by_email(email)
    if not user:
        st.error(f"User with email {email} not found. They need to create an account first.")
        return
    
    # Add collaborator
    collaboration_service.add_collaborator(project_id, user["id"], role)
    
    # TODO: Send email notification
    st.success(f"Invitation sent to {email}!")
    st.rerun()
```

#### 2.4.2 Team Workspaces

**Purpose:** Group multiple projects under a shared team for organizations.

**Features:**
- Create workspace with name and branding
- Invite team members with roles (Admin, Member, Viewer)
- All workspace projects visible to members
- Workspace-level billing and quotas

**Schema Reference:**
- `team_workspaces` table
- `workspace_members` table
- Projects can belong to a workspace via `workspace_id` foreign key

---

### 2.5 Structured Writing System

**Business Value:** Organize manuscripts with fine-grained scene-level control like Squibler.

#### 2.5.1 Hierarchy

**Current Structure:**
```
Project → Chapters
```

**Proposed Structure:**
```
Project
└── Manuscript (new)
    └── Chapter
        └── Scene (new)
```

**Benefits:**
- Multiple manuscripts per project (e.g., first draft, revision, alternate version)
- Scene-level organization for better planning
- Drag-and-drop scene reordering
- Scene templates for consistent structure

#### 2.5.2 Database Schema

See Section 2.1.2 for `manuscripts` and `scenes` tables.

#### 2.5.3 UI Changes

**New View: Manuscript Manager**
```
app/views/manuscripts.py
```

**Features:**
1. List all manuscripts in current project
2. Create/rename/delete manuscripts
3. Set manuscript status (Draft, Revision, Final)
4. Clone manuscript to create new version

**Updated Editor View:**
```python
# app/views/editor.py (enhanced)

def render_editor_page():
    """Render enhanced editor with scene support."""
    st.title("🧩 Editor")
    
    # Manuscript selector
    manuscript = render_manuscript_selector()
    if not manuscript:
        return
    
    # Chapter and scene navigation
    col1, col2 = st.columns([1, 3])
    
    with col1:
        st.subheader("Chapters")
        chapter = render_chapter_list(manuscript)
        
        if chapter:
            st.divider()
            st.subheader("Scenes")
            scene = render_scene_list(chapter)
    
    with col2:
        if scene:
            render_scene_editor(scene)
        elif chapter:
            render_chapter_editor(chapter)
        else:
            st.info("Select a chapter or scene to start writing.")

def render_scene_list(chapter):
    """Render list of scenes in chapter."""
    scenes = get_scenes_for_chapter(chapter.id)
    
    selected_scene = None
    for idx, scene in enumerate(scenes):
        # Scene card with drag handle
        col1, col2, col3 = st.columns([1, 6, 1])
        with col1:
            st.write("⋮⋮")  # Drag handle placeholder
        with col2:
            if st.button(
                f"{scene.title or f'Scene {idx + 1}'}",
                key=f"scene_{scene.id}",
                use_container_width=True
            ):
                selected_scene = scene
        with col3:
            if st.button("×", key=f"delete_scene_{scene.id}"):
                delete_scene(scene.id)
    
    # Add new scene button
    if st.button("➕ New Scene", use_container_width=True):
        create_new_scene(chapter.id)
    
    return selected_scene
```

#### 2.5.4 Scene Metadata

**Each scene stores:**
- Title (optional)
- Content (text)
- Summary/purpose
- POV character
- Location (linked to World Bible)
- Timeline/date
- Word count
- Status (Draft, Revision, Final)
- Tags

**Scene Card UI:**
```
┌─────────────────────────────────────┐
│ ⋮⋮ Scene 1: The Chase              │
│                                     │
│ 📍 Downtown Market                 │
│ 👤 POV: Sarah                      │
│ 📅 Day 3, Morning                  │
│ 📝 347 words                       │
│                                     │
│ [Edit] [Delete] [Move Up/Down]     │
└─────────────────────────────────────┘
```

---

### 2.6 AI Narrative Workflows

**Business Value:** Match Sudowrite's core AI tools for creative writers.

#### 2.6.1 Describe (Sensory Enrichment)

**Purpose:** Expand descriptions with vivid sensory details.

**User Flow:**
1. User selects text in editor (e.g., "The room was dark.")
2. Clicks "Describe" button
3. AI generates sensory-rich expansion
4. User reviews and inserts/replaces text

**Prompt Template:**
```python
DESCRIBE_TEMPLATE = """
You are a skilled creative writer helping to enrich a scene with sensory details.

SELECTED TEXT:
{selected_text}

CONTEXT (previous text):
{previous_context}

TASK:
Expand the selected text with vivid sensory details covering:
- Sight (visual details, colors, lighting)
- Sound (ambient noise, dialogue, silence)
- Smell (scents, aromas, odors)
- Touch (textures, temperature, physical sensations)
- Taste (if relevant)

Maintain the narrative voice and style. Do not change the core meaning.
Return ONLY the expanded description, no explanations.

EXPANDED DESCRIPTION:
"""
```

**Implementation:**
```python
# app/services/ai_narrative.py

class AIDescribe:
    """AI-powered sensory description expansion."""
    
    def __init__(self, ai_engine):
        self.ai_engine = ai_engine
    
    def describe(
        self,
        selected_text: str,
        context: str = "",
        focus: str = "all"  # or "sight", "sound", "smell", etc.
    ) -> str:
        """Generate sensory-rich description."""
        prompt = self._build_describe_prompt(selected_text, context, focus)
        result = self.ai_engine.generate(prompt)
        return result
    
    def _build_describe_prompt(self, text, context, focus):
        """Build describe prompt with context injection."""
        # Inject World Bible entries related to location/character
        world_context = self._get_relevant_world_context(text)
        
        prompt = f"""
You are a skilled creative writer helping to enrich a scene with sensory details.

WORLD CONTEXT:
{world_context}

SELECTED TEXT:
{text}

PREVIOUS CONTEXT:
{context[:500]}

FOCUS: {focus}

Expand the selected text with vivid sensory details.
Maintain the narrative voice and style.
Return ONLY the expanded description.

EXPANDED DESCRIPTION:
"""
        return prompt
    
    def _get_relevant_world_context(self, text):
        """Extract relevant World Bible entries based on text content."""
        # TODO: Implement keyword matching with World Bible
        return ""
```

**UI Integration:**
```python
# In editor view
if st.button("✨ Describe"):
    selected_text = get_selected_text()  # From editor component
    if selected_text:
        with st.spinner("Generating sensory details..."):
            ai_describe = AIDescribe(ai_engine)
            enriched = ai_describe.describe(
                selected_text,
                context=get_previous_paragraph()
            )
            
            # Show result with options
            st.write("### AI-Generated Description")
            st.write(enriched)
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("Replace Selected Text"):
                    replace_text(selected_text, enriched)
            with col2:
                if st.button("Insert After"):
                    insert_after(selected_text, enriched)
```

#### 2.6.2 Expand (Scene Continuation)

**Purpose:** Generate next paragraphs/scenes based on context.

**Prompt Template:**
```python
EXPAND_TEMPLATE = """
You are a creative writing assistant continuing a story.

HARD CANON (MUST follow these rules):
{hard_canon_rules}

WORLD BIBLE:
{world_bible_context}

STORY SO FAR:
{previous_text}

CURRENT TEXT:
{current_text}

TASK:
Continue the story naturally from where it left off.
- Maintain character voices and personalities
- Follow established canon and worldbuilding
- Match the narrative style and pacing
- Generate approximately {word_count} words

Do NOT summarize or explain. Write the story continuation directly.

CONTINUATION:
"""
```

**Features:**
- Multiple generation options (try 3 different continuations)
- Length control (short: 100 words, medium: 300 words, long: 500 words)
- Tone control (maintain current / lighter / darker / more tense)

#### 2.6.3 Rewrite (Tone, POV, Pacing)

**Purpose:** Transform existing text with different attributes.

**Options:**
1. **Change POV:**
   - 1st person → 3rd person
   - 3rd person limited → 3rd person omniscient
   - Past tense → Present tense

2. **Adjust Tone:**
   - Darker / lighter
   - More humorous
   - More serious
   - More suspenseful

3. **Change Pacing:**
   - Faster (condense, remove details)
   - Slower (expand, add details)

**Prompt Template:**
```python
REWRITE_TEMPLATE = """
You are a skilled editor rewriting a passage.

ORIGINAL TEXT:
{original_text}

REWRITE INSTRUCTIONS:
{instructions}

WORLD BIBLE CONTEXT:
{world_context}

TASK:
Rewrite the text according to the instructions above.
Preserve the core story events and character actions.
Return ONLY the rewritten text, no explanations.

REWRITTEN TEXT:
"""
```

**Example Instructions:**
```python
# Change to 3rd person
instructions = "Rewrite in 3rd person limited POV from Sarah's perspective."

# Adjust tone
instructions = "Rewrite with a darker, more ominous tone. Emphasize danger and uncertainty."

# Change pacing
instructions = "Slow down the pacing. Add more sensory details and internal thoughts."
```

#### 2.6.4 Consistency Checker

**Purpose:** Detect canon violations, character inconsistencies, timeline errors.

**Features:**
1. **Character Consistency:**
   - Track character traits across chapters
   - Flag contradictions (eye color, backstory, abilities)
   - Suggest corrections based on World Bible

2. **Lore Consistency:**
   - Check magic system rules
   - Verify world geography
   - Validate historical events

3. **Timeline Tracking:**
   - Build automatic timeline from chapter dates
   - Flag temporal inconsistencies
   - Suggest reordering or date corrections

**Implementation:**
```python
# app/services/consistency_checker.py

class ConsistencyChecker:
    """Check narrative consistency across project."""
    
    def check_character_consistency(self, project_id):
        """Find character description conflicts."""
        issues = []
        
        # Get all character entries from World Bible
        characters = get_world_bible_entries(project_id, category="character")
        
        # Get all chapter content
        chapters = get_all_chapters(project_id)
        
        for character in characters:
            # Extract mentions of character in chapters
            mentions = extract_character_mentions(character, chapters)
            
            # Compare descriptions for conflicts
            conflicts = detect_description_conflicts(mentions)
            
            if conflicts:
                issues.append({
                    "type": "character_conflict",
                    "character": character.name,
                    "conflicts": conflicts
                })
        
        return issues
    
    def check_timeline_consistency(self, project_id):
        """Check for timeline errors."""
        issues = []
        
        # Extract timeline events from chapters
        events = extract_timeline_events(project_id)
        
        # Sort by date and check for conflicts
        sorted_events = sorted(events, key=lambda e: e["date"])
        
        for i in range(len(sorted_events) - 1):
            if sorted_events[i]["date"] > sorted_events[i+1]["date"]:
                issues.append({
                    "type": "timeline_conflict",
                    "event1": sorted_events[i],
                    "event2": sorted_events[i+1]
                })
        
        return issues
```

---

## 3. Nice-to-Have / Differentiation Features

These features will differentiate Mantis Studio from competitors and provide additional value to users. They should be implemented after the must-have features are complete.

---

### 3.1 Export to Ebook/Print Formats

**Business Value:** Enable professional manuscript delivery and self-publishing.

#### 3.1.1 Supported Formats

| Format | Use Case | Priority | Complexity |
|--------|----------|----------|------------|
| **DOCX** | Manuscript submissions, editing | High | Low |
| **PDF** | Print-ready manuscripts, sharing | High | Medium |
| **EPUB** | Ebook publishing (Kindle, Apple Books) | High | Medium |
| **MOBI** | Kindle-specific ebook format | Medium | Low (via Calibre) |
| **LaTeX** | Academic writing, advanced formatting | Low | High |
| **Markdown** | Simple export, version control | Medium | Low |

#### 3.1.2 Current State

Mantis Studio currently supports:
- ✅ TXT export (basic)
- ⚠️ DOCX export (limited formatting)
- ❌ PDF export
- ❌ EPUB export

#### 3.1.3 Enhanced DOCX Export

**Requirements:**
- Chapter headings with proper styles
- Page numbers and headers/footers
- Custom fonts and formatting
- Table of contents generation
- Scene breaks (visual separators)
- Front matter (title page, copyright, dedication)

**Implementation:**
```python
# app/services/export/docx_exporter.py

from docx import Document
from docx.shared import Pt, Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH

class EnhancedDOCXExporter:
    """Export manuscript to professionally formatted DOCX."""
    
    def __init__(self, project, manuscript):
        self.project = project
        self.manuscript = manuscript
        self.doc = Document()
    
    def export(self, output_path, options=None):
        """Export manuscript to DOCX with formatting."""
        options = options or {}
        
        # Set page margins
        self._set_page_margins()
        
        # Add front matter if requested
        if options.get("include_front_matter", True):
            self._add_title_page()
            self._add_copyright_page()
            self._add_dedication()
        
        # Add table of contents
        if options.get("include_toc", True):
            self._add_table_of_contents()
        
        # Add chapters
        chapters = self._get_chapters_in_order()
        for chapter in chapters:
            self._add_chapter(chapter, options)
        
        # Add back matter
        if options.get("include_back_matter", False):
            self._add_about_author()
        
        # Save document
        self.doc.save(output_path)
    
    def _set_page_margins(self):
        """Set standard manuscript margins (1 inch all sides)."""
        sections = self.doc.sections
        for section in sections:
            section.top_margin = Inches(1)
            section.bottom_margin = Inches(1)
            section.left_margin = Inches(1)
            section.right_margin = Inches(1)
    
    def _add_title_page(self):
        """Add formatted title page."""
        # Title
        title = self.doc.add_paragraph(self.manuscript.title)
        title.alignment = WD_ALIGN_PARAGRAPH.CENTER
        title_run = title.runs[0]
        title_run.font.size = Pt(24)
        title_run.font.bold = True
        
        # Author
        author = self.doc.add_paragraph("\n\nby\n\n")
        author.alignment = WD_ALIGN_PARAGRAPH.CENTER
        
        author_name = self.doc.add_paragraph(
            self.project.metadata.get("author_name", "Author")
        )
        author_name.alignment = WD_ALIGN_PARAGRAPH.CENTER
        author_name.runs[0].font.size = Pt(16)
        
        # Page break
        self.doc.add_page_break()
    
    def _add_chapter(self, chapter, options):
        """Add chapter with proper formatting."""
        # Chapter heading
        heading = self.doc.add_heading(chapter.title, level=1)
        heading.alignment = WD_ALIGN_PARAGRAPH.CENTER
        
        self.doc.add_paragraph()  # Spacing
        
        # Chapter content
        # Split content by scenes if they exist
        scenes = self._get_scenes_for_chapter(chapter.id)
        
        if scenes:
            for idx, scene in enumerate(scenes):
                # Scene content
                self._add_formatted_text(scene.content)
                
                # Scene break (except for last scene)
                if idx < len(scenes) - 1:
                    self._add_scene_break()
        else:
            # No scenes, just add chapter content
            self._add_formatted_text(chapter.content)
        
        # Page break after chapter
        if options.get("chapter_page_breaks", True):
            self.doc.add_page_break()
    
    def _add_formatted_text(self, text):
        """Add text with paragraph formatting."""
        paragraphs = text.split("\n\n")
        
        for para_text in paragraphs:
            if para_text.strip():
                para = self.doc.add_paragraph(para_text.strip())
                para.paragraph_format.first_line_indent = Inches(0.5)
                para.paragraph_format.line_spacing = 2.0  # Double spaced
                
                # Set font
                for run in para.runs:
                    run.font.name = "Times New Roman"
                    run.font.size = Pt(12)
    
    def _add_scene_break(self):
        """Add visual scene separator."""
        separator = self.doc.add_paragraph("* * *")
        separator.alignment = WD_ALIGN_PARAGRAPH.CENTER
        self.doc.add_paragraph()  # Spacing
```

#### 3.1.4 EPUB Export

**Requirements:**
- Valid EPUB 3.0 format
- Proper metadata (title, author, ISBN, description)
- Table of contents navigation
- Cover image support
- Chapter-based file structure

**Implementation:**
```python
# app/services/export/epub_exporter.py

from ebooklib import epub

class EPUBExporter:
    """Export manuscript to EPUB format."""
    
    def export(self, project, manuscript, output_path, options=None):
        """Generate EPUB file."""
        book = epub.EpubBook()
        
        # Set metadata
        book.set_identifier(options.get("isbn", f"mantis-{project.id}"))
        book.set_title(manuscript.title)
        book.set_language("en")
        book.add_author(
            project.metadata.get("author_name", "Unknown Author")
        )
        
        # Add cover image if provided
        if options.get("cover_image"):
            book.set_cover("cover.jpg", open(options["cover_image"], "rb").read())
        
        # Add chapters
        chapters = self._get_chapters_in_order(manuscript.id)
        epub_chapters = []
        
        for idx, chapter in enumerate(chapters):
            # Create EPUB chapter
            epub_chapter = epub.EpubHtml(
                title=chapter.title,
                file_name=f"chap_{idx:02d}.xhtml",
                lang="en"
            )
            
            # Format chapter content as HTML
            content_html = self._format_chapter_content(chapter)
            epub_chapter.content = content_html
            
            book.add_item(epub_chapter)
            epub_chapters.append(epub_chapter)
        
        # Add table of contents
        book.toc = tuple(epub_chapters)
        
        # Add navigation files
        book.add_item(epub.EpubNcx())
        book.add_item(epub.EpubNav())
        
        # Define spine
        book.spine = ["nav"] + epub_chapters
        
        # Write EPUB file
        epub.write_epub(output_path, book)
```

#### 3.1.5 PDF Export

**Options:**
1. **Via LaTeX:** High-quality typesetting (complex)
2. **Via ReportLab:** Programmatic PDF generation (medium)
3. **Via DOCX → PDF:** Convert DOCX to PDF using LibreOffice (simple)

**Recommended Approach:** DOCX → PDF conversion

```python
# app/services/export/pdf_exporter.py

import subprocess
from pathlib import Path

class PDFExporter:
    """Export manuscript to PDF format."""
    
    def export(self, project, manuscript, output_path, options=None):
        """Generate PDF via DOCX intermediate."""
        # First, generate DOCX
        docx_path = Path(output_path).with_suffix(".docx")
        
        docx_exporter = EnhancedDOCXExporter(project, manuscript)
        docx_exporter.export(str(docx_path), options)
        
        # Convert DOCX to PDF using LibreOffice
        self._convert_docx_to_pdf(docx_path, output_path)
        
        # Clean up intermediate DOCX if requested
        if options.get("cleanup_intermediate", True):
            docx_path.unlink()
    
    def _convert_docx_to_pdf(self, docx_path, pdf_path):
        """Convert DOCX to PDF using LibreOffice."""
        try:
            subprocess.run(
                [
                    "libreoffice",
                    "--headless",
                    "--convert-to", "pdf",
                    "--outdir", str(Path(pdf_path).parent),
                    str(docx_path)
                ],
                check=True,
                capture_output=True
            )
        except subprocess.CalledProcessError as e:
            raise ExportError(f"PDF conversion failed: {e}")
```

---

### 3.2 Timeline and Story Chronology Views

**Business Value:** Visualize story timeline and catch chronology errors.

#### 3.2.1 Features

1. **Timeline Visualization:**
   - Interactive timeline chart (using Plotly)
   - Events from chapters and scenes
   - Character ages and milestones
   - Historical events from World Bible

2. **Chapter Date Tracking:**
   - Assign date/time to each scene
   - Automatic duration calculation
   - Flashback/flash-forward markers

3. **Chronological vs. Narrative Order:**
   - View chapters in chronological order
   - Rearrange scenes to match timeline
   - Identify timeline gaps

#### 3.2.2 Implementation

**Data Model:**
```python
# Add to scenes table
ALTER TABLE scenes ADD COLUMN timeline_date TIMESTAMP;
ALTER TABLE scenes ADD COLUMN timeline_duration_hours INTEGER DEFAULT 1;
ALTER TABLE scenes ADD COLUMN timeline_type VARCHAR(20) DEFAULT 'present'; 
-- present, flashback, flash_forward
```

**Timeline View:**
```python
# app/views/timeline.py

import streamlit as st
import plotly.express as px
import pandas as pd
from datetime import datetime, timedelta

def render_timeline_view():
    """Render project timeline visualization."""
    st.title("📅 Story Timeline")
    
    project = st.session_state.get("project")
    if not project:
        st.warning("Please select a project first.")
        return
    
    # Get all scenes with dates
    scenes_with_dates = get_scenes_with_timeline_data(project.id)
    
    if not scenes_with_dates:
        st.info("No timeline data yet. Add dates to your scenes to build a timeline.")
        return
    
    # Convert to DataFrame
    df = pd.DataFrame([
        {
            "Scene": scene.title or f"Scene {scene.order_index}",
            "Start": scene.timeline_date,
            "Duration": scene.timeline_duration_hours,
            "Chapter": scene.chapter_title,
            "Type": scene.timeline_type
        }
        for scene in scenes_with_dates
    ])
    
    # Create Gantt chart
    fig = px.timeline(
        df,
        x_start="Start",
        x_end=df["Start"] + pd.to_timedelta(df["Duration"], unit="h"),
        y="Chapter",
        color="Type",
        hover_data=["Scene", "Duration"],
        title="Story Timeline"
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Show chronological vs. narrative order
    st.subheader("Chronological vs. Narrative Order")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**Chronological Order:**")
        chronological = sorted(scenes_with_dates, key=lambda s: s.timeline_date)
        for scene in chronological:
            st.write(f"- {scene.title} ({scene.timeline_date.strftime('%Y-%m-%d')})")
    
    with col2:
        st.write("**Narrative Order:**")
        narrative = sorted(scenes_with_dates, key=lambda s: (s.chapter_order, s.order_index))
        for scene in narrative:
            st.write(f"- {scene.title} (Chapter {scene.chapter_order})")
```

---

### 3.3 Writing Analytics

**Business Value:** Track progress, set goals, and maintain writing discipline.

#### 3.3.1 Metrics to Track

1. **Word Counts:**
   - Total project word count
   - Per-chapter word count
   - Daily word count (writing sessions)
   - Word count over time (chart)

2. **Progress Tracking:**
   - Completion percentage
   - Chapters completed vs. planned
   - Daily writing streak
   - Average words per session

3. **Consistency Warnings:**
   - Character name variations
   - Timeline inconsistencies
   - Repeated phrases/clichés
   - Pacing issues (scene length variation)

4. **Writing Velocity:**
   - Words per hour
   - Words per day
   - Estimated completion date

#### 3.3.2 Implementation

**Analytics Service:**
```python
# app/services/analytics.py

from datetime import datetime, timedelta
from collections import defaultdict

class WritingAnalytics:
    """Track and analyze writing progress."""
    
    def get_project_stats(self, project_id):
        """Get comprehensive project statistics."""
        chapters = get_all_chapters(project_id)
        
        total_words = sum(c.word_count for c in chapters)
        completed_chapters = sum(1 for c in chapters if c.status == "final")
        
        return {
            "total_words": total_words,
            "total_chapters": len(chapters),
            "completed_chapters": completed_chapters,
            "completion_percentage": (completed_chapters / len(chapters) * 100) 
                if chapters else 0,
            "average_chapter_length": total_words / len(chapters) if chapters else 0
        }
    
    def get_writing_history(self, project_id, days=30):
        """Get daily word count history."""
        # Query revisions table for writing activity
        query = """
            SELECT 
                DATE(created_at) as date,
                SUM(LENGTH(content) - LENGTH(REPLACE(content, ' ', '')) + 1) as words_written
            FROM revisions
            WHERE entity_type = 'chapter'
                AND entity_id IN (
                    SELECT id FROM chapters 
                    WHERE manuscript_id IN (
                        SELECT id FROM manuscripts WHERE project_id = %s
                    )
                )
                AND created_at >= NOW() - INTERVAL '%s days'
            GROUP BY DATE(created_at)
            ORDER BY date
        """
        
        results = db.execute_query(query, (str(project_id), days))
        
        # Fill in missing dates with 0
        history = defaultdict(int)
        start_date = datetime.now() - timedelta(days=days)
        
        for i in range(days):
            date = (start_date + timedelta(days=i)).date()
            history[date] = 0
        
        for row in results:
            history[row["date"]] = row["words_written"]
        
        return history
    
    def calculate_writing_streak(self, project_id):
        """Calculate current writing streak (consecutive days)."""
        history = self.get_writing_history(project_id, days=365)
        
        streak = 0
        current_date = datetime.now().date()
        
        while current_date in history and history[current_date] > 0:
            streak += 1
            current_date -= timedelta(days=1)
        
        return streak
```

**Analytics Dashboard:**
```python
# app/views/analytics.py

def render_analytics_page():
    """Render writing analytics dashboard."""
    st.title("📊 Writing Analytics")
    
    project = st.session_state.get("project")
    if not project:
        st.warning("Please select a project first.")
        return
    
    analytics = WritingAnalytics()
    
    # Overall stats
    stats = analytics.get_project_stats(project.id)
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Words", f"{stats['total_words']:,}")
    
    with col2:
        st.metric("Chapters", f"{stats['completed_chapters']}/{stats['total_chapters']}")
    
    with col3:
        st.metric("Completion", f"{stats['completion_percentage']:.1f}%")
    
    with col4:
        streak = analytics.calculate_writing_streak(project.id)
        st.metric("Writing Streak", f"{streak} days")
    
    # Word count over time
    st.subheader("Writing Progress (Last 30 Days)")
    
    history = analytics.get_writing_history(project.id, days=30)
    df = pd.DataFrame([
        {"Date": date, "Words Written": words}
        for date, words in sorted(history.items())
    ])
    
    fig = px.bar(df, x="Date", y="Words Written", title="Daily Word Count")
    st.plotly_chart(fig, use_container_width=True)
    
    # Chapter completion status
    st.subheader("Chapter Status")
    
    chapters = get_all_chapters(project.id)
    chapter_data = pd.DataFrame([
        {
            "Chapter": c.title,
            "Words": c.word_count,
            "Target": c.target_words,
            "Progress": (c.word_count / c.target_words * 100) if c.target_words > 0 else 0,
            "Status": c.status
        }
        for c in chapters
    ])
    
    st.dataframe(chapter_data, use_container_width=True)
```

---

### 3.4 Templates for Different Writing Types

**Business Value:** Provide guided workflows for different content types.

#### 3.4.1 Template Categories

1. **Novel Templates:**
   - Three-Act Structure
   - Hero's Journey
   - Save the Cat (Beat Sheet)
   - Romance Novel Structure
   - Mystery Novel Structure

2. **Screenplay Templates:**
   - Feature Film (3-act)
   - TV Episode (teaser + 4 acts)
   - Short Film

3. **Worldbuilding Bible:**
   - Fantasy world template
   - Sci-fi universe template
   - Historical fiction research

4. **Marketing Copy:**
   - Blog post structure
   - Product description
   - Email campaign
   - Social media content

#### 3.4.2 Template Structure

**Template Metadata:**
```json
{
  "id": "three-act-novel",
  "name": "Three-Act Novel Structure",
  "description": "Classic three-act structure for novel writing",
  "category": "novel",
  "target_word_count": 80000,
  "acts": [
    {
      "name": "Act 1: Setup",
      "description": "Introduce characters, world, and conflict",
      "target_percentage": 0.25,
      "beats": [
        {
          "name": "Opening Image",
          "description": "First impression of the protagonist's world",
          "suggested_words": 1000
        },
        {
          "name": "Inciting Incident",
          "description": "Event that disrupts the status quo",
          "suggested_words": 500
        },
        {
          "name": "First Plot Point",
          "description": "Protagonist commits to the journey",
          "suggested_words": 1000
        }
      ]
    },
    {
      "name": "Act 2: Confrontation",
      "description": "Protagonist faces obstacles and grows",
      "target_percentage": 0.50,
      "beats": [
        {
          "name": "Midpoint",
          "description": "Major revelation or reversal",
          "suggested_words": 1500
        },
        {
          "name": "All Is Lost",
          "description": "Lowest point for protagonist",
          "suggested_words": 1000
        }
      ]
    },
    {
      "name": "Act 3: Resolution",
      "description": "Climax and resolution",
      "target_percentage": 0.25,
      "beats": [
        {
          "name": "Climax",
          "description": "Final confrontation",
          "suggested_words": 2000
        },
        {
          "name": "Resolution",
          "description": "New status quo established",
          "suggested_words": 1000
        }
      ]
    }
  ]
}
```

**Template Application:**
```python
# app/services/templates.py

class TemplateService:
    """Apply templates to new projects."""
    
    def apply_template(self, project_id, template_id):
        """Apply a template to a project."""
        template = self.load_template(template_id)
        
        # Create manuscript from template
        manuscript = create_manuscript(
            project_id=project_id,
            title=template["name"],
            description=template["description"]
        )
        
        # Create chapters from beats
        chapter_index = 0
        for act in template["acts"]:
            for beat in act["beats"]:
                create_chapter(
                    manuscript_id=manuscript.id,
                    title=beat["name"],
                    order_index=chapter_index,
                    summary=beat["description"],
                    target_words=beat["suggested_words"]
                )
                chapter_index += 1
        
        return manuscript
```

---

## 4. Technical Design Specifications

This section provides detailed technical specifications for implementing the features described above.

---

### 4.1 System Architecture Overview

**Current Architecture:**
```
┌─────────────────────────────────────┐
│   Streamlit Frontend (Python)       │
│   - Session State Management        │
│   - Component Rendering             │
└──────────────┬──────────────────────┘
               │
┌──────────────▼──────────────────────┐
│   Services Layer                    │
│   - Projects (JSON storage)         │
│   - AI Engine (Groq API)            │
│   - Export (TXT, DOCX)              │
│   - World Bible                     │
└──────────────┬──────────────────────┘
               │
┌──────────────▼──────────────────────┐
│   Local Storage                     │
│   - JSON files in storage/          │
│   - No user accounts                │
└─────────────────────────────────────┘
```

**Proposed Cloud Architecture:**
```
┌─────────────────────────────────────┐
│   Streamlit Frontend (Python)       │
│   - Session State + Cloud Sync      │
│   - Component Rendering             │
│   - Real-time Collaboration         │
└──────────────┬──────────────────────┘
               │
┌──────────────▼──────────────────────┐
│   API Layer (FastAPI)               │
│   - RESTful API endpoints           │
│   - WebSocket for real-time         │
│   - Authentication middleware       │
└──────────────┬──────────────────────┘
               │
┌──────────────▼──────────────────────┐
│   Services Layer                    │
│   - User Service                    │
│   - Project Service (DB-backed)     │
│   - Collaboration Service           │
│   - AI Narrative Workflows          │
│   - Analytics Service               │
│   - Export Service (enhanced)       │
└──────────────┬──────────────────────┘
               │
      ┌────────┴────────┐
      │                 │
┌─────▼──────┐  ┌──────▼────────┐
│ PostgreSQL │  │  Redis Cache  │
│  (Supabase)│  │  (Sessions)   │
└────────────┘  └───────────────┘
```

---

### 4.2 Database Design

See Section 2.1.2 for complete schema. Key design decisions:

1. **Multi-tenancy via Row-Level Security (RLS)**
2. **UUID primary keys** for distributed systems
3. **JSONB for flexible metadata** (extensibility)
4. **Indexes on foreign keys** for performance
5. **Audit fields** (created_at, modified_at) on all tables

---

### 4.3 API Endpoint Specifications

**REST API Design (FastAPI):**

```python
# app/api/main.py

from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from app.api.auth import get_current_user
from app.api.routes import projects, manuscripts, chapters, world_bible, collaboration

app = FastAPI(title="Mantis Studio API", version="2.0")

# CORS middleware for Streamlit frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8501"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(projects.router, prefix="/api/v1/projects", tags=["projects"])
app.include_router(manuscripts.router, prefix="/api/v1/manuscripts", tags=["manuscripts"])
app.include_router(chapters.router, prefix="/api/v1/chapters", tags=["chapters"])
app.include_router(world_bible.router, prefix="/api/v1/world-bible", tags=["world-bible"])
app.include_router(collaboration.router, prefix="/api/v1/collaboration", tags=["collaboration"])
```

**Example Routes:**

```python
# app/api/routes/projects.py

from fastapi import APIRouter, Depends, HTTPException
from typing import List
from uuid import UUID
from app.api.auth import get_current_user
from app.services.project_service import project_service
from app.models.project import ProjectCreate, ProjectUpdate, ProjectResponse

router = APIRouter()

@router.get("/", response_model=List[ProjectResponse])
async def list_projects(current_user = Depends(get_current_user)):
    """List all projects for current user."""
    return project_service.get_user_projects(current_user.id)

@router.post("/", response_model=ProjectResponse, status_code=201)
async def create_project(
    project: ProjectCreate,
    current_user = Depends(get_current_user)
):
    """Create a new project."""
    return project_service.create_project(
        owner_id=current_user.id,
        title=project.title,
        description=project.description,
        project_type=project.project_type
    )

@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(
    project_id: UUID,
    current_user = Depends(get_current_user)
):
    """Get project by ID."""
    project = project_service.get_project(project_id)
    
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Check permission
    if not collaboration_service.check_permission(
        project_id, current_user.id, "viewer"
    ):
        raise HTTPException(status_code=403, detail="Access denied")
    
    return project

@router.put("/{project_id}", response_model=ProjectResponse)
async def update_project(
    project_id: UUID,
    project_update: ProjectUpdate,
    current_user = Depends(get_current_user)
):
    """Update project."""
    # Check permission
    if not collaboration_service.check_permission(
        project_id, current_user.id, "editor"
    ):
        raise HTTPException(status_code=403, detail="Access denied")
    
    return project_service.update_project(project_id, project_update)

@router.delete("/{project_id}", status_code=204)
async def delete_project(
    project_id: UUID,
    current_user = Depends(get_current_user)
):
    """Delete project."""
    # Check permission (only owner can delete)
    if not collaboration_service.check_permission(
        project_id, current_user.id, "owner"
    ):
        raise HTTPException(status_code=403, detail="Only owner can delete project")
    
    project_service.delete_project(project_id)
```

---

### 4.4 Frontend Architecture Changes

**Component-Based Design:**

```
app/components/
├── auth/
│   ├── login_form.py
│   ├── signup_form.py
│   └── oauth_buttons.py
├── editor/
│   ├── text_editor.py
│   ├── scene_editor.py
│   ├── ai_tools_panel.py
│   └── revision_history.py
├── project/
│   ├── project_card.py
│   ├── project_selector.py
│   └── collaborator_list.py
├── world_bible/
│   ├── entity_card.py
│   ├── entity_editor.py
│   └── entity_search.py
└── analytics/
    ├── progress_chart.py
    ├── word_count_meter.py
    └── streak_badge.py
```

**State Management Strategy:**

```python
# app/state/store.py

from dataclasses import dataclass, field
from typing import Optional, Dict, List, Any
from uuid import UUID

@dataclass
class AppState:
    """Centralized application state."""
    
    # Authentication
    user: Optional[Dict[str, Any]] = None
    user_id: Optional[UUID] = None
    authenticated: bool = False
    
    # Navigation
    page: str = "dashboard"
    previous_page: str = "dashboard"
    
    # Current selections
    current_project_id: Optional[UUID] = None
    current_manuscript_id: Optional[UUID] = None
    current_chapter_id: Optional[UUID] = None
    current_scene_id: Optional[UUID] = None
    
    # Editor state
    editor_content: str = ""
    editor_dirty: bool = False
    selected_text: str = ""
    
    # AI state
    ai_generating: bool = False
    ai_result: str = ""
    
    # Collaboration
    collaborators: List[Dict[str, Any]] = field(default_factory=list)
    
    # UI state
    sidebar_collapsed: bool = False
    dark_mode: bool = False

def initialize_state():
    """Initialize Streamlit session state with AppState."""
    if "app_state" not in st.session_state:
        st.session_state.app_state = AppState()

def get_state() -> AppState:
    """Get current application state."""
    if "app_state" not in st.session_state:
        initialize_state()
    return st.session_state.app_state
```

---

### 4.5 Real-Time Collaboration Implementation

**WebSocket Architecture:**

```python
# app/api/websocket.py

from fastapi import WebSocket, WebSocketDisconnect
from typing import Dict, Set
from uuid import UUID

class ConnectionManager:
    """Manage WebSocket connections for real-time collaboration."""
    
    def __init__(self):
        # Map: project_id -> set of websockets
        self.active_connections: Dict[UUID, Set[WebSocket]] = {}
    
    async def connect(self, websocket: WebSocket, project_id: UUID):
        """Connect user to project room."""
        await websocket.accept()
        
        if project_id not in self.active_connections:
            self.active_connections[project_id] = set()
        
        self.active_connections[project_id].add(websocket)
    
    def disconnect(self, websocket: WebSocket, project_id: UUID):
        """Disconnect user from project room."""
        if project_id in self.active_connections:
            self.active_connections[project_id].discard(websocket)
    
    async def broadcast(self, project_id: UUID, message: dict):
        """Broadcast message to all users in project."""
        if project_id in self.active_connections:
            for connection in self.active_connections[project_id]:
                try:
                    await connection.send_json(message)
                except:
                    # Connection closed, will be cleaned up later
                    pass

manager = ConnectionManager()

@app.websocket("/ws/{project_id}")
async def websocket_endpoint(websocket: WebSocket, project_id: UUID):
    """WebSocket endpoint for real-time updates."""
    await manager.connect(websocket, project_id)
    
    try:
        while True:
            # Receive message from client
            data = await websocket.receive_json()
            
            # Handle different message types
            if data["type"] == "edit":
                # Someone edited a chapter
                await manager.broadcast(project_id, {
                    "type": "chapter_updated",
                    "chapter_id": data["chapter_id"],
                    "user_id": data["user_id"],
                    "content": data["content"]
                })
            
            elif data["type"] == "cursor":
                # User cursor position update
                await manager.broadcast(project_id, {
                    "type": "cursor_update",
                    "user_id": data["user_id"],
                    "chapter_id": data["chapter_id"],
                    "position": data["position"]
                })
    
    except WebSocketDisconnect:
        manager.disconnect(websocket, project_id)
```

---

### 4.6 Performance Optimizations

**Caching Strategy:**

```python
# app/services/cache.py

import redis
import json
from typing import Optional, Any
from functools import wraps

class CacheService:
    """Redis-based caching service."""
    
    def __init__(self):
        self.redis = redis.from_url(os.getenv("REDIS_URL", "redis://localhost:6379"))
        self.default_ttl = 3600  # 1 hour
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        value = self.redis.get(key)
        if value:
            return json.loads(value)
        return None
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None):
        """Set value in cache."""
        ttl = ttl or self.default_ttl
        self.redis.setex(key, ttl, json.dumps(value))
    
    def delete(self, key: str):
        """Delete value from cache."""
        self.redis.delete(key)
    
    def cache_result(self, key_prefix: str, ttl: Optional[int] = None):
        """Decorator to cache function results."""
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                # Generate cache key from function args
                cache_key = f"{key_prefix}:{args}:{kwargs}"
                
                # Check cache
                cached = self.get(cache_key)
                if cached is not None:
                    return cached
                
                # Call function and cache result
                result = func(*args, **kwargs)
                self.set(cache_key, result, ttl)
                
                return result
            return wrapper
        return decorator

cache = CacheService()

# Example usage:
@cache.cache_result("project", ttl=600)
def get_project_cached(project_id):
    return project_service.get_project(project_id)
```

**Database Query Optimization:**

```sql
-- Materialized view for project statistics
CREATE MATERIALIZED VIEW project_stats AS
SELECT 
    p.id as project_id,
    p.title,
    COUNT(DISTINCT m.id) as manuscript_count,
    COUNT(DISTINCT c.id) as chapter_count,
    SUM(c.word_count) as total_words,
    MAX(c.modified_at) as last_modified
FROM projects p
LEFT JOIN manuscripts m ON m.project_id = p.id
LEFT JOIN chapters c ON c.manuscript_id = m.id
GROUP BY p.id, p.title;

-- Refresh periodically
REFRESH MATERIALIZED VIEW project_stats;

-- Index for fast lookups
CREATE INDEX idx_project_stats_id ON project_stats(project_id);
```

---

## 5. Implementation Roadmap

**Phased rollout over 12 months:**

### Phase 1: Foundation (Months 1-3) - **Must-Have Core**

**Goal:** Establish cloud infrastructure and multi-user support

**Deliverables:**
- ✅ PostgreSQL database deployment (Supabase)
- ✅ User authentication system (email + OAuth)
- ✅ Cloud storage migration tool (local → cloud)
- ✅ Project sharing and permissions (basic)
- ✅ Scene-level organization (add scenes table)

**Acceptance Criteria:**
- Users can create accounts and log in
- Existing local projects can be migrated to cloud
- Projects can be shared with collaborators
- Scenes can be created and edited within chapters

**Team Requirements:**
- 1 Backend Engineer (database, API)
- 1 Frontend Engineer (authentication UI)
- 1 DevOps Engineer (deployment)

---

### Phase 2: AI Narrative Tools (Months 4-6) - **Competitive Feature Parity**

**Goal:** Implement Describe, Expand, Rewrite workflows

**Deliverables:**
- ✅ AI Describe tool with sensory expansion
- ✅ AI Expand tool with multiple generation options
- ✅ AI Rewrite tool (POV, tone, pacing)
- ✅ Context injection from World Bible
- ✅ Consistency checker (basic)

**Acceptance Criteria:**
- Users can select text and apply AI transformations
- World Bible entries are automatically injected into prompts
- Multiple AI generation options are presented
- Consistency checker flags character/lore conflicts

**Team Requirements:**
- 1 AI/ML Engineer (prompt engineering, context injection)
- 1 Frontend Engineer (AI tools UI)

---

### Phase 3: Professional Export (Months 7-8) - **Publishing Ready**

**Goal:** Export to professional manuscript formats

**Deliverables:**
- ✅ Enhanced DOCX export with formatting
- ✅ EPUB export for ebooks
- ✅ PDF export (via DOCX conversion)
- ✅ Export templates (cover pages, formatting)

**Acceptance Criteria:**
- DOCX exports are properly formatted for submission
- EPUB files pass validation and work on Kindle/Apple Books
- PDF exports are print-ready

**Team Requirements:**
- 1 Backend Engineer (export services)
- 1 Technical Writer (export templates)

---

### Phase 4: Analytics & Insights (Months 9-10) - **User Engagement**

**Goal:** Track progress and maintain writing discipline

**Deliverables:**
- ✅ Writing analytics dashboard
- ✅ Word count tracking and charts
- ✅ Writing streak calculation
- ✅ Timeline visualization
- ✅ Progress widgets

**Acceptance Criteria:**
- Users can view daily word count history
- Writing streaks are calculated correctly
- Timeline view shows chronological vs. narrative order
- Progress charts update in real-time

**Team Requirements:**
- 1 Frontend Engineer (analytics UI, charts)
- 1 Data Engineer (analytics queries)

---

### Phase 5: Templates & Onboarding (Months 11-12) - **User Acquisition**

**Goal:** Improve new user experience and provide guided workflows

**Deliverables:**
- ✅ Template library (novel, screenplay, worldbuilding)
- ✅ First-run wizard
- ✅ Guided project creation
- ✅ Sample projects
- ✅ In-app tutorials

**Acceptance Criteria:**
- New users can create a project from a template
- First-run wizard guides through setup
- Sample projects demonstrate key features
- In-app tutorials reduce support tickets

**Team Requirements:**
- 1 UX Designer (onboarding flows)
- 1 Frontend Engineer (wizard UI)
- 1 Technical Writer (templates, tutorials)

---

### Post-Launch: Advanced Features (Year 2)

**Collaboration Enhancements:**
- Real-time collaborative editing (WebSocket)
- Commenting and feedback system
- Team workspaces with billing

**Advanced AI:**
- Character voice consistency (fine-tuning)
- Plot hole detection
- Theme and symbolism analysis
- Genre-specific writing suggestions

**Integrations:**
- Scrivener import/export
- Notion integration
- Google Docs sync
- Obsidian plugin

**Platform Expansion:**
- Mobile app (iOS, Android)
- Desktop app (Electron)
- API for third-party integrations

---

## 6. Risk Assessment

### 6.1 Technical Risks

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| **Database migration data loss** | High | Medium | Implement robust backup/restore, test migration extensively, provide rollback option |
| **Supabase vendor lock-in** | Medium | High | Abstract database layer, use standard PostgreSQL features, maintain option for self-hosted |
| **AI API rate limits** | Medium | Medium | Implement request queuing, caching, and fallback to alternative providers |
| **Real-time collaboration conflicts** | Medium | Medium | Implement operational transformation or CRDT for conflict resolution |
| **Performance degradation with scale** | High | Medium | Implement caching, query optimization, CDN for static assets |

### 6.2 Business Risks

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| **User resistance to cloud migration** | High | Medium | Maintain local-mode option, provide clear benefits, seamless migration tool |
| **Competitor feature velocity** | High | High | Focus on unique differentiation (World Bible, modular design), rapid iteration |
| **Privacy concerns (cloud storage)** | Medium | Medium | Transparent privacy policy, end-to-end encryption option, data export tools |
| **Pricing model rejection** | High | Low | Freemium model with generous free tier, transparent pricing, no lock-in |

### 6.3 User Experience Risks

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| **Complexity overwhelming new users** | High | High | Strong onboarding, templates, progressive disclosure, contextual help |
| **Feature creep** | Medium | High | Maintain clear product vision, user feedback loops, regular UX audits |
| **Migration friction** | Medium | Medium | One-click migration tool, clear instructions, support team |

---

## 7. Success Metrics

### 7.1 Adoption Metrics

- **User Accounts Created:** Target 10,000 in first 6 months
- **Active Projects:** Target 5,000 active projects
- **Cloud Migration Rate:** 70% of existing users migrate to cloud
- **Collaboration Adoption:** 30% of projects have 2+ collaborators

### 7.2 Engagement Metrics

- **Daily Active Users (DAU):** Target 1,000 DAU
- **Weekly Active Users (WAU):** Target 3,000 WAU
- **Writing Streak Avg:** Target 5 days average streak
- **Words Written per User:** Target 500 words/day average

### 7.3 Feature Usage Metrics

- **AI Tool Usage:**
  - Describe: 40% of users
  - Expand: 60% of users
  - Rewrite: 35% of users
- **Export Usage:** 50% of users export at least once
- **World Bible Entries:** Average 20 entries per project
- **Scene Organization:** 40% of projects use scene-level structure

### 7.4 Quality Metrics

- **Bug Report Rate:** < 5% of users report bugs
- **Support Ticket Rate:** < 2% of users need support
- **User Satisfaction (NPS):** Target NPS > 40
- **Consistency Checker Accuracy:** 80% of flagged issues are valid

---

## Appendix A: Technology Stack

### Backend
- **Language:** Python 3.11+
- **Web Framework:** Streamlit 1.30+ (UI), FastAPI (API)
- **Database:** PostgreSQL 15 (via Supabase)
- **Cache:** Redis 7
- **ORM:** SQLAlchemy or raw SQL with psycopg2
- **Authentication:** Supabase Auth (OIDC providers)

### Frontend
- **Framework:** Streamlit components
- **State Management:** Streamlit session state + custom store
- **Charts:** Plotly
- **Rich Text Editing:** Custom Streamlit text components

### AI/ML
- **Primary Provider:** Groq (existing)
- **Fallback Providers:** OpenAI, Anthropic (future)
- **Embeddings:** OpenAI text-embedding-ada-002 (for semantic search)

### DevOps
- **Hosting:** Railway, Heroku, or self-hosted Docker
- **CI/CD:** GitHub Actions
- **Monitoring:** Sentry (errors), PostHog (analytics)
- **Logging:** Structured logging with Winston or Python logging

### Export
- **DOCX:** python-docx
- **PDF:** LibreOffice headless conversion
- **EPUB:** ebooklib

---

## Appendix B: Glossary

- **World Bible:** Structured database of canonical worldbuilding elements (characters, locations, lore)
- **Scene:** Subdivision of a chapter representing a single continuous narrative unit
- **Manuscript:** Collection of chapters representing a complete work or version
- **Describe:** AI tool that expands text with sensory details
- **Expand:** AI tool that continues narrative from a given point
- **Rewrite:** AI tool that transforms text with different attributes
- **Consistency Checker:** Tool that detects contradictions in narrative elements
- **Row-Level Security (RLS):** Database feature that restricts data access based on user context
- **Operational Transformation (OT):** Algorithm for resolving concurrent editing conflicts
- **CRDT:** Conflict-free Replicated Data Type for distributed collaboration

---

## Appendix C: References

### Competitive Platforms Analyzed
1. **Sudowrite:** https://www.sudowrite.com/
2. **NovelAI:** https://novelai.net/
3. **Jasper AI:** https://www.jasper.ai/
4. **Squibler:** https://www.squibler.io/

### Technical References
1. **Supabase Documentation:** https://supabase.com/docs
2. **PostgreSQL Row-Level Security:** https://www.postgresql.org/docs/current/ddl-rowsecurity.html
3. **Streamlit Documentation:** https://docs.streamlit.io/
4. **FastAPI Documentation:** https://fastapi.tiangolo.com/

---

## Document Change Log

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-02-09 | GitHub Copilot | Initial comprehensive design document |

---

**End of Document**

*This is an implementation-ready specification. For questions or clarifications, consult the Mantis Studio development team.*
