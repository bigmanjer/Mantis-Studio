# How to Verify

1. **Install dependencies**
   - `pip install -r requirements.txt`

2. **Run the app**
   - `streamlit run Mantis_Studio.py --server.headless true`

3. **Enable debug panel (optional)**
   - Add `DEBUG = true` to `.streamlit/secrets.toml` and reload the app.

4. **Click-test routing and CTAs**
   - Dashboard → Projects/Outline/Editor/World/Export via the main CTA and quick actions.
   - Projects → Open, Export, Delete, and Import flows.
   - Outline → Save Project, Save Outline, Generate Structure, Scan Entities.
   - Editor → Save Chapter, Update Summary, AI Improve/Rewrite actions.
   - World Bible → Add entities, Apply/Ignore suggestions, Run Coherence Check.
   - Export → Export buttons, Close export, Go to Projects.
   - AI Settings → Session key, Save key, Fetch/Test models, Save settings.
   - Account Settings → Log in, Sign up, Reset password, Log out.
   - Legal Center → Back to Studio, section navigation.

5. **Verify no crashes**
   - Check the debug panel for `last_exception` and confirm it is empty during normal navigation.
