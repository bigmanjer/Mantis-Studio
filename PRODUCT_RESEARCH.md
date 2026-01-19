# MANTIS Studio — Product & UX Research Notes

## Why this document exists
This captures a lightweight product audit, competitive scan, and a pragmatic testing checklist for MANTIS Studio. It is intended to guide UX/UI iterations and retention work without blocking engineering execution.

## Competitive landscape (high-level)
| Product | Primary strength | Retention hooks | Gaps users complain about | Opportunity for MANTIS |
| --- | --- | --- | --- | --- |
| Scrivener | Deep project organization + export | Project trees, custom templates | Steep learning curve, dated UI | Emphasize fast onboarding + AI assist without overload |
| Plottr | Visual outlining | Visual timelines, beat sheets | Limited prose writing, export friction | Seamless outline → chapter drafting, no export friction |
| Sudowrite | AI writing assistant | Frequent AI prompts + suggestions | Can feel “AI-first,” less control | Keep author control + AI only on demand |
| NovelAI | AI fiction generation | Persistent memory, story tools | UX complexity for beginners | “Beginner-safe mode” with progressive disclosure |
| Notion/Docs | Familiar docs UX | Collaboration, low friction | Not story-specific | Story-specific guardrails + auto-structure |

## NovelAI comparison (UI + workflow depth)
**What NovelAI does well**
- **Studio-first canvas**: A single writing surface with adjacent “modules” (memory, lorebook, author’s note).
- **Tight hierarchy**: Left navigation keeps projects + story tools in view without overwhelming the editor.
- **Distinctive dark theme**: Purple-blue gradients, glassy cards, bright accent for primary actions.
- **Rapid entry**: Story template selection + quick prompt fields reduce blank-page friction.
- **Memory scaffolding**: Persistent context (memory/author note) is clearly labeled and easy to edit.

**Where MANTIS differs today**
- **Dashboard-first flow**: Powerful, but the home screen can feel like a control panel vs. a focused studio.
- **Tool density**: Features are spread across sections (outline/world/chapters) instead of adjacent modules.
- **Visual hierarchy**: Green accent and card-heavy layout reads as a productivity tool vs. a creative studio.

**Alignment targets for a “NovelAI-close” experience**
1. **Studio-first layout**
   - Emphasize the writing surface and reduce top-level dashboard noise.
   - Keep quick modules (outline/world bible/chapters) in a tight cluster.
2. **Memory modules up front**
   - Display author’s note, style note, and summary cards near the editor entry point.
3. **Dark, luminous theme**
   - Shift to purple-blue accents, glassy cards, and subtle glow for primary actions.
4. **Frictionless start**
   - Add a short “create story” workflow with template-like starter fields.
5. **Narrative flow controls**
   - Bring rewrite, style presets, and AI guidance closer to the editor.

## NovelAI deep-dive audit checklist (use during live review)
> Note: This checklist is meant for a hands-on audit. Capture screenshots and timings when you have access.

**Entry + onboarding**
- How quickly can a new user start a blank story vs. template?
- What fields are required before the first generation?
- Where does the UI explain “memory” vs. “lorebook” concepts?

**Writer workspace**
- Editor width and focus: is the canvas centered or full-width?
- Context modules placement: are memory/lore blocks adjacent to the editor?
- Generation controls: are settings visible without leaving the editor?

**Story memory systems**
- Are “author’s note” and “style” notes separate?
- How is memory scope explained (global vs. story)?
- Does the UI show what context will be injected into the prompt?

**Navigation + hierarchy**
- How many clicks to reach: editor, lorebook, settings, export?
- Does navigation emphasize “continue writing” over tooling?

**Visual system**
- Accent color use for primary action
- Card treatment (glass, borders, subtle glow)
- Typography hierarchy between editor, labels, and metadata

## MANTIS enhancement ideas (NovelAI-inspired, non-derivative)
1. **Context stack panel**
   - Show “Memory / Author Note / Style Guide / Outline” as editable cards with visibility toggles.
2. **Focus-first editor**
   - Offer a “studio mode” that reduces dashboard cards and brings the chapter editor forward.
3. **Prompt preview**
   - Add a “preview context” drawer that shows the exact AI prompt blocks before running.
4. **Quick-start story setup**
   - Provide an optional 3-step starter: setting, protagonist, tone.
5. **Continuity radar**
   - Surface recent coherence issues as a compact badge near the editor.

## What users consistently value (patterns)
1. **Time-to-first-value**: First session must result in something tangible (outline or first chapter). 
2. **Clarity of next step**: Clear “what should I do now?” reduces drop-off. 
3. **Progress visibility**: Visible momentum (word counts, streaks, sessions) improves return rate. 
4. **Low cognitive load**: Minimal UI noise; hide advanced controls until needed. 
5. **Trust and control**: Users want to know what the AI will do before it runs.
6. **Reliability**: Autosave, backups, and export confidence drive long-term retention.

## Observations about current MANTIS Studio
- Strong “all-in-one” feature set (outline, chapters, world bible, export). 
- UI can feel dense for new writers; onboarding only partially directs flow. 
- Default entry points are mostly project creation or import; there is no explicit “guided first session.”
- Retention signals are present but can be made more prominent and actionable.

## UX gaps to address next
1. **Guided first session**
   - Add a 3-step onboarding checklist on the home screen.
   - Provide explicit “Start here” button (outline wizard or first chapter).
2. **Focus mode**
   - Provide a distraction-free writing mode with a simple timer.
3. **Project health**
   - Show word count trend and chapter completion percent.
4. **AI transparency**
   - Add AI action previews and “undo” history per feature.

## Retention mechanics to implement
- Daily goal & streaks.
- Quick actions for last project.
- One-click “continue writing” resume.
- Weekly summary email (optional) with word count delta and chapter progress.

## Suggested KPIs (local instrumentation)
- First session conversion: % of users who create a project and write >200 words.
- Week-1 retention: % returning within 7 days.
- Feature activation: % who use outline or world bible in first 3 sessions.

## QA + test checklist (manual)
> These checks map to core user paths. Run before releases.

### Account & session
- Sign in, create account, invalid password policy.
- Guest flow, guest project saved, reopen app.
- Sign out, session reset.

### Project lifecycle
- Create project with title/genre present or missing.
- Import a .txt and .md with/without chapter headers.
- Load, delete, and recover projects.
- Backup creation and restore.

### Outline
- Manual edit, save, auto-entity scan.
- Generate outline; regenerate after edits.
- Reverse outline to confirm behavior.

### Chapters
- Add, delete, reorder (if supported), write content.
- AI auto-write, rewrite presets, revision history restore.

### World Bible
- Add, edit, delete entities.
- Entity scan from text, confirm merge logic.
- Search and category filters.

### Export
- Export markdown and confirm includes outline, world bible, chapters.

### Settings + AI
- Save Groq/OpenAI keys, refresh models, test model.
- Toggle auto-save and verify.

## Implementation plan (phased)
1. **Retention & guidance (now)**: onboarding checklist, clearer CTAs, progress cards.
2. **Focus & flow**: full-screen writing, session timer, daily goal prompt.
3. **Trust & control**: AI previews, undo history, confirmations.
4. **Instrumentation**: privacy-friendly local analytics + optional export.

## Product plan & enhancement roadmap (internal)
**Vision & objective**
- Transform Mantis Studio into a Narrative Operating System that surpasses NovelAI.

**Key features to add & enhance**
- **Long-form narrative**
  - Multi-chapter editor
  - Revision history
  - World Bible integration
- **Story & genre modules**
  - Genre presets
  - Outline & character builders
  - Canon consistency checks
- **Writer’s toolbox**
  - Rewrite & expand
  - Tone & style control
  - Entity extraction

**Development phases**
- **Phase 1: Stability & foundations**
  - State management
  - Save/load projects
  - Session fixes
- **Phase 2: Achieve NovelAI parity**
  - World Bible system
  - Generation history
  - Genre presets
- **Phase 3: Competitive advantage**
  - Advanced toolbox
  - Canon validation
  - Image generation
- **Phase 4: SaaS & monetization**
  - User accounts
  - Premium tiers
  - Analytics

**Success metrics**
- User engagement & retention
- Story quality & consistency
- Revenue growth

**Goal**
- Elevate Mantis Studio to be the best-in-class writing platform with unmatched creative and editing power.

---
If you want, I can turn this into an in-app “Product Settings” section and a release checklist.
