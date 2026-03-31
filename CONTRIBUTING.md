# Contributing to MANTIS Studio

Thank you for your interest in contributing to MANTIS Studio! This guide will help you get started.

## Development Setup

### Prerequisites

- Python 3.10 or later
- pip (Python package manager)

### Getting Started

```bash
# Clone the repository
git clone https://github.com/bigmanjer/Mantis-Studio.git
cd Mantis-Studio

# Create a virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
pip install pytest  # For running tests

# Run the app
streamlit run app/main.py
```

## Project Structure

```
app/
├── main.py              # Main Streamlit entry point (state-driven navigation)
├── app_context.py       # Alternative implementation (reference only)
├── config/              # Application settings and configuration
│   └── settings.py      # AppConfig, env vars, logging setup
├── views/               # UI screens (dashboard, projects, editor, etc.)
├── components/          # Reusable UI blocks (buttons, forms, editors)
├── services/            # Business logic (AI, projects, export, storage)
│   ├── ai.py            # AI engine and LLM integration
│   ├── projects.py      # Project/Chapter/Entity data models
│   ├── storage.py       # File locking and storage helpers
│   ├── export.py        # Markdown export
│   └── world_bible*.py  # World Bible database and merge logic
├── layout/              # Sidebar, header, layout components
├── ui/                  # UI utilities, theme, and component helpers
└── utils/               # Navigation, auth, keys, versioning helpers
```

## Running Tests

```bash
# Run the full test suite
python -m pytest tests/ -v

# Run the healthcheck
python scripts/healthcheck.py

# Run the smoke test
python scripts/smoke_test.py
```

## Architecture Notes

- **State-driven navigation**: The app uses `st.session_state.page` for routing rather than Streamlit's built-in multipage system.
- **Single entry point**: All UI rendering flows through `app/main.py`.
- **Views are thin wrappers**: Files in `app/views/` delegate to context methods defined in the main module.
- **AI providers**: Supports Groq and OpenAI. API keys are stored in session state and persisted to a local config file.

## Making Changes

1. **Create a branch** from `main` for your changes.
2. **Keep changes focused** — one feature or fix per pull request.
3. **Run existing tests** before and after your changes to make sure nothing breaks.
4. **Add tests** for new functionality when possible.
5. **Follow existing code style** — use type hints, docstrings, and consistent naming.

## Code Style

- Use `from __future__ import annotations` at the top of new modules.
- Add type hints to function signatures.
- Use `logging.getLogger("MANTIS")` for application logging.
- Prefer `pathlib.Path` over `os.path` for file operations in new code.
- Use `AppConfig` constants instead of hardcoding values.

## Submitting a Pull Request

1. Push your branch and open a pull request against `main`.
2. Describe what the PR does and link any related issues.
3. CI will automatically run tests — make sure they pass.
4. A maintainer will review and merge when ready.

## Reporting Issues

- Use [GitHub Issues](https://github.com/bigmanjer/Mantis-Studio/issues) to report bugs or request features.
- Include steps to reproduce, expected vs. actual behavior, and your Python/Streamlit version.

## License

By contributing, you agree that your contributions will be licensed under the project's existing license.
