# MANTIS Handbook

This is the single active documentation source for setup, workflows, testing, and maintenance.

## 1) Setup

```bash
pip install -r requirements.txt
streamlit run app/main.py
```

## 2) Core Workflow

1. Projects: create/open project metadata.
2. Outline: plan structure and beats.
3. Chapters: draft and revise chapter content.
4. World Bible: maintain canon entities and continuity.
5. Projects export panel: generate manuscript outputs from the selected project.

## 3) QA and Testing

Use the full repository audit as the main quality gate:

```bash
python scripts/full_repo_audit.py
```

Useful toolbox commands:

```bash
python scripts/toolbox.py health
python scripts/toolbox.py smoke
python scripts/toolbox.py test --target tests
python scripts/toolbox.py visual --base-url http://localhost:8501
python scripts/toolbox.py qa --with-visual
```

Visual checks require the Playwright Chromium browser. After dependency install,
run this once on the machine:

```bash
python -m playwright install chromium
```

Canonical pytest target:

```bash
python -m pytest tests -q
```

QA report output:

- `artifacts/full_repo_audit/full_repo_audit.md`
- `artifacts/full_repo_audit/full_repo_audit.json`
- `artifacts/visual_regression/summary.json`

### Tests vs Scripts

- `tests/` contains pytest assertions. These files should not perform repo
  maintenance; they prove app behavior and source contracts.
- `scripts/` contains command-line tools. These files may compile code, run
  tests, bump versions, capture screenshots, or generate reports.
- Canonical quality gate: `scripts/full_repo_audit.py`.
- Canonical command wrapper: `scripts/toolbox.py`.
- Smaller direct scripts (`healthcheck.py`, `smoke_test.py`,
  `visual_regression_pass.py`, `bump_version.py`) are compatibility entry points
  or specialized helpers. Prefer adding new commands to `toolbox.py` or
  `full_repo_audit.py` instead of creating another standalone script.

### Documentation Freshness Rule

Every user-visible routing, testing, script, navigation, theme, legal/help, or
workflow change must update the relevant active doc in the same change set:

- Root overview: `README.md`
- Operating guide: `docs/HANDBOOK.md`
- Test entry points: `tests/README.md`
- App architecture: `app/README.md`
- Legal/support copy: `legal/*.md`
- User-visible changes: `docs/CHANGELOG.md`

`scripts/full_repo_audit.py` scans active docs for known stale references, but
the rule is still human: if behavior changes, update the doc that teaches it.

## 4) Versioning

```bash
python scripts/toolbox.py bump
```

Rule:
- Every change merged into the project must bump `VERSION.txt`.
- No change is considered complete until the version is incremented and documented in `docs/CHANGELOG.md`.

## 5) Repository Conventions

- Full audit entrypoint: `scripts/full_repo_audit.py`
- Toolbox entrypoint: `scripts/toolbox.py`
- Single canonical test target: `tests`
- Legacy duplicate files were removed after consolidation.
- Keep one active workspace copy for development and remove stale snapshots and local cache artifacts (`__pycache__`, temporary Streamlit logs) during cleanup.
## 6) Troubleshooting

- If Streamlit UI is stale, hard refresh browser and rerun app.
- If visual checks fail, ensure app is running on the `--base-url` provided.
- If tests fail after state/schema changes, update the relevant suite under `tests/`.

## 7) Current Stability Defaults (March 2026)

- Sidebar visibility uses one clear control path:
  - `Hide Sidebar` when the sidebar is open
  - `Show Sidebar` when the sidebar is collapsed
- The duplicate Streamlit top-left collapse control is intentionally hidden.
- Streamlit toast/stat icons must use valid emoji characters; placeholder values such as `!` are not allowed.
- Disabled actions in light mode should render with muted readable text on light neutral surfaces.
- Light mode now uses a final enforcement layer injected after shared button CSS, so disabled buttons/alerts/sidebar chips cannot fall back to dark unreadable styles on any page.
- Sidebar toggle wording is standardized:
  - `Hide Sidebar` when visible
  - `Show Sidebar` when collapsed

- World Bible auto-apply default confidence is now `0.83` (83%); suggestions at or above the threshold apply automatically, while lower-confidence suggestions remain queued for review.
- Insights includes Coherence Check as a primary risk workflow. Each coherence issue must explain the problem, target text, suggested replacement, and whether Apply Fix will replace exact, normalized, or fuzzy-matched text. It must block instead of appending when no reliable passage is found.
- Memory pages should not render Coherence Check. Memory is for canon instructions and context only; coherence review belongs in Insights.
- Insights owns review workflows: Canon Scanner, queued World Bible suggestions, and Coherence Check live there. World Bible remains the canon entity database/editor.
- Editor workspace layout keeps chapter movement in the left rail, the manuscript editor as the widest column, and Assistant controls grouped by task modes.
- Query-param page routing now includes a loop guard to prevent repeated rerun redirects.
- Page navigation may use the one-shot `#mantis-top` anchor reset when the active page changes. Do not reintroduce repeated scroll timers, mutation observers, or global `scrollRestoration` overrides.
- Sidebar/footer IA: `Insights` appears before `Memory` in the `Intelligence` section because risk, health, canon suggestions, and coherence review are checked before editing AI memory/instructions.
- Sidebar IA: there is no separate `Export` page; export actions live in Projects so project management and manuscript download stay together.
- Light mode regression baseline is validated with `python scripts/toolbox.py visual --base-url http://localhost:8501`.
- Theme CSS now explicitly styles Streamlit metric internals (`stMetricLabel`, `stMetricValue`, `stMetricDelta`) to prevent washed-out values in Light mode.
- Dashboard checklist order is standardized to: `AI connected` -> `Project created` -> `Outline drafted` -> `Chapter drafted`.
- Dashboard KPI wording now uses `Workflow readiness` (replacing the old `System health` label).
- Light mode button enforcement now includes:
  - base/hover/primary button states
  - primary text color lock (white on green)
  - disabled button readability
  - sidebar button label color lock
  - sidebar workspace chip title/meta color lock
- Navigation/top landing hardening: the earlier scroll nonce/top-scroll routine was removed after it caused viewport jumps; keep top landing limited to the page-change anchor reset and footer `#mantis-top` links.
- Light mode consistency pass: legacy dark-hardcoded dashboard utility styles were converted to theme-token-driven colors.
- Docs policy: when behavior changes in routing/state/theme/footer, update `HANDBOOK.md` and `CHANGELOG.md` in the same change set.
