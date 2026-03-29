"""
score_leads.py — GTM Brain MVP

Reads dummy_leads.csv, scores each lead Hot/Warm/Cold via Claude API,
drafts outreach emails for Hot leads, and saves all results to outputs/scored_leads.csv.

ICP criteria are read from environment variables if set (injected by the Flask app
from config/icp_config.json). Falls back to hardcoded defaults if not set.
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
DATA_FILE = Path(__file__).parent.parent / "data" / "dummy_leads.csv"
OUTPUT_FILE = Path(__file__).parent.parent / "outputs" / "scored_leads.csv"


# ---------------------------------------------------------------------------
# ICP prompt builder — reads from env vars with hardcoded fallbacks
# ---------------------------------------------------------------------------

def _get_env_list(key, default):
    """Read a JSON-encoded list from an env var, falling back to default."""
    val = os.environ.get(key)
    if val:
        try:
            return json.loads(val)
        except (json.JSONDecodeError, ValueError):
            pass
    return default


def build_scoring_prompt():
    """Build the ICP scoring prompt, injecting values from env vars if set."""
    titles = _get_env_list("ICP_TARGET_TITLES", [
        "Operations Manager", "Facilities Director", "Maintenance Manager",
        "Plant Manager", "VP of Operations", "Reliability Engineer",
        "Director of Facilities", "Head of Facilities", "Head of Manufacturing Ops",
    ])
    industries = _get_env_list("ICP_TARGET_INDUSTRIES", [
        "manufacturing", "facilities management", "healthcare", "logistics/warehousing",
        "hospitality",
    ])
    size_min = int(os.environ.get("ICP_COMPANY_SIZE_MIN", 100))
    size_max = int(os.environ.get("ICP_COMPANY_SIZE_MAX", 1000))
    signals = _get_env_list("ICP_BUYING_SIGNALS", [
        "job postings for maintenance roles", "CMMS vendor evaluations",
        "RFPs", "LinkedIn activity about maintenance pain", "attended content",
    ])
    disq_industries = _get_env_list("ICP_DISQUALIFIER_INDUSTRIES", [
        "retail", "SaaS/tech", "consumer", "government",
    ])
    disq_titles = _get_env_list("ICP_DISQUALIFIER_TITLES", [
        "HR", "finance", "IT",
    ])

    return (
        "You are a GTM analyst for a company that sells AI-powered CMMS "
        "(Computerized Maintenance Management System) software to mid-market "
        "manufacturers and facilities companies.\n\n"
        "## ICP Criteria\n\n"
        f"**Ideal buyer:** {', '.join(titles)} — decision makers who own "
        "maintenance workflows and asset management budgets.\n\n"
        "**Ideal company:**\n"
        f"- Industries: {', '.join(industries)}\n"
        f"- Company size: {size_min}–{size_max} employees (mid-market)\n"
        "- Current solution: spreadsheets, legacy CMMS, or nothing formal\n"
        f"- Buying signals: {', '.join(signals)}\n\n"
        "**Disqualifiers:**\n"
        f"- Industry: {', '.join(disq_industries)}\n"
        f"- Title is IC-level (no budget authority) or completely off-function "
        f"({', '.join(disq_titles)})\n"
        "- No connection to maintenance or facilities operations\n\n"
        "## Channel & Offer Signals\n\n"
        "Use these signals to adjust score and reason when the lead data includes "
        "offer_type or inbound_channel fields:\n\n"
        "**offer_type signals:**\n"
        "- Demo Request: strong positive signal — buyer is actively evaluating.\n\n"
        "**inbound_channel signals:**\n"
        "- Zapier / Integrations: soft disqualifier — inflates MQL counts, rarely "
        "converts to SAO. Treat as mild negative.\n"
        "- Organic / Direct: mild positive signal — higher purchase intent than paid.\n"
        "- Microsoft Ads: mild positive signal — strong SAO efficiency, high-intent search.\n"
        "- LinkedIn Ads: neutral — reaches ICP titles but lower purchase intent than search.\n\n"
        "**Geography signals:**\n"
        "- Canada or any international geography: mild positive signal — converts at "
        "higher SAO rate per lead than US average.\n\n"
        "## Scoring Tiers\n\n"
        "- **Hot** — Strong ICP fit (right title + right industry + right size) "
        "AND at least one clear buying signal\n"
        "- **Warm** — Good ICP fit but no strong signal, OR mixed signals "
        "(e.g., right industry but borderline title)\n"
        "- **Cold** — Poor ICP fit, wrong industry, disqualifying title, or no "
        "plausible path to a deal\n\n"
        "## Your Task\n\n"
        "Score the following lead. Return a JSON object with exactly these fields:\n"
        '- "score": one of "Hot", "Warm", or "Cold"\n'
        '- "reason": one sentence explaining the score (be specific — reference '
        "the title, industry, signal, or gap)\n"
        '- "priority_flag": REQUIRED. Set to exactly '
        '"HIGH PRIORITY — respond within 2 hours" if offer_type is "Demo Request" '
        'AND score is "Hot". Set to "" (empty string) in all other cases. '
        "No exceptions — this field must always be present.\n"
        '- "outreach_email": if score is "Hot", write a personalized first-touch '
        "email (subject line + body, ~100 words). If not Hot, return an empty string.\n\n"
        "The email should:\n"
        "- Address the contact by first name\n"
        "- Reference their specific company and role\n"
        "- Connect to a pain point it solves that is relevant to their signal or context\n"
        "- Include a soft CTA (15-min call, not a demo push)\n"
        "- Sound like a human wrote it — no buzzword soup\n"
        "- Sign off with [Your Name] — never use \"Team\" or any other signature\n"
        "- Don't ever use 'em-dash (—) in the email.\n\n"
        "Return only the JSON object. No preamble, no explanation outside the JSON.\n\n"
        "## Lead Data\n\n"
        "{lead_data}\n"
    )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def load_leads(path: Path) -> list[dict]:
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def format_lead(lead: dict) -> str:
    lines = [f"- {k}: {v}" for k, v in lead.items()]
    return "\n".join(lines)


def score_lead(client: anthropic.Anthropic, lead: dict, prompt_template: str) -> dict:
    lead_data = format_lead(lead)
    prompt = prompt_template.format(lead_data=lead_data)

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
    extra_fields = ["score", "reason", "priority_flag", "outreach_email"]
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
    prompt_template = build_scoring_prompt()

    print(f"Loading leads from {DATA_FILE}...")
    leads = load_leads(DATA_FILE)
    print(f"  {len(leads)} leads loaded.\n")

    results = []
    for i, lead in enumerate(leads, 1):
        name = lead.get("contact_name", "Unknown")
        company = lead.get("company_name", "Unknown")
        print(f"[{i}/{len(leads)}] Scoring {name} @ {company}...")

        result = score_lead(client, lead, prompt_template)
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

    scores = [r.get("score") for r in results]
    print(f"\nSummary: Hot={scores.count('Hot')} | Warm={scores.count('Warm')} | Cold={scores.count('Cold')}")


if __name__ == "__main__":
    main()
