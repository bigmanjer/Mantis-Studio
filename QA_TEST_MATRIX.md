# QA Test Matrix

| Page | Button/Action | Expected | Actual (Before) | Fix Applied | Actual (After) | Notes |
| --- | --- | --- | --- | --- | --- | --- |
| App boot | `python -m compileall .` | Compile succeeds | NameError on `Generator` annotation | Swapped Generator imports to `collections.abc` | Compile succeeds | Phase 0 requirement |
| App boot | `python -m streamlit run Mantis_Studio.py --server.headless true --server.port 8501 --server.address 0.0.0.0` | UI reachable | Crash before UI | Added Generator import + auth fixes | UI reachable | Verified via `/_stcore/health` |
| Account (guest) | Open Account page | Email signup + login available | Only OIDC sign-in; no MANTIS account creation | Added Supabase email auth (signup/sign-in/reset/magic link) | Email auth UI available | Requires Supabase config |
| Account (logged in) | Email reset | Password reset link sent | Not available | Added Supabase reset flow + rate limits | Reset link sent (if configured) | Rate limit enforced |
| AI Tools (guest) | Add Groq/OpenAI key | Key stored for session only | Keys overwritten by saved config; no session precedence | Added session `ai_keys` + precedence | Keys persist in session | Saved keys only when logged in |
| Outline | Generate outline | Works for guests with key | Guest blocked by key precedence | Session keys honored for generation | Generation available with session key | Requires key |
| Chapters/Editor | Generate chapter | Works for guests with key | Guest blocked by key precedence | Session keys honored for generation | Generation available with session key | Requires key |
| World Bible | Scan entities | Works for guests with key | Guest blocked by key precedence | Session keys honored for generation | Scan available with session key | Requires key |
| Export | Open Export page (guest) | Paywall + CTA | Warning only | Added paywall card + CTA | Paywall CTA shown | Export gated for guests |
| Dashboard | CTA buttons | All CTAs route correctly | Some flows blocked by auth | Guest messaging updated | CTAs route correctly | Manual click coverage |
| Projects | Create/Save (guest) | Guest can create and save locally | Save/create blocked by auth gate | Allow guest save + create/import locally | Guest projects save locally; export gated | Uses guest projects dir |
