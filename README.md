# GTM Brain

An AI-powered GTM intelligence layer that scores inbound leads, outbound leads, and free trial users using Claude AI, routes each to the correct GTM motion, and drafts personalized outreach where applicable. Runs as a five-page Flask web UI — no terminal required for day-to-day use.

---

## System Overview

Three scoring scripts unified under a Flask web interface:

| Script | What it does |
|---|---|
| `scripts/score_leads.py` | Scores inbound and outbound leads Hot/Warm/Cold against ICP; drafts personalized first-touch emails for Hot leads |
| `scripts/score_trials.py` | Two-dimensional scoring of free trial users on ICP fit AND behavioral engagement; routes to AE fast-track, BDR sequence, CS monitoring, or suppression |
| `scripts/run_gtm_engine.py` | Orchestrator that runs both scoring scripts in sequence and produces a unified full-funnel report |

All three are accessible from the Flask UI without touching the terminal.

---

## The Five Pages

| Page | What it does |
|---|---|
| **Dashboard** | At-a-glance summary of recent scoring runs — Hot/Warm/Cold counts, routing distribution, last run timestamp |
| **Lead Scoring** | Run `score_leads.py` from the browser, view results in a sortable table, export to CSV |
| **Trial Conversion** | Run `score_trials.py` from the browser, view two-dimensional scores and routing actions, export to CSV |
| **Full Funnel** | Run `run_gtm_engine.py` from the browser, view the unified cross-funnel report |
| **ICP Settings** | Edit scoring criteria — target industries, company size range, ideal titles, buying signals, disqualifiers — via a form. Saves to `config/icp_config.json`. No code required. |

---

## How to Run

### 1. Clone and enter the project

```bash
cd gtm-lead-scoring-engine
```

### 2. Create a virtual environment

```bash
python3 -m venv venv
source venv/bin/activate
```

Run `source venv/bin/activate` each time you open a new terminal session.

### 3. Install dependencies

```bash
pip install anthropic flask
```

### 4. Set your API key

Get a key at [console.anthropic.com](https://console.anthropic.com) → API Keys. Then:

```bash
export ANTHROPIC_API_KEY=your-key-here
```

To make it permanent, add that line to your `~/.zshrc` or `~/.bash_profile`.

### 5. Start the web UI

```bash
python3 app.py
```

Then open [http://localhost:5000](http://localhost:5000) in your browser.

---

## How to Run Scripts Directly from the Terminal

If you prefer to run scripts without the UI:

```bash
# Score leads only
python3 scripts/score_leads.py

# Score trial users only
python3 scripts/score_trials.py

# Run full-funnel engine (runs both scripts, produces unified report)
python3 scripts/run_gtm_engine.py
```

Results are written to `outputs/` in all cases.

---

## Output Format

### Lead scoring output (`outputs/scored_leads.csv`)

| Field | Example |
|---|---|
| `score` | `Hot` |
| `reason` | Director of Facilities at an 850-person manufacturer with a maintenance coordinator job posting and 47 site visits in 30 days — strong ICP fit with clear buying signal. |
| `outreach_email` | **Subject:** Maintenance ops at Apex — quick question // Hi Diana... |
| `priority_flag` | `speed-to-lead` |

### Trial scoring output (`outputs/scored_trials.csv`)

| Field | Example |
|---|---|
| `icp_score` | `Strong` |
| `engagement_score` | `High` |
| `routing_action` | `AE Fast-Track` |
| `reason` | Strong ICP fit + high engagement — demo request + 12 work orders created in trial. |

---

## File Structure

```
gtm-lead-scoring-engine/
├── CLAUDE.md                   Project context and rules for Claude Code
├── ARCHITECTURE.md             Technical reference — how the system works
├── PROBLEM_STATEMENT.md        Business case and design decisions
├── ROADMAP.md                  V1 through V4 product roadmap
├── SKILL.md                    GTM playbook — how to run and tune the system
├── GOTCHAS.md                  Issues encountered and how they were fixed
├── README.md                   This file
│
├── app.py                      Flask application — routes, UI logic, subprocess calls
│
├── templates/                  Jinja2 HTML templates
│   ├── base.html               Shared layout and navigation
│   ├── dashboard.html          Dashboard page
│   ├── leads.html              Lead Scoring page
│   ├── trials.html             Trial Conversion page
│   ├── funnel.html             Full Funnel page
│   └── settings.html           ICP Settings page
│
├── static/                     CSS and frontend assets
│   └── style.css
│
├── config/
│   └── icp_config.json         Editable ICP criteria — readable and writable by the UI
│
├── data/
│   ├── dummy_leads.csv         Input leads — edit to change who gets scored
│   └── dummy_trials.csv        Input trial users with Mixpanel behavioral data
│
├── scripts/
│   ├── score_leads.py          Lead scoring script
│   ├── score_trials.py         Trial user scoring script
│   └── run_gtm_engine.py       Full-funnel orchestrator
│
└── outputs/
    ├── scored_leads.csv        Lead scoring results
    ├── scored_trials.csv       Trial scoring results
    └── full_funnel_report.csv  Unified cross-funnel report
```

---

## How to Update Scoring Criteria

### Via the UI (recommended)

Go to the **ICP Settings** page in the web UI. Edit the criteria fields and click Save. Changes take effect on the next scoring run. No code required.

### Via the config file directly

Open `config/icp_config.json` and edit in plain text. The scoring scripts read from this file at runtime.

---

## How to Swap In Real Data

1. Open `data/dummy_leads.csv` in Excel or Google Sheets
2. Delete the dummy rows (keep the header row)
3. Paste in your real leads — column headers must match:

```
company_name, contact_name, title, industry, company_size,
recent_signal, website_visits_last_30_days, current_solution,
offer_type, inbound_channel, notes
```

4. Save as CSV (not .xlsx)
5. Run from the Lead Scoring page or via terminal

If a field is unknown, leave it blank. The model handles missing data and will note the gap in its reasoning.
