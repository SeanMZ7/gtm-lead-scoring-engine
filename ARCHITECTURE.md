# ARCHITECTURE.md

---

## 1. PROJECT STRUCTURE

```
gtm-lead-scoring-engine/
│
├── CLAUDE.md                   # Project context and working rules for Claude Code
├── ARCHITECTURE.md             # This file — technical reference for the system
├── PROBLEM_STATEMENT.md        # Business case, design decisions, and future roadmap
├── ROADMAP.md                  # V1 through V4 product roadmap
├── GOTCHAS.md                  # Issues encountered, fixes applied, lessons learned
├── SKILL.md                    # GTM playbook (prompt patterns, scoring rationale)
├── README.md                   # Quick-start guide and output format reference
│
├── app.py                      # Flask application — routes, UI logic, subprocess calls
│
├── templates/                  # Jinja2 HTML templates
│   ├── base.html               # Shared layout and navigation
│   ├── dashboard.html          # Dashboard page
│   ├── leads.html              # Lead Scoring page
│   ├── trials.html             # Trial Conversion page
│   ├── funnel.html             # Full Funnel page
│   └── settings.html           # ICP Settings page
│
├── static/                     # CSS and frontend assets
│   └── style.css
│
├── config/
│   └── icp_config.json         # Editable ICP criteria — readable and writable by the UI
│
├── data/
│   ├── dummy_leads.csv         # 10 hand-crafted leads covering good/borderline/off-ICP cases
│   └── dummy_trials.csv        # 12 mock trial users with Mixpanel behavioral data
│
├── scripts/
│   ├── score_leads.py          # Entry point — reads leads, calls Claude API, writes output
│   ├── score_trials.py         # Trial scoring — two-dimensional ICP fit + engagement
│   └── run_gtm_engine.py       # Orchestrator — runs both scripts, produces unified report
│
├── outputs/
│   ├── .gitkeep                # Keeps outputs/ tracked by git when empty
│   ├── scored_leads.csv        # Lead scoring output
│   ├── scored_trials.csv       # Trial scoring output
│   └── full_funnel_report.csv  # Unified cross-funnel report
│
└── venv/                       # Python virtual environment (not committed)
```

---

## 2. HIGH-LEVEL SYSTEM DIAGRAM

```
┌──────────────────────────────────────────────────────────────────────┐
│                         FLASK WEB UI (app.py)                        │
│                                                                      │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌────────────┐  │
│  │  Dashboard  │  │Lead Scoring │  │   Trial     │  │    ICP     │  │
│  │             │  │             │  │ Conversion  │  │  Settings  │  │
│  └─────────────┘  └──────┬──────┘  └──────┬──────┘  └─────┬──────┘  │
│                          │                │               │          │
│             ┌────────────┘    ┌───────────┘               │          │
│             ▼                 ▼                           ▼          │
│     subprocess call   subprocess call           writes/reads         │
│             │                 │             config/icp_config.json   │
└─────────────┼─────────────────┼────────────────────────────────────-─┘
              │                 │
              ▼                 ▼
┌─────────────────────┐   ┌─────────────────────┐
│   score_leads.py    │   │   score_trials.py    │
│                     │   │                      │
│  data/              │   │  data/               │
│  dummy_leads.csv    │   │  dummy_trials.csv    │
│       │             │   │       │              │
│       ▼             │   │       ▼              │
│  ICP Scoring        │   │  Two-dimensional     │
│  Prompt + Lead      │   │  Scoring Prompt      │
│  Data               │   │  (ICP fit +          │
│       │             │   │   engagement)        │
│       ▼             │   │       │              │
│  Claude API         │   │  Claude API          │
│  claude-sonnet-4-6  │   │  claude-sonnet-4-6   │
│       │             │   │       │              │
│       ▼             │   │       ▼              │
│  outputs/           │   │  outputs/            │
│  scored_leads.csv   │   │  scored_trials.csv   │
└─────────────────────┘   └─────────────────────┘
              │                 │
              └────────┬────────┘
                       │
                       ▼
           ┌─────────────────────────┐
           │   run_gtm_engine.py     │
           │                         │
           │  Runs both scripts      │
           │  in sequence, merges    │
           │  outputs into unified   │
           │  full_funnel_report.csv │
           └─────────────────────────┘
                       │
                       ▼
           ┌─────────────────────────┐
           │  Flask reads CSV        │
           │  → renders HTML table   │
           │  → browser displays     │
           └─────────────────────────┘
```

---

## 3. CORE COMPONENTS

### Flask UI (`app.py`) — Web Interface Layer
- **What it does:** Serves the five-page internal tool. Routes map to pages; run actions call the scoring scripts via `subprocess`. Results are read from output CSVs and passed to Jinja2 templates for rendering.
- **Routes:** `/` (dashboard), `/leads` (lead scoring), `/trials` (trial conversion), `/funnel` (full funnel), `/settings` (ICP settings)
- **Data flow:** Browser request → Flask route → subprocess call → script executes → output CSV written → Flask reads CSV → renders HTML table

### `config/icp_config.json` — ICP Configuration
- **What it does:** Stores editable ICP criteria in JSON: target industries, company size range, ideal titles, buying signals, and disqualifiers. Readable and writable by the ICP Settings page — no code changes required.
- **Consumed by:** `score_leads.py` and `score_trials.py` at runtime

### `load_leads(path)` — Data Ingestion
- **What it does:** Reads the input CSV into memory as a list of dicts
- **Input:** Path to `data/dummy_leads.csv` or `data/dummy_trials.csv`
- **Output:** `list[dict]` — one dict per row, keys are CSV column headers

### `ICP_SCORING_PROMPT` — Scoring Rubric
- **What it does:** Defines ICP criteria, scoring tiers, and output format in natural language. This is the intelligence layer — all scoring logic lives here, not in code.
- **Input:** Lead data formatted as a `- key: value` list (via `format_lead()`)
- **Output:** A filled prompt string ready to send to the Claude API

### `score_lead(client, lead)` — API Orchestration
- **What it does:** Sends one lead to Claude, receives a structured JSON response, strips any markdown fencing, and parses the result
- **Input:** An `anthropic.Anthropic` client instance + one lead dict
- **Output:** `dict` with keys `score`, `reason`, `outreach_email`, `priority_flag`

### `score_trial(client, trial)` — Trial API Orchestration
- **What it does:** Sends one trial user to Claude with a two-dimensional scoring prompt (ICP fit + behavioral engagement), parses the result into routing tier
- **Input:** An `anthropic.Anthropic` client instance + one trial user dict
- **Output:** `dict` with keys `icp_score`, `engagement_score`, `routing_action`, `reason`, `outreach_email`

### `save_results(leads, results, output_path)` — Output Writer
- **What it does:** Merges original data with scoring results and writes to CSV. Collects all unique fieldnames across both datasets before writing to handle schema differences between leads and trials.
- **Input:** Original data list, results list (same order), output file path
- **Output:** CSV with all original columns plus scoring result columns

### `main()` — Entry Point & Orchestrator
- **What it does:** Validates the API key, loads data, iterates calling the scoring function for each record, prints progress to stdout, calls `save_results()`, and prints a final summary
- **Input:** `ANTHROPIC_API_KEY` environment variable
- **Output:** Populated output CSV + terminal summary

---

## 4. DATA FLOW

```
Browser Request
  User clicks "Run Lead Scoring" on the Flask UI

Flask Route (/leads/run)
  app.py receives the POST request
  Calls subprocess.run(["python3", "scripts/score_leads.py"])

Script Execution (score_leads.py)
  Step 1 — Startup
    main() checks os.environ for ANTHROPIC_API_KEY
    Raises EnvironmentError immediately if missing
    Loads icp_config.json for scoring criteria

  Step 2 — Load
    load_leads() opens data/dummy_leads.csv
    csv.DictReader parses headers from row 1, yields one dict per lead

  Step 3 — Per-lead loop
    format_lead() converts dict to "- key: value\n" string
    ICP_SCORING_PROMPT.format(lead_data=...) inserts lead into prompt template
    client.messages.create() sends prompt to Claude API (claude-sonnet-4-6)
    API returns JSON string in content[0].text
    Script strips markdown code fences if present
    json.loads() parses JSON → dict with {score, reason, outreach_email, priority_flag}
    Result appended to results[]
    Progress printed to stdout

  Step 4 — Save
    save_results() zips leads[] and results[]
    Writes header row: all original CSV columns + score + reason + outreach_email + priority_flag
    File saved to outputs/scored_leads.csv

  Step 5 — Summary
    Counts Hot / Warm / Cold across all results
    Prints final tally to stdout

Flask Reads Output
  app.py opens outputs/scored_leads.csv
  Passes rows to leads.html Jinja2 template

Browser Displays Results
  HTML table rendered with sortable columns
  Export to CSV button available
```

---

## 5. EXTERNAL DEPENDENCIES

| Dependency | Role in this system | Production replacement |
|---|---|---|
| `anthropic` (Python SDK) | Sends prompts to Claude API, handles auth and HTTP | Same SDK — add retry logic, rate limit handling, and cost tracking |
| `flask` (Python) | Serves the web UI, handles routing, renders templates | Same — add gunicorn for production deployment |
| `claude-sonnet-4-6` (model) | Performs ICP scoring, routing decisions, and email drafting | Could tier: cheap model for initial Cold filter, sonnet only for borderline/Hot decisions |
| `csv` (stdlib) | Reads input, writes output | Replace with pandas + SQLAlchemy for database-backed I/O |
| `json` (stdlib) | Parses Claude's structured response and icp_config.json | Add schema validation (pydantic) to catch malformed API responses |
| `subprocess` (stdlib) | Flask calls scoring scripts as subprocesses | Replace with direct function calls or a task queue (Celery, RQ) for production |
| `pathlib` (stdlib) | Resolves file paths relative to script location | Same — already production-appropriate |
| `os` (stdlib) | Reads `ANTHROPIC_API_KEY` from environment | Use a secrets manager (AWS Secrets Manager, 1Password CLI) in production |

---

## 6. SCORING LOGIC

All scoring happens inside the LLM prompt — there are no hardcoded if/else rules. This is intentional: it allows the criteria to be updated without code changes.

### Lead Scoring Criteria (as defined in `ICP_SCORING_PROMPT` and `icp_config.json`)

**Strong positive signals:**
- Title is an operational decision maker: Operations Manager, Facilities Director, Maintenance Manager, Plant Manager, VP of Operations
- Industry: manufacturing, facilities management, hospitality, healthcare, logistics/warehousing
- Company size: 100–1,000 employees
- Current solution: spreadsheets, paper, legacy CMMS (Maximo, IBM), or nothing formal
- Buying signals: job postings for maintenance roles, CMMS evaluations, RFPs, LinkedIn posts about maintenance pain, attended content, high website engagement (30+ visits/30 days)
- Offer type: Demo Request leads flagged for speed-to-lead urgency
- Inbound channel: channel source weighted as a buying signal indicator

**Disqualifiers:**
- Industry: retail, SaaS/tech, consumer, government (procurement velocity too slow)
- Title has no maintenance/facilities mandate (HR, IT, finance, customer success, IC-level)
- No plausible connection to a maintenance workflow

### Lead Scoring Tiers

| Tier | Criteria | Action |
|---|---|---|
| **Hot** | Strong ICP fit (title + industry + size) AND ≥1 clear buying signal | Score + reason + personalized outreach email |
| **Warm** | Good ICP fit but no clear signal, OR mixed signals | Score + reason only |
| **Cold** | Poor ICP fit, disqualifying industry/title, or no deal path | Score + reason only |

### Trial User Scoring Tiers

| Routing Action | Criteria |
|---|---|
| **AE Fast-Track** | Strong ICP fit AND high behavioral engagement |
| **BDR Sequence** | Strong ICP fit AND low engagement, OR moderate fit AND high engagement |
| **CS Monitoring** | Weak ICP fit AND high engagement (product-led growth candidate) |
| **Suppression** | Weak ICP fit AND low engagement |

### Why LLM-based scoring over rules

A rules engine evaluates signals independently. A language model reasons across all signals simultaneously. A Facilities Manager at a 1,200-person healthcare company who just evaluated two CMMS vendors and has 89 website visits in 30 days is a different lead than one with only the title match — the model weights the full picture, not individual attributes in isolation.

---

## 7. FUTURE ARCHITECTURE

At production scale, the system expands from a batch CSV processor into a real-time pipeline with live enrichment, CRM integration, and a feedback loop. CSV inputs are replaced by live API connections — the scoring logic, routing decisions, and email drafts are already production-ready.

```
┌─────────────────────────────────────────────────────────────────────────┐
│                     PRODUCTION GTM BRAIN                                │
│                                                                         │
│  DATA SOURCES                 ENRICHMENT LAYER          SCORING ENGINE  │
│  ┌─────────────┐              ┌──────────────┐          ┌─────────────┐ │
│  │ HubSpot /   │              │ ZoomInfo     │          │             │ │
│  │ Salesforce  │─────────────▶│ (firmographic│─────────▶│ Claude API  │ │
│  │ CRM webhook │              │  enrichment) │          │ (tiered:    │ │
│  └─────────────┘              └──────────────┘          │  filter →   │ │
│  ┌─────────────┐              ┌──────────────┐          │  score →    │ │
│  │ Mixpanel    │              │ Bombora / G2 │          │  draft)     │ │
│  │ nightly     │─────────────▶│ (intent      │─────────▶│             │ │
│  │ export      │              │  signals)    │          └──────┬──────┘ │
│  └─────────────┘              └──────────────┘                 │        │
│  ┌─────────────┐              ┌──────────────┐                 │        │
│  │ LinkedIn /  │              │ HG Insights  │                 │        │
│  │ Job postings│─────────────▶│ (tech stack) │─────────────────┘        │
│  └─────────────┘              └──────────────┘                          │
│                                                                         │
│  DECISION LAYER                                OUTPUT LAYER             │
│  ┌────────────────────────────┐               ┌─────────────────────┐   │
│  │                            │               │                     │   │
│  │  AE Fast-Track ────────────┼──────────────▶│ ChiliPiper booking  │   │
│  │                            │               │ flow triggered      │   │
│  │  BDR Sequence ─────────────┼──────────────▶│ Outreach sequence   │   │
│  │                            │               │ + draft in rep inbox│   │
│  │  CS Monitoring ────────────┼──────────────▶│ Tagged in CRM,      │   │
│  │                            │               │ re-score in 30 days │   │
│  │  Suppression ──────────────┼──────────────▶│ Suppressed from     │   │
│  │                            │               │ active outreach     │   │
│  └────────────────────────────┘               └─────────────────────┘   │
│                                                                         │
│  FEEDBACK LOOP                                                          │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │  Rep feedback (accepted/rejected email) + deal outcomes          │   │
│  │  → logged to database → used to refine ICP scoring prompt        │   │
│  └──────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 8. SETUP & RUNNING

### First-time setup on a new machine

```bash
# 1. Clone the repo
git clone <repo-url>
cd gtm-lead-scoring-engine

# 2. Create and activate a virtual environment
python3 -m venv venv
source venv/bin/activate

# 3. Install dependencies
pip install anthropic flask

# 4. Set your Anthropic API key (get one at console.anthropic.com)
export ANTHROPIC_API_KEY=sk-ant-...your-key-here...

# 5. Start the web UI
python3 app.py
# Then open http://localhost:5000
```

### Running scripts directly from the terminal

```bash
# Score leads only
python3 scripts/score_leads.py

# Score trial users only
python3 scripts/score_trials.py

# Run full-funnel engine
python3 scripts/run_gtm_engine.py
```

### Output file locations

```
outputs/scored_leads.csv        Lead scoring results
outputs/scored_trials.csv       Trial scoring results
outputs/full_funnel_report.csv  Unified cross-funnel report
```

### To update scoring criteria without code

Go to the **ICP Settings** page in the web UI and edit the form fields. Changes are saved to `config/icp_config.json` and take effect on the next scoring run.
