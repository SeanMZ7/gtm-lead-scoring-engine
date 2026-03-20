# SKILL.md — GTM Brain Operational Playbook

A guide for operating, evaluating, and tuning the lead scoring system. Written for a GTM or marketing operator who needs to run this without engineering support.

---

## When to Use This System

**Use it when:**
- You have a batch of 10–500 leads to prioritize and don't want reps manually researching each one
- You're kicking off a new outreach sequence and need to sort the list before enrolling anyone
- You've received a list from marketing, a tradeshow, or an SDR and want a first-pass filter
- You want to test whether a new lead source is producing ICP-fit accounts before investing further

**Don't use it when:**
- You have fewer than 5 leads — just score them manually, it's faster
- The lead data is thin (missing title, company size, industry for most rows) — garbage in, garbage out
- You need real-time scoring on a single inbound lead — this is a batch tool, not a live API endpoint
- You want to score leads already in an active sequence — risk of duplicating outreach

---

## Order of Operations for a Full Scoring Run

Follow this sequence every time for consistent, reliable results.

**1. Prepare your lead data**
- Export leads from your CRM, spreadsheet, or list source
- Format as CSV with the required columns (see README.md)
- Fill in as many fields as possible — especially `title`, `industry`, `company_size`, and `recent_signal`
- Remove duplicates and leads already in active sequences
- Save as `data/dummy_leads.csv` (replace the existing file)

**2. Open your terminal and activate the environment**
```bash
cd gtm-brain
source venv/bin/activate
```

**3. Confirm your API key is set**
```bash
echo $ANTHROPIC_API_KEY
```
If it returns blank, run: `export ANTHROPIC_API_KEY=sk-ant-...your-key...`

**4. Run the script**
```bash
python3 scripts/score_leads.py
```
Watch the terminal output. Each lead prints its score and reason as it's processed.

**5. Open the output**
Open `outputs/scored_leads.csv` in Excel or Google Sheets.

**6. Review and act**
- Sort by `score` column — Hot leads first
- Spot-check 3–5 scores against your own intuition (see evaluation section below)
- Copy Hot lead email drafts into your outreach tool or send queue
- Tag Warm leads for re-engagement in 30 days
- Archive or suppress Cold leads

---

## How to Evaluate Whether a Scoring Run Was Good

A run is good when the scores match what a sharp, experienced SDR would have called. Here's how to check:

**Quick gut-check (takes 5 minutes):**
1. Look at all Hot leads. Ask: would I personally prioritize outreach to these accounts this week? If yes for 80%+, the run is solid.
2. Look at all Cold leads. Ask: are there any accounts here I'd want to call? If yes, the ICP prompt needs tuning.
3. Read 3–4 `reason` fields. Are they specific? Do they reference the actual signal or gap? Vague reasons ("this lead doesn't fit the ICP") mean the model is uncertain — flag those rows for manual review.

**Red flags that signal a bad run:**
- More than 40% Hot — criteria are too loose
- Fewer than 10% Hot from a well-sourced list — criteria may be too strict or data is too thin
- Reason fields are generic or repetitive across many leads
- A known good account came back Cold, or a known bad account came back Hot

---

## How to Tune the ICP Prompt When Scores Feel Off

All scoring logic is in `scripts/score_leads.py` inside `ICP_SCORING_PROMPT`. Open that file in any text editor and find the block.

**Common tuning scenarios:**

**Too many Hots (criteria too loose):**
Add a stricter requirement. Example: change "buying signals: job postings" to "buying signals: active CMMS job postings specifically for a Maintenance Manager or higher role."

**Too many Colds (criteria too strict):**
Loosen a requirement or remove a disqualifier. Example: if healthcare facilities are coming back Cold, add "healthcare facilities management" explicitly to the ideal industries list.

**Scores are right but reasons are weak:**
Add this instruction to the prompt: "Be specific — reference the exact signal, title, or gap that determined the score. Do not write generic reasons."

**One specific industry keeps mis-scoring:**
Add an explicit note in the prompt. Example: "Note: government utilities are Cold due to slow procurement cycles, even if the title and size are ideal."

**After any edit:** Run the script on a small test batch (5–10 leads) and review the output before running your full list.

---

## How to Add a New Signal Column

If you want the scoring model to consider a new data point — say, `funding_round` or `g2_review_count` — here's how to add it end-to-end with no code changes needed.

**Step 1 — Add the column to your CSV**
Add a column header to `data/dummy_leads.csv` and fill in values for your leads. Example: add a `funding_round` column with values like `Series B`, `None`, or `Unknown`.

**Step 2 — Tell the model what to do with it**
In `ICP_SCORING_PROMPT`, add a line to the buying signals or scoring criteria section. Example:

```
- Recent funding (Series A or later) may indicate growth investment in operations infrastructure — treat as a mild positive signal
```

That's it. The model automatically reads all columns from the CSV and will now apply your new rule.

**Step 3 — Test on a small batch**
Run 5 leads that have varied values for the new column and confirm the scores shift the way you intended.

---

## How to Extend to a New Use Case

The system is built around a prompt — which means you can repurpose it for any scoring or drafting task by swapping the prompt.

**Example: Account re-engagement (churned customers)**

1. Copy `scripts/score_leads.py` to `scripts/score_reengagement.py`
2. Update `DATA_FILE` and `OUTPUT_FILE` paths to point to new files
3. Replace `ICP_SCORING_PROMPT` with a re-engagement rubric. Example criteria:
   - High → Churned within 12 months, had 5+ users, left due to price not product
   - Medium → Churned 12–24 months ago, mid-sized account, reason unknown
   - Low → Churned 3+ years ago, single user, left due to product gaps now addressed

4. Update the email drafting instructions to fit re-engagement context ("We've made a lot of changes since you left...")
5. Run: `python3 scripts/score_reengagement.py`

The same pattern works for: competitive displacement campaigns, upsell/expansion scoring, event invite prioritization, or partner scoring.

---

## Common Failure Modes and Fixes

**Script exits immediately with "ANTHROPIC_API_KEY environment variable is not set"**
Your API key isn't loaded in this terminal session.
Fix: `export ANTHROPIC_API_KEY=sk-ant-...your-key...` then re-run.

**Script exits with "pip: command not found" or import errors**
Your virtual environment isn't activated.
Fix: `source venv/bin/activate` then `pip install anthropic` then re-run.

**Output CSV is empty or has only headers**
The script ran but all API calls failed, or the input CSV was empty.
Fix: Check that `data/dummy_leads.csv` has data rows. Check your API key has credits at console.anthropic.com.

**Score column contains "?" for some leads**
The model returned a response the parser couldn't read — usually happens when the model adds explanation outside the JSON.
Fix: Re-run the script. If it persists for specific leads, check if those rows have unusual characters (quotes, commas inside fields) in the CSV.

**Email drafts are generic / sound templated**
The lead data was too thin — the model had nothing specific to personalize with.
Fix: Enrich those leads with a real signal (LinkedIn activity, job posting, website data) in the `recent_signal` or `notes` column and re-run.

**All leads came back the same tier**
Either the data is uniformly good/bad, or the prompt criteria are miscalibrated.
Fix: Check your input data first. If it's varied, open the prompt and check whether the Hot/Warm/Cold definitions are clearly differentiated.

**Script is slow (takes more than 30 seconds per lead)**
Normal — each lead makes one API call, and the model is writing a full email for Hot leads. 10 leads typically takes 2–4 minutes total.
No fix needed unless you're running hundreds of leads at once.
