# Black Screen Troubleshooting Guide

## Quick Fix Steps

If you're experiencing a black or blank screen in Mantis Studio, follow these steps:

### Step 1: Enable Debug Mode
```bash
export MANTIS_DEBUG=1
streamlit run app/main.py
```

Or enable it in the UI (if you can see the sidebar):
1. Open sidebar > Advanced
2. Check "Enable Debug Mode"

### Step 2: Check the Terminal
Look for error messages in the terminal where you started the app. Common patterns:

**Good startup (no black screen):**
```
============================================================
MANTIS Studio Starting...
============================================================
Starting UI initialization...
Page config set successfully
Theme injected successfully
STARTUP DIAGNOSTICS COMPLETE - App initialized successfully
```

**Problem indicators:**
- Lines containing `[ERROR]` or `[WARNING]`
- Python exceptions or tracebacks
- "Failed to load", "Failed to set", or similar messages

### Step 3: Common Causes and Solutions

#### 1. Missing or Corrupt Config File
**Symptom:** App loads but shows black screen
**Logs show:** `Failed to load app config` or JSON errors

**Solution:**
```bash
# Backup existing config (if any)
mv projects/.mantis_config.json projects/.mantis_config.json.backup

# Restart the app - it will create a new config
streamlit run app/main.py
```

#### 2. Streamlit Version Mismatch
**Symptom:** Page doesn't render at all
**Logs show:** Import errors or attribute errors related to Streamlit

**Solution:**
```bash
# Reinstall requirements
pip install -r requirements.txt --upgrade
```

#### 3. Theme Injection Failed
**Symptom:** Screen is blank or all white/black
**Logs show:** `Failed to inject theme`

**Solution:**
```bash
# Check if assets directory exists
ls -la assets/

# If missing, the app should still work with default theme
# Try disabling custom theme in sidebar if you can access it
```

#### 4. Session State Corruption
**Symptom:** App worked before, now shows black screen
**Logs show:** Various attribute errors or state-related issues

**Solution:**
1. In sidebar, go to Debug Panel
2. Click "Clear Session State"
3. Or, clear browser cache and reload (Ctrl+Shift+R or Cmd+Shift+R)

#### 5. Projects Directory Issues
**Symptom:** App fails during initialization
**Logs show:** `Cannot create storage directory` or permission errors

**Solution:**
```bash
# Check if projects directory exists and is writable
ls -la projects/
chmod 755 projects/  # Linux/Mac only

# Or specify a different directory
mkdir ~/mantis_projects
# Edit app/main.py to point to this directory
```

### Step 4: Verify Installation

Run the self-test:
```bash
cd /path/to/Mantis-Studio
python app/main.py --selftest
```

Expected output:
```
[MANTIS SELFTEST]
SELFTEST RESULT: PASS
```

If the self-test fails, there's a deeper issue with the installation.

### Step 5: Browser Developer Console

1. Open browser developer tools (F12)
2. Check Console tab for JavaScript errors
3. Check Network tab for failed requests

Common browser issues:
- Ad blockers interfering with Streamlit
- Browser extensions blocking content
- CORS issues (if running on remote server)

### Step 6: Clean Restart

If nothing works, try a clean restart:

```bash
# Stop the app (Ctrl+C)
# Clear Streamlit cache
rm -rf ~/.streamlit/cache/

# Clear session state
rm -rf /tmp/streamlit-*

# Restart with debug mode
export MANTIS_DEBUG=1
streamlit run app/main.py --server.port 8501
```

### Step 7: Test with Minimal State

If issue persists, test with a fresh state:

```bash
# Backup your projects
cp -r projects projects_backup

# Create fresh projects directory
rm -rf projects
mkdir projects

# Restart
streamlit run app/main.py
```

If this works, the issue is in your project data. Restore projects one by one to find the problematic one.

## Collecting Debug Information

Before reporting the issue, collect this information:

1. **Terminal output** (copy everything from startup)
   ```bash
   streamlit run app/main.py 2>&1 | tee debug.log
   ```

2. **Debug panel info** (if accessible)
   - Open sidebar > Debug Panel
   - Take screenshots of each section

3. **System info**
   ```bash
   python --version
   streamlit --version
   cat VERSION.txt
   uname -a  # Linux/Mac
   systeminfo  # Windows
   ```

4. **Browser info**
   - Browser name and version
   - Any extensions installed
   - Console errors (from F12 developer tools)

## Reporting the Issue

Create a GitHub issue with:

1. **Title:** "Black Screen: [Brief Description]"
2. **Environment:**
   - OS
   - Python version
   - Streamlit version
   - Mantis version
3. **Steps to reproduce**
4. **Debug logs** (from terminal)
5. **Screenshots** (if relevant)
6. **What you tried** (from this guide)

## Known Issues and Workarounds

### Issue: Black screen on Windows with certain terminals
**Workaround:** Use Command Prompt or PowerShell instead of Git Bash

### Issue: Theme not loading on first run
**Workaround:** Refresh the page (F5) after the app fully loads

### Issue: Sidebar not visible
**Workaround:** Press the `>` button in the top-left corner or press `[` key

## Still Need Help?

1. Check [GitHub Issues](https://github.com/bigmanjer/Mantis-Studio/issues)
2. Search for similar problems
3. Create a new issue with debug information
4. Join community discussions (if available)

---

**Last Updated:** 2026-02-18
**For:** Mantis Studio v47.0+
