# MANTIS Full QA Audit Report

Date: 2026-02-18
Scope: Entire repository (`app/`, `scripts/`, `tests/`, docs for deployment consistency)

## Method & Commands Run

- `python -m pytest -q`
- `ruff check app tests`
- `python scripts/healthcheck.py`
- Custom AST scans for:
  - function/class/import inventory
  - Streamlit widget inventory and key collisions
  - circular import graph
  - oversized function detection

## 1) Static Code Analysis

### Inventory Summary

- Python files scanned in `app/`: 44
- Functions: 427
- Classes: 16
- Import statements: 206
- Streamlit widget calls (targeted set): 246

### Architecture findings

1. **Dual large UI implementations exist and have drifted**:
   - Active app shell in `app/main.py`.
   - Alternate/legacy implementation in `app/app_context.py`.
   - This creates maintenance divergence risk.

2. **Oversized functions (high complexity / high risk of hidden branch errors)**:
   - `app/main.py::_run_ui` spans ~4,500+ lines.
   - `app/app_context.py::_run_ui` spans ~2,900+ lines.
   - `render_world`, `render_chapters`, `render_home`, and `render_ai_settings` are each very large in both files.

3. **Circular import risk exists**:
   - `app.utils.navigation -> app.router -> app.utils.navigation`
   - Extended cycle via layout: `app.utils.navigation -> app.router -> app.layout.layout -> app.utils.navigation`
   - Not currently crashing due to deferred imports, but fragile and failure-prone during refactors.

4. **Lint-level structural debt is high in non-active/legacy paths** (`ruff`):
   - Undefined names, unused imports/variables, and import-order issues are concentrated in `app/app_context.py`.

## 2) Button & UI Action Trace

### Coverage summary

Detected widget usage in audited code:
- `st.button`: 152
- `st.form_submit_button`: 6
- `st.toggle`: 2
- `st.checkbox`: 14
- `st.radio`: 4
- `st.selectbox`: 13
- `st.text_input`: 33
- `st.text_area`: 22
- `st.slider`: 0

### Behavior patterns observed

- The app mostly uses **inline `if st.button(...):` handlers** with explicit state updates + `st.rerun()`.
- **No `on_click` callbacks** were found for these target widgets (all direct inline logic).
- Navigation buttons generally set `st.session_state.page` and rerun, which is consistent.

### UI-action risks

- Because handlers are inline and large, many actions mutate multiple keys before rerun, increasing stale-state coupling risk.
- In the legacy `app/app_context.py`, coherence-action buttons call `update_locked_chapters()` but that symbol is not defined there.

## 3) Session State Audit

### Good patterns

- `app/session_init.py` uses `setdefault` heavily and initializes many keys defensively.
- Fallback minimum state is applied on initialization failure.

### Risks

1. **Global mutable config mutation**:
   - Session values are written back into class-level `AppConfig` attributes each run, which can create side effects if reused across contexts/tests.

2. **State and UI tightly coupled in huge functions**:
   - Massive inline logic blocks create high risk of key drift and unguarded assumptions during edits.

3. **Legacy path inconsistent with active path**:
   - Missing helper function (`update_locked_chapters`) in `app/app_context.py` indicates state management drift between codepaths.

### Widget key collision check

- No duplicate constant widget keys found **within the same file**.
- Reused keys exist across `app/main.py` and `app/app_context.py`; this is safe only if those files are never rendered in the same runtime scope.

## 4) Rerun Loop & Recursion Detection

### Findings

- No direct recursive function definitions were detected in core UI functions.
- Very frequent `st.rerun()` use in both `app/main.py` and `app/app_context.py`.
- Most reruns are button-gated, but overall rerun density is high and makes regression/flicker bugs more likely when adding new conditional logic.

### Specific risk points

- Error fallback blocks include rerun controls; safe as implemented now, but brittle when nested inside broad `try/except` envelopes.

## 5) Error Handling Review

### Findings

- No `bare except:` found.
- Many broad `except Exception` blocks in UI and service layers.
- Several blocks intentionally suppress errors with `pass` or warnings to keep UI alive.

### Risks

- API/model probe and some config-loading flows degrade silently to empty/default outputs, which can mask operational issues for users.
- Broad exception handling around large UI blocks can hide root causes and make failures appear as no-op UX.

## 6) Performance Review

### Risks

1. **Large rerun-driven monolith rendering**:
   - Large `_run_ui` and page render functions recompute and redraw substantial UI on every rerun.

2. **Heavy state blobs likely in session state**:
   - World/coherence logs and chapter/project structures are persisted in session state; growth control is partial.

3. **Caching usage is limited to selected helpers**:
   - Some asset loading is cached, but many expensive operations are still trigger-path dependent in large handlers.

## 7) Deployment Stability Review

### Findings

1. **Healthcheck script failure**:
   - `scripts/healthcheck.py` imports `app.ui.layout`, which does not exist.

2. **Dependency drift between docs and install manifest**:
   - README claims stack includes Pillow and Supabase, but `requirements.txt` does not list them.

3. **Optional API/env usage is mostly guarded**, but broad fallback behavior can hide missing env issues until runtime features are used.

## 8) User Flow Simulation (Risk-Based)

### First-time user
- Likely successful for happy path due robust defaults.
- Risk: silent degradation when config/API setup fails; users may see empty AI/model outputs without clear remediation.

### Rapid-clicking user
- High rerun density plus inline state mutation can produce transient flicker and race-like UX (especially around create/delete/apply flows).

### Partial/empty input user
- Most flows have guards; however some actions silently no-op due broad exception swallowing, reducing clarity.

### Very large text input
- Prompt truncation safeguards exist for AI prompts, reducing API failure risk.
- Large chapter/world content may still cause sluggish reruns due monolithic render structure.

### Invalid input
- Many parsing operations have `try/except` fallbacks; app usually survives.
- Survivability is good, diagnosability is weaker.

### Switching modules mid-process
- The app is state-driven and should persist major keys.
- Biggest risk is stale/interdependent key assumptions in very large view functions.

---

## Severity Buckets

### Critical Errors (Must Fix Immediately)

1. **Undefined function call in legacy UI path**: `update_locked_chapters()` used but not defined in `app/app_context.py` coherence action path.
2. **Broken healthcheck import target** (`app.ui.layout`) causes official healthcheck to fail.

### High Risk Issues

1. Circular import chain between navigation/router/layout modules.
2. Massive monolithic UI functions causing maintainability and regression risk.
3. Broad exception handling that can mask runtime failures in UI logic.

### Medium Issues

1. Dependency/documentation mismatch (README stack vs `requirements.txt`).
2. Large number of inline button handlers with no callback abstraction/tests per action.
3. High rerun density increases flicker/regression potential.

### Minor Improvements

1. Reduce unused imports/variables and import-order debt.
2. Add explicit user-facing diagnostics where silent fallbacks occur.
3. Add lightweight telemetry for failed AI/provider calls.

### Dead Code (or likely dead/secondary path)

1. `app/app_context.py` appears intentionally non-active but remains extensive and partially inconsistent.
2. Additional helper/util modules have functions with low observable usage in static call scans (candidate for verification and cleanup).

### UX Logic Problems

1. Silent fallback behavior can look like “button did nothing.”
2. Dense action panels with rerun-based state changes can feel unstable under rapid interactions.

### State Management Problems

1. AppConfig class-level mutation from session state.
2. Legacy path state helper mismatch (`update_locked_chapters`).
3. Large cross-feature key surface increases accidental coupling risk.

### Performance Risks

1. Full rerender approach with very large functions.
2. Potential growth of session logs and chapter payloads.
3. Limited cache coverage outside specific helpers.

### Structural Risks

1. Duplicate app shells (`main.py` + `app_context.py`) diverging over time.
2. Circular imports relying on fragile lazy-import behavior.

## Stability Score

**6.2 / 10**

Rationale: strong test pass rate and defensive defaults, but reduced by structural complexity, drifted legacy path defects, circular imports, and masking exception patterns.

## Prioritized Fix Order

1. Fix hard failures:
   - `update_locked_chapters` mismatch in `app/app_context.py` (or retire path explicitly).
   - `scripts/healthcheck.py` invalid import target.
2. Decide and enforce single active UI shell:
   - Deprecate/remove or isolate `app/app_context.py` from production paths.
3. Break circular imports:
   - Extract shared navigation constants into a pure data module with no back-imports.
4. Refactor largest UI functions incrementally:
   - Split into feature modules + testable action handlers.
5. Tighten exception handling:
   - Replace broad catches in critical action paths with scoped exceptions and user-visible error messages.
6. Strengthen state contracts:
   - Central key schema + typed accessors; avoid mutating global config class from session.
7. Align dependencies and docs:
   - Reconcile README stack claims with `requirements.txt`.
8. Expand automated UI behavior tests:
   - Add per-button action tests for critical flows (project create/delete, chapter create/delete, world apply/ignore, AI settings save/test).
