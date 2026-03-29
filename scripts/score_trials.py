"""
score_trials.py — GTM Brain: Free Trial Conversion Engine

Reads dummy_trials.csv, scores each trial user on ICP fit AND behavioral
engagement, determines routing action, drafts personalized outreach where
applicable, and saves all results to outputs/scored_trials.csv.
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
DATA_FILE = Path(__file__).parent.parent / "data" / "dummy_trials.csv"
OUTPUT_FILE = Path(__file__).parent.parent / "outputs" / "scored_trials.csv"

TRIAL_SCORING_PROMPT = """You are a GTM analyst for a company that sells AI-powered CMMS (Computerized Maintenance Management System) software to mid-market manufacturers and facilities companies.

You are evaluating a free trial user to determine how the GTM team should respond to them. You will score them on two independent dimensions — ICP fit and behavioral engagement — then assign a routing action.

## ICP Fit Criteria

**High fit:**
- Title: Operations Manager, Facilities Director, Maintenance Manager, Plant Manager, VP of Operations, Reliability Engineer, Head of Facilities, Director of Plant Operations, Head of Manufacturing Ops
- Industry: manufacturing, facilities management, healthcare, logistics/warehousing, food and beverage, energy/utilities, hospitality
- Company size: 100–1,000 employees
- Current solution: spreadsheets, legacy CMMS, nothing formal
- Geography: Canada or international geography is a mild positive fit signal — these accounts convert at a higher SAO rate per lead than the US average

**Low fit (disqualifiers):**
- Industry: retail, SaaS/tech, consumer
- Title: IC-level or no maintenance/facilities mandate (HR, IT, finance, customer success)
- Company size: 1,001+ employees (above mid-market, different sales motion)
- Inbound source: Zapier / Integrations (typically non-ICP signups inflating MQL counts)

## Behavioral Engagement Criteria

**High engagement — user is actively building in the product:**
- sessions_last_7_days: 8 or more
- sessions_last_30_days: 20 or more
- avg_session_duration_minutes: 12 or more
- features_activated: 6 or more out of total_features_available
- key_milestones_hit: 3 or more distinct milestones
- team_members_invited: 3 or more (signals internal buy-in)
- mobile_app_used: Yes
- work_orders_created: 20 or more
- pm_schedules_created: 3 or more
- assets_added: 15 or more
- reports_run: 5 or more
- last_active_days_ago: 3 or fewer

**Low engagement / stalled — user has gone quiet:**
- sessions_last_7_days: 3 or fewer
- last_active_days_ago: 7 or more
- features_activated: 2 or fewer
- key_milestones_hit: 1 or fewer
- work_orders_created: 5 or fewer with no PM schedules created

Use all available signals together — a user who hits several high engagement markers scores High even if one metric is borderline.

## Routing Logic

Assign exactly one of these four routing actions:

1. **"Route to AE via ChiliPiper"**
   High ICP fit + High engagement. This user fits our ICP and is actively using the product. Book them directly onto an AE calendar. No outreach email — the ChiliPiper booking flow handles communication automatically.

2. **"Enroll in BDR sequence via Outreach"**
   High ICP fit + Low or stalled engagement. Right company, right buyer, but they have gone quiet. A BDR should reach out in a direct, human voice to re-engage and surface any blockers.

3. **"Flag for CS monitoring"**
   Low ICP fit + High engagement. They are actively using the product but do not fit our mid-market sales motion. Do not invest AE or BDR time. Monitor for 14 days and reassess fit.

4. **"Suppress from active outreach"**
   Low ICP fit + Low engagement. No commercial opportunity at this time. Remove from active sequences.

## Outreach Draft Instructions

- **"Route to AE via ChiliPiper"**: return empty string. System handles this automatically.
- **"Enroll in BDR sequence via Outreach"**: Write a BDR-voiced re-engagement email. Tone: direct, human, conversational — not a marketing email. Reference what they actually did in the trial (milestones hit, work orders created, features tried). Connect to a real operational pain point. Soft CTA: 15-minute call. Do NOT mention the product name.
- **"Flag for CS monitoring"** or **"Suppress from active outreach"**: return empty string.

## Your Task

Evaluate the following trial user. Return a JSON object with exactly these fields:
- "fit_score": one of "High" or "Low"
- "engagement_score": one of "High" or "Low"
- "routing_action": one of the four routing action strings above — use the exact text
- "reason": one sentence explaining the routing decision — reference specific signals (title, industry, milestones hit, session data, last active date)
- "outreach_draft": personalized email (subject line + body, ~100 words) or empty string per the rules above

Return only the JSON object. No preamble, no explanation outside the JSON.

## Trial User Data

{trial_data}
"""


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def load_trials(path: Path) -> list[dict]:
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def format_trial(trial: dict) -> str:
    lines = [f"- {k}: {v}" for k, v in trial.items()]
    return "\n".join(lines)


def score_trial(client: anthropic.Anthropic, trial: dict) -> dict:
    trial_data = format_trial(trial)
    prompt = TRIAL_SCORING_PROMPT.format(trial_data=trial_data)

    message = client.messages.create(
        model=MODEL,
        max_tokens=1024,
        messages=[{"role": "user", "content": prompt}],
    )

    raw = message.content[0].text.strip()

    # Strip markdown code fences if present
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
        raw = raw.strip()

    result = json.loads(raw)
    return result


def save_results(trials: list[dict], results: list[dict], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)

    base_fields = list(trials[0].keys())
    extra_fields = ["fit_score", "engagement_score", "routing_action", "reason", "outreach_draft"]
    fieldnames = base_fields + extra_fields

    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for trial, result in zip(trials, results):
            row = {**trial, **result}
            writer.writerow(row)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise EnvironmentError("ANTHROPIC_API_KEY environment variable is not set.")

    client = anthropic.Anthropic(api_key=api_key)

    print(f"Loading trial users from {DATA_FILE}...")
    trials = load_trials(DATA_FILE)
    print(f"  {len(trials)} trial users loaded.\n")

    results = []
    for i, trial in enumerate(trials, 1):
        name = trial.get("contact_name", "Unknown")
        company = trial.get("company_name", "Unknown")
        print(f"[{i}/{len(trials)}] Scoring {name} @ {company}...")

        result = score_trial(client, trial)
        results.append(result)

        fit = result.get("fit_score", "?")
        engagement = result.get("engagement_score", "?")
        routing = result.get("routing_action", "?")
        reason = result.get("reason", "")

        print(f"  -> Fit: {fit} | Engagement: {engagement}")
        print(f"  -> Routing: {routing}")
        print(f"  -> {reason}")

        if result.get("outreach_draft"):
            preview = result.get("outreach_draft", "")[:80]
            print(f"  -> Draft: {preview}...")

        print()

    save_results(trials, results, OUTPUT_FILE)
    print(f"\nResults saved to {OUTPUT_FILE}")

    # Routing summary
    routing_actions = [r.get("routing_action", "") for r in results]
    ae_count =       sum(1 for r in routing_actions if "ChiliPiper" in r)
    bdr_count =      sum(1 for r in routing_actions if "BDR" in r)
    monitor_count =  sum(1 for r in routing_actions if "monitoring" in r)
    suppress_count = sum(1 for r in routing_actions if "Suppress" in r)

    print(f"\nRouting Summary:")
    print(f"  AE Fast-Track  (ChiliPiper):  {ae_count}")
    print(f"  BDR Sequence   (Outreach):    {bdr_count}")
    print(f"  CS Monitor:                   {monitor_count}")
    print(f"  Suppressed:                   {suppress_count}")


if __name__ == "__main__":
    main()