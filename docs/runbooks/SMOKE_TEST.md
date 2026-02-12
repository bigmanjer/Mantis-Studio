# MANTIS Studio Smoke Test

## Install
1. `python -m venv .venv`
2. `source .venv/bin/activate` (or `\.venv\Scripts\activate` on Windows)
3. `pip install -r requirements.txt`

## Run
1. `streamlit run app/main.py`

## Click-Test Checklist
- Dashboard
  - CTA buttons (new project, open recent, AI settings)
  - KPI cards render
- Projects
  - Create new project
  - Load recent project
  - Delete project confirmation
- Outline
  - Save outline
  - AI title/genre generation
- Editor
  - Chapter create/edit/save
  - AI improve and rewrite presets
- World Bible
  - Entity create/edit/delete
  - Entity scan from outline/chapters
- Export
  - Export markdown
  - Copy/export buttons
- AI Tools
  - Open settings
  - Fetch/test models (if API keys set)
- Legal footer
  - Terms link opens Terms of Service page
  - Privacy link opens Privacy Policy page
  - Legal link opens All Policies with all policies
  - Support link opens GitHub Issues
  - Contact link opens email

## Expected Results
- No blank screens.
- No AttributeError.
- Project JSON data remains compatible and persistent.
- All footer links navigate to valid destinations.
