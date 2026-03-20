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
- API key exposed in Claude Code chat — rotated immediately at console.anthropic.com

---

## API

- _Document rate limits, token costs, or retry behavior here._

## Data

- _Document CSV formatting issues, encoding quirks, or column gotchas here._

## Scoring

- _Document edge cases where the model mis-scored or required prompt tuning here._
