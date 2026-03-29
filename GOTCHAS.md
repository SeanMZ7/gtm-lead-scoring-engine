# GOTCHAS.md — Known Issues & Lessons Learned

---

## Session 1 — Project Setup & First Successful Run
Date: March 20, 2026

### What was built
- Full project scaffold: CLAUDE.md, SKILL.md, README.md, GOTCHAS.md
- 10 dummy leads in data/dummy_leads.csv covering good ICP fit, borderline, and disqualified accounts
- score_leads.py — Python script that reads leads, scores each one Hot/Warm/Cold via Claude API, drafts personalized emails for Hot leads, saves all results to outputs/scored_leads.csv

### First run results
- Hot: 6 (Apex, Riverfront, BrightPath, Vanguard, Nova Snack, Hartwell)
- Warm: 1 (Cascade Property Services)
- Cold: 3 (Summit Retail, Clearwater Municipal, Pinnacle SaaS)

### What worked
- ICP scoring logic was accurate — disqualified retail, government, and SaaS correctly
- Reasoning quality was strong — not just industry filtering but title authority and signal compounding
- Personalized email subjects were contextually relevant to each lead's specific situation

### Issues hit and how they were fixed
- pyenv python version conflict — fixed by using `python3` explicitly
- pip externally managed error — fixed by creating a virtual environment (`python3 -m venv venv`)
- API credits not loaded — fixed by adding credits at console.anthropic.com

---

## Session 2 — Trial Scoring, Flask UI, and Full-Funnel Engine
Date: March 28, 2026

### What was built
- **score_trials.py** — two-dimensional trial user scoring on ICP fit and behavioral engagement using Mixpanel signals; four routing tiers: AE fast-track, BDR sequence, CS monitoring, suppression
- **run_gtm_engine.py** — orchestrator running both scoring scripts in sequence, producing a unified full-funnel report
- **Flask web UI** — five-page internal tool with dashboard, lead scoring, trial conversion, full funnel, and ICP settings pages
- **dummy_trials.csv** — 12 mock trial users with full Mixpanel behavioral data
- **config/icp_config.json** — editable ICP criteria readable and writable by non-engineers via the ICP Settings page

### Issues hit and how they were fixed
- **venv broken after recreation** — fixed by fully deactivating, deleting the venv directory, and recreating with `python3 -m venv venv`, then reinstalling all dependencies
- **Port 5000 conflict** — caused by macOS AirPlay Receiver using the same port; fixed by disabling AirPlay Receiver in System Settings → General → AirDrop & Handoff
- **Divergent git branches** — local and remote had diverged after a direct edit on GitHub; fixed with `git pull origin main --rebase` before pushing
- **anthropic module not found** — caused by a mismatch between the venv Python and the system Python running the script; fixed by recreating the venv and confirming `which python3` matched the venv path
- **CSV writer error on unified report** — leads and trials have different column schemas; fixed by collecting all unique fieldnames across both datasets with a set union before writing the header row

---

## API

- _Document rate limits, token costs, or retry behavior here._

## Data

- _Document CSV formatting issues, encoding quirks, or column gotchas here._

## Scoring

- _Document edge cases where the model mis-scored or required prompt tuning here._
