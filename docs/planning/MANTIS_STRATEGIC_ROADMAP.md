# MANTIS Strategic Roadmap

## 1) Executive Summary

### What MANTIS Is
MANTIS (Modular AI Narrative Text Intelligence System) is an AI-native narrative intelligence platform currently delivered as a Streamlit-based application for long-form writing, worldbuilding, story development, and editorial iteration. It combines modular writing tools, AI-assisted generation, and narrative workflows into a single authoring environment.

### Long-Term Vision
MANTIS will become the operating system for narrative production: a secure, collaborative SaaS platform where individual creators, studios, and content teams can plan, generate, refine, and ship high-quality narrative assets across books, games, film/TV, education, and branded storytelling.

### Transformation Goal
Transform MANTIS from a single-instance, Streamlit-heavy AI tool into a multi-tenant, production-grade SaaS product with:
- Role-based collaboration
- API-first architecture
- Metered monetization
- Enterprise controls
- Scalable inference orchestration
- Repeatable growth loops and conversion funnels

### Why It Matters in the AI Market
The current AI writing market is saturated with generic chat interfaces and broad marketing-copy tools. Narrative creation requires continuity, structure, lore consistency, iterative drafting, and editorial control over long time horizons. MANTIS addresses this gap by focusing on workflow depth rather than prompt novelty. This positions it in a durable segment where switching costs can be driven by project context, team processes, and accumulated narrative assets.

---

## 2) Product Positioning Strategy

### Core Category
AI Narrative Workflow Platform (not just an AI writing assistant).

### New Category MANTIS Could Create
Narrative Intelligence Operating System (NIOS): a modular, project-centric AI layer for story development and production pipelines.

### Core Differentiator
MANTIS is workflow-first and continuity-aware: it organizes creative work into structured modules (planning, drafting, revision, continuity, and export) instead of isolated prompt-response sessions.

### Messaging Pillars
1. **Narrative Continuity at Scale** — Keep voice, lore, and structure consistent across long projects.
2. **Modular Creative Control** — Use specialized tools for each writing stage instead of one monolithic chat.
3. **Production-Ready Collaboration** — Move from solo ideation to team delivery in a shared workspace.
4. **Cost-Visible AI Usage** — Transparent token economics and controllable model routing.
5. **Creator-Owned Output** — Clear ownership, exportability, and portability of narrative assets.

### Brand Personality
- Precise, creative, pragmatic
- Author-friendly, not hype-driven
- Professional but inspiring
- Trustworthy with IP-sensitive workflows

### One-Sentence Positioning Statement
MANTIS is the AI narrative workflow platform that helps creators and teams build long-form stories with continuity, structure, and production-grade collaboration.

### 10-Second Elevator Pitch
MANTIS helps writers and narrative teams create better long-form stories with modular AI workflows, not just chat prompts.

### 30-Second Pitch
Most AI writing tools are chatbots optimized for short outputs. MANTIS is different: it is a modular narrative system designed for real story production—planning, drafting, revision, and continuity in one workflow. It gives creators AI acceleration without losing creative control, and it gives teams the structure needed to ship cohesive narrative work.

### 2-Minute Founder Pitch
Narrative creation is one of the hardest AI-assisted workflows because quality depends on continuity over thousands of decisions: character voice, world rules, pacing, and revision history. Current tools treat writing like single-turn prompting, which breaks down at project scale.

MANTIS solves this by structuring AI assistance into purpose-built modules across the writing lifecycle. Instead of asking users to engineer perfect prompts from scratch each time, MANTIS provides workflow-native tooling for ideation, outlining, scene development, continuity checks, style alignment, and editorial refinement. The output is not just text—it is a maintainable narrative system.

From a business perspective, this creates stronger retention than generic chat products. As users build projects in MANTIS, they accumulate reusable context, assets, and team workflows that increase platform value over time. Our roadmap moves from a Streamlit application to a multi-tenant SaaS with role-based collaboration, usage-based monetization, and enterprise controls. We are targeting independent creators first, then studios and institutions that need scalable narrative pipelines.

### Differentiation vs Major Alternatives
- **ChatGPT**: Broad general assistant; MANTIS is narrative workflow-specific with project scaffolding and continuity operations.
- **Claude**: Strong long-context model interaction; MANTIS adds modular production workflows, team collaboration, and structured narrative artifacts.
- **Jasper**: Marketing-centric content engine; MANTIS is built for long-form narrative and story systems, not conversion copy.
- **Copy.ai**: Template-driven short-form generation; MANTIS emphasizes deep story lifecycle management.
- **Notion AI**: Embedded productivity AI; MANTIS is purpose-built for narrative creation pipelines and AI orchestration.

---

## 3) Conversion-Optimized Landing Page Structure

### Hero Messaging Strategy
- **Headline**: “Build Better Stories with AI-Native Narrative Workflows.”
- **Subheadline**: “From outline to final draft, MANTIS keeps your story coherent, your process modular, and your team aligned.”
- **Primary CTA**: “Start Free”
- **Secondary CTA**: “Watch 2-Minute Demo”
- **Proof Strip**: model partners, creator testimonials, usage counts (if validated), and privacy statement.

### Problem Section Positioning
Frame three pains:
1. Generic AI chat loses long-form continuity.
2. Narrative workflows are fragmented across too many tools.
3. Team collaboration breaks consistency and slows delivery.

### Solution Explanation
Present MANTIS as a guided modular system:
- Plan story architecture
- Generate with controlled context
- Audit continuity and style
- Revise with targeted editorial tools
- Export production-ready narrative assets

### Core Capabilities Breakdown
Use “jobs to be done” cards:
- Story Planning & Outlining
- Character and Lore Management
- Scene Drafting & Expansion
- Continuity & Consistency Checks
- Revision & Tone Alignment
- Team Review, Commenting, and Versioning

### Comparison Strategy
Use a concise comparison table with credibility-first claims:
- Column set: MANTIS vs Generic Chat vs Marketing AI Tools
- Rows: Long-form continuity, modular workflow, collaboration, project memory, token controls, export readiness
- Avoid unverifiable “best” claims.

### Use Case Targeting
Segmented blocks with persona-specific copy:
- Novelists and indie authors
- Game narrative teams
- Screenwriting and production teams
- Educational writing programs
- Branded storytelling teams

### CTA Hierarchy
1. **Primary**: Start Free
2. **Secondary**: Book Live Demo (for team/enterprise)
3. **Tertiary**: Explore Use Cases / View Documentation

### Trust-Building Elements
- Security and privacy policy summary
- Data ownership statement
- Transparent pricing teaser (“No hidden AI overages”)
- Roadmap visibility (“Built in public milestones”)
- Testimonials/case snippets with measurable outcomes

---

## 4) Product Architecture Roadmap

### Target Evolution
- **Current**: Streamlit-heavy monolith
- **Target**: Multi-tenant SaaS with decoupled frontend, API backend, AI orchestration services, and async task infrastructure

### Recommended Backend Stack
- **API Framework**: FastAPI (Python) for consistency with existing ecosystem
- **Service Runtime**: Containerized microservices (Docker)
- **Task Queue**: Celery or Dramatiq with Redis/RabbitMQ
- **Inference Orchestration**: Internal AI Gateway service for model routing/fallback
- **Observability**: OpenTelemetry + Prometheus + Grafana

### Recommended Frontend Stack
- **Primary**: Next.js (React, TypeScript)
- **UI System**: Tailwind + component library (shadcn/ui or equivalent)
- **State/Data**: React Query + lightweight global store
- **Auth UX**: Token/session handling via secure HTTP-only cookies

### Modular AI Service Layer Design
- `prompt-service`: Template registry and prompt versioning
- `context-service`: Retrieval, context assembly, memory windows
- `generation-service`: Model orchestration (OpenAI/Anthropic/local)
- `evaluation-service`: Quality checks, continuity scoring, guardrails
- `cost-service`: Token accounting and budget enforcement

### API Layer
- Versioned REST API (`/api/v1`) + optional GraphQL read endpoints
- WebSocket/SSE for streaming generation
- Public API keys for approved external integrations
- Rate limits by plan and endpoint criticality

### Authentication Strategy
- Managed auth (Auth0/Clerk/Supabase Auth) or custom OAuth/OIDC
- Email/password + OAuth providers
- RBAC roles: owner, editor, reviewer, viewer
- SSO/SAML on enterprise tier
- Audit logs for sensitive workspace actions

### Token Usage Management
- Per-workspace token budgets
- Per-request hard limits + soft warnings
- Model routing policies by plan (economy/balanced/premium)
- User-facing usage dashboards (daily/monthly spend)

### Database Structure
- **Primary DB**: PostgreSQL
- Multi-tenant patterns:
  - Shared DB, tenant-scoped tables (early stage)
  - Option to isolate high-value enterprise tenants later
- Core entities:
  - organizations, users, memberships
  - projects, narrative_assets, revisions
  - prompts, generations, evaluations
  - usage_events, invoices, subscriptions

### Caching Layer
- Redis for:
  - Session caches
  - Response caching for deterministic requests
  - Hot context cache (project metadata)
  - Rate limit counters

### Async Job Handling
- Queue long-running operations:
  - Multi-scene generation
  - Batch continuity audits
  - Export compilation
  - Embedding/index refresh
- Job statuses exposed in UI with retry/cancel controls

### Cost Optimization
- Dynamic model routing based on task class
- Prompt compression and context truncation heuristics
- Cache hit strategies for repeat operations
- Budget alerts + auto-downgrade to cheaper models under thresholds

### Deployment Architecture
- Frontend: Vercel/Cloudflare Pages
- Backend/services: AWS ECS/Fargate or Kubernetes (later)
- DB: Managed PostgreSQL (RDS/Neon/Supabase)
- Cache/queue: Managed Redis
- File storage: S3-compatible object store
- CDN for static assets and export delivery

### Environment Separation
- `dev`: local containers + seeded demo data
- `staging`: production-like environment with test billing
- `prod`: hardened infrastructure, strict monitoring, incident response
- CI/CD: branch previews, automated tests, gated deployment approvals

### Example Folder Structure
```text
mantis/
├── apps/
│   ├── web/                      # Next.js frontend
│   └── admin/                    # Internal ops/admin portal
├── services/
│   ├── api-gateway/              # FastAPI public API
│   ├── auth-service/
│   ├── generation-service/
│   ├── context-service/
│   ├── evaluation-service/
│   ├── billing-service/
│   └── worker-service/           # Async job consumers
├── packages/
│   ├── ui/                       # Shared UI components
│   ├── types/                    # Shared TS/Pydantic contracts
│   ├── prompts/                  # Prompt templates + versions
│   └── sdk/                      # Public API SDK
├── infra/
│   ├── terraform/
│   ├── k8s/
│   └── monitoring/
├── docs/
│   ├── architecture/
│   ├── product/
│   └── runbooks/
└── .github/
    └── workflows/
```

---

## 5) UX & Workflow Redesign Plan

### Product Direction
Reframe MANTIS as a **Guided Modular Intelligence System** with explicit steps, role-aware interfaces, and progressive controls.

### First-Time Onboarding Flow
1. Sign up and choose role (solo creator, team lead, educator)
2. Select project type (novel, game narrative, screenplay, course)
3. Define goals (tone, output length, delivery cadence)
4. Import or start from template
5. Run first guided workflow (“Create Story Blueprint”)
6. View success state and next recommended action

### Step-Based Workflow Model
- Step 1: Ideation & premise
- Step 2: Structure & outline
- Step 3: Character/lore foundations
- Step 4: Drafting by scene/chapter
- Step 5: Continuity and style audit
- Step 6: Revision and export

### Feature Grouping
- **Create**: ideation, drafting, expansion
- **Organize**: lore, characters, timeline, assets
- **Refine**: continuity checks, style alignment, editorial rewrite
- **Collaborate**: comments, approvals, version compare
- **Publish**: export, API handoff, package generation

### Progressive Disclosure
- Free users: guided defaults, minimal configuration
- Pro users: advanced controls, model selection, parameter tuning
- Team/Enterprise: workflow templates, permissions, policy controls

### Primary Action Path
“Create/Advance Next Narrative Milestone” as the single dominant CTA on dashboard.

### Dashboard Redesign
- Left navigation by workflow stage
- Central “Project Health” panel (progress, continuity status, pending reviews)
- Right rail “Next Best Actions” and token budget indicator
- Activity stream for collaborative updates

### Reduced Cognitive Load Strategy
- Limit visible controls per stage
- Use task presets instead of exposing raw prompt fields initially
- Offer contextual helper text and one-click examples
- Surface only relevant modules based on project maturity

### Pro vs Free Feature Visibility
- Always show locked advanced modules with clear value statements
- Provide in-context upgrade prompts tied to user intent
- Avoid aggressive modal interruptions; use milestone-triggered nudges

### Mobile Responsiveness Considerations
- Mobile first for review/commenting and lightweight generation
- Desktop optimized for deep drafting and multi-panel editing
- Responsive layout priority:
  1. Project status + quick actions
  2. Inline notes/review
  3. Compact generation controls

---

## 6) Monetization & Pricing Strategy

### Pricing Principles
- Predictable base subscription + transparent usage controls
- Strong free-to-paid value step
- Margin-aware model routing and overage policies

### Tier Design

#### Free Tier
- 1 workspace, 2 active projects
- Monthly token quota (low)
- Standard model routing only
- Core modules: ideation, outline, basic drafting
- Watermarked/limited export options

#### Pro Tier
- 1 user, expanded projects
- Higher token quota
- Access to premium models in capped mode
- Continuity audit, style controls, richer exports
- Priority support and early feature access

#### Team Tier
- 3–25 seats
- Shared workspace and collaboration controls
- Pooled token allocation + admin budgets
- Role permissions, approval workflows, version history
- Team analytics and productivity dashboards

#### Enterprise Tier
- Custom seats and SLAs
- SSO/SAML, advanced compliance controls
- Dedicated onboarding and success management
- Optional private model routing / VPC deployment model
- Contracted pricing with minimum annual commitment

### Usage Limits and Cost Control
- Quotas reset monthly
- Hard stop at 100% for Free unless upgraded
- Soft overage threshold for paid plans (e.g., +20%)
- Auto-route to lower-cost models when user opts for “cost saver” mode

### Feature Gating Logic
- Gate by value complexity, not arbitrary friction:
  - Basic generation = accessible
  - Continuity QA, team controls, advanced exports = paid
- Enterprise-only for governance-heavy features

### Overage Handling
- Credit packs for Pro/Team
- Automatic overage billing with opt-out cap
- Real-time warning banners at 70/90/100% quota

### API Monetization Possibility
- Metered API access for external narrative tools
- Developer tier with API keys, usage analytics, and webhooks
- Premium endpoints (continuity scoring, narrative diagnostics)

### Future Marketplace / Plugin Potential
- Template marketplace (genre packs, workflow templates)
- Expert-crafted narrative modules
- Revenue split model with creators/integrators

### Margin Realism Guardrails
- Target gross margin bands:
  - Pro: 70%+
  - Team: 75%+
  - Enterprise: 80%+ (with negotiated usage bands)
- Enforce per-tier model mix and context limits to protect unit economics

---

## 7) Go-To-Market & Funnel Strategy

### Ideal Customer Profiles (ICPs)
1. **Indie Narrative Creator**: solo author needing continuity and speed
2. **Small Narrative Studio**: game/interactive story teams needing collaboration
3. **Creative Education Program**: institutions teaching writing workflows
4. **Content Innovation Teams**: brands producing serialized narrative content

### Traffic Acquisition Channels
- SEO around long-form writing workflows and narrative AI
- YouTube demos and teardown-style product videos
- Creator partnerships and affiliate programs
- Reddit/Discord/X communities in writing and gamedev
- Product Hunt and targeted launch cycles

### Content Strategy
- Pillar content: narrative workflow playbooks
- Comparison pages: “MANTIS vs generic AI chat for long-form projects”
- Case-study storytelling with measurable improvements
- Weekly practical tutorials and project templates

### Lead Magnet Strategy
- “Narrative Consistency Toolkit” downloadable framework
- Free genre-specific story blueprint templates
- Email-gated interactive continuity checklist

### Onboarding Activation Sequence
- Day 0: Welcome + guided first project
- Day 1: Prompt to complete narrative blueprint
- Day 3: Introduce continuity audit with sample report
- Day 7: Showcase upgrade value tied to usage behavior

### Email Nurture Sequence Outline
- Email 1: Quick start and first milestone
- Email 2: Workflow best practices and template recommendation
- Email 3: Case study + measurable creator outcomes
- Email 4: Feature spotlight (continuity intelligence)
- Email 5: Upgrade offer with usage-based trigger

### Conversion Triggers
- Hitting project limit
- Attempting premium continuity checks
- Inviting collaborators (team signal)
- Reaching 70% token quota with high weekly activity

### Retention Loops
- Weekly “Project Progress Digest” email
- Automated revision reminders tied to project goals
- “Continuity score improvements” feedback loop
- Template recommendations based on genre and behavior

### Referral Strategy
- Double-sided referral credits
- Team referral bounty for paid seat conversions
- Showcase referral leaderboard for community creators

### Community-Building Approach
- Creator council for roadmap input
- Monthly challenge prompts with public showcases
- Community template exchange
- Office hours and workflow clinics

---

## 8) Competitive Moat Strategy

### Short-Term Advantages
- Narrative-focused positioning in a crowded generic AI landscape
- Faster user value through guided workflows vs blank chat interfaces
- Domain-specific modules that reduce prompt engineering burden

### Long-Term Defensibility
- Compounding project data structure (assets, revisions, continuity metadata)
- Deep workflow integration into team processes
- Ecosystem lock-in through templates, plugins, and APIs

### Feature-Based Moat
- Continuity intelligence tools
- Modular stage-aware generation pipelines
- Team editorial and approval workflows

### Data-Based Moat
- Opt-in anonymized usage telemetry for workflow optimization
- Proprietary quality signals for narrative coherence and revision effectiveness
- Continuous model-routing optimization based on historical performance/cost

### Workflow-Based Moat
- Embedded “story production system” that mirrors professional pipelines
- Reusable project archetypes and template libraries
- Role-based handoff flows from creator to editor to producer

### Brand Positioning Moat
- Own “Narrative Intelligence” category language
- Build trust with creator-first IP and transparency commitments
- Establish authority through published methodology, not hype claims

---

## 9) Development Phase Roadmap

### Phase 1 – Stabilization
**Objectives**
- Improve reliability and baseline performance
- Harden core generation and project persistence flows

**Deliverables**
- Error tracking and observability baseline
- Refactored critical path modules
- Regression test coverage for core user journeys

**Risks**
- Technical debt in legacy Streamlit logic
- Incomplete instrumentation delaying diagnosis

**Success Metrics**
- Crash-free session rate > 99%
- Core action latency reduced by 30%
- Support tickets per active user reduced by 25%

### Phase 2 – UX Overhaul
**Objectives**
- Shift from feature-dense UI to guided workflow UX
- Improve first-session activation and clarity

**Deliverables**
- New IA/navigation model
- Onboarding wizard + milestone progress system
- Dashboard with next-best-action patterns

**Risks**
- Existing users may resist UX changes
- Scope creep in redesign iterations

**Success Metrics**
- Activation (first project completed) +40%
- Day-7 retention +20%
- Time-to-first-value < 15 minutes

### Phase 3 – Architecture Refactor
**Objectives**
- Decouple frontend/backend and introduce service boundaries
- Prepare multi-tenant SaaS foundations

**Deliverables**
- FastAPI gateway
- Worker queue + async jobs
- PostgreSQL multi-tenant schema + Redis cache
- Next.js frontend baseline

**Risks**
- Migration complexity from monolith
- Integration defects between services

**Success Metrics**
- 95% API success rate under load target
- Async task throughput meeting SLA
- Deployment frequency doubled with lower failure rates

### Phase 4 – Monetization Integration
**Objectives**
- Introduce paid tiers and usage metering
- Protect margins via model routing controls

**Deliverables**
- Subscription billing (Stripe or equivalent)
- Usage dashboard and budget alerts
- Feature gating and overage framework

**Risks**
- Pricing mismatch with perceived value
- Unexpected inference cost spikes

**Success Metrics**
- Free-to-paid conversion >= 4–7% initial band
- Gross margin target met per tier
- Churn below early-stage benchmark threshold

### Phase 5 – Public Launch
**Objectives**
- Execute broad GTM release with reliable onboarding
- Validate acquisition channels and messaging

**Deliverables**
- Launch campaign assets
- SEO pages and comparison content
- Referral and creator partnership programs

**Risks**
- Traffic spikes impacting stability
- Messaging not resonating with ICP segments

**Success Metrics**
- Launch month signup target achieved
- Activation and conversion benchmarks met
- CAC payback trend within target range

### Phase 6 – SaaS Scale
**Objectives**
- Expand team/enterprise motion
- Build defensible ecosystem and operational maturity

**Deliverables**
- Enterprise security controls and SSO
- API and plugin ecosystem foundations
- Customer success and lifecycle automation

**Risks**
- Sales cycle complexity for enterprise
- Operational burden from rapid feature expansion

**Success Metrics**
- Net revenue retention > 100%
- Enterprise pipeline growth QoQ
- Expansion revenue from existing accounts

---

## 10) 12-Month Strategic Timeline

### Q1 (Months 1–3): Foundation and Product Clarity
- Stabilization sprint and instrumentation rollout
- UX research and onboarding redesign prototypes
- Pricing experiments with controlled cohorts
- Initial content engine launch (SEO + educational assets)

### Q2 (Months 4–6): Core Rebuild and Beta SaaS Readiness
- Launch decoupled frontend/backend beta
- Introduce async generation jobs and usage metering
- Ship Free + Pro plans in private beta
- Begin creator partnership pilot and referral framework

### Q3 (Months 7–9): Monetized Public Launch
- Public launch with conversion-optimized website
- Team tier launch and collaborative workflows
- Lifecycle messaging and retention automation
- Infrastructure hardening for scale + uptime targets

### Q4 (Months 10–12): Scale and Enterprise Entry
- Enterprise controls (SSO, audit logs, governance)
- API access and integration pilots
- Template/plugin marketplace alpha
- Revenue optimization and internationalization planning

---

## 11) Investor Readiness Section

### Problem Statement
Long-form narrative creation is poorly served by generic AI chat products. Teams need continuity, structured workflows, and production-grade collaboration, none of which are solved reliably by prompt-first interfaces.

### Market Opportunity Framing
MANTIS sits at the intersection of:
- AI productivity software
- Creator economy tooling
- Narrative production workflows for media, games, and education
This creates a wedge into a broad software market with expansion from individual creators to team and enterprise contracts.

### Why Now
- AI model capabilities now support higher-quality narrative generation
- Creators and teams are actively adopting AI but dissatisfied with fragmented tools
- SaaS infrastructure, billing, and deployment stacks reduce time-to-market for specialized platforms

### Revenue Model Summary
- Subscription SaaS (Free, Pro, Team, Enterprise)
- Usage-based overages/credits
- API monetization for external integrations
- Marketplace take-rate potential for templates/plugins

### Capital Requirements (Structured Placeholder)
- **Seed Raise Target**: $X million
- **Runway Goal**: 18–24 months
- **Primary KPI Targets**:
  - Product: activation, retention, continuity feature adoption
  - Revenue: MRR growth, conversion, NRR
  - Efficiency: gross margin, CAC payback

### Use of Funds Strategy
1. **Product & Engineering (40–50%)**
   - Architecture refactor, AI orchestration, reliability, security
2. **GTM & Growth (25–35%)**
   - Content engine, partnerships, paid acquisition experiments
3. **Customer Success & Operations (10–20%)**
   - Onboarding systems, support scale, lifecycle operations
4. **Contingency & Compliance (5–10%)**
   - Legal, privacy, enterprise-readiness requirements

### Investor Narrative
MANTIS is a focused, workflow-native AI SaaS play. It avoids direct competition with general assistants by owning the narrative production layer where continuity, collaboration, and process structure create stronger retention and higher willingness to pay. The roadmap prioritizes realistic execution: reliability first, UX clarity second, architecture and monetization third, then scaled GTM and enterprise expansion.
