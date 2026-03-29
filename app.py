"""
app.py — GTM Brain Flask Web UI

Wraps the existing scoring scripts with a clean web interface.
Scripts are executed via subprocess; this file never modifies them.
"""

import csv
import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path

from flask import Flask, flash, redirect, render_template, request, url_for

app = Flask(__name__)
app.secret_key = os.urandom(24)

BASE_DIR = Path(__file__).parent
OUTPUTS_DIR = BASE_DIR / "outputs"
SCRIPTS_DIR = BASE_DIR / "scripts"
CONFIG_FILE = BASE_DIR / "config" / "icp_config.json"

SCORED_LEADS_CSV = OUTPUTS_DIR / "scored_leads.csv"
SCORED_TRIALS_CSV = OUTPUTS_DIR / "scored_trials.csv"
GTM_REPORT_CSV = OUTPUTS_DIR / "gtm_intelligence_report.csv"
LEADS_CSV = BASE_DIR / "data" / "dummy_leads.csv"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def read_csv(path: Path):
    if not path.exists():
        return None
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def get_file_mtime(path: Path):
    if path.exists():
        ts = path.stat().st_mtime
        return datetime.fromtimestamp(ts).strftime("%b %d, %Y at %I:%M %p")
    return None


def load_lead_source_lookup() -> dict:
    """Return {company_name: lead_source_type} from dummy_leads.csv."""
    rows = read_csv(LEADS_CSV)
    if not rows:
        return {}
    return {r["company_name"]: r.get("lead_source_type", "Inbound") for r in rows}


def load_icp_config():
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE, encoding="utf-8") as f:
            return json.load(f)
    return {}


def get_icp_env_vars() -> dict:
    """Convert icp_config.json values into environment variables for subprocesses."""
    config = load_icp_config()
    if not config:
        return {}
    return {
        "ICP_TARGET_TITLES":           json.dumps(config.get("target_titles", [])),
        "ICP_TARGET_INDUSTRIES":       json.dumps(config.get("target_industries", [])),
        "ICP_COMPANY_SIZE_MIN":        str(config.get("company_size_min", 100)),
        "ICP_COMPANY_SIZE_MAX":        str(config.get("company_size_max", 2500)),
        "ICP_BUYING_SIGNALS":          json.dumps(config.get("buying_signals", [])),
        "ICP_DISQUALIFIER_INDUSTRIES": json.dumps(config.get("disqualifier_industries", [])),
        "ICP_DISQUALIFIER_TITLES":     json.dumps(config.get("disqualifier_titles", [])),
    }


def run_script(script_name: str, inject_icp: bool = False):
    """Run a scoring script as a subprocess.

    If inject_icp=True, reads icp_config.json and passes values as env vars
    so the script can use updated ICP criteria at runtime.
    """
    script_path = SCRIPTS_DIR / script_name
    env = os.environ.copy()
    if inject_icp:
        env.update(get_icp_env_vars())
    result = subprocess.run(
        [sys.executable, str(script_path)],
        capture_output=True,
        text=True,
        env=env,
    )
    return result


def routing_class(row: dict) -> str:
    """Return a CSS class name based on routing_action or score."""
    score = row.get("score", "")
    routing = row.get("routing_action", "")
    combined = (score + " " + routing).lower()
    if "hot" in combined or "chilipiper" in combined:
        return "row-ae"
    elif "warm" in combined or "bdr" in combined:
        return "row-bdr"
    elif "monitoring" in combined:
        return "row-cs"
    elif "cold" in combined or "suppress" in combined:
        return "row-suppress"
    return ""


def derive_lead_routing(score: str) -> str:
    if score == "Hot":
        return "Route to AE via ChiliPiper"
    elif score == "Warm":
        return "Enroll in BDR sequence via Outreach"
    return "Suppress from active outreach"


def annotate_leads(rows):
    """Add derived fields to lead rows for template use."""
    for row in rows:
        row["routing_action"] = derive_lead_routing(row.get("score", ""))
        row["row_class"] = routing_class(row)
        row["routing_key"] = row["row_class"].replace("row-", "")
        row["has_draft"] = (
            "BDR" in row["routing_action"]
            and bool(row.get("outreach_email", "").strip())
        )
    return rows


def annotate_trials(rows):
    for row in rows:
        row["row_class"] = routing_class(row)
        row["routing_key"] = row["row_class"].replace("row-", "")
        row["has_draft"] = (
            "BDR" in row.get("routing_action", "")
            and bool(row.get("outreach_draft", "").strip())
        )
    return rows


def annotate_funnel(rows, lead_source_lookup=None):
    if lead_source_lookup is None:
        lead_source_lookup = load_lead_source_lookup()
    for row in rows:
        row["row_class"] = routing_class(row)
        row["routing_key"] = row["row_class"].replace("row-", "")
        row["has_draft"] = (
            "BDR" in row.get("routing_action", "")
            and bool(row.get("outreach_draft", "").strip())
        )
        lt = row.get("lead_type", "")
        if "Trial" in lt:
            row["lead_type_badge"] = "Trial"
        else:
            # Prefer the field on the row; fall back to the source CSV lookup
            source = (
                row.get("lead_source_type", "").strip()
                or lead_source_lookup.get(row.get("company_name", ""), "Inbound")
            )
            row["lead_type_badge"] = "Outbound" if source.lower() == "outbound" else "Inbound"
    return rows


def count_routing(rows):
    ae = sum(1 for r in rows if "ChiliPiper" in r.get("routing_action", ""))
    bdr = sum(1 for r in rows if "BDR" in r.get("routing_action", ""))
    cs = sum(1 for r in rows if "monitoring" in r.get("routing_action", ""))
    supp = sum(1 for r in rows if "Suppress" in r.get("routing_action", ""))
    return {"ae": ae, "bdr": bdr, "cs": cs, "suppress": supp}


def _safe_int(val, default=0):
    try:
        return int(val or default)
    except (ValueError, TypeError):
        return default


def get_insights(rows):
    """Surface 3 callout records from the full funnel report."""
    if not rows:
        return None

    # Top AE fast-track: prefer trials sorted by sessions_last_30_days, else first lead
    ae_rows = [r for r in rows if "ChiliPiper" in r.get("routing_action", "")]
    top_ae = None
    if ae_rows:
        ae_rows.sort(key=lambda r: _safe_int(r.get("sessions_last_30_days")), reverse=True)
        top_ae = ae_rows[0]

    # Highest-risk stalled trial: BDR + Free Trial, most days since last active
    stalled = [
        r for r in rows
        if "BDR" in r.get("routing_action", "")
        and "Trial" in r.get("lead_type", "")
    ]
    top_stalled = None
    if stalled:
        stalled.sort(key=lambda r: _safe_int(r.get("last_active_days_ago")), reverse=True)
        top_stalled = stalled[0]

    # Top suppressed account: first suppressed row
    suppressed = [r for r in rows if "Suppress" in r.get("routing_action", "")]
    top_suppressed = suppressed[0] if suppressed else None

    if not any([top_ae, top_stalled, top_suppressed]):
        return None

    return {
        "top_ae": top_ae,
        "top_stalled": top_stalled,
        "top_suppressed": top_suppressed,
    }


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.route("/")
def dashboard():
    rows = read_csv(GTM_REPORT_CSV)
    last_run = get_file_mtime(GTM_REPORT_CSV)

    stats = None
    insights = None
    if rows:
        counts = count_routing(rows)
        total = len(rows)
        pct = lambda n: round(n / total * 100) if total else 0
        stats = {
            "total": total,
            "ae": counts["ae"],
            "bdr": counts["bdr"],
            "cs": counts["cs"],
            "suppress": counts["suppress"],
            "ae_pct": pct(counts["ae"]),
            "bdr_pct": pct(counts["bdr"]),
            "cs_pct": pct(counts["cs"]),
            "suppress_pct": pct(counts["suppress"]),
        }
        annotated = annotate_funnel([dict(r) for r in rows])
        insights = get_insights(annotated)

    return render_template("dashboard.html", stats=stats, last_run=last_run, insights=insights)


@app.route("/run/leads", methods=["POST"])
def run_leads():
    result = run_script("score_leads.py", inject_icp=True)
    if result.returncode != 0:
        error = result.stderr or result.stdout or "Unknown error"
        flash(f"Lead engine failed:\n{error}", "error")
    return redirect(url_for("leads"))


@app.route("/run/trials", methods=["POST"])
def run_trials():
    result = run_script("score_trials.py", inject_icp=False)
    if result.returncode != 0:
        error = result.stderr or result.stdout or "Unknown error"
        flash(f"Trial engine failed:\n{error}", "error")
    return redirect(url_for("trials"))


@app.route("/run/funnel", methods=["POST"])
def run_funnel():
    result = run_script("run_gtm_engine.py", inject_icp=True)
    if result.returncode != 0:
        error = result.stderr or result.stdout or "Unknown error"
        flash(f"Full funnel engine failed:\n{error}", "error")
    return redirect(url_for("funnel"))


@app.route("/leads")
def leads():
    rows = read_csv(SCORED_LEADS_CSV)
    if rows:
        rows = annotate_leads(rows)
        scores = [r.get("score", "") for r in rows]
        summary = {
            "hot": scores.count("Hot"),
            "warm": scores.count("Warm"),
            "cold": scores.count("Cold"),
        }
    else:
        summary = None
    return render_template("leads.html", rows=rows, summary=summary)


@app.route("/trials")
def trials():
    rows = read_csv(SCORED_TRIALS_CSV)
    if rows:
        rows = annotate_trials(rows)
        counts = count_routing(rows)
        summary = counts
    else:
        summary = None
    return render_template("trials.html", rows=rows, summary=summary)


@app.route("/funnel")
def funnel():
    rows = read_csv(GTM_REPORT_CSV)
    if rows:
        rows = annotate_funnel(rows)
        counts = count_routing(rows)
        summary = {"total": len(rows), **counts}
    else:
        summary = None
    return render_template("funnel.html", rows=rows, summary=summary)


@app.route("/settings", methods=["GET", "POST"])
def settings():
    if request.method == "POST":
        config = {
            "target_industries": [
                l.strip() for l in request.form.get("target_industries", "").splitlines() if l.strip()
            ],
            "target_titles": [
                l.strip() for l in request.form.get("target_titles", "").splitlines() if l.strip()
            ],
            "company_size_min": int(request.form.get("company_size_min", 100)),
            "company_size_max": int(request.form.get("company_size_max", 2500)),
            "buying_signals": [
                l.strip() for l in request.form.get("buying_signals", "").splitlines() if l.strip()
            ],
            "disqualifier_industries": [
                l.strip() for l in request.form.get("disqualifier_industries", "").splitlines() if l.strip()
            ],
            "disqualifier_titles": [
                l.strip() for l in request.form.get("disqualifier_titles", "").splitlines() if l.strip()
            ],
        }
        CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2)
        flash("ICP settings saved. Next run will use updated criteria.", "success")
        return redirect(url_for("settings"))

    config = load_icp_config()
    return render_template("settings.html", config=config)


# ---------------------------------------------------------------------------
# Run
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
