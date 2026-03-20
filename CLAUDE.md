# CLAUDE.md — GTM Brain

## Project Purpose

This is a **lead scoring and signal trigger system** built as an MVP. It demonstrates GTM thinking through code: how to identify ICP fit, prioritize outreach, and personalize messaging at scale using AI.

## Context

- **Target market:** Mid-market manufacturers and facilities management companies
- **Deal size / segment:** Mid-market (not SMB, not Enterprise)
- **ICP buyer:** Operations Managers, Facilities Directors, Maintenance Managers, Plant Managers — decision makers who own maintenance workflows and budgets
- **NOT the ICP:** Floor technicians, IT teams, HR, finance, or anyone without a maintenance/facilities mandate
- **Pain points solved:** Reactive maintenance, manual work order tracking, lack of real-time asset visibility, compliance documentation gaps

## ICP Scoring Criteria

When scoring leads, Claude should weigh:

| Signal | Weight |
|---|---|
| Title matches ops/facilities/maintenance decision maker | High |
| Industry: manufacturing, facilities mgmt, healthcare, logistics | High |
| Company size: 100–2,500 employees (mid-market) | High |
| Recent buying signal (job posting, tech evaluation, funding) | Medium |
| High website engagement (30+ visits/30 days) | Medium |
| Current solution: spreadsheets, legacy CMMS, or nothing | Medium |
| Notes indicate pain or active search | Medium |
| Off-industry (retail, SaaS, consumer) | Disqualifier |
| Title is individual contributor / non-decision maker | Disqualifier |

## Output Tiers

- **Hot** — Strong ICP fit + at least one buying signal. Draft a personalized outreach email.
- **Warm** — Good ICP fit but no strong signal, or mixed signals.
- **Cold** — Poor ICP fit, wrong industry, or no buying intent.

## Tech Stack

- **Language:** Python 3
- **AI:** Claude API (`anthropic` SDK) — model `claude-opus-4-6`
- **Data:** CSV (dummy data in `data/dummy_leads.csv`)
- **Output:** CSV to `outputs/scored_leads.csv`

## Working Rules for Claude Code

1. **Plan before coding.** Outline the approach before writing any script.
2. **Never mark a task done without testing it** — at minimum a dry run or print verification.
3. **Keep scoring logic in the prompt, not hardcoded if/else.** The Claude API does the reasoning.
4. **Log everything.** Every scored lead must include the rating AND a one-sentence reason.
5. **Personalization matters.** Hot lead emails should reference the specific company, title, signal, and pain — no generic templates.
6. **Output to `outputs/` only.** Never overwrite source data in `data/`.
