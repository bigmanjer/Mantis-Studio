# Mantis Studio Documentation

Welcome to the Mantis Studio documentation! This directory contains all project documentation organized by topic.

## 📖 Getting Started

New to Mantis Studio? Start here:

- **[Getting Started Guide](guides/GETTING_STARTED.md)** - Installation, setup, and your first project
- **[README (Main)](../README.md)** - Project overview and high-level features

## 📚 User Guides

Step-by-step guides for users and developers:

| Guide | Description |
|-------|-------------|
| **[Getting Started](guides/GETTING_STARTED.md)** | Complete installation and onboarding for new users |
| **[Using Custom Agent](guides/USING_CUSTOM_AGENT.md)** | How to use the GitHub Copilot mantis-engineer agent |
| **[Agent Quick Reference](guides/AGENT_QUICK_REFERENCE.md)** | One-page quick reference for the custom agent |
| **[Debugging Guide](guides/DEBUGGING.md)** | Comprehensive troubleshooting and debug mode guide |
| **[Contributing Guide](guides/CONTRIBUTING.md)** | Development setup and contribution workflow |
| **[Testing Guide](guides/testing.md)** | Complete testing strategy, best practices, and how-to |
| **[Maintenance Guide](guides/MAINTENANCE_GUIDE.md)** | Best practices for ongoing maintenance |
| **[Dashboard Components Guide](guides/DASHBOARD_COMPONENTS_GUIDE.md)** | Developer reference for dashboard components |

## 🏗️ Architecture & Technical

Deep dives into the system architecture and technical decisions:

| Document | Description |
|----------|-------------|
| **[Architecture](architecture/architecture.md)** | System design and component overview |
| **[Stabilization Implementation Guide](architecture/STABILIZATION_IMPLEMENTATION_GUIDE.md)** | Complete guide to stabilization refactoring, patterns, and usage |
| **[App Structure](../app/README.md)** | Detailed app directory structure and design principles |
| **[Detailed Audit Report](DETAILED_AUDIT_REPORT.md)** | Comprehensive code audit from 2024 with 2026 follow-up |

## 🎨 Design

UI/UX design documentation:

| Document | Description |
|----------|-------------|
| **[Design System](design/DESIGN_SYSTEM.md)** | UI components, design tokens, and style guide |
| **[Dashboard Redesign](DASHBOARD_REDESIGN.md)** | Dashboard UI improvements and redesign documentation |

## 📋 Planning & Roadmap

Project planning and future direction:

| Document | Description |
|----------|-------------|
| **[Technical Product Roadmap](planning/ROADMAP.md)** | Technical implementation roadmap and engineering milestones |
| **[Business Strategy Roadmap](planning/BUSINESS_STRATEGY_ROADMAP.md)** | Market positioning, business strategy, and go-to-market approach |
| **[Competitive Analysis](planning/COMPETITIVE_ANALYSIS.md)** | Market positioning and feature comparison |

## 🔧 Runbooks

Operational procedures and testing:

| Document | Description |
|----------|-------------|
| **[Smoke Test](runbooks/SMOKE_TEST.md)** | QA smoke testing procedures |

## 📜 Audit & Quality

Code quality, security, and audit documentation:

| Document | Description |
|----------|-------------|
| **[Detailed Audit Report](DETAILED_AUDIT_REPORT.md)** | Complete code audit from 2024 with 2026 follow-up and production readiness assessment |
| **[QA Audit Report](architecture/QA_AUDIT_REPORT.md)** | QA-focused audit findings |

## 📦 Releases & Issue Resolutions

Release documentation and specific issue resolutions:

| Document | Description |
|----------|-------------|
| **[Releases Index](releases/README.md)** | Index of all release notes and issue resolutions |
| **[2026-02-18 Project Creation Resolution](releases/2026-02-18_PROJECT_CREATION_RESOLUTION.md)** | Resolution for project creation issues |

## 📜 Other

| Document | Description |
|----------|-------------|
| **[Changelog](CHANGELOG.md)** | Version history and release notes |

## 🔗 Quick Links

### For New Users
1. [Getting Started Guide](guides/GETTING_STARTED.md) - Start here!
2. [Main README](../README.md) - What is Mantis Studio?
3. [Debugging Guide](guides/DEBUGGING.md) - Having issues?

### For Contributors
1. [Contributing Guide](guides/CONTRIBUTING.md) - How to contribute
2. [Testing Guide](guides/testing.md) - Writing and running tests
3. [Architecture](architecture/architecture.md) - Understanding the codebase

### For GitHub Copilot Users
1. [Using Custom Agent](guides/USING_CUSTOM_AGENT.md) - Full guide
2. [Agent Quick Reference](guides/AGENT_QUICK_REFERENCE.md) - Quick start

## 📂 Documentation Structure

```
docs/
├── README.md                              # This file - navigation hub
├── CHANGELOG.md                           # Version history
├── DETAILED_AUDIT_REPORT.md               # Full technical audit report (2024 + 2026)
├── DASHBOARD_REDESIGN.md                  # Dashboard redesign documentation
│
├── guides/                                # User-facing guides
│   ├── GETTING_STARTED.md                 # Installation & first project
│   ├── USING_CUSTOM_AGENT.md              # GitHub Copilot agent guide
│   ├── AGENT_QUICK_REFERENCE.md           # Agent quick reference
│   ├── DEBUGGING.md                       # Troubleshooting guide
│   ├── CONTRIBUTING.md                    # Development setup
│   ├── MAINTENANCE_GUIDE.md               # Maintenance best practices
│   ├── DASHBOARD_COMPONENTS_GUIDE.md      # Dashboard components reference
│   ├── testing.md                         # Testing guide (consolidated)
│   └── index.md                           # Guides index
│
├── architecture/                          # Technical deep dives
│   ├── architecture.md                    # System design
│   ├── QA_AUDIT_REPORT.md                 # QA audit findings
│   └── STABILIZATION_IMPLEMENTATION_GUIDE.md  # Complete stabilization guide
│
├── design/                                # UI/UX design
│   └── DESIGN_SYSTEM.md                   # Design system and tokens
│
├── planning/                              # Project planning
│   ├── ROADMAP.md                         # Technical product roadmap
│   ├── BUSINESS_STRATEGY_ROADMAP.md       # Business strategy and market positioning
│   └── COMPETITIVE_ANALYSIS.md            # Market positioning
│
├── releases/                              # Release notes & resolutions
│   ├── README.md                          # Releases index
│   └── 2026-02-18_PROJECT_CREATION_RESOLUTION.md
│
└── runbooks/                              # Operational procedures
    └── SMOKE_TEST.md                      # QA testing
```

## 🤝 Contributing to Documentation

Found an issue or want to improve the docs?

1. **For typos or small fixes**: Open a PR directly
2. **For new guides or major changes**: Open an issue first to discuss
3. **Follow the structure**: Keep docs in the appropriate subdirectory
4. **Update this index**: When adding new docs, update this README

### Documentation Style Guide

- Use clear, concise language
- Include code examples where helpful
- Add links to related documentation
- Use headers and sections for easy navigation
- Include a table of contents for long documents

---

**Need help?** Open an [issue on GitHub](https://github.com/bigmanjer/Mantis-Studio/issues) or ask `@mantis-engineer` in GitHub Copilot Chat!

---

*Last Updated: 2026-02-18*
