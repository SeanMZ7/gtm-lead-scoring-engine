"""
run_gtm_engine.py — GTM Brain Orchestrator

Runs both scoring engines in sequence and produces a unified
GTM intelligence report in outputs/gtm_intelligence_report.csv.
"""

import csv
import json
import os
from pathlib import Path

import anthropic

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

MODEL = "claude-sonnet-4-6"
LEADS_FILE = Path(__file__).parent.parent / "data" / "dummy_leads.csv"
TRIALS_FILE = Path(__file__).parent.parent / "data" / "dummy_trials.csv"
OUTPUT_FILE = Path(__file__).parent.parent / "outputs" / "gtm_intelligence_report.csv"

# ---------------------------------------------------------------------------
# Shared Helpers
# ---------------------------------------------------------------------------

def load_csv(path: Path) -> list[dict]:
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))

def format_row(row: dict) -> str:
    return "\n".join([f"- {k}: {v}" for k, v in row.items()])

def call_claude(client: anthropic.Anthropic, prompt: str) -> dict:
    message = client.messages.create(
        model=MODEL,
        max_tokens=1024,
        messages=[{"role": "user", "content": prompt}],
    )
    raw = message.content[0].text.strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
        raw = raw.strip()
    return json.loads(raw)

# ---------------------------------------------------------------------------
# Lead Scoring Prompt
# ---------------------------------------------------------------------------

LEAD_PROMPT = """You are a GTM analyst for a company that sells AI-powered CMMS software to mid-market manufacturers and facilities companies.

## ICP Criteria

**Ideal buyer:** Operations Managers, Facilities Directors, Maintenance Managers, Plant Managers — decision makers who own maintenance workflows and asset management budgets.

**Ideal company:**
- Industries: manufacturing, facilities management, healthcare, logistics/warehousing
- Company size: 100–2,500 employees
- Current solution: spreadsheets, legacy CMMS, or nothing formal
- Buying signals: job postings for maintenance roles, CMMS evaluations, RFPs, LinkedIn activity, attended content

**Disqualifiers:**
- Industry: retail, SaaS/tech, consumer, government
- Title: IC-level or off-function (HR, IT, finance)
- No connection to maintenance or facilities

## Scoring Tiers
- **Hot** — Strong ICP fit AND at least one buying signal
- **Warm** — Good fit but no signal, or mixed signals
- **Cold** — Poor fit, wrong industry, or no deal path

## Task
Score this lead. Return JSON with:
- "score": "Hot", "Warm", or "Cold"
- "routing_action": "Route to AE via ChiliPiper" if Hot, "Enroll in BDR sequence via Outreach" if Warm, "Suppress from active outreach" if Cold
- "reason": one specific sentence referencing title, industry, signal, or gap
- "outreach_draft": personalized email (subject + body, ~100 words) for Hot leads only. Address by first name, reference company and role, connect to a pain point, soft CTA (15-min call). No em-dashes. Sign off with [Your Name]. Empty string if not Hot.

Return only the JSON object.

## Lead Data
{data}
"""

# ---------------------------------------------------------------------------
# Trial Scoring Prompt
# ---------------------------------------------------------------------------

TRIAL_PROMPT = """You are a GTM analyst for a company that sells AI-powered CMMS software to mid-market manufacturers and facilities companies.

## ICP Fit Criteria
**High fit:** Titles like Operations Manager, Facilities Director, Maintenance Manager, Plant Manager, VP Operations. Industries: manufacturing, facilities management, healthcare, logistics, food and beverage, energy. Size: 100-2,500 employees.
**Low fit disqualifiers:** Retail, SaaS/tech. IC-level titles. 3,000+ employees. Zapier/Integrations source.

## Behavioral Engagement Criteria
**High engagement:** 8+ sessions last 7 days, 20+ sessions last 30 days, 12+ min avg session, 6+ features activated, 3+ milestones hit, 3+ team members invited, mobile app used, 20+ work orders, 3+ PM schedules, last active 3 or fewer days ago.
**Low engagement:** 3 or fewer sessions last 7 days, last active 7+ days ago, 2 or fewer features activated.

## Routing Logic
- High fit + High engagement → "Route to AE via ChiliPiper"
- High fit + Low engagement → "Enroll in BDR sequence via Outreach"
- Low fit + High engagement → "Flag for CS monitoring"
- Low fit + Low engagement → "Suppress from active outreach"

## Outreach Draft
- AE fast-track: empty string (ChiliPiper handles automatically)
- BDR sequence: direct, human BDR-voiced re-engagement email referencing what they did in trial. Soft CTA: 15-min call. No em-dashes. Sign off with [Your Name].
- Monitor or Suppress: empty string

## Task
Return JSON with:
- "fit_score": "High" or "Low"
- "engagement_score": "High" or "Low"
- "routing_action": exact routing string from above
- "reason": one specific sentence referencing signals
- "outreach_draft": email or empty string per rules above

Return only the JSON object.

## Trial User Data
{data}
"""

# ---------------------------------------------------------------------------
# Scoring Functions
# ---------------------------------------------------------------------------

def score_lead(client, lead: dict) -> dict:
    result = call_claude(client, LEAD_PROMPT.format(data=format_row(lead)))
    return {
        "lead_type": "Inbound/Outbound Lead",
        "fit_score": result.get("score", "?"),
        "engagement_score": "N/A",
        "routing_action": result.get("routing_action", "?"),
        "reason": result.get("reason", ""),
        "outreach_draft": result.get("outreach_draft", ""),
    }

def score_trial(client, trial: dict) -> dict:
    result = call_claude(client, TRIAL_PROMPT.format(data=format_row(trial)))
    return {
        "lead_type": "Free Trial User",
        "fit_score": result.get("fit_score", "?"),
        "engagement_score": result.get("engagement_score", "?"),
        "routing_action": result.get("routing_action", "?"),
        "reason": result.get("reason", ""),
        "outreach_draft": result.get("outreach_draft", ""),
    }

# ---------------------------------------------------------------------------
# Save
# ---------------------------------------------------------------------------

def save_report(all_rows: list[dict], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    if not all_rows:
        return
    # Collect all unique fieldnames across both lead and trial rows
    fieldnames = []
    for row in all_rows:
        for key in row.keys():
            if key not in fieldnames:
                fieldnames.append(key)
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for row in all_rows:
            writer.writerow(row)

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise EnvironmentError("ANTHROPIC_API_KEY environment variable is not set.")

    client = anthropic.Anthropic(api_key=api_key)
    all_results = []

    # --- Score leads ---
    print("=" * 60)
    print("SCORING INBOUND / OUTBOUND LEADS")
    print("=" * 60)
    leads = load_csv(LEADS_FILE)
    print(f"  {len(leads)} leads loaded.\n")

    for i, lead in enumerate(leads, 1):
        name = lead.get("contact_name", "Unknown")
        company = lead.get("company_name", "Unknown")
        print(f"[{i}/{len(leads)}] {name} @ {company}")
        result = score_lead(client, lead)
        row = {"lead_type": result["lead_type"], **lead, **result}
        all_results.append(row)
        print(f"  -> {result['fit_score']} | {result['routing_action']}")
        print()

    # --- Score trials ---
    print("=" * 60)
    print("SCORING FREE TRIAL USERS")
    print("=" * 60)
    trials = load_csv(TRIALS_FILE)
    print(f"  {len(trials)} trial users loaded.\n")

    for i, trial in enumerate(trials, 1):
        name = trial.get("contact_name", "Unknown")
        company = trial.get("company_name", "Unknown")
        print(f"[{i}/{len(trials)}] {name} @ {company}")
        result = score_trial(client, trial)
        row = {"lead_type": result["lead_type"], **trial, **result}
        all_results.append(row)
        print(f"  -> Fit: {result['fit_score']} | Engagement: {result['engagement_score']} | {result['routing_action']}")
        print()

    # --- Save unified report ---
    save_report(all_results, OUTPUT_FILE)
    print(f"\nUnified report saved to {OUTPUT_FILE}")

    # --- Summary ---
    routing_all = [r["routing_action"] for r in all_results]
    ae =       sum(1 for r in routing_all if "ChiliPiper" in r)
    bdr =      sum(1 for r in routing_all if "BDR" in r)
    monitor =  sum(1 for r in routing_all if "monitoring" in r)
    suppress = sum(1 for r in routing_all if "Suppress" in r)

    print("\n" + "=" * 60)
    print("GTM INTELLIGENCE SUMMARY — FULL FUNNEL")
    print("=" * 60)
    print(f"  Total records scored:          {len(all_results)}")
    print(f"  AE Fast-Track (ChiliPiper):    {ae}")
    print(f"  BDR Sequence  (Outreach):      {bdr}")
    print(f"  CS Monitor:                    {monitor}")
    print(f"  Suppressed:                    {suppress}")
    print("=" * 60)

if __name__ == "__main__":
    main()