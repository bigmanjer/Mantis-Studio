# MANTIS Studio — Product & UX Research Notes

## Why this document exists
This captures a lightweight product audit, competitive scan, and a pragmatic testing checklist for MANTIS Studio. It is intended to guide UX/UI iterations and retention work without blocking engineering execution.

## Competitive landscape (high-level)
| Product | Primary strength | Retention hooks | Gaps users complain about | Opportunity for MANTIS |
| --- | --- | --- | --- | --- |
| Scrivener | Deep project organization + export | Project trees, custom templates | Steep learning curve, dated UI | Emphasize fast onboarding + AI assist without overload |
| Plottr | Visual outlining | Visual timelines, beat sheets | Limited prose writing, export friction | Seamless outline → chapter drafting, no export friction |
| Sudowrite | AI writing assistant | Frequent AI prompts + suggestions | Can feel “AI-first,” less control | Keep author control + AI only on demand |
| Notion/Docs | Familiar docs UX | Collaboration, low friction | Not story-specific | Story-specific guardrails + auto-structure |

## MANTIS enhancement ideas (inspired by modern writing studios)
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
- Transform Mantis Studio into a Narrative Operating System that surpasses current writing tools.

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
- **Phase 2: Achieve feature parity**
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
