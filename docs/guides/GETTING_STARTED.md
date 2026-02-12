# 🚀 Getting Started with Mantis Studio

Welcome to **Mantis Studio**! This guide will help you get up and running in just a few minutes.

## What is Mantis Studio?

Mantis Studio is an AI-powered writing environment designed for novelists, screenwriters, and creative writers. Think of it as your all-in-one workspace where you can:

- **Plan your story** with AI-assisted outlining
- **Write chapters** in a distraction-free editor
- **Build your world** by tracking characters, locations, and lore
- **Export your work** to Word, PDF, or text files

No more juggling between notes apps, Google Docs, and ChatGPT—everything lives in one place.

---

## Prerequisites

Before you begin, make sure you have:

- [ ] **Python 3.10 or newer** installed on your computer
  - Check by running: `python --version` or `python3 --version`
  - [Download Python here](https://www.python.org/downloads/) if needed
  
- [ ] **Basic command line knowledge** (don't worry, we'll guide you!)
  - Know how to open Terminal (Mac/Linux) or Command Prompt (Windows)
  - Know how to navigate to a folder with `cd`

- [ ] **(Optional) AI API Key** if you want AI writing assistance
  - We support [Groq](https://groq.com) (free tier available) or [OpenAI](https://openai.com)
  - You can use Mantis Studio without AI, but you'll miss out on cool features!

---

## Installation (Step-by-Step)

### Step 1: Download Mantis Studio

**Option A: Download ZIP** (Easiest for beginners)
1. Go to https://github.com/bigmanjer/Mantis-Studio
2. Click the green "Code" button
3. Select "Download ZIP"
4. Extract the ZIP file to a folder like `Documents/Mantis-Studio`

**Option B: Clone with Git** (If you know Git)
```bash
git clone https://github.com/bigmanjer/Mantis-Studio.git
cd Mantis-Studio
```

---

### Step 2: Open Your Terminal/Command Prompt

- **Windows**: Press `Win + R`, type `cmd`, press Enter
- **Mac**: Press `Cmd + Space`, type "Terminal", press Enter
- **Linux**: Press `Ctrl + Alt + T`

Navigate to where you downloaded Mantis Studio:
```bash
cd path/to/Mantis-Studio
```

💡 **Tip**: On Windows/Mac, you can often drag the folder into Terminal to auto-fill the path!

---

### Step 3: Set Up Python Environment

This creates a safe, isolated space for Mantis Studio's dependencies:

**On Windows:**
```bash
python -m venv .venv
.venv\Scripts\activate
```

**On Mac/Linux:**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

You should see `(.venv)` appear at the start of your command line. This means it worked! ✅

---

### Step 4: Install Dependencies

Now we'll install everything Mantis Studio needs to run:

```bash
pip install -r requirements.txt
```

This might take 1-2 minutes. You'll see a bunch of packages being downloaded—that's normal!

**Troubleshooting:**
- If you get "pip not found", try `python -m pip install -r requirements.txt`
- If you see permission errors on Mac/Linux, try adding `--user` flag
- If installation fails, check that you're inside the Mantis-Studio folder

---

### Step 5: Launch Mantis Studio

**Option A: Use the Launcher (Windows Only)**
```bash
Mantis_Launcher.bat
```
This gives you a cool animated startup screen and auto-opens your browser!

**Option B: Manual Launch (All Platforms)**
```bash
streamlit run app/main.py
```

After a few seconds, your browser should automatically open to `http://localhost:8501`

If it doesn't, manually open your browser and go to that address.

---

## First Time Setup

### Welcome to Mantis Studio! 🎉

When you first open the app, you'll see:

1. **Sidebar on the left** with navigation (Dashboard, Projects, Outline, etc.)
2. **Main area** showing your Dashboard

Your work saves locally on your computer. Start creating right away!

---

## Your First Project

Let's create your first story project:

### Step 1: Create a New Project

1. Click **"📁 Projects"** in the sidebar
2. Click the **"➕ Create New Project"** button
3. Enter a project name (e.g., "My First Novel")
4. Click **"Create"**

### Step 2: Build Your Outline

1. Click **"📋 Outline"** in the sidebar
2. Describe your story idea in a sentence or two
3. (If you have an AI key) Click **"Generate Outline"** for AI suggestions
4. (If not) Manually add acts, chapters, or scenes

### Step 3: Start Writing

1. Click **"✏️ Chapters / Editor"** in the sidebar
2. Select a chapter from your outline
3. Start typing in the editor!
4. Use the AI tools on the right for help (if you set up AI)

### Step 4: Build Your World

1. Click **"🌍 World Bible"** in the sidebar
2. Add characters, locations, or lore
3. Keep everything organized in one place

### Step 5: Export Your Work

1. Click **"📤 Export"** in the sidebar
2. Choose your format (Word, PDF, or TXT)
3. Download your manuscript!

---

## Setting Up AI Features (Optional)

AI writing assistance makes Mantis Studio truly powerful. Here's how to enable it:

### Getting an API Key

**Option 1: Groq (Recommended for beginners)**
1. Go to https://console.groq.com
2. Sign up for a free account
3. Navigate to "API Keys" in the dashboard
4. Click "Create API Key"
5. Copy the key (it looks like `gsk_...`)

**Option 2: OpenAI (More powerful, costs money)**
1. Go to https://platform.openai.com
2. Create an account
3. Add payment method (pay-as-you-go)
4. Create an API key
5. Copy the key (it looks like `sk-...`)

### Adding the Key to Mantis Studio

**Method 1: Environment File** (Recommended)

1. Create a new file in the Mantis-Studio folder named `.env`
2. Add your key:
   ```
   GROQ_API_KEY=gsk_your_key_here
   ```
   OR
   ```
   OPENAI_API_KEY=sk_your_key_here
   ```
3. Save the file
4. Restart Mantis Studio

**Method 2: Streamlit Secrets** (More secure)

1. Create folder: `.streamlit` in the Mantis-Studio folder
2. Create file: `.streamlit/secrets.toml`
3. Add your key:
   ```toml
   GROQ_API_KEY = "gsk_your_key_here"
   ```
   OR
   ```toml
   OPENAI_API_KEY = "sk_your_key_here"
   ```
4. Save and restart Mantis Studio

Now you can use AI features like:
- **Generate Outline** from a story idea
- **Expand Scene** to add more detail
- **Rewrite** to change tone or style
- **Brainstorm** for new plot ideas

---

## Understanding the Interface

### Sidebar Sections

| Section | What It Does |
|---------|--------------|
| 🏠 **Dashboard** | Overview of your project's progress |
| 📁 **Projects** | Create, switch, or manage projects |
| 📋 **Outline** | Plan your story structure |
| ✏️ **Chapters** | Write and edit your manuscript |
| 🌍 **World Bible** | Track characters, places, and lore |
| 🤖 **AI Tools** | Quick AI utilities (rewrite, summarize, etc.) |
| 📤 **Export** | Download your work as a file |
| ⚖️ **Legal** | Terms and privacy information |

### Tips for Navigation

- Your current section is highlighted in the sidebar
- All your work auto-saves as you type
- Use the project selector to switch between stories
- Check the version number in the UI header to see which version you're running

---

## Common Questions

### "The app won't start"

**Check these:**
1. Did you activate the virtual environment? (You should see `(.venv)` in your terminal)
2. Did you install dependencies? Try running `pip install -r requirements.txt` again
3. Is Streamlit installed? Try `pip install streamlit --upgrade`
4. Try running with verbose errors: `streamlit run app/main.py --logger.level=debug`

### "I don't see my AI features working"

**Check these:**
1. Did you add your API key to `.env` or `.streamlit/secrets.toml`?
2. Did you restart Mantis Studio after adding the key?
3. Is your API key valid? (Check on the provider's website)
4. Do you have credits/quota remaining on your API account?

### "Where are my files saved?"

- Projects are saved in the `projects/` folder inside Mantis-Studio
- Each project is a separate folder with JSON files
- You can back up by copying the entire `projects/` folder

### "Can I use this offline?"

- Yes! The app works completely offline for writing and editing
- AI features require internet (they call external APIs)
- Your data stays on your computer—we don't upload anything

### "How do I update to the latest version?"

If you downloaded as ZIP:
1. Download the new ZIP from GitHub
2. Copy your `projects/` folder to the new version
3. Re-run the installation steps

If you cloned with Git:
```bash
git pull origin main
pip install -r requirements.txt --upgrade
```

---

## Next Steps

Now that you're set up, try these:

1. 📖 Read the full [README.md](../../README.md) for advanced features
2. 🎨 Check out [DESIGN_SYSTEM.md](../design/DESIGN_SYSTEM.md) to understand the UI
3. 🐛 Found a bug? [Open an issue](https://github.com/bigmanjer/Mantis-Studio/issues)

---

## Need Help?

- **Documentation**: Check the `/docs` folder for detailed guides
- **Issues**: Report bugs or request features on [GitHub Issues](https://github.com/bigmanjer/Mantis-Studio/issues)
- **Community**: (Coming soon) Discord/forum for users

---

## What to Expect

Mantis Studio is actively being improved! Here's what you might notice:

✅ **Working well:**
- Project creation and management
- Writing and editing chapters
- World Bible for organizing your story elements
- Export to Word/TXT formats

🚧 **Still being polished:**
- Some AI features may be experimental
- UI improvements are ongoing

We're committed to making this the best writing environment possible. Your feedback helps!

---

**Ready to start writing? Let's go! 🚀**

*For version information, check the VERSION.txt file or the app header.*
