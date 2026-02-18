# Using the Mantis Studio Custom GitHub Copilot Agent

## Overview

The **mantis-engineer** custom agent is a specialized GitHub Copilot agent designed to help you work with the Mantis Studio codebase. It has deep knowledge of:

- Streamlit architecture and best practices
- Mantis Studio's session state management patterns
- Common debugging and deployment issues
- Code organization and refactoring strategies
- Performance optimization techniques

## What is a Custom GitHub Copilot Agent?

Custom agents are specialized versions of GitHub Copilot that have been trained on specific instructions and context for your repository. They provide more relevant and accurate suggestions than the general Copilot assistant because they understand your project's architecture, patterns, and conventions.

## How to Access the Agent

### Prerequisites

1. **GitHub Copilot Subscription**: You need an active GitHub Copilot subscription (Individual, Business, or Enterprise)
2. **Repository Access**: The agent is available to anyone with access to this repository
3. **Supported Environments**:
   - GitHub.com web interface
   - GitHub Copilot Chat in VS Code
   - GitHub Copilot Chat in supported IDEs
   - GitHub CLI with Copilot extension

### Method 1: Using on GitHub.com

1. **Navigate to the repository** on GitHub.com
2. **Open GitHub Copilot Chat**:
   - Click the Copilot icon in the top right corner, or
   - Press `Ctrl+Shift+.` (Windows/Linux) or `Cmd+Shift+.` (Mac)
3. **Select the mantis-engineer agent**:
   - Type `@mantis-engineer` in the chat to invoke the agent
   - The agent will appear with its specialized context

### Method 2: Using in VS Code

1. **Install GitHub Copilot Chat extension** (if not already installed)
2. **Open the Mantis Studio repository** in VS Code
3. **Open Copilot Chat**:
   - Press `Ctrl+Alt+I` (Windows/Linux) or `Cmd+Alt+I` (Mac), or
   - Click the chat icon in the sidebar
4. **Invoke the agent**:
   - Type `@mantis-engineer` followed by your question
   - Example: `@mantis-engineer How do I fix session state resets?`

### Method 3: Using with GitHub CLI

1. **Install GitHub CLI** with Copilot extension:
   ```bash
   gh extension install github/gh-copilot
   ```

2. **Use the agent in terminal**:
   ```bash
   gh copilot explain "@mantis-engineer why does my streamlit page show blank?"
   ```

## Common Use Cases

### 1. Debugging Streamlit Issues

**Example Questions:**
- `@mantis-engineer The app shows a blank page. How do I debug this?`
- `@mantis-engineer Help me understand why session state keeps resetting`
- `@mantis-engineer I'm getting widget key collision errors, what's wrong?`

**What the Agent Knows:**
- Common Streamlit rendering issues and solutions
- Session state initialization patterns used in Mantis Studio
- Widget key scoping best practices with `ctx.key_scope()`
- Multi-layer error handling patterns from `app/router.py`

### 2. Code Refactoring

**Example Questions:**
- `@mantis-engineer How should I extract this code from main.py?`
- `@mantis-engineer Show me the proper way to create a new view`
- `@mantis-engineer Help me move this business logic to a service module`

**What the Agent Knows:**
- Current architecture patterns in Mantis Studio
- File organization conventions (`app/views/`, `app/services/`, etc.)
- How to properly use `app/router.py` for navigation
- UI context utilities from `app/ui_context.py`

### 3. Session State Management

**Example Questions:**
- `@mantis-engineer What's the correct way to initialize session state?`
- `@mantis-engineer Show me how to safely access session state variables`
- `@mantis-engineer How do I update state without causing reruns?`

**What the Agent Knows:**
- Proper use of `st.session_state.setdefault()` vs direct assignment
- Session initialization patterns in `app/session_init.py`
- State mutation best practices
- Common state-related pitfalls and how to avoid them

### 4. Deployment and Production Issues

**Example Questions:**
- `@mantis-engineer How do I prepare my code for Streamlit Cloud deployment?`
- `@mantis-engineer What error handling should I add for production?`
- `@mantis-engineer Help me make config loading more robust`

**What the Agent Knows:**
- Production error handling patterns with fallback UI
- Robust file I/O with proper exception handling
- Config loading with safe defaults
- Deployment checklist and common pitfalls

### 5. Performance Optimization

**Example Questions:**
- `@mantis-engineer This string building is slow, how can I optimize it?`
- `@mantis-engineer How do I efficiently build AI prompts?`
- `@mantis-engineer Show me how to cache expensive computations`

**What the Agent Knows:**
- String concatenation optimization (list + join pattern)
- AI prompt building best practices from `app/services/ai.py`
- Streamlit caching strategies
- Performance patterns used throughout the codebase

## Conversation Starters

The agent provides these built-in conversation starters for common scenarios:

1. "How do I debug a blank page in Streamlit?"
2. "Show me how to properly initialize session state"
3. "Help me refactor code from main.py into proper modules"
4. "Why does my session state keep resetting?"
5. "How can I improve deployment reliability?"
6. "What's the proper way to handle errors in Streamlit?"
7. "Help me add error handling to my render function"
8. "How do I prevent widget key collisions?"
9. "Show me the correct way to build AI prompts efficiently"
10. "How do I test my changes before deploying?"

## Tips for Getting Better Results

### Be Specific

❌ **Poor**: "My app doesn't work"
✅ **Good**: "The dashboard page shows blank after I click the navigation button"

❌ **Poor**: "Fix my code"
✅ **Good**: "This session state variable keeps resetting when I navigate between pages. Here's the code: [paste code]"

### Provide Context

When asking questions, mention:
- **What you're trying to do**: "I'm adding a new export format"
- **What's happening**: "The file saves but the UI doesn't update"
- **What you've tried**: "I added st.rerun() but it caused an infinite loop"
- **Relevant file paths**: "The issue is in app/views/export.py line 45"

### Enable Debug Mode First

Before asking about errors, enable debug mode to get better error information:

```python
# In code
st.session_state.debug = True

# Or via environment
export MANTIS_DEBUG=1
```

Then include the debug output in your question to the agent.

### Reference Specific Files

The agent knows the codebase structure, so reference specific files:

```
@mantis-engineer I'm working on app/views/dashboard.py and need to call 
a function from app/services/projects.py. What's the proper import pattern?
```

### Ask for Examples

Request specific code examples:

```
@mantis-engineer Show me an example of a render function with proper 
error handling using the patterns from app/router.py
```

## What the Agent Can Help With

✅ **The agent CAN help with:**
- Debugging Streamlit rendering issues
- Understanding session state management
- Refactoring code following project patterns
- Adding proper error handling
- Optimizing performance
- Preparing code for deployment
- Understanding the codebase architecture
- Following project conventions
- Implementing features using established patterns

❌ **The agent is NOT designed for:**
- General Python questions unrelated to the project
- Non-Streamlit web frameworks
- Database schema design (Mantis Studio uses JSON storage)
- Authentication systems outside OIDC patterns used in the app
- Creating entirely new architectural patterns (stick to established ones)

## Agent Configuration Files

The agent is defined in these files:

1. **`.github/agents/mantis-engineer.yml`**: Main configuration with instructions, capabilities, and conversation starters
2. **`.github/agents/my-agent.agent.md`**: Basic template/stub file

The `.yml` file contains:
- Agent name and description
- Detailed instructions and patterns
- Common use cases and solutions
- Code examples and anti-patterns
- File structure reference
- Conversation starters

## Updating the Agent

If you want to improve or customize the agent:

1. **Edit the configuration**: Modify `.github/agents/mantis-engineer.yml`
2. **Add new patterns**: Include new code patterns or conventions
3. **Update instructions**: Add new use cases or common issues
4. **Commit and push**: Changes take effect after merging to `main` branch
5. **Test the agent**: Verify the agent responds with updated knowledge

## Troubleshooting

### "Agent not found" or "@mantis-engineer" doesn't work

**Solutions:**
1. Ensure you have GitHub Copilot enabled
2. Verify you're in the Mantis Studio repository context
3. Check that the agent file is in the `main` branch
4. Try refreshing your browser or restarting your IDE

### Agent gives generic responses

**Solutions:**
1. Be more specific in your question
2. Mention specific files or error messages
3. Provide code snippets and context
4. Reference the patterns you want to follow

### Agent doesn't know about recent changes

**Solutions:**
1. The agent uses the configuration from the `main` branch
2. Recent changes in your working branch may not be visible
3. Explicitly mention recent changes in your question
4. Consider updating the agent configuration if patterns have changed

## Examples

### Example 1: Debugging a Blank Page

**Question:**
```
@mantis-engineer I'm seeing a blank page when I navigate to the world bible 
section. The terminal shows no errors. How do I debug this?
```

**Expected Response:**
The agent will guide you through:
1. Enabling debug mode
2. Checking for unhandled exceptions
3. Verifying widget key scoping
4. Adding proper error handling with `render_error_fallback`
5. Checking session state initialization

### Example 2: Refactoring Code

**Question:**
```
@mantis-engineer I have inline rendering code in app/main.py around line 2500 
for the export page. How do I properly extract this to app/views/export.py?
```

**Expected Response:**
The agent will provide:
1. Step-by-step extraction process
2. Proper function signature with context parameter
3. How to register the route in `app/router.py`
4. Key scoping pattern to use
5. Error handling to include

### Example 3: Session State Issue

**Question:**
```
@mantis-engineer My session state variable `current_chapter` keeps resetting 
to None when I navigate between pages. Here's my initialization code:

st.session_state.current_chapter = None

What am I doing wrong?
```

**Expected Response:**
The agent will explain:
1. The problem: direct assignment overwrites existing values
2. The solution: use `st.session_state.setdefault("current_chapter", None)`
3. Where to put initialization: `app/session_init.py`
4. Pattern to follow from existing code
5. Related best practices

## Additional Resources

- **[Getting Started Guide](GETTING_STARTED.md)**: New user onboarding
- **[Contributing Guide](CONTRIBUTING.md)**: Development setup and practices
- **[Debugging Guide](DEBUGGING.md)**: Comprehensive debugging steps
- **[Stabilization Implementation Guide](../architecture/STABILIZATION_IMPLEMENTATION_GUIDE.md)**: Complete stabilization guide with patterns and usage

## Support

If you have questions about using the agent that aren't covered here:

1. **Open an issue**: [GitHub Issues](https://github.com/bigmanjer/Mantis-Studio/issues)
2. **Check existing docs**: Review other guides in `docs/guides/`
3. **Ask the agent**: Use `@mantis-engineer` for questions about the agent itself

---

*Last Updated: February 2026*
