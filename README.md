# GTM Brain

A lead scoring and outreach system that reads a list of leads, scores each one Hot/Warm/Cold against specific ICP using Claude AI, and drafts a personalized first-touch email for every Hot lead. It replaces manual rep research and gut-feel prioritization with a consistent, auditable scoring process.

---

## What the Output Looks Like

Results are saved to `outputs/scored_leads.csv`. Every row from the input gets three new columns appended:

| Field | Example |
|---|---|
| `score` | `Hot` |
| `reason` | Director of Facilities at an 850-person manufacturer with a maintenance coordinator job posting and 47 site visits in 30 days — strong ICP fit with clear buying signal. |
| `outreach_email` | **Subject:** Maintenance ops at Apex — quick question // Hi Diana, noticed Apex is hiring a Maintenance Coordinator... |

Hot leads get a full email draft. Warm and Cold leads get a score and reason only.

---

## Setup

### 1. Clone and enter the project

```bash
cd gtm-brain
```

### 2. Create a virtual environment

```bash
python3 -m venv venv
source venv/bin/activate
```

You'll need to run `source venv/bin/activate` each time you open a new terminal session before running the script.

### 3. Install dependencies

```bash
pip install anthropic
```

### 4. Set your API key

Get a key at [console.anthropic.com](https://console.anthropic.com) → API Keys. Then set it in your terminal:

```bash
export ANTHROPIC_API_KEY=your-key-here...
```

This only lasts for the current terminal session. To make it permanent, add that line to your `~/.zshrc` or `~/.bash_profile`.

### 5. Run the script

```bash
python3 scripts/score_leads.py
```

You'll see live progress in the terminal. Results land in `outputs/scored_leads.csv` when done.

---

## File Structure

```
gtm-brain/
├── CLAUDE.md               Project context and rules for Claude Code
├── ARCHITECTURE.md         Technical reference — how the system works
├── PROBLEM_STATEMENT.md    Business case and design decisions
├── SKILL.md                Operational playbook — how to run and tune the system
├── GOTCHAS.md              Issues encountered and how they were fixed
├── README.md               This file
│
├── data/
│   └── dummy_leads.csv     Input leads — edit this to change who gets scored
│
├── scripts/
│   └── score_leads.py      The script — don't edit unless changing how it works
│
└── outputs/
    └── scored_leads.csv    Generated results — safe to open, sort, and share
```

---

## How to Update the Scoring Criteria

You do not need to touch code to change how leads are scored. All ICP logic lives in the prompt inside `scripts/score_leads.py`.

Open the file and find the block that starts with:

```python
ICP_SCORING_PROMPT = """You are a GTM analyst...
```

Inside that block you'll see sections for ideal buyer titles, ideal industries, company size ranges, buying signals, and disqualifiers. Edit those sections in plain English — the model will apply your updated criteria on the next run.

**Example:** To add "property management" as a target industry, find the industries list and add it. To make government leads Warm instead of Cold, update the disqualifiers section. No coding required.

---

## How to Swap In Real Leads

1. Open `data/dummy_leads.csv` in Excel or Google Sheets
2. Delete the dummy rows (keep the header row)
3. Paste in your real leads — the column headers must match exactly:

```
company_name, contact_name, title, industry, company_size,
recent_signal, website_visits_last_30_days, current_solution, notes
```

4. Save as CSV (not .xlsx)
5. Run the script — results will overwrite `outputs/scored_leads.csv`

If a field is unknown for a lead, leave it blank. The model handles missing data gracefully and will note the gap in its reasoning.
