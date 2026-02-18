# Visual Guide - Debug Features in Mantis Studio

## What the User Will See

### 1. Debug Mode Toggle (Sidebar)
```
┌─────────────────────────────────────┐
│  ### MANTIS Studio                  │
│  Version 89.3                       │
│                                     │
│  Appearance                         │
│  Theme: [Dark ▼]                    │
│                                     │
│  🔧 Advanced ▼                      │
│  ┌─────────────────────────────┐   │
│  │ ☐ Enable Debug Mode         │   │
│  │ Show detailed debugging      │   │
│  │ information and logs         │   │
│  └─────────────────────────────┘   │
│  ─────────────────────────────────  │
└─────────────────────────────────────┘
```

When checked:
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

### 2. Debug Panel (appears when debug mode enabled)
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
│                                     │
│  📝 Session State Keys ▶            │
│                                     │
│  [🔄 Force Rerun]                   │
│  [🗑️ Clear Session State]          │
└─────────────────────────────────────┘
```

### 3. Enhanced Error Display
When an error occurs:
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

### 4. Terminal Output (with debug mode)
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

============================================================
Starting page render cycle
============================================================
Rendering page: home
Rendering home/dashboard page
Rendering footer
Page 'home' rendered successfully
Page render cycle completed successfully
```

### 5. When Error Occurs (Terminal)
```
============================================================
Starting page render cycle
============================================================
Rendering page: chapters
Rendering chapters/editor page
============================================================
UNHANDLED UI EXCEPTION
============================================================
Page: chapters
Error: AttributeError: 'NoneType' object has no attribute 'title'
Exception details:
Traceback (most recent call last):
  File "app/main.py", line 5951, in <module>
    _render_current_page()
  File "app/main.py", line 5914, in _render_current_page
    render_chapters()
  File "app/main.py", line 4523, in render_chapters
    st.write(chapter.title)
AttributeError: 'NoneType' object has no attribute 'title'
============================================================
```

## User Journey for Troubleshooting

### Scenario: User Experiences Black Screen

1. **User opens app** → Sees black screen
2. **User enables debug mode** → Opens sidebar > Advanced > Enable Debug Mode
3. **User checks Debug Panel** → Sees last exception in Session State section
4. **User checks terminal** → Sees detailed error logs
5. **User follows troubleshooting doc** → Opens docs/TROUBLESHOOTING_BLACK_SCREEN.md
6. **User applies fix** → Follows steps from guide
7. **Issue resolved** → App works correctly

### Alternative: Using Environment Variable

1. **User sets env variable**: `export MANTIS_DEBUG=1`
2. **User starts app**: `streamlit run app/main.py`
3. **Terminal shows diagnostics** → Complete startup sequence logged
4. **Error occurs** → Full details logged immediately
5. **User can diagnose** → Has all information needed

## Key Features Visualization

### Log Level Indicators
```
[INFO]    - General information
[DEBUG]   - Detailed diagnostic info (only in debug mode)
[WARNING] - Potential issues
[ERROR]   - Failures and errors
```

### Debug Panel Sections
```
📊 Session State    - Current app state
🔧 System Info      - Version and paths
📝 State Keys       - All session variables
[Action Buttons]    - Manual controls
```

### Error Display Components
```
⚠️ User Message      - Friendly explanation
📋 Troubleshooting   - Step-by-step guide
🔍 Error Details     - Technical information
🏠 Quick Actions     - Return/Reload buttons
```

## Benefits Summary

✅ **One-Click Debug** - Enable/disable with checkbox
✅ **Visual Feedback** - Debug panel shows state at a glance
✅ **Detailed Logs** - Terminal provides complete diagnostic info
✅ **Guided Troubleshooting** - Error messages include next steps
✅ **Self-Service** - Users can diagnose without developer help
✅ **Developer Friendly** - Complete information for bug reports

---

This visual guide demonstrates how the debug features appear to users and how they can be used to troubleshoot black screen issues.
