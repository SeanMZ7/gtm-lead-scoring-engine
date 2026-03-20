"""
score_leads.py — GTM Brain MVP

Reads dummy_leads.csv, scores each lead Hot/Warm/Cold via Claude API,
drafts outreach emails for Hot leads, and saves all results to outputs/scored_leads.csv.
"""

import csv
import json
import os
from pathlib import Path

import anthropic

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

MODEL = "claude-opus-4-6"
DATA_FILE = Path(__file__).parent.parent / "data" / "dummy_leads.csv"
OUTPUT_FILE = Path(__file__).parent.parent / "outputs" / "scored_leads.csv"

ICP_SCORING_PROMPT = """You are a GTM analyst, a company that sells AI-powered CMMS (Computerized Maintenance Management System) software to mid-market manufacturers and facilities companies.

## ICP Criteria

**Ideal buyer:** Operations Managers, Facilities Directors, Maintenance Managers, Plant Managers — decision makers who own maintenance workflows and asset management budgets.

**Ideal company:**
- Industries: manufacturing, facilities management, healthcare, logistics/warehousing
- Company size: 100–2,500 employees (mid-market)
- Current solution: spreadsheets, legacy CMMS, or nothing formal
- Buying signals: job postings for maintenance roles, CMMS vendor evaluations, RFPs, LinkedIn activity about maintenance pain, attended content

**Disqualifiers:**
- Industry: retail, SaaS/tech, consumer, government (slow procurement)
- Title is IC-level (no budget authority) or completely off-function (HR, finance, IT)
- No connection to maintenance or facilities operations

## Scoring Tiers

- **Hot** — Strong ICP fit (right title + right industry + right size) AND at least one clear buying signal
- **Warm** — Good ICP fit but no strong signal, OR mixed signals (e.g., right industry but borderline title)
- **Cold** — Poor ICP fit, wrong industry, disqualifying title, or no plausible path to a deal

## Your Task

Score the following lead. Return a JSON object with exactly these fields:
- "score": one of "Hot", "Warm", or "Cold"
- "reason": one sentence explaining the score (be specific — reference the title, industry, signal, or gap)
- "outreach_email": if score is "Hot", write a personalized first-touch email (subject line + body, ~100 words). If not Hot, return an empty string.

The email should:
- Address the contact by first name
- Reference their specific company and role
- Connect to a pain point solves that is relevant to their signal or context
- Include a soft CTA (15-min call, not a demo push)
- Sound like a human wrote it — no buzzword soup

Return only the JSON object. No preamble, no explanation outside the JSON.

## Lead Data

{lead_data}
"""


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def load_leads(path: Path) -> list[dict]:
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def format_lead(lead: dict) -> str:
    lines = [f"- {k}: {v}" for k, v in lead.items()]
    return "\n".join(lines)


def score_lead(client: anthropic.Anthropic, lead: dict) -> dict:
    lead_data = format_lead(lead)
    prompt = ICP_SCORING_PROMPT.format(lead_data=lead_data)

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


def save_results(leads: list[dict], results: list[dict], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)

    base_fields = list(leads[0].keys())
    extra_fields = ["score", "reason", "outreach_email"]
    fieldnames = base_fields + extra_fields

    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for lead, result in zip(leads, results):
            row = {**lead, **result}
            writer.writerow(row)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise EnvironmentError("ANTHROPIC_API_KEY environment variable is not set.")

    client = anthropic.Anthropic(api_key=api_key)

    print(f"Loading leads from {DATA_FILE}...")
    leads = load_leads(DATA_FILE)
    print(f"  {len(leads)} leads loaded.\n")

    results = []
    for i, lead in enumerate(leads, 1):
        name = lead.get("contact_name", "Unknown")
        company = lead.get("company_name", "Unknown")
        print(f"[{i}/{len(leads)}] Scoring {name} @ {company}...")

        result = score_lead(client, lead)
        results.append(result)

        score = result.get("score", "?")
        reason = result.get("reason", "")
        print(f"  -> {score}: {reason}")

        if score == "Hot":
            email_preview = result.get("outreach_email", "")[:80]
            print(f"  -> Email drafted: {email_preview}...")

        print()

    save_results(leads, results, OUTPUT_FILE)
    print(f"Results saved to {OUTPUT_FILE}")

    # Summary
    scores = [r.get("score") for r in results]
    print(f"\nSummary: Hot={scores.count('Hot')} | Warm={scores.count('Warm')} | Cold={scores.count('Cold')}")


if __name__ == "__main__":
    main()
