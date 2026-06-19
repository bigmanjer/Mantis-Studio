# MANTIS TODO

- [ ] Add search-provider support for lesson intake, so /learn-web can learn from a topic query instead of only a direct URL.
- [x] Build a Knowledge Base author/style matcher for imported books and project text.
- [ ] Add simulator drills for todo saving, command honesty, rate-limit handling, web-vs-reasoning clarity, and auto-learn quality.
- [ ] Add a /learn search provider so MANTIS can turn researched topics into saved lessons, not just direct URLs.
- [x] Add /save-research-key so MANTIS can store a Tavily search API key with a hidden prompt and clipboard fallback.
- [x] Organize new runtime logs into logs/launcher, logs/streamlit, and logs/chat with retention per folder.
- [x] Add /research-status so MANTIS can confirm whether the saved research key is actually loaded.
- [x] Add a paste-box workflow so long rules/notes can be saved without fighting the console prompt.
- [x] Simplify /help and move the full command list to /commands.
- [x] Add user-facing command guidance that explains what each function is for.
- [ ] Build real long-running learning jobs with saved progress, percentage/status updates, pause, and resume.
- [ ] Upgrade /resume-research from chat-log topic recovery into a real resumable research queue.
- [ ] Add a research plan runner that can expand broad topics like fiction writing craft or human history into smaller source-backed lesson batches.
- [ ] Make MANTIS refuse fake background learning claims unless a real tracked learning job is running.
- [x] Improve MANTIS rate-limit behavior so local commands still work cleanly when higher reasoning is throttled.
- [x] Add a visible chat-key health check that confirms the dedicated MANTIS chat key is separate from the main app key.
- [ ] Keep casual mentions conversational; only slash commands should trigger status, logs, simulator results, or restart actions.
