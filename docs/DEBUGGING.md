# Debugging Guide for Mantis Studio

Complete guide for troubleshooting black screens, rendering problems, and other errors in Mantis Studio.

## Table of Contents
- [Overview](#overview)
- [Quick Start](#quick-start)
- [Enabling Debug Mode](#enabling-debug-mode)
- [Troubleshooting Black Screens](#troubleshooting-black-screens)
- [Debug Features](#debug-features)
- [Visual Guide](#visual-guide)
- [Advanced Topics](#advanced-topics)

---

## Overview

Mantis Studio includes comprehensive debugging features to help you diagnose and resolve issues. Whether you're experiencing a black screen, rendering problems, or errors, this guide provides step-by-step instructions to troubleshoot and fix issues.

### What's Included
- **Enhanced Logging**: Detailed diagnostics in terminal
- **Debug Panel**: Visual inspection of app state
- **Error Tracking**: User-friendly error messages with solutions
- **Self-Service Tools**: Clear session state, force rerun, and more

---

## Quick Start

### If You're Seeing a Black Screen

**Enable debug mode immediately:**

```bash
export MANTIS_DEBUG=1
streamlit run app/main.py
```

Or if you can see the sidebar:
1. Open sidebar > **Advanced**
2. Check **"Enable Debug Mode"**

Then check the terminal for error messages and jump to [Troubleshooting Black Screens](#troubleshooting-black-screens).

---

## Enabling Debug Mode

Debug mode provides detailed information about what the app is doing and any errors that occur.

### Method 1: UI Toggle (Recommended)

1. Launch Mantis Studio: `streamlit run app/main.py`
2. Open the sidebar (if not already open)
3. Click on **"Advanced"** expander
4. Check the **"Enable Debug Mode"** checkbox
5. Debug information will now appear in the sidebar and terminal

### Method 2: Environment Variable

Set the environment variable before running the app:

**Linux/Mac:**
```bash
export MANTIS_DEBUG=1
streamlit run app/main.py
```

**Windows (Command Prompt):**
```cmd
set MANTIS_DEBUG=1
streamlit run app/main.py
```

**Windows (PowerShell):**
```powershell
$env:MANTIS_DEBUG="1"
streamlit run app/main.py
```

### What You'll See

With debug mode enabled:
- ✓ Detailed logs in terminal showing startup sequence
- ✓ Debug Panel in sidebar with app state
- ✓ Enhanced error messages with stack traces
- ✓ Session state inspection tools

---

## Troubleshooting Black Screens

Follow these steps in order if you're experiencing a black or blank screen.

### Step 1: Enable Debug Mode

Use one of the methods above to enable debug mode. This will provide diagnostic information.

### Step 2: Check the Terminal

Look for error messages in the terminal where you started the app.

**✅ Good startup (no issues):**
```
============================================================
MANTIS Studio Starting...
============================================================
Starting UI initialization...
Page config set successfully
Theme injected successfully
STARTUP DIAGNOSTICS COMPLETE - App initialized successfully
```

**❌ Problem indicators:**
- Lines containing `[ERROR]` or `[WARNING]`
- Python exceptions or tracebacks
- "Failed to load", "Failed to set", or similar messages

### Step 3: Common Issues and Solutions

#### Issue 1: Missing or Corrupt Config File

**Symptoms:**
- App loads but shows black screen
- Logs show: `Failed to load app config` or JSON errors

**Solution:**
```bash
# Backup existing config (if any)
mv projects/.mantis_config.json projects/.mantis_config.json.backup

# Restart the app - it will create a new config
streamlit run app/main.py
```

#### Issue 2: Streamlit Version Mismatch

**Symptoms:**
- Page doesn't render at all
- Logs show: Import errors or attribute errors related to Streamlit

**Solution:**
```bash
# Reinstall requirements
pip install -r requirements.txt --upgrade
```

#### Issue 3: Theme Injection Failed

**Symptoms:**
- Screen is blank or all white/black
- Logs show: `Failed to inject theme`

**Solution:**
```bash
# Check if assets directory exists
ls -la assets/

# If missing, the app should still work with default theme
# Try disabling custom theme in sidebar if you can access it
```

#### Issue 4: Session State Corruption

**Symptoms:**
- App worked before, now shows black screen
- Logs show: Various attribute errors or state-related issues

**Solution:**
1. In sidebar, go to Debug Panel
2. Click "Clear Session State"
3. Or, clear browser cache and reload (Ctrl+Shift+R or Cmd+Shift+R)

#### Issue 5: Projects Directory Issues

**Symptoms:**
- App fails during initialization
- Logs show: `Cannot create storage directory` or permission errors

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

Run the self-test to verify the installation:

```bash
cd /path/to/Mantis-Studio
python app/main.py --selftest
```

**Expected output:**
```
[MANTIS SELFTEST]
SELFTEST RESULT: PASS
```

If the self-test fails, there's a deeper issue with the installation.

### Step 5: Browser Developer Console

1. Open browser developer tools (F12)
2. Check **Console** tab for JavaScript errors
3. Check **Network** tab for failed requests

**Common browser issues:**
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

If the issue persists, test with a fresh state:

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

---

## Debug Features

When debug mode is enabled, you get access to powerful diagnostic tools.

### 1. Enhanced Logging

Detailed logs appear in the terminal showing:
- Startup diagnostics
- Page rendering status
- Session state changes
- Error tracking with full stack traces

**Startup sequence example:**
```
============================================================
MANTIS Studio Starting...
============================================================
Starting UI initialization...
Page config set successfully
Theme injected successfully
Session state initialized for first time
App config loaded: 12 keys
Initializing session state...
Session state initialization complete
```

**Page rendering example:**
```
============================================================
Starting page render cycle
============================================================
Rendering page: home
Rendering home/dashboard page
Rendering footer
Page 'home' rendered successfully
Page render cycle completed successfully
```

**Error example:**
```
============================================================
UNHANDLED UI EXCEPTION
============================================================
Page: chapters
Error: AttributeError: 'NoneType' object has no attribute 'title'
Exception details:
[Full stack trace follows]
============================================================
```

### 2. Debug Panel (Sidebar)

When debug mode is active, a **"🛠 Debug Panel"** appears in the sidebar with expandable sections:

#### 📊 Session State Section
- Current page
- Initialization status
- Loaded project information
- Last action performed with timestamp
- Last exception (if any)

#### 🔧 System Info Section
- Python version
- Streamlit version
- App version
- Projects directory path
- Config file path

#### 📝 Session State Keys Section
- Lists all session state variables
- Shows first 20 keys with their values
- Useful for debugging state issues
- Total count displayed

#### Action Buttons
- **🔄 Force Rerun**: Manually trigger a page refresh
- **🗑️ Clear Session State**: Reset user session variables (preserves Streamlit internals)

### 3. Enhanced Error Display

When an error occurs, you'll see:
- **User-friendly error message**: Clear explanation of what went wrong
- **Troubleshooting steps**: Actionable guidance on what to do next
- **Expandable error details**: Full stack trace for developers
- **Quick action buttons**: 
  - 🏠 Return to Dashboard
  - 🔄 Reload App

---

## Visual Guide

This section shows what the debug features look like in the UI.

### Debug Mode Toggle

**When disabled:**
```
┌─────────────────────────────────────┐
│  🔧 Advanced ▼                      │
│  ┌─────────────────────────────┐   │
│  │ ☐ Enable Debug Mode         │   │
│  │ Show detailed debugging      │   │
│  │ information and logs         │   │
│  └─────────────────────────────┘   │
└─────────────────────────────────────┘
```

**When enabled:**
```
┌─────────────────────────────────────┐
│  🔧 Advanced ▼                      │
│  ┌─────────────────────────────┐   │
│  │ ☑ Enable Debug Mode         │   │
│  │ ✓ Debug mode active          │   │
│  │ Check terminal for detailed  │   │
│  │ logs                         │   │
│  └─────────────────────────────┘   │
└─────────────────────────────────────┘
```

### Debug Panel Layout

```
┌─────────────────────────────────────┐
│  ### 🛠 Debug Panel                 │
│                                     │
│  📊 Session State ▼                 │
│  ┌─────────────────────────────┐   │
│  │ Current Page: home           │   │
│  │ Initialized: True            │   │
│  │ Project Loaded: True         │   │
│  │   - Title: My Novel          │   │
│  │   - Path: projects/my.json   │   │
│  │ Last Action: Save Project    │   │
│  │               (14:32:15)     │   │
│  │ Last Exception: —            │   │
│  └─────────────────────────────┘   │
│                                     │
│  🔧 System Info ▶                   │
│  📝 Session State Keys ▶            │
│                                     │
│  [🔄 Force Rerun]                   │
│  [🗑️ Clear Session State]          │
└─────────────────────────────────────┘
```

### Error Display

```
┌──────────────────────────────────────────────┐
│  ⚠️ Something went wrong while rendering     │
│     this page.                               │
│                                              │
│  ### Troubleshooting Steps:                  │
│  1. Try reloading the app (F5 or Ctrl+R)    │
│  2. Return to dashboard using sidebar        │
│  3. Check terminal/logs for detailed errors  │
│  4. If issue persists, report on GitHub     │
│     with error details below                 │
│                                              │
│  🔍 Error Details ▶                          │
│  ┌──────────────────────────────────────┐   │
│  │ AttributeError: 'NoneType' object    │   │
│  │ has no attribute 'title'             │   │
│  │                                      │   │
│  │ Debug Mode Active - Stack Trace:     │   │
│  │ [Full stack trace shown here]        │   │
│  └──────────────────────────────────────┘   │
│                                              │
│  [🏠 Return to Dashboard] [🔄 Reload App]   │
└──────────────────────────────────────────────┘
```

### Terminal Output with Debug Mode

```
============================================================
MANTIS Studio Starting...
============================================================
Starting UI initialization...
Assets directory: /path/to/assets
Icon path exists: True, using: mantis_logo_trans.png
Page config set successfully
Theme injected successfully
Session state initialized for first time
App config loaded: 12 keys
Config keys: ['ui_theme', 'daily_word_goal', ...]
Initializing session state...
Default page set to: home
Session state initialization complete
Projects directory set to: projects

============================================================
STARTUP DIAGNOSTICS
============================================================
App Version: 89.3
Python Version: 3.11.0
Streamlit Version: 1.32.0
Projects Directory: projects
Projects Dir Exists: True
Config Path: projects/.mantis_config.json
Config Exists: True
Assets Directory: /path/to/assets
Assets Dir Exists: True
Current Page: home
Project Loaded: True
  - Project Title: My Novel
  - Project Path: projects/my_novel.json
Session State Keys: 45 total
Debug Mode: True
============================================================
STARTUP DIAGNOSTICS COMPLETE - App initialized successfully
============================================================
```

### Typical User Journey

**Scenario: User Experiences Black Screen**

1. **User opens app** → Sees black screen
2. **User enables debug mode** → Opens sidebar > Advanced > Enable Debug Mode
3. **User checks Debug Panel** → Sees last exception in Session State section
4. **User checks terminal** → Sees detailed error logs
5. **User identifies issue** → Follows solution from troubleshooting section
6. **User applies fix** → Follows steps from guide
7. **Issue resolved** → App works correctly

---

## Advanced Topics

### Log Levels

The logging system uses these levels:
- `DEBUG`: Detailed diagnostic information (only when debug mode enabled)
- `INFO`: General informational messages
- `WARNING`: Warning messages for potential issues
- `ERROR`: Error messages for failures
- `EXCEPTION`: Critical errors with full stack traces

### Custom Logging

You can add temporary logging for specific troubleshooting:

```python
from app.main import logger

logger.debug("Custom debug message")
logger.info("Custom info message")
logger.warning("Custom warning message")
logger.error("Custom error message")
```

### Collecting Debug Information

Before reporting an issue, collect this information:

**1. Terminal output** (copy everything from startup)
```bash
streamlit run app/main.py 2>&1 | tee debug.log
```

**2. Debug panel info** (if accessible)
- Open sidebar > Debug Panel
- Take screenshots of each section

**3. System info**
```bash
python --version
streamlit --version
cat VERSION.txt
uname -a  # Linux/Mac
systeminfo  # Windows
```

**4. Browser info**
- Browser name and version
- Any extensions installed
- Console errors (from F12 developer tools)

### Reporting Issues

Create a GitHub issue with:

1. **Title:** "Black Screen: [Brief Description]"
2. **Environment:**
   - OS (Windows/Mac/Linux)
   - Python version
   - Streamlit version
   - Mantis Studio version (shown in Debug Panel)
3. **Steps to reproduce**
4. **Debug logs** (from terminal)
5. **Screenshots** (if relevant)
6. **What you tried** (from this guide)

### Known Issues and Workarounds

#### Black screen on Windows with certain terminals
**Workaround:** Use Command Prompt or PowerShell instead of Git Bash

#### Theme not loading on first run
**Workaround:** Refresh the page (F5) after the app fully loads

#### Sidebar not visible
**Workaround:** Press the `>` button in the top-left corner or press `[` key

### Performance Considerations

Debug mode adds some overhead:
- More detailed logging
- Additional UI elements in sidebar
- Extra state tracking

For production use or when performance is critical, disable debug mode.

### Privacy Note

Debug logs may contain:
- File paths
- Project names
- Session state information

Be cautious when sharing debug logs publicly. Redact sensitive information.

### Disabling Debug Mode

**UI Method:** Uncheck "Enable Debug Mode" in sidebar > Advanced

**Environment Method:** Remove or unset `MANTIS_DEBUG` environment variable

The app will return to normal operation with standard logging.

---

## Still Need Help?

1. Check [GitHub Issues](https://github.com/bigmanjer/Mantis-Studio/issues)
2. Search for similar problems
3. Create a new issue with debug information
4. Include all debug logs and screenshots

---

**Last Updated:** 2026-02-18  
**Version:** Mantis Studio v47.0+  
**Need Help?** [Create an Issue](https://github.com/bigmanjer/Mantis-Studio/issues)
