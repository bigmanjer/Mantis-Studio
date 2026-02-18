# Mantis Studio - Maintenance & Best Practices Guide

**For:** Development Team  
**Purpose:** Ongoing maintenance and future improvements  
**Last Updated:** February 18, 2026

---

## 🎯 Quick Reference

### Current Status
- **Version:** 47.0
- **Tests:** 530/530 passing ✅
- **Security:** 0 vulnerabilities ✅
- **Production Ready:** YES ✅

### Key Commands
```bash
# Run tests
pytest tests/ -v

# Start app
streamlit run app/main.py

# Run self-test
python -m app.main --selftest

# Lint code
flake8 app/ --max-line-length=120
```

---

## 📋 Development Workflow

### Before Making Changes
1. ✅ Pull latest code: `git pull origin main`
2. ✅ Run tests: `pytest tests/ -v`
3. ✅ Check current status: `python -m app.main --selftest`

### While Developing
1. ✅ Make small, focused changes
2. ✅ Add tests for new features
3. ✅ Run affected tests frequently: `pytest tests/test_xxx.py`
4. ✅ Use type hints on new functions
5. ✅ Add docstrings to public functions

### Before Committing
1. ✅ Run full test suite: `pytest tests/`
2. ✅ Check for unused imports: `autoflake --check app/**/*.py`
3. ✅ Run linter: `flake8 app/`
4. ✅ Verify app starts: `streamlit run app/main.py` (test for 10 seconds)

### Commit Guidelines
- Use conventional commits: `feat:`, `fix:`, `docs:`, `refactor:`
- Keep commits focused and atomic
- Reference issue numbers when applicable
- Add meaningful commit messages

---

## 🛡️ Security Best Practices

### API Keys & Secrets
- ❌ **NEVER** hardcode API keys in source code
- ✅ Use environment variables: `os.getenv("API_KEY")`
- ✅ Use `.env` files (gitignored)
- ✅ Document required env vars in README

### File Operations
- ✅ Always use atomic writes (temp file → rename)
- ✅ Validate file paths before reading/writing
- ✅ Use proper error handling for I/O operations
- ✅ Clean up temp files in `finally` blocks

### Input Validation
- ✅ Always sanitize user input
- ✅ Use the `sanitize_ai_input()` function for AI prompts
- ✅ Validate file uploads (size, type)
- ✅ Escape HTML when rendering user content

### Dependencies
- ✅ Run security scan before adding new dependencies
- ✅ Pin versions in requirements.txt
- ✅ Review dependency licenses
- ✅ Update dependencies regularly (monthly)

---

## 🧪 Testing Guidelines

### Writing Tests
- ✅ Follow the AAA pattern: Arrange, Act, Assert
- ✅ One assertion per test (generally)
- ✅ Use descriptive test names: `test_<what>_<scenario>_<expected>`
- ✅ Add docstrings to complex tests

### Test Organization
```
tests/
├── test_all.py              # Core unit tests (imports, helpers, etc.)
├── test_workflows.py        # Integration/workflow tests
├── test_integration_ai.py   # AI service integration tests
└── conftest.py              # Pytest fixtures
```

### Coverage Goals
- Target: 70% minimum
- Core services: 90%+
- UI components: 50%+ (harder to test)
- Run coverage: `pytest --cov=app tests/`

---

## 📦 Adding New Features

### Checklist
1. ✅ Create feature branch: `git checkout -b feature/my-feature`
2. ✅ Add implementation in appropriate layer:
   - Business logic → `app/services/`
   - UI components → `app/components/`
   - Views/pages → `app/views/`
   - Utilities → `app/utils/`
3. ✅ Add tests in `tests/`
4. ✅ Add docstrings and type hints
5. ✅ Update documentation if needed
6. ✅ Run full test suite
7. ✅ Create PR with description

### Architecture Layers
```
app/
├── main.py              # Entry point, routing
├── views/               # UI screens (thin, delegate to services)
├── services/            # Business logic (no Streamlit dependencies)
├── components/          # Reusable UI components
├── layout/              # Layout components (sidebar, header)
├── utils/               # Helper functions
└── config/              # Configuration
```

### Separation of Concerns
- **Views:** Display UI, handle user input, delegate to services
- **Services:** Business logic, data processing, API calls
- **Components:** Reusable UI widgets
- **Utils:** Shared utilities (no business logic)

---

## 🎨 UI/UX Best Practices

### Streamlit Guidelines
- ✅ Use `st.cache_data` for expensive computations
- ✅ Use `st.cache_resource` for connections/resources
- ✅ Add `key=` to interactive widgets (especially in loops)
- ✅ Use `with st.spinner():` for long operations
- ✅ Show progress with `st.progress()`

### User Experience
- ✅ Always show feedback for user actions (toast, success message)
- ✅ Use error messages that guide users to solutions
- ✅ Keep loading times under 3 seconds
- ✅ Disable buttons during processing
- ✅ Validate input before submission

### Responsive Design
- ✅ Test on different screen sizes
- ✅ Use `st.columns()` for layouts
- ✅ Use `use_container_width=True` for buttons
- ✅ Keep text readable (avoid tiny fonts)

---

## 🐛 Debugging Tips

### Common Issues

#### Streamlit Widget State
**Problem:** Widget state not persisting  
**Solution:** Ensure widget has a unique `key=` parameter

#### Rerun Loops
**Problem:** Infinite rerun loops  
**Solution:** Check for state modifications that trigger reruns

#### Import Errors
**Problem:** Module not found  
**Solution:** Verify `sys.path` includes project root

#### Cache Issues
**Problem:** Cached data not updating  
**Solution:** Use `st.cache_data(ttl=3600)` or clear cache

### Debugging Tools
```python
# Print debug info
st.write("DEBUG:", st.session_state)

# Add breakpoint
import pdb; pdb.set_trace()

# Log to console
import logging
logging.debug("Debug message")
```

### Test in Isolation
```bash
# Test single module
python -c "from app.services import projects; print(projects.__file__)"

# Run single test
pytest tests/test_all.py::TestProjectCRUD::test_create_project -v
```

---

## 📊 Performance Optimization

### Caching Strategy
```python
# Cache data that doesn't change often
@st.cache_data(ttl=3600)  # 1 hour
def fetch_models():
    return expensive_api_call()

# Cache resources (connections)
@st.cache_resource
def get_database_connection():
    return create_connection()
```

### Session State
- ✅ Store only necessary data
- ✅ Avoid large objects in session state
- ✅ Clean up unused state keys
- ✅ Use lazy loading when possible

### Asset Loading
```python
# Cache assets permanently
@st.cache_data
def load_logo():
    return open("logo.png", "rb").read()
```

---

## 🔄 Code Refactoring

### When to Refactor
- Function exceeds 50 lines
- Code is duplicated 3+ times
- Complex conditionals (nested >3 levels)
- Tests are difficult to write
- Code is hard to understand

### Refactoring Patterns
1. **Extract Function** - Move code block to new function
2. **Extract Class** - Group related functions
3. **Remove Duplication** - Create shared utility
4. **Simplify Conditionals** - Use early returns
5. **Rename** - Use descriptive names

### Safety Checklist
- ✅ Tests pass before refactoring
- ✅ Make small changes incrementally
- ✅ Tests pass after each change
- ✅ Commit frequently
- ✅ Code review if changing critical paths

---

## 📝 Documentation Standards

### Code Comments
- ✅ Explain **why**, not **what**
- ✅ Update comments when changing code
- ✅ Remove outdated comments
- ❌ Don't comment obvious code

### Docstrings (Required for Public Functions)
```python
def calculate_word_count(text: str) -> int:
    """Calculate the word count of given text.
    
    Args:
        text: Input text to count words
        
    Returns:
        Number of words in text
        
    Example:
        >>> calculate_word_count("Hello world")
        2
    """
    return len(text.split())
```

### README Updates
- Update when adding major features
- Document new environment variables
- Update installation instructions
- Keep examples current

---

## 🚀 Deployment Checklist

### Pre-Deployment
- [ ] All tests pass (530/530)
- [ ] No security vulnerabilities (CodeQL)
- [ ] No linting errors
- [ ] Version bumped in VERSION.txt
- [ ] CHANGELOG.md updated
- [ ] Documentation updated

### Deployment
- [ ] Backup current production data
- [ ] Deploy to staging first
- [ ] Run smoke tests on staging
- [ ] Monitor logs for errors
- [ ] Deploy to production
- [ ] Run smoke tests on production
- [ ] Monitor for 24 hours

### Post-Deployment
- [ ] Verify all features work
- [ ] Check error logs
- [ ] Monitor performance metrics
- [ ] Notify users of updates
- [ ] Document any issues

---

## 🆘 Getting Help

### Resources
- **Documentation:** `docs/` directory
- **Debugging Guide:** `docs/guides/DEBUGGING.md`
- **Contributing:** `docs/guides/CONTRIBUTING.md`
- **Audit Reports:** Root directory (AUDIT*.md files)

### Common Questions

**Q: How do I add a new page?**  
A: Add view in `app/views/`, add route in `app/router.py`, add nav in `app/utils/navigation.py`

**Q: How do I add a new service?**  
A: Create in `app/services/`, add tests in `tests/`, import in views as needed

**Q: Tests are failing, what do I do?**  
A: Run `pytest tests/ -v --tb=short` to see detailed errors, fix issues, run again

**Q: How do I update dependencies?**  
A: Update `requirements.txt`, run `pip install -r requirements.txt`, run tests

---

## 📈 Monitoring & Maintenance

### Weekly Tasks
- [ ] Review error logs
- [ ] Check for security updates
- [ ] Review open issues
- [ ] Update dependencies (minor versions)

### Monthly Tasks
- [ ] Run full test suite
- [ ] Review code quality metrics
- [ ] Update major dependencies
- [ ] Review and clean up technical debt
- [ ] Update documentation

### Quarterly Tasks
- [ ] Security audit (CodeQL)
- [ ] Performance review
- [ ] Architecture review
- [ ] Dependency audit
- [ ] Documentation review

---

## 🎓 Learning Resources

### Streamlit
- Official Docs: https://docs.streamlit.io/
- Best Practices: https://docs.streamlit.io/develop/concepts
- Caching Guide: https://docs.streamlit.io/develop/concepts/architecture/caching

### Python
- Type Hints: https://docs.python.org/3/library/typing.html
- Dataclasses: https://docs.python.org/3/library/dataclasses.html
- Testing: https://docs.pytest.org/

### Code Quality
- PEP 8: https://peps.python.org/pep-0008/
- Clean Code: https://github.com/zedr/clean-code-python
- Design Patterns: https://refactoring.guru/design-patterns/python

---

## 🎉 Success Metrics

### Code Quality
- Test Coverage: >70%
- Tests Passing: 100%
- Linting Errors: 0
- Security Vulnerabilities: 0

### Performance
- Page Load Time: <3 seconds
- API Response Time: <2 seconds
- Memory Usage: <500 MB
- Error Rate: <0.1%

### Developer Experience
- Onboarding Time: <2 hours
- Build Time: <30 seconds
- Test Suite Time: <2 minutes
- Documentation Complete: >80%

---

**Last Updated:** February 18, 2026  
**Maintained By:** Development Team  
**Questions?** See docs/ or create an issue
