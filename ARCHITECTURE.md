# ARCHITECTURE.md — GTM Brain

---

## 1. PROJECT STRUCTURE

```
gtm-brain/
│
├── CLAUDE.md               # Project context and working rules for Claude Code
├── ARCHITECTURE.md         # This file — technical reference for the system
├── PROBLEM_STATEMENT.md    # Business case, design decisions, and future roadmap
├── GOTCHAS.md              # Issues encountered, fixes applied, lessons learned
├── SKILL.md                # GTM playbook (prompt patterns, scoring rationale)
├── README.md               # Quick-start guide and output format reference
│
├── data/
│   └── dummy_leads.csv     # 10 hand-crafted leads covering good/borderline/off-ICP cases
│
├── scripts/
│   └── score_leads.py      # Entry point — reads leads, calls Claude API, writes output
│
├── outputs/
│   ├── .gitkeep            # Keeps the outputs/ directory tracked by git when empty
│   └── scored_leads.csv    # Generated output — original fields + score + reason + email
│
└── venv/                   # Python virtual environment (not committed)
```

---

## 2. HIGH-LEVEL SYSTEM DIAGRAM

```
┌─────────────────────────────────────────────────────────────────┐
│                        score_leads.py                           │
│                                                                 │
│  ┌──────────────┐     ┌─────────────────┐     ┌─────────────┐  │
│  │              │     │                 │     │             │  │
│  │  data/       │────▶│  ICP Scoring    │────▶│  Decision   │  │
│  │  dummy_      │     │  Prompt +       │     │  Parser     │  │
│  │  leads.csv   │     │  Lead Data      │     │  (JSON)     │  │
│  │              │     │                 │     │             │  │
│  └──────────────┘     └────────┬────────┘     └──────┬──────┘  │
│                                │                     │         │
│                                ▼                     ▼         │
│                       ┌────────────────┐    ┌────────────────┐ │
│                       │                │    │                │ │
│                       │  Claude API    │    │  Hot → Draft   │ │
│                       │  claude-opus-  │    │  email         │ │
│                       │  4-6           │    │                │ │
│                       │                │    │  Warm/Cold →   │ │
│                       └────────────────┘    │  Score + reason│ │
│                                             │  only          │ │
│                                             └───────┬────────┘ │
│                                                     │          │
└─────────────────────────────────────────────────────┼──────────┘
                                                      │
                                                      ▼
                                          ┌───────────────────────┐
                                          │  outputs/             │
                                          │  scored_leads.csv     │
                                          │                       │
                                          │  [all original fields │
                                          │  + score + reason     │
                                          │  + outreach_email]    │
                                          └───────────────────────┘
```

---

## 3. CORE COMPONENTS

### `load_leads(path)` — Data Ingestion
- **What it does:** Reads the input CSV into memory as a list of dicts
- **Input:** Path to `data/dummy_leads.csv`
- **Output:** `list[dict]` — one dict per lead, keys are CSV column headers

### `ICP_SCORING_PROMPT` — Scoring Rubric
- **What it does:** Defines ICP criteria, scoring tiers, and output format in natural language. This is the intelligence layer — all scoring logic lives here, not in code.
- **Input:** Lead data formatted as a `- key: value` list (via `format_lead()`)
- **Output:** A filled prompt string ready to send to the Claude API

### `score_lead(client, lead)` — API Orchestration
- **What it does:** Sends one lead to Claude, receives a structured JSON response, strips any markdown fencing, and parses the result
- **Input:** An `anthropic.Anthropic` client instance + one lead dict
- **Output:** `dict` with keys `score`, `reason`, `outreach_email`

### `save_results(leads, results, output_path)` — Output Writer
- **What it does:** Merges original lead data with scoring results and writes to CSV
- **Input:** Original leads list, results list (same order), output file path
- **Output:** `outputs/scored_leads.csv` with all original columns plus `score`, `reason`, `outreach_email`

### `main()` — Entry Point & Orchestrator
- **What it does:** Validates the API key, loads leads, iterates through them calling `score_lead()` for each, prints progress to stdout, calls `save_results()`, and prints a final summary
- **Input:** `ANTHROPIC_API_KEY` environment variable
- **Output:** Populated `outputs/scored_leads.csv` + terminal summary

---

## 4. DATA FLOW

```
Step 1 — Startup
  main() checks os.environ for ANTHROPIC_API_KEY
  Raises EnvironmentError immediately if missing

Step 2 — Load
  load_leads() opens data/dummy_leads.csv
  csv.DictReader parses headers from row 1, yields one dict per lead
  Returns list of 10 dicts

Step 3 — Per-lead loop (runs 10 times)
  format_lead() converts dict to "- key: value\n" string
  ICP_SCORING_PROMPT.format(lead_data=...) inserts lead into prompt template
  client.messages.create() sends prompt to Claude API (claude-opus-4-6)
  API returns message object with JSON string in content[0].text
  Script strips markdown code fences if present
  json.loads() parses JSON → dict with {score, reason, outreach_email}
  Result appended to results[]
  Progress printed to stdout

Step 4 — Save
  save_results() zips leads[] and results[] (preserves order)
  Writes header row: all original CSV columns + score + reason + outreach_email
  Writes one row per lead
  File saved to outputs/scored_leads.csv

Step 5 — Summary
  Counts Hot / Warm / Cold across all results
  Prints final tally to stdout
```

---

## 5. EXTERNAL DEPENDENCIES

| Dependency | Role in this system | Production replacement |
|---|---|---|
| `anthropic` (Python SDK) | Sends prompts to Claude API, handles auth and HTTP | Same SDK — add retry logic, rate limit handling, and cost tracking |
| `claude-opus-4-6` (model) | Performs ICP scoring and email drafting | Could tier: cheap model for initial Cold filter, Opus only for borderline/Hot decisions |
| `csv` (stdlib) | Reads input, writes output | Replace with pandas + SQLAlchemy for database-backed I/O |
| `json` (stdlib) | Parses Claude's structured response | Add schema validation (pydantic) to catch malformed API responses |
| `pathlib` (stdlib) | Resolves file paths relative to script location | Same — already production-appropriate |
| `os` (stdlib) | Reads `ANTHROPIC_API_KEY` from environment | Use a secrets manager (AWS Secrets Manager, 1Password CLI) in production |

---

## 6. SCORING LOGIC

All scoring happens inside the LLM prompt — there are no hardcoded if/else rules. This is intentional: it allows the criteria to be updated without code changes.

### ICP Criteria (as defined in `ICP_SCORING_PROMPT`)

**Strong positive signals:**
- Title is an operational decision maker: Operations Manager, Facilities Director, Maintenance Manager, Plant Manager, VP of Operations
- Industry: manufacturing, facilities management, healthcare, logistics/warehousing
- Company size: 100–2,500 employees
- Current solution: spreadsheets, paper, legacy CMMS (Maximo, IBM), or nothing formal
- Buying signals: job postings for maintenance roles, CMMS evaluations, RFPs, LinkedIn posts about maintenance pain, attended content, high website engagement (30+ visits/30 days)

**Disqualifiers:**
- Industry: retail, SaaS/tech, consumer, government (procurement velocity too slow)
- Title has no maintenance/facilities mandate (HR, IT, finance, customer success, IC-level)
- No plausible connection to a maintenance workflow

### Tier Definitions

| Tier | Criteria | Action |
|---|---|---|
| **Hot** | Strong ICP fit (title + industry + size) AND ≥1 clear buying signal | Score + reason + personalized outreach email |
| **Warm** | Good ICP fit but no clear signal, OR mixed signals | Score + reason only |
| **Cold** | Poor ICP fit, disqualifying industry/title, or no deal path | Score + reason only |

### Why LLM-based scoring over rules

A rules engine evaluates signals independently. A language model reasons across all signals simultaneously. A Facilities Manager at a 1,200-person healthcare company who just evaluated two CMMS vendors and has 89 website visits in 30 days is a different lead than one with only the title match — the model weights the full picture, not individual attributes in isolation.

---

## 7. FUTURE ARCHITECTURE

At production scale, the system expands from a batch CSV processor into a real-time pipeline with live enrichment, CRM integration, and a feedback loop.

```
┌─────────────────────────────────────────────────────────────────────────┐
│                     PRODUCTION GTM BRAIN                                │
│                                                                         │
│  DATA SOURCES                 ENRICHMENT LAYER          SCORING ENGINE  │
│  ┌─────────────┐              ┌──────────────┐          ┌─────────────┐ │
│  │ HubSpot /   │              │ Clay / Apollo│          │             │ │
│  │ Salesforce  │─────────────▶│ (firmographic│─────────▶│ Claude API  │ │
│  │ CRM         │              │  enrichment) │          │ (tiered:    │ │
│  └─────────────┘              └──────────────┘          │  filter →  │ │
│  ┌─────────────┐              ┌──────────────┐          │  score →   │ │
│  │ Intent data │              │ Bombora / G2 │          │  draft)    │ │
│  │ (web visits,│─────────────▶│ (intent      │─────────▶│             │ │
│  │  signals)   │              │  signals)    │          └──────┬──────┘ │
│  └─────────────┘              └──────────────┘                 │        │
│  ┌─────────────┐              ┌──────────────┐                 │        │
│  │ LinkedIn /  │              │ BuiltWith    │                 │        │
│  │ Job postings│─────────────▶│ (tech stack) │─────────────────┘        │
│  └─────────────┘              └──────────────┘                          │
│                                                                         │
│  DECISION LAYER                                OUTPUT LAYER             │
│  ┌────────────────────────────┐               ┌─────────────────────┐  │
│  │                            │               │                     │  │
│  │  Hot ──────────────────────┼──────────────▶│ Rep outbox draft +  │  │
│  │  (enroll in hot sequence)  │               │ CRM task created    │  │
│  │                            │               │                     │  │
│  │  Warm ─────────────────────┼──────────────▶│ Tagged in CRM,      │  │
│  │  (nurture queue)           │               │ re-score in 30 days │  │
│  │                            │               │                     │  │
│  │  Cold ─────────────────────┼──────────────▶│ Suppressed from     │  │
│  │  (suppress)                │               │ active outreach     │  │
│  │                            │               │                     │  │
│  └────────────────────────────┘               └─────────────────────┘  │
│                                                                         │
│  FEEDBACK LOOP                                                          │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │  Rep feedback (accepted/rejected email) + deal outcomes          │  │
│  │  → logged to database → used to refine ICP scoring prompt        │  │
│  └──────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 8. SETUP & RUNNING

### First-time setup on a new machine

```bash
# 1. Clone the repo
git clone <repo-url>
cd gtm-brain

# 2. Create and activate a virtual environment
python3 -m venv venv
source venv/bin/activate

# 3. Install dependencies
pip install anthropic

# 4. Set your Anthropic API key (get one at console.anthropic.com)
export ANTHROPIC_API_KEY=sk-ant-...your-key-here...

# 5. Run the scoring script
python3 scripts/score_leads.py
```

### Expected output

```
Loading leads from .../data/dummy_leads.csv...
  10 leads loaded.

[1/10] Scoring Diana Ruiz @ Apex Precision Manufacturing...
  -> Hot: Director of Facilities at an 850-person manufacturer with a job posting signal and 47 site visits.
  -> Email drafted: Subject: Maintenance at Apex — quick question...

...

Results saved to .../outputs/scored_leads.csv

Summary: Hot=6 | Warm=1 | Cold=3
```

### Output file location

```
outputs/scored_leads.csv
```

Columns: all original lead fields + `score` + `reason` + `outreach_email`

### To re-run with different leads

Replace or edit `data/dummy_leads.csv`. The script reads whatever is in that file — column headers must match exactly:

```
company_name, contact_name, title, industry, company_size,
recent_signal, website_visits_last_30_days, current_solution, notes
```

### To update scoring criteria

Edit `ICP_SCORING_PROMPT` in `scripts/score_leads.py`. No other changes required — the scoring logic is entirely prompt-driven.
