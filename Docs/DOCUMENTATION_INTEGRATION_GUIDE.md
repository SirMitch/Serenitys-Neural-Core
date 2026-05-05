# DOCUMENTATION VIEWER INTEGRATION - Setup & Usage Guide

## What's New

The Neural AI Loader now includes an **integrated documentation viewer** directly in the main menu with smart navigation. No need to open separate files!

### New Features

✅ **Integrated Help Menu** - Access all docs from main menu  
✅ **Dynamic Document Scanning** - Automatically finds docs in root\docs  
✅ **Smart Categorization** - Documents auto-organized by type  
✅ **Interactive Paging** - Navigate long documents page by page  
✅ **Full Navigation** - Back/Main Menu options throughout  
✅ **Auto-discovery** - Works with .md and .txt files  

---

## Directory Structure

```
ProjectRoot/
├── neural_ai_loader.py
├── logs/                    (auto-created)
├── docs/                    (NEW - create this folder)
│   ├── README.md
│   ├── QUICK_START.md
│   ├── TROUBLESHOOTING.md
│   ├── GUIDE_*.md
│   └── ... (any .txt or .md files)
└── tools/
    ├── logging_helper.py
    ├── nav_helper.py
    ├── system_info_helper.py
    ├── doc_viewer.py        (NEW)
    ├── ollama_helper.py
    ├── interpreter_helper.py
    ├── openhands_helper.py
    ├── configure_agent.py
    └── gather_system_info.ps1
```

---

## Setup Instructions

### Step 1: Create Docs Directory

```bash
# Create docs folder at project root
mkdir ProjectRoot\docs

# Copy your documentation files there
# Supported formats: .md (Markdown) and .txt (Text)
```

### Step 2: Add Documentation Files

Place any documentation files in the docs\ directory:

```
docs/
├── README.md
├── QUICK_START.md
├── GUIDE_Installation.md
├── GUIDE_Configuration.md
├── TROUBLESHOOTING.md
├── FAQ.md
└── ... (any .txt or .md files)
```

**File Naming Tips:**
- Use descriptive names (QUICK_START, GUIDE_*, TROUBLESHOOTING, etc.)
- Start names with prefixes for auto-categorization:
  - `README`, `START`, `QUICK` → "Getting Started"
  - `GUIDE`, `HOW`, `MANUAL` → "Guides"
  - `REFERENCE`, `IMPLEMENTATION` → "Reference"
  - `TROUBLE`, `DEBUG`, `ERROR` → "Troubleshooting"
  - Other names → "Other" category

### Step 3: Copy New Files

Copy these new/updated files to your tools\ directory:

```
tools/
├── doc_viewer.py           (NEW - documentation viewer)
├── neural_ai_loader.py     (UPDATED - integrated menu)
└── ... (other existing files unchanged)
```

---

## Usage

### From Main Menu

```
┌──────────────────────────────────────────┐
│  Neural AI Loader                        │
├──────────────────────────────────────────┤
│                                          │
│  Main Menu:                              │
│                                          │
│  1) Start AI Session (New Run)           │
│  2) Documentation & Help (5 files)       │
│  3) Quit                                 │
│                                          │
│  Select option (1-3): 2                  │
└──────────────────────────────────────────┘
```

### Documentation Menu

```
┌──────────────────────────────────────────┐
│  DOCUMENTATION & GUIDES                  │
├──────────────────────────────────────────┤
│                                          │
│  Available Documents: 5                  │
│                                          │
│  ── Getting Started ──                   │
│  1) README.md                            │
│  2) QUICK_START.md                       │
│                                          │
│  ── Guides ──                            │
│  3) GUIDE_Installation.md                │
│  4) GUIDE_Configuration.md               │
│                                          │
│  ── Troubleshooting ──                   │
│  5) TROUBLESHOOTING.md                   │
│                                          │
│  B) Back to Main Menu                    │
│  Q) Quit Program                         │
│                                          │
│  Select document or option: 1            │
└──────────────────────────────────────────┘
```

### Reading Documents

```
┌──────────────────────────────────────────┐
│  DOCUMENT: README.md                     │
├──────────────────────────────────────────┤
│                                          │
│  [Document content here...]              │
│                                          │
│  [Page content, 18 lines per page]       │
│                                          │
├──────────────────────────────────────────┤
│  Page 1 of 3                             │
│                                          │
│  N) Next   B) Back to Docs Menu   Q) Quit│
│                                          │
│  Choose: N                               │
└──────────────────────────────────────────┘
```

---

## Navigation System

### Main Menu → Options
- **1** - Start AI Session
  - Follows original flow (system info → backend → interpreter → model → launch)
  - **M** option at each step returns to main menu
  - **B** option goes back to previous step
  
- **2** - Documentation & Help
  - Shows all available docs organized by category
  - Select any document to read
  - Use **N/P** to navigate pages
  - **B** returns to docs menu
  - **Q** quits program

- **3** - Quit
  - Exits the program gracefully

---

## Document Viewer Features

### Smart Categorization

Documents are automatically sorted into categories based on filename:

| Category | Keywords | Example Files |
|----------|----------|---|
| Getting Started | START, QUICK, README | README.md, QUICK_START.md |
| Guides | GUIDE, HOW, MANUAL | GUIDE_Installation.md |
| Reference | REFERENCE, IMPLEMENTATION | IMPLEMENTATION_SUMMARY.md |
| Troubleshooting | TROUBLE, DEBUG, ERROR | TROUBLESHOOTING.md |
| Other | (other filenames) | FAQ.md, NOTES.txt |

### Page Navigation

- **N** - Next page (if available)
- **P** - Previous page (if available)
- **B** - Back to documentation menu
- **Q** - Quit program

### File Support

- **.md** (Markdown files)
- **.txt** (Text files)
- Both displayed as plain text with line wrapping
- Pagination: 18 lines per page (customizable)

---

## Example Workflow

### First-Time User Workflow

```
1. Run: python neural_ai_loader.py
   ↓
2. Enable debug? (y/n): n
   ↓
3. Main Menu appears
   ↓
4. Select: 2 (Documentation & Help)
   ↓
5. See: QUICK_START.md and other guides
   ↓
6. Read through Getting Started section
   ↓
7. Select: B (Back to Main Menu)
   ↓
8. Select: 1 (Start AI Session)
   ↓
9. Follow system info → model selection → launch
```

### Troubleshooting Workflow

```
1. Running session → Error occurs
   ↓
2. User Ctrl+C or quits
   ↓
3. Returned to Main Menu
   ↓
4. Select: 2 (Documentation)
   ↓
5. Open: TROUBLESHOOTING.md
   ↓
6. Find answer to issue
   ↓
7. Back to main menu, try again
```

---

## Creating Documentation Files

### Markdown Format

```markdown
# Installation Guide

## Step 1: Prerequisites

You will need:
- Python 3.8+
- Ollama

## Step 2: Setup

Copy files to project...

## Troubleshooting

If something goes wrong...
```

### Text Format

```
INSTALLATION GUIDE
==================

STEP 1: Prerequisites
You will need:
- Python 3.8+
- Ollama

STEP 2: Setup
Copy files to project...
```

### Formatting Tips

- Use clear headers (# or ===)
- Keep lines to ~80 characters
- Use lists for readability
- One topic per file (easier to navigate)

---

## Logging

All documentation viewer activity is logged:

```
[14:30:23] [INFO   ] [DOCVIEWER          ] Documentation system ready (5 files)
[14:30:24] [INFO   ] [DOCVIEWER          ] User opened main help menu
[14:30:25] [DEBUG  ] [DOCVIEWER          ] Read document: QUICK_START.md
[14:30:26] [INFO   ] [DOCVIEWER          ] User returned to main menu from docs
```

### Log Files
- `logs/neural_ai_*.log` - Full documentation viewer activity
- `logs/errors_*.log` - Any errors reading or displaying docs

---

## Troubleshooting Documentation System

### "Documentation directory not found"

**Cause:** No `docs\` folder in project root

**Solution:**
```bash
mkdir ProjectRoot\docs
# Copy .md or .txt files there
```

### "No documentation files found"

**Cause:** docs\ folder is empty

**Solution:**
1. Copy documentation files to docs\ folder
2. Ensure files have .md or .txt extension
3. Verify filenames don't start with _ (underscore)

### "Files not showing in alphabetical order"

**Files are categorized by:**
1. File content keywords in name
2. Alphabetical within category
3. Categories: Getting Started, Guides, Reference, Troubleshooting, Other

### "Long document won't fit on screen"

**Feature:** Documents auto-paginate at 18 lines per page

**Navigation:**
- Use **N** for next page
- Use **P** for previous page
- Use **B** to go back to menu

---

## Advanced: Customize Categorization

Edit `tools/doc_viewer.py` line ~100 to change keywords:

```python
keywords = {
    "Getting Started": ["START", "QUICK", "README"],
    "Guides": ["GUIDE", "HOW", "MANUAL"],
    "Reference": ["REFERENCE", "API", "IMPLEMENTATION"],
    "Troubleshooting": ["TROUBLE", "DEBUG", "ERROR"],
}
```

Add or modify category keywords to auto-organize your docs differently.

---

## Integration with Existing Docs

### Already Have Documentation?

If you already have documentation files:

```bash
# Move them to docs folder
mv your_docs/* ProjectRoot\docs\

# Rename if needed for auto-categorization
# e.g., README.txt → START_HERE.md
```

### Multiple Formats?

- Convert .docx, .pdf → .txt or .md
- Existing .md files work as-is
- Plain text files (.txt) supported

---

## Performance Notes

- **Scanning:** Fast (sub-second for <100 files)
- **Display:** Instant (text is read on demand)
- **Navigation:** No lag (pagination is local)
- **Memory:** Minimal (only current page loaded)

---

## Complete File List (With Integration)

```
tools/
├── logging_helper.py       ✓ (unchanged)
├── nav_helper.py           ✓ (unchanged)
├── system_info_helper.py   ✓ (unchanged)
├── ollama_helper.py        ✓ (unchanged)
├── interpreter_helper.py   ✓ (unchanged)
├── openhands_helper.py     ✓ (unchanged)
├── configure_agent.py      ✓ (unchanged)
├── gather_system_info.ps1  ✓ (unchanged)
└── doc_viewer.py           ✨ (NEW)

root/
├── neural_ai_loader.py     ✨ (UPDATED)
├── logs/                   ✓ (auto-created)
└── docs/                   ✨ (NEW - you create this)
```

---

## Summary

The documentation viewer is now **fully integrated** into Neural AI Loader's main menu. Users can:

1. ✅ Access help directly from the program
2. ✅ Browse all documentation in one place
3. ✅ Navigate between pages easily
4. ✅ Return to main menu or quit anytime
5. ✅ See all activity logged

**No external files to open - everything is in-program!**

---

**Version:** 2.1 (With Integrated Documentation)  
**Status:** Ready for Deployment ✅
