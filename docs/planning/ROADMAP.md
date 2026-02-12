# 🚀 MANTIS Studio Product Roadmap

> **Transforming MANTIS from a Local Writing Tool into a Hosted AI Narrative Intelligence Platform**

---

## Document Purpose

This roadmap outlines the strategic evolution of **MANTIS Studio** (Modular AI Narrative Text Intelligence System) from a single-user Streamlit application into a fully hosted, scalable, multi-user SaaS platform. This document is designed for:

- **Developers** looking to contribute to platform features
- **Potential Contributors** seeking technical direction
- **Investors & Early Adopters** evaluating product vision and market opportunity
- **Platform & DevOps Teams** planning hosting and deployment infrastructure

---

## 1. Current State Assessment

### What MANTIS Studio Is Today

MANTIS Studio is a **local-first AI-assisted creative writing environment** built with Streamlit. It provides writers, novelists, screenwriters, and game developers with:

- **Structured project management** for narrative development
- **AI-powered outlining and drafting** with support for multiple LLM providers (Groq, OpenAI, Ollama)
- **World Bible system** for managing characters, locations, lore, and narrative canon
- **Chapter-by-chapter editor** with AI assistance for rewriting, expansion, and summarization
- **Export capabilities** to DOCX, TXT, and planned PDF formats
- **Session-based state management** using Streamlit's native session state

### Current Technical Architecture

**Frontend**: Streamlit 1.30.0+ (Python-based declarative UI)  
**State Management**: Streamlit session state (ephemeral, per-browser session)  
**Storage**: Local JSON files in `projects/` directory  
**AI Integration**: Direct API calls to Groq/OpenAI/Ollama with user-provided API keys  
**Authentication**: Optional OAuth (Google/Microsoft/Apple) via Supabase for single-user scenarios  
**Deployment**: Runs locally via `streamlit run app/main.py`

### Key Limitations

1. **Single-User Only**: No concept of accounts, user profiles, or multi-tenancy
2. **Local Data Storage**: Projects are stored as JSON files on the user's filesystem; no cloud persistence
3. **No Hosted Demo**: Users must install Python, dependencies, and run the app locally
4. **API Key Management**: Each user must provide their own AI provider API keys
5. **No Collaboration**: Projects cannot be shared, versioned, or co-edited
6. **Session-Based State**: State is lost when the browser closes; no server-side persistence
7. **Limited Scalability**: Single-threaded Streamlit process cannot handle concurrent users efficiently
8. **Lack of Usage Analytics**: No visibility into feature adoption, error rates, or user behavior

### Current Strengths

- **Modular architecture** with clear separation of concerns (`app/services/`, `app/views/`, `app/components/`)
- **Rich feature set** already validated by local users
- **Extensible AI abstraction** supporting multiple providers
- **Professional documentation** and onboarding materials
- **Active development** with version control and CI/CD foundations

---

## 2. Vision & Product Goals

### Product Vision

**MANTIS Studio will become the leading hosted AI narrative intelligence platform for creators, enabling writers, studios, and teams to develop stories collaboratively with AI assistance in a secure, scalable, and accessible cloud environment.**

### Strategic Goals

#### Accessibility
- **Zero-Setup Experience**: Users can sign up and start creating within 60 seconds
- **Cross-Platform Access**: Work from any device with a browser—desktop, tablet, or mobile
- **No Technical Barriers**: Eliminate Python installation, dependency management, and local configuration

#### Persistence
- **Cloud-Native Storage**: All projects, drafts, and world-building data persisted in secure cloud databases
- **Automatic Versioning**: Track changes, rollback drafts, and recover deleted content
- **Cross-Device Sync**: Start on desktop, continue on mobile, without manual file transfers

#### Scalability
- **Multi-User Concurrent Access**: Support thousands of simultaneous users with responsive performance
- **Elastic Infrastructure**: Auto-scale compute and storage based on demand
- **Global Availability**: Low-latency access via CDN and regional hosting

#### Collaboration
- **Team Workspaces**: Writers, editors, and studios collaborate on shared projects
- **Granular Permissions**: Owner, Editor, Viewer roles for controlled access
- **Real-Time Awareness**: See who's editing what, with live cursors and presence indicators (future)

### Target User Segments

1. **Individual Creators**: Novelists, screenwriters, game writers needing AI-assisted drafting
2. **Writing Teams**: Co-authors collaborating on shared universes or series
3. **Content Studios**: Production companies managing multiple projects and writers
4. **Educators**: Teachers and students using MANTIS for creative writing courses
5. **Enterprises**: Large organizations with IP-sensitive narrative development needs

---

## 3. Architecture Evolution Plan

### Current Architecture (Local Single-User)

```
┌─────────────────────────────────────┐
│  Browser (Single User)              │
│  ┌───────────────────────────────┐  │
│  │  Streamlit UI + State         │  │
│  │  (Session-based, ephemeral)   │  │
│  └───────────────┬───────────────┘  │
│                  │                   │
│  ┌───────────────▼───────────────┐  │
│  │  Local JSON Files             │  │
│  │  (projects/*.json)            │  │
│  └───────────────────────────────┘  │
└─────────────────────────────────────┘
```

### Target Architecture (Hosted Multi-User Platform)

```
┌──────────────────────────────────────────────────────────────┐
│  Frontend Layer (Browser)                                    │
│  ┌────────────────────────────────────────────────────────┐  │
│  │  Option A: Enhanced Streamlit (rapid iteration)        │  │
│  │  Option B: React/Vue SPA (modern UX, better control)   │  │
│  └────────────────────┬───────────────────────────────────┘  │
└─────────────────────────┼────────────────────────────────────┘
                          │ HTTPS / JWT Auth
┌─────────────────────────▼────────────────────────────────────┐
│  API Layer (Stateless Backend)                              │
│  ┌────────────────────────────────────────────────────────┐  │
│  │  FastAPI / Django / Node.js                            │  │
│  │  - REST/GraphQL endpoints                              │  │
│  │  - Authentication middleware                           │  │
│  │  - Rate limiting & quotas                              │  │
│  │  - WebSocket support (collaboration)                   │  │
│  └──────────────┬──────────────────┬──────────────────────┘  │
└─────────────────┼──────────────────┼─────────────────────────┘
                  │                  │
       ┌──────────▼─────────┐  ┌────▼──────────────┐
       │  PostgreSQL /      │  │  Redis Cache      │
       │  Supabase DB       │  │  (Sessions,       │
       │  (User data,       │  │   Rate limits)    │
       │   Projects, WB)    │  │                   │
       └────────────────────┘  └───────────────────┘
                  │
       ┌──────────▼─────────────────────────────────┐
       │  AI Service Layer (Abstraction)            │
       │  - Groq / OpenAI / Ollama routing          │
       │  - Cost tracking & limits                  │
       │  - Response caching                        │
       └────────────────────────────────────────────┘
```

### Frontend Options Analysis

#### Option A: Enhanced Streamlit (Recommended for Phase 1)

**Pros**:
- Leverage existing codebase (~90% reusable)
- Faster time-to-market (weeks vs. months)
- Streamlit Cloud native deployment
- Team familiarity with Python stack

**Cons**:
- Limited customization for advanced UX
- WebSocket limitations for real-time collaboration
- Performance overhead for complex state

**Best For**: MVP, early beta, rapid validation

#### Option B: React/Vue Migration (Future State)

**Pros**:
- Modern SPA experience (instant navigation, offline-first)
- Full control over UI/UX
- Better mobile responsiveness
- Rich ecosystem for real-time features (Yjs, Automerge)

**Cons**:
- Complete rewrite of frontend (~6 months)
- New tech stack learning curve
- Requires backend API design

**Best For**: Scale phase, post-PMF, funding secured

### Backend API Layer Design

**Recommended Stack**: **FastAPI** (Python)

**Rationale**:
- Python ecosystem alignment (reuse `app/services/`)
- Built-in async support for high concurrency
- Automatic OpenAPI documentation
- WebSocket support for real-time features
- Strong typing with Pydantic

**Core API Domains**:

```
/api/v1/auth          # Registration, login, OAuth, sessions
/api/v1/users         # Profile management, preferences
/api/v1/projects      # CRUD, list, search
/api/v1/outlines      # Outline management
/api/v1/chapters      # Chapter CRUD + AI operations
/api/v1/world-bible   # Characters, locations, lore
/api/v1/ai            # AI generation, model selection
/api/v1/export        # Document generation
/api/v1/collaborate   # Sharing, permissions, teams
```

### Key Architectural Principles

1. **Stateless Servers**: All session state in Redis or JWT; enables horizontal scaling
2. **Environment-Based Config**: Dev, staging, prod environments with isolated secrets
3. **Service Separation**: Frontend, API, DB, AI services independently deployable
4. **API-First Design**: All features exposed via REST/GraphQL before UI implementation
5. **Database Transactions**: ACID guarantees for multi-step operations (project creation, sharing)

---

## 4. User Authentication & Accounts (CRITICAL)

### Requirements

User authentication is the **foundational requirement** for a multi-user platform. Without it, no other hosted features are possible.

### Registration & Login Flows

#### Email/Password Registration

1. User submits email + password (minimum 8 chars, complexity rules)
2. System validates uniqueness, hashes password (bcrypt/Argon2)
3. Sends verification email with time-limited token
4. User clicks link → account activated
5. Redirect to onboarding flow

#### OAuth Social Login

**Supported Providers**:
- Google (OAuth 2.0)
- GitHub (OAuth 2.0)
- Microsoft (OAuth 2.0)
- Apple Sign-In (future)

**Flow**:
1. User clicks "Continue with Google"
2. Redirected to provider consent screen
3. Provider returns auth code
4. Backend exchanges code for user profile
5. Create or link account
6. Issue session token

### Session Management

**Technology**: JWT (JSON Web Tokens)

**Token Structure**:
```json
{
  "user_id": "uuid-v4",
  "email": "user@example.com",
  "plan": "free|pro|enterprise",
  "exp": 1678886400,
  "iat": 1678800000
}
```

**Security**:
- Access token: 1-hour expiry (short-lived)
- Refresh token: 30-day expiry (HttpOnly cookie, stored in DB)
- Token rotation on refresh
- Revocation list for logged-out tokens

### User Profiles

**Core Fields**:
- `user_id` (UUID, primary key)
- `email` (unique, indexed)
- `display_name`
- `avatar_url`
- `plan_tier` (free, pro, enterprise)
- `created_at`, `updated_at`
- `preferences` (JSON: theme, default AI model, etc.)

**Editable by User**:
- Display name
- Avatar (upload or Gravatar)
- Email (requires re-verification)
- Password (requires current password)
- Notification preferences

### Password Reset Flow

1. User clicks "Forgot Password"
2. Enters email → backend generates time-limited token (15 min expiry)
3. Email sent with reset link
4. User sets new password
5. All existing sessions invalidated
6. Confirmation email sent

### Email Verification

**Purpose**: Prevent spam accounts, enable password recovery

**Flow**:
1. On registration, send verification email
2. Unverified users have limited access (view-only mode, or blocked)
3. Verified users unlock full features
4. Re-send verification link option (rate-limited)

### Guest/Demo Access

**Use Case**: Allow exploration without commitment

**Implementation**:
- "Try Demo" button creates ephemeral guest account
- Guest session expires after 24 hours
- Limited to 1 project, 10 chapters, 50 AI calls
- Prompt to register to persist work
- Guest data purged after 7 days

---

## 5. Persistent Cloud Data Storage

### Migration from Local JSON to Cloud Database

#### Current Storage (Local JSON)

```
projects/
├── my-novel.json
├── screenplay-draft.json
└── .backups/
    └── my-novel_20260209.json
```

**Problems**:
- No concurrent access
- Prone to corruption
- No query capabilities
- Manual backup management

#### Target Storage (Cloud Database)

**Recommended Database**: **PostgreSQL** (via Supabase or managed AWS RDS)

**Rationale**:
- ACID transactions for data integrity
- Rich query language (JOIN, aggregations)
- JSON column support for flexible schema
- Proven scalability (billions of rows)
- Row-level security (RLS) for multi-tenancy

### Database Schema Design

#### Users Table
```sql
CREATE TABLE users (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  email VARCHAR(255) UNIQUE NOT NULL,
  password_hash VARCHAR(255),
  display_name VARCHAR(100),
  avatar_url TEXT,
  plan_tier VARCHAR(20) DEFAULT 'free',
  email_verified BOOLEAN DEFAULT FALSE,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);
```

#### Projects Table
```sql
CREATE TABLE projects (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  owner_id UUID REFERENCES users(id) ON DELETE CASCADE,
  title VARCHAR(255) NOT NULL,
  description TEXT,
  outline JSONB,
  metadata JSONB,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);
CREATE INDEX idx_projects_owner ON projects(owner_id);
```

#### Chapters Table
```sql
CREATE TABLE chapters (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
  chapter_number INT NOT NULL,
  title VARCHAR(255),
  content TEXT,
  word_count INT DEFAULT 0,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW(),
  UNIQUE(project_id, chapter_number)
);
CREATE INDEX idx_chapters_project ON chapters(project_id);
```

#### World Bible Entities Table
```sql
CREATE TABLE world_bible_entities (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
  entity_type VARCHAR(50), -- character, location, lore, etc.
  name VARCHAR(255) NOT NULL,
  description TEXT,
  attributes JSONB,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);
CREATE INDEX idx_entities_project ON world_bible_entities(project_id);
CREATE INDEX idx_entities_type ON world_bible_entities(entity_type);
```

### Data Isolation & Security

**Row-Level Security (RLS)**:

```sql
-- Enable RLS
ALTER TABLE projects ENABLE ROW LEVEL SECURITY;

-- Policy: Users can only see their own projects
CREATE POLICY projects_isolation ON projects
  FOR ALL
  USING (owner_id = current_user_id());
```

**Application-Level Isolation**:
- All queries filtered by `user_id` from JWT token
- No cross-user data leakage via API
- Audit logging of all data access

### Versioning & Change History

**Approach**: Event Sourcing or Snapshot-Based

#### Snapshot-Based (Recommended for MVP)

```sql
CREATE TABLE project_versions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
  version_number INT NOT NULL,
  snapshot JSONB, -- Full project state at this version
  created_at TIMESTAMP DEFAULT NOW(),
  created_by UUID REFERENCES users(id)
);
```

**Features**:
- Auto-save every 5 minutes
- Manual "Save Version" button
- Version comparison UI
- Rollback to previous version

### Backups & Disaster Recovery

**Automated Backups**:
- Daily full database snapshots (retained 30 days)
- Point-in-time recovery (PITR) within 7 days
- Cross-region replication for disaster recovery

**User-Initiated Exports**:
- Download entire project as JSON
- Export to cloud storage (Google Drive, Dropbox)

### Migration Strategy from Local to Cloud

**Phase 1: Import Tool**
1. User uploads local JSON file
2. Backend validates schema
3. Parse and insert into DB tables
4. Associate with user account

**Phase 2: Hybrid Mode** (Optional)
- Support both local and cloud storage
- Sync local → cloud on save
- Graceful deprecation over 6 months

---

## 6. Multi-User & Collaboration Features

### Multiple Projects Per User

**Requirements**:
- Users can create unlimited projects (free tier: 3 projects max, pro: unlimited)
- Project list view with search, sort, and filters
- Project templates (novel, screenplay, game narrative)

**UI**:
- Dashboard: "My Projects" grid with thumbnails, titles, last-modified
- Quick actions: Open, Duplicate, Archive, Delete

### Team Workspaces

**Concept**: Shared container for multiple projects

**Schema**:
```sql
CREATE TABLE workspaces (
  id UUID PRIMARY KEY,
  name VARCHAR(255) NOT NULL,
  owner_id UUID REFERENCES users(id),
  plan_tier VARCHAR(20) DEFAULT 'team',
  created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE workspace_members (
  workspace_id UUID REFERENCES workspaces(id),
  user_id UUID REFERENCES users(id),
  role VARCHAR(20), -- owner, admin, member
  joined_at TIMESTAMP DEFAULT NOW(),
  PRIMARY KEY (workspace_id, user_id)
);
```

**Features**:
- Invite members via email
- Team billing (single subscription for all members)
- Shared AI usage quota

### Project Sharing & Permissions

#### Sharing Modes

1. **Private**: Only owner can access
2. **Shared with Specific Users**: Invite by email
3. **Link-Based Sharing**: Anyone with link (read-only or editable)
4. **Public**: Listed in community gallery (future)

#### Permission Levels

| Role     | View | Comment | Edit | Delete | Share | Manage Team |
|----------|------|---------|------|--------|-------|-------------|
| **Owner**    | ✅   | ✅      | ✅   | ✅     | ✅    | ✅          |
| **Editor**   | ✅   | ✅      | ✅   | ❌     | ❌    | ❌          |
| **Commenter**| ✅   | ✅      | ❌   | ❌     | ❌    | ❌          |
| **Viewer**   | ✅   | ❌      | ❌   | ❌     | ❌    | ❌          |

#### Implementation

```sql
CREATE TABLE project_shares (
  id UUID PRIMARY KEY,
  project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
  shared_with_user_id UUID REFERENCES users(id),
  permission_level VARCHAR(20), -- owner, editor, commenter, viewer
  shared_by UUID REFERENCES users(id),
  created_at TIMESTAMP DEFAULT NOW()
);
```

**Access Control**:
- Check `project_shares` table before granting access
- Cache permissions in Redis for performance
- Revoke share → immediate access removal

### Real-Time Collaboration Roadmap (Future)

**Phase 1**: Asynchronous Collaboration (MVP)
- Users take turns editing (lock-based)
- Change notifications via email/in-app

**Phase 2**: Operational Transform (OT) or CRDT
- Google Docs-style simultaneous editing
- Live cursors and presence indicators
- Conflict-free merges

**Technology Options**:
- Yjs (CRDT library) + WebSocket server
- ShareDB (OT library)
- Automerge (CRDT, local-first)

**Challenges**:
- High infrastructure cost (persistent WebSocket connections)
- Complex conflict resolution for AI-generated content
- Latency for global users

**Timeline**: 12-18 months post-launch

---

## 7. AI Service Layer Improvements

### Centralized AI Service Abstraction

**Current State**: Direct API calls in `app/services/ai.py`

**Target State**: Unified AI gateway with provider abstraction

```python
class AIGateway:
    def __init__(self, user_id: str, plan_tier: str):
        self.user_id = user_id
        self.plan_tier = plan_tier
        self.rate_limiter = RateLimiter(user_id)
        self.cost_tracker = CostTracker(user_id)
    
    async def generate(
        self,
        prompt: str,
        model: str,
        temperature: float = 0.7,
        max_tokens: int = 2000
    ) -> str:
        # Rate limiting
        await self.rate_limiter.check_limit()
        
        # Route to appropriate provider
        provider = self._get_provider(model)
        
        # Execute request
        response = await provider.generate(prompt, temperature, max_tokens)
        
        # Track usage and cost
        await self.cost_tracker.record(model, response.tokens)
        
        return response.text
```

### Rate Limiting

**Purpose**: Prevent abuse, control costs, enforce plan limits

**Implementation**: Token bucket algorithm

```python
# Free tier: 100 AI calls/day
# Pro tier: 1000 AI calls/day
# Enterprise: Custom limits

redis_key = f"rate_limit:{user_id}:{date}"
current_count = redis.incr(redis_key)
if current_count > plan_limits[plan_tier]:
    raise RateLimitExceeded("Daily AI quota exceeded. Upgrade plan.")
```

**User Feedback**:
- Progress bar showing quota usage
- Warning at 80% usage
- Upgrade prompt at limit

### Model Switching

**User-Selectable Models**:

| Provider | Model              | Speed | Quality | Cost/1K tokens |
|----------|--------------------|-------|---------|----------------|
| Groq     | llama-3.1-70b      | ⚡⚡⚡   | ⭐⭐⭐   | $0.50          |
| OpenAI   | gpt-4o-mini        | ⚡⚡     | ⭐⭐⭐⭐  | $1.50          |
| OpenAI   | gpt-4o             | ⚡      | ⭐⭐⭐⭐⭐ | $5.00          |
| Ollama   | llama3.1 (local)   | ⚡      | ⭐⭐     | $0.00          |

**Implementation**:
- Dropdown in AI settings
- Model capabilities metadata (context length, streaming support)
- Automatic fallback if primary model unavailable

### Cost Control & Budgeting

**Per-User Tracking**:

```sql
CREATE TABLE ai_usage_log (
  id UUID PRIMARY KEY,
  user_id UUID REFERENCES users(id),
  model VARCHAR(50),
  prompt_tokens INT,
  completion_tokens INT,
  cost_usd DECIMAL(10, 4),
  created_at TIMESTAMP DEFAULT NOW()
);
```

**Dashboard Metrics**:
- Total spend this month
- Cost breakdown by model
- Projected monthly cost (based on current usage)

**Budget Alerts**:
- Set spending limit (e.g., $50/month)
- Email alert at 80%, 100%
- Auto-pause AI features if exceeded

### API Key Management

**Bring-Your-Own-Key (BYOK) Mode** (Optional for Pro Users):
- User provides their own OpenAI/Groq API key
- Bypasses platform rate limits and costs
- Securely encrypted in database

**Platform-Managed Keys** (Default):
- MANTIS provides API keys
- Usage billed to user's plan
- Keys rotated regularly
- Rate limiting per account

### Logging & Error Handling

**Comprehensive Logging**:

```python
logger.info("AI request", extra={
    "user_id": user_id,
    "model": model,
    "prompt_length": len(prompt),
    "temperature": temperature,
    "response_tokens": response.tokens,
    "latency_ms": response.latency,
    "status": "success"
})
```

**Error Handling**:
- Retry logic for transient failures (3 retries with exponential backoff)
- Graceful degradation (fallback to simpler model)
- User-friendly error messages ("AI service temporarily unavailable. Retrying...")

**Monitoring**:
- Alert on error rate > 5%
- Track average latency per model
- Dashboard for AI service health

---

## 8. Security & Compliance

### Input/Output Sanitization

**User Input Validation**:
- Strip HTML/scripts from text fields
- Limit input length (max 50K chars per chapter)
- Reject null bytes, control characters
- Validate JSON schema for structured data

**AI Output Sanitization**:
- Filter harmful content (hate speech, violence) via content moderation API
- Truncate excessively long responses
- Escape special characters before rendering

### CSRF & XSS Protection

**Cross-Site Request Forgery (CSRF)**:
- SameSite cookies for session tokens
- CSRF tokens for state-changing operations
- Validate Origin/Referer headers

**Cross-Site Scripting (XSS)**:
- Content Security Policy (CSP) headers
- Sanitize all user-generated content before rendering
- Use templating engines with auto-escaping

### Secure Secrets Handling

**Environment Variables**:
- API keys, DB passwords in `.env` (dev) or secret management service (prod)
- Never commit secrets to Git
- Rotate credentials quarterly

**Secret Management Services**:
- AWS Secrets Manager
- HashiCorp Vault
- GCP Secret Manager

**In-Database Encryption**:
- Encrypt sensitive fields (API keys, OAuth tokens) at rest
- Use application-level encryption (AES-256) before storing

### Audit Logging

**What to Log**:
- User login/logout
- Project creation/deletion
- Permission changes (sharing, role updates)
- AI API calls (user, model, cost)
- Data exports

**Log Structure**:

```json
{
  "timestamp": "2026-02-09T23:00:00Z",
  "user_id": "uuid",
  "action": "project.share",
  "resource_id": "project-uuid",
  "metadata": {"shared_with": "user@example.com", "role": "editor"},
  "ip_address": "203.0.113.42",
  "user_agent": "Mozilla/5.0..."
}
```

**Retention**: 90 days (compliance), 1 year (enterprise)

### GDPR & Privacy Compliance

**GDPR Requirements**:

1. **Right to Access**: Users can download all their data (JSON export)
2. **Right to Deletion**: Account deletion purges all personal data within 30 days
3. **Right to Rectification**: Users can edit profile, projects
4. **Right to Portability**: Export data in machine-readable format (JSON, CSV)
5. **Consent Management**: Clear opt-in for marketing emails, analytics

**Privacy Policy**:
- Located at `/legal/privacy.md`
- Covers: data collection, usage, retention, sharing, user rights
- Updated: 2026-02-09 (maintain current version)

**Cookie Policy**:
- Disclose session cookies, analytics cookies
- Cookie consent banner (EU users)
- Opt-out mechanism for non-essential cookies

### Terms of Service

**Key Sections**:
- Acceptable Use Policy (no illegal content, spam, abuse)
- Intellectual Property (user owns their content, MANTIS owns platform)
- Limitation of Liability
- Termination clause

### Abuse Prevention

**Rate Limiting**:
- API endpoints: 100 req/min per user
- Registration: 5 accounts per IP per day
- Login attempts: 5 failures → 15-min lockout

**Content Moderation**:
- Automated flagging of ToS violations (via OpenAI Moderation API)
- User reporting mechanism
- Manual review queue for flagged content

**DDoS Protection**:
- Cloudflare or AWS Shield
- Rate limiting at CDN layer
- IP reputation checks

---

## 9. Deployment & Hosting Strategy

### Cloud Hosting Options

#### Option 1: Fly.io (Recommended for MVP)

**Pros**:
- Simple deployment (`flyctl deploy`)
- Built-in global load balancing
- Low-cost for small-scale ($20-50/month for MVP)
- Auto-scaling support

**Cons**:
- Limited managed services (need external DB)
- Smaller ecosystem vs. AWS/GCP

**Best For**: Rapid launch, small teams, budget-conscious

---

#### Option 2: Render.com

**Pros**:
- Managed PostgreSQL included
- Free tier for prototyping
- Auto-deploy from GitHub
- Built-in SSL and CDN

**Cons**:
- Performance limits on free tier
- Less control vs. AWS/GCP

**Best For**: Solo developers, early beta

---

#### Option 3: AWS (Amazon Web Services)

**Pros**:
- Comprehensive service catalog (RDS, S3, Lambda, CloudFront)
- Battle-tested scalability
- Global presence (20+ regions)
- Strong enterprise adoption

**Cons**:
- Steep learning curve
- Complex pricing
- High operational overhead

**Best For**: Post-PMF, funded startups, enterprise customers

**Services**:
- **Compute**: ECS Fargate (containers) or EC2 (VMs)
- **Database**: RDS PostgreSQL (managed)
- **Storage**: S3 (files, backups)
- **CDN**: CloudFront
- **DNS**: Route 53

---

#### Option 4: Google Cloud Platform (GCP)

**Pros**:
- Generous free tier ($300 credit)
- Superior AI/ML services (Vertex AI)
- Global network performance

**Cons**:
- Smaller market share (less community support)
- Frequent product deprecations

**Best For**: AI-heavy workloads, startups with GCP credits

---

#### Option 5: Azure

**Pros**:
- Strong enterprise integrations (Active Directory, Office 365)
- Hybrid cloud capabilities

**Cons**:
- Complex pricing
- Less developer-friendly

**Best For**: Enterprise sales, Microsoft-aligned customers

---

### Database Hosting

**Recommended**: **Supabase** (PostgreSQL + Auth + Storage)

**Rationale**:
- Managed PostgreSQL with auto-scaling
- Built-in authentication (OAuth, email/password)
- Row-level security (RLS) for multi-tenancy
- Real-time subscriptions (WebSocket)
- Free tier: 500MB DB, 50K monthly active users

**Alternatives**:
- **AWS RDS**: Production-grade, higher cost
- **Neon**: Serverless Postgres, auto-scaling
- **PlanetScale**: MySQL, branching workflows

---

### CI/CD Pipelines

**Tooling**: GitHub Actions (already in use)

**Pipeline Stages**:

```yaml
# .github/workflows/deploy.yml
name: Deploy to Production

on:
  push:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - run: pip install -r requirements.txt
      - run: pytest tests/
  
  build:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - run: docker build -t mantis-studio:${{ github.sha }} .
      - run: docker push mantis-studio:${{ github.sha }}
  
  deploy:
    needs: build
    runs-on: ubuntu-latest
    steps:
      - run: kubectl set image deployment/mantis-studio app=mantis-studio:${{ github.sha }}
```

**Automated Checks**:
- Lint (flake8, black)
- Type checking (mypy)
- Security scan (bandit, safety)
- Unit tests (pytest)
- Integration tests (API endpoints)

---

### Environment Separation

| Environment | Purpose                     | Database       | URL                        |
|-------------|-----------------------------|----------------|----------------------------|
| **Development** | Local dev machines         | Local Postgres | localhost:8000             |
| **Staging**     | Pre-production testing     | Staging DB     | staging.mantis.studio      |
| **Production**  | Live user traffic          | Prod DB        | app.mantis.studio          |

**Configuration Management**:
- Environment variables for secrets
- Feature flags for gradual rollouts (LaunchDarkly, Flagsmith)

---

### Domain, HTTPS, and SSL

**Domain Registration**: Namecheap, Google Domains, Route 53

**DNS Setup**:
```
app.mantis.studio       → Production load balancer
staging.mantis.studio   → Staging load balancer
api.mantis.studio       → API gateway
www.mantis.studio       → Marketing site (redirect to app)
```

**SSL Certificates**:
- **Let's Encrypt** (free, auto-renewal)
- **AWS Certificate Manager** (if using AWS)
- **Cloudflare SSL** (if using Cloudflare CDN)

**Enforcement**:
- Redirect HTTP → HTTPS
- HSTS header (force HTTPS)

---

### Monitoring & Logging

**Application Monitoring**:
- **Sentry**: Error tracking and alerting
- **DataDog / New Relic**: APM (latency, throughput)
- **Prometheus + Grafana**: Custom metrics

**Log Aggregation**:
- **Logtail / Papertrail**: Centralized logging
- **CloudWatch Logs** (AWS)
- **GCP Cloud Logging** (GCP)

**Alerts**:
- Error rate > 1%
- API latency p95 > 2 seconds
- Database CPU > 80%
- Disk usage > 85%

**Dashboards**:
- Real-time user count
- AI API call volume
- Revenue (MRR, ARR)
- Funnel metrics (signup → activation → retention)

---

## 10. Monetization & Growth

### Pricing Tiers

#### Free Tier

**Purpose**: Onboarding, viral growth, education

**Limits**:
- 3 projects max
- 50 AI calls/month
- 100 chapters total
- 10 World Bible entities per project
- Community support only

**Target Users**: Students, hobbyists, casual writers

---

#### Pro Tier ($19/month or $190/year)

**Features**:
- Unlimited projects
- 1,000 AI calls/month
- Unlimited chapters
- Unlimited World Bible entities
- Version history (30 days)
- Priority support (48-hour response)
- Export to PDF
- Custom AI model selection

**Target Users**: Professional writers, indie authors

---

#### Team Tier ($49/month per workspace)

**Features**:
- All Pro features
- Shared workspace (up to 10 members)
- 3,000 AI calls/month (shared quota)
- Role-based permissions
- Team analytics
- Dedicated onboarding

**Target Users**: Writing teams, small studios

---

#### Enterprise Tier (Custom Pricing)

**Features**:
- All Team features
- Unlimited members
- Unlimited AI calls or BYOK (Bring Your Own Key)
- On-premise deployment option
- SSO (SAML, LDAP)
- SLA guarantee (99.9% uptime)
- Custom integrations
- Dedicated account manager

**Target Users**: Production studios, publishing houses, large organizations

---

### Usage-Based Add-Ons

**AI Token Packs**:
- $10 for 500 extra calls
- $25 for 1,500 extra calls
- $50 for 4,000 extra calls

**Storage Add-Ons**:
- $5/month for 10GB extra storage (media, attachments)

---

### Billing Integration

**Payment Processor**: **Stripe**

**Features**:
- Subscription management
- Automatic invoicing
- Proration for mid-cycle upgrades
- Dunning management (failed payments)
- Tax calculation (Stripe Tax)

**Implementation**:

```python
# Create subscription
stripe.Subscription.create(
    customer=user.stripe_customer_id,
    items=[{"price": "price_pro_monthly"}],
    payment_behavior="default_incomplete",
    expand=["latest_invoice.payment_intent"]
)
```

**User Dashboard**:
- View current plan
- Upgrade/downgrade
- Update payment method
- Download invoices
- Cancel subscription (with retention offer)

---

### Upgrade Paths

**In-App Prompts**:
- Project limit reached: "Upgrade to Pro for unlimited projects"
- AI quota depleted: "You've used all your AI calls. Upgrade or wait until next month."
- Feature gate: "Version history is a Pro feature. Upgrade now!"

**Conversion Tactics**:
- 7-day free trial for Pro (credit card required)
- Annual plan discount (2 months free)
- Limited-time promotions (Black Friday, NaNoWriMo)

---

### Growth Strategies

**Viral Loops**:
- Referral program: Invite 3 friends → get 1 month Pro free
- Public project gallery: Showcase best work, drive signups

**Content Marketing**:
- Writing guides, AI prompt libraries
- Blog: "How to outline a novel with AI"
- YouTube tutorials

**Partnerships**:
- Integrate with writing communities (NaNoWriMo, Scribophile)
- Affiliate program for writing coaches

**SEO**:
- Target keywords: "AI writing tool," "novel outlining software," "world-building app"

---

## 11. UX/UI Modernization Roadmap

### Beyond Default Streamlit

**Current Limitations**:
- Limited styling customization
- Clunky form interactions
- No drag-and-drop support
- Mobile responsiveness issues

**Enhancements**:

#### Phase 1: CSS Customization
- Custom theme (`assets/theme.css`)
- Branded color palette (already implemented)
- Improved typography (Inter, Merriweather fonts)
- Dark mode toggle

#### Phase 2: Component Library
- Replace default Streamlit widgets with custom React components (Streamlit Components API)
- Rich text editor (TipTap, ProseMirror)
- Drag-and-drop chapter reordering (React DnD)
- Autocomplete for entity mentions

#### Phase 3: Full SPA Migration (Future)
- React or Vue frontend
- Modern design system (Tailwind CSS, Chakra UI)
- Instant navigation (no page reloads)

---

### Loading States & Feedback

**Current**: Spinners, but inconsistent

**Target**:
- Skeleton screens for data loading
- Progress bars for AI generation (streaming)
- Toast notifications for success/error
- Optimistic UI updates (instant feedback, sync in background)

---

### Dashboard Experience

**Empty States**:
- No projects: "Create your first project to get started"
- No chapters: "Start writing your first chapter"

**Quick Actions**:
- "New Project" button (prominent)
- Recently edited projects (top of list)
- Template gallery (novel, screenplay, game script)

**Analytics**:
- Writing streak (days in a row)
- Word count progress (goal: 50K for NaNoWriMo)
- AI usage stats

---

### Accessibility Improvements

**WCAG 2.1 AA Compliance**:
- Keyboard navigation (tab order, shortcuts)
- Screen reader support (ARIA labels)
- Color contrast ratios (4.5:1 minimum)
- Focus indicators (visible outlines)

**Tools**:
- Lighthouse audits
- Axe DevTools
- Manual testing with NVDA/JAWS

---

### Mobile Responsiveness

**Current**: Streamlit is desktop-first

**Target**:
- Responsive breakpoints (mobile, tablet, desktop)
- Touch-friendly controls (larger tap targets)
- Mobile-optimized editor (simplified toolbar)
- Progressive Web App (PWA) for offline access

**Challenges**:
- Streamlit lacks native mobile support
- SPA migration may be required for best mobile experience

---

## 12. Milestone-Based Timeline

### Phase 1: Foundation & Architecture (Months 1-3)

**Goal**: Establish hosted platform foundation with authentication and cloud storage

**Technical Deliverables**:
- [ ] Set up FastAPI backend with core API endpoints (`/auth`, `/projects`, `/users`)
- [ ] Deploy PostgreSQL database (Supabase) with schema v1
- [ ] Implement JWT-based authentication (email/password + Google OAuth)
- [ ] Migrate local JSON storage to database CRUD operations
- [ ] Deploy staging environment (Render or Fly.io)
- [ ] Set up CI/CD pipeline (GitHub Actions → staging auto-deploy)

**User-Facing Deliverables**:
- [ ] User registration and login flow
- [ ] User dashboard with project list
- [ ] Single-user project CRUD (create, read, update, delete)
- [ ] Data import tool (upload local JSON)

**Success Metrics**:
- 100 beta users signed up
- 80% of local users migrated to cloud
- <100ms API latency (p95)

---

### Phase 2: Auth, Persistence & Multi-User (Months 4-6)

**Goal**: Enable multi-user accounts, secure data persistence, and basic collaboration

**Technical Deliverables**:
- [ ] Implement password reset and email verification flows
- [ ] Add project versioning (snapshots every 5 minutes)
- [ ] Build project sharing API with permission levels (owner, editor, viewer)
- [ ] Implement rate limiting and quota enforcement
- [ ] Add audit logging for security events
- [ ] Optimize database queries (indexes, caching)

**User-Facing Deliverables**:
- [ ] Share project with specific users (by email)
- [ ] Version history UI (view/restore previous versions)
- [ ] User profile settings (avatar, display name, password change)
- [ ] Usage dashboard (AI calls, storage, plan limits)

**Success Metrics**:
- 500 active users
- 20% of projects shared with collaborators
- 90% user satisfaction (NPS survey)

---

### Phase 3: Hosting & Public Beta (Months 7-9)

**Goal**: Launch public beta with production-grade infrastructure

**Technical Deliverables**:
- [ ] Deploy production environment on AWS/GCP with auto-scaling
- [ ] Set up custom domain with SSL (app.mantis.studio)
- [ ] Configure CDN (CloudFront or Cloudflare) for static assets
- [ ] Implement monitoring (Sentry, DataDog) and alerting
- [ ] Complete GDPR compliance audit
- [ ] Load testing (1000 concurrent users)

**User-Facing Deliverables**:
- [ ] Public landing page with pricing tiers
- [ ] Stripe integration for Pro subscriptions
- [ ] Onboarding tutorial for new users
- [ ] Help center and knowledge base
- [ ] Public beta announcement (Product Hunt, HackerNews)

**Success Metrics**:
- 2,000 total users
- $5K MRR (Monthly Recurring Revenue)
- 99.5% uptime
- 50% free → Pro conversion rate

---

### Phase 4: Collaboration & Scaling (Months 10-12)

**Goal**: Enable team workspaces and scale infrastructure for growth

**Technical Deliverables**:
- [ ] Build team workspace system (multi-member, shared billing)
- [ ] Implement real-time presence indicators (who's online)
- [ ] Add WebSocket support for live notifications
- [ ] Optimize AI service layer (response caching, model routing)
- [ ] Migrate frontend to React SPA (if required for real-time features)
- [ ] Add automated testing coverage to 80%+

**User-Facing Deliverables**:
- [ ] Team plan with member invitations
- [ ] Comment threads on chapters (async collaboration)
- [ ] Activity feed (who edited what, when)
- [ ] Advanced export options (PDF, ePub, integration with Scrivener)

**Success Metrics**:
- 5,000 total users
- $20K MRR
- 100 team workspaces
- 60% free → paid conversion rate

---

### Phase 5: Monetization & Growth (Months 13-18)

**Goal**: Achieve product-market fit and sustainable revenue growth

**Technical Deliverables**:
- [ ] Enterprise features (SSO, on-premise deployment)
- [ ] Marketplace for templates and plugins (extensibility layer)
- [ ] Advanced analytics (user behavior tracking, funnel analysis)
- [ ] Localization support (i18n for Spanish, French, German)
- [ ] Mobile app (React Native or Progressive Web App)

**User-Facing Deliverables**:
- [ ] Enterprise tier launch
- [ ] Template marketplace (community-contributed)
- [ ] Referral program (earn credits)
- [ ] Public project gallery (showcase feature)
- [ ] Annual plan with 2-month discount

**Success Metrics**:
- 20,000 total users
- $100K MRR
- 500 team workspaces
- 10 enterprise customers
- Break-even or profitability

---

## 13. Contribution Guidelines (High-Level)

### How Contributors Can Help

**Code Contributions**:
- **Backend**: FastAPI endpoints, database migrations, AI service improvements
- **Frontend**: Streamlit components, React SPA migration, CSS/UI polish
- **Infrastructure**: CI/CD enhancements, deployment automation, monitoring setup

**Non-Code Contributions**:
- **Documentation**: Guides, tutorials, API references
- **Design**: UI/UX mockups, design system evolution
- **Community**: Support in forums, bug triage, feature advocacy

**Good First Issues**:
- Add unit tests for existing services
- Improve error messages for user-facing failures
- Write migration guide from competitor tools
- Create project templates (screenplay, game narrative)

---

### Code Quality Expectations

**Coding Standards**:
- Follow PEP 8 for Python (enforced by `black` formatter)
- Type hints for all function signatures
- Docstrings for public APIs (Google style)

**Testing Requirements**:
- Unit tests for business logic (pytest)
- Integration tests for API endpoints (pytest + TestClient)
- Minimum 80% code coverage for new features

**Pull Request Process**:
1. Fork repository and create feature branch (`feature/your-feature-name`)
2. Write code + tests
3. Run linters: `black . && flake8 && mypy`
4. Submit PR with description of changes and test results
5. Address code review feedback
6. Merge after 2 approvals

---

### Documentation Expectations

**Required Documentation**:
- **API Changes**: Update OpenAPI spec and API docs
- **Database Changes**: Migration script + schema documentation
- **User-Facing Features**: Update user guides, changelog
- **Architecture Changes**: Update architecture diagrams, ADRs

**Formats**:
- Markdown for guides (stored in `docs/`)
- Inline comments for complex logic
- README for new modules

---

### Roadmap Alignment Rules

**Feature Proposals**:
- Check existing roadmap to avoid duplication
- Discuss in GitHub Discussions or Discord before building
- Align with current phase priorities (don't jump to Phase 5 features in Phase 1)

**Breaking Changes**:
- Require team discussion and approval
- Provide migration path for users
- Announce in changelog with 1-month notice

**Experimental Features**:
- Flag as `[EXPERIMENTAL]` in UI
- Collect user feedback before stabilizing
- Can be removed if low adoption

---

## Conclusion

This roadmap represents a clear path from MANTIS Studio's current state as a local writing tool to a world-class hosted AI narrative platform. The journey is ambitious but achievable with:

- **Disciplined execution** following the phased milestones
- **User-centric design** prioritizing writers' needs over technical complexity
- **Sustainable architecture** built for scale and maintainability
- **Community engagement** leveraging contributors and early adopters

**Next Steps**:

1. **For Developers**: Review Phase 1 deliverables and claim a task in GitHub Issues
2. **For Contributors**: Join Discord, introduce yourself, explore "good first issues"
3. **For Investors**: Contact team for pitch deck and financial projections
4. **For Users**: Sign up for beta waitlist at mantis.studio

*Let's build the future of AI-assisted storytelling together.*

---

**Document Version**: 1.0  
**Last Updated**: 2026-02-09  
**Maintained By**: MANTIS Studio Core Team  
**License**: MIT (code), CC BY 4.0 (documentation)
