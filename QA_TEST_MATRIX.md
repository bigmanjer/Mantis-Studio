# QA Test Matrix

| Page | Action | Expected | Actual (Before) | Fix Applied | Actual (After) | Pass/Fail | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Account Access | Create account with email + password | Account created (Supabase) and user can log in | Not tested | Added Supabase signup flow + profile creation | Not tested | Pending | Requires Supabase project + email confirmation. |
| Account Access | Log in with valid credentials | User logged in, session stored, redirect works | Not tested | Added Supabase login flow | Not tested | Pending | Requires Supabase credentials. |
| Account Access | Log out | Session cleared and user returns to guest mode | Not tested | Added Supabase logout + session clear | Not tested | Pending | Use Account Settings log out button. |
| Account Access | Forgot password | Supabase sends reset email | Not tested | Added reset request + cooldown | Not tested | Pending | Requires SMTP in Supabase Auth settings. |
| Account Settings | Load settings after login | Email shown as read-only | Not tested | Added settings card + profile fetch | Not tested | Pending | Depends on profile table. |
| Account Settings | Save display name | Display name saved to profiles table | Not tested | Added profile update flow | Not tested | Pending | Verify in Supabase table. |
| Account Settings | Save username | Username saved and unique constraint enforced | Not tested | Added profile update flow | Not tested | Pending | Ensure unique index in Supabase. |
| Outline | Guest generate outline | Outline generated with provided API key | Not tested | No change required | Not tested | Pending | Requires valid AI key. |
| Chapters/Editor | Guest generate chapter | Chapter generated with provided API key | Not tested | No change required | Not tested | Pending | Requires valid AI key. |
| Export | Guest visits Export page | Paywall card + CTA to Account Access | Not tested | Guarded export with require_login(feature="export") | Not tested | Pending | Ensure guest mode enabled. |
| Export | Logged-in export | Export downloads markdown | Not tested | Guard uses login check before export | Not tested | Pending | Requires valid project. |
| App boot | Launch app | App boots with no red errors | Not tested | Updated auth modules + docs | Streamlit started successfully on port 8501 | Pass | Ran locally for screenshot capture. |
| App-wide | Widget keys | No StreamlitDuplicateElementKey errors | Not tested | Added stable keys for auth widgets | Not tested | Pending | Exercise auth flow and account page. |
