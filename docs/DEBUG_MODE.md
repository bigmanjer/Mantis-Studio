# Debug Mode Guide for Mantis Studio

## Overview

Mantis Studio now includes comprehensive debugging features to help troubleshoot issues like black screens, rendering problems, and other errors.

## How to Enable Debug Mode

### Method 1: UI Toggle (Recommended)
1. Launch Mantis Studio: `streamlit run app/main.py`
2. Open the sidebar (if not already open)
3. Click on **"Advanced"** expander
4. Check the **"Enable Debug Mode"** checkbox
5. Debug information will now appear in the sidebar and terminal

### Method 2: Environment Variable
Set the environment variable before running the app:

```bash
export MANTIS_DEBUG=1
streamlit run app/main.py
```

Or on Windows:
```cmd
set MANTIS_DEBUG=1
streamlit run app/main.py
```

## What Debug Mode Provides

### 1. Enhanced Logging
- Detailed startup diagnostics
- Page rendering status
- Session state changes
- Error tracking with full stack traces
- Logs appear in the terminal/console

### 2. Debug Panel (Sidebar)
When debug mode is active, a **"🛠 Debug Panel"** appears in the sidebar with:

#### Session State Section
- Current page
- Initialization status
- Loaded project information
- Last action performed
- Last exception (if any)

#### System Info Section
- Python version
- Streamlit version
- App version
- Projects directory path
- Config file path

#### Session State Keys Section
- Lists all session state variables
- Shows first 20 keys with their values
- Useful for debugging state issues

#### Action Buttons
- **Force Rerun**: Manually trigger a page refresh
- **Clear Session State**: Reset all session variables (use with caution)

### 3. Enhanced Error Display
When an error occurs, debug mode shows:
- User-friendly error message
- Troubleshooting steps
- Expandable error details with full stack trace
- Quick action buttons to return to dashboard or reload

## Troubleshooting Black Screen Issues

If you experience a black screen:

1. **Enable Debug Mode** (see methods above)

2. **Check Terminal Logs**
   - Look for error messages in the terminal where you ran Streamlit
   - Search for lines containing `[ERROR]` or `[WARNING]`
   - Look for "STARTUP DIAGNOSTICS" section

3. **Check Debug Panel**
   - Open the sidebar
   - Expand the Debug Panel sections
   - Look for the "Last exception" field
   - Check if the current page is correct

4. **Common Issues and Solutions**

   - **Page not rendering**: Try Force Rerun button
   - **Session state corrupted**: Try Clear Session State button (note: this will log you out)
   - **Config file issues**: Check if `projects/.mantis_config.json` exists and is valid JSON
   - **Project loading failure**: Check "Last exception" for project-related errors

5. **Collect Debug Information**
   If the issue persists, collect this information for support:
   - Terminal logs (copy everything from startup)
   - Screenshot of the Debug Panel
   - Error details from the error display
   - Steps to reproduce the issue

## Logging Output Explained

### Startup Sequence
```
============================================================
MANTIS Studio Starting...
============================================================
Starting UI initialization...
Page config set successfully
Theme injected successfully
Session state initialized for first time
App config loaded: X keys
Initializing session state...
Session state initialization complete
```

### Page Rendering
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

### Error Example
```
============================================================
UNHANDLED UI EXCEPTION
============================================================
Page: chapters
Error: AttributeError: 'NoneType' object has no attribute 'title'
[Full stack trace follows]
============================================================
```

## Performance Considerations

Debug mode adds some overhead:
- More detailed logging
- Additional UI elements in sidebar
- Extra state tracking

For production use or when performance is critical, disable debug mode.

## Privacy Note

Debug logs may contain:
- File paths
- Project names
- Session state information

Be cautious when sharing debug logs publicly. Redact sensitive information.

## Reporting Issues

When reporting issues on GitHub, please include:

1. Debug logs from terminal (startup to error)
2. Screenshot of Debug Panel
3. Steps to reproduce
4. Expected vs actual behavior
5. Your environment:
   - OS (Windows/Mac/Linux)
   - Python version
   - Streamlit version
   - Mantis Studio version (shown in Debug Panel)

## Advanced Debugging

### Log Levels
The logging system uses these levels:
- `DEBUG`: Detailed diagnostic information
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

## Disabling Debug Mode

1. **UI Method**: Uncheck "Enable Debug Mode" in sidebar > Advanced
2. **Environment**: Remove or unset `MANTIS_DEBUG` environment variable

The app will return to normal operation with standard logging.

---

**Need Help?** Check the [GitHub Issues](https://github.com/bigmanjer/Mantis-Studio/issues) or create a new issue with your debug information.
