# PROBLEM_STATEMENT.md — GTM Brain

---

## The Business Problem

Runs on a three-tier outreach strategy — hot, warm, and cold sequences — but the assignment of leads to those tiers is done manually, inconsistently, and without synthesizing the signals that actually predict fit and intent. A rep looks at a name, a title, and maybe a company, and makes a judgment call. That call is only as good as their experience, their energy that day, and their familiarity with the ICP.

The deeper problem is data synthesis. Signals — website visits, job postings, content engagement, current solution data, firmographic fit — but they live in disconnected places. No single rep is pulling all of those threads before deciding whether to write a personalized email or drop someone into a generic cadence. The result is that genuinely hot leads get treated like warm ones, warm leads get ignored, and reps burn time crafting emails to accounts that will never convert.

Jake described this as a prioritization problem masquerading as a volume problem. The pipeline isn't thin because there aren't enough leads — it's thin because the right leads aren't getting the right treatment fast enough.

---

## Why The Current State Fails

When lead scoring is manual and inconsistent, three things break down operationally:

**Pipeline velocity slows.** Hot leads that should get a same-day personalized touch sit in a generic sequence. By the time a rep escalates them, a competitor has already had the discovery call.

**Rep capacity gets wasted.** Time spent researching, scoring, and writing first-touch emails for 20 leads is time not spent closing the three accounts that were actually ready to buy. At mid-market deal sizes, that tradeoff is expensive.

**Personalization at scale is impossible without a system.** A great rep can write five excellent personalized emails a day. That doesn't scale to a 200-lead list. The choice becomes: send generic emails to everyone, or personalize for a few and ignore the rest. Neither is right.

The compounding effect is a pipeline that feels full but converts poorly — because fit and timing were never properly evaluated at the top of the funnel.

---

## The System I Built

The GTM Brain is an MVP lead scoring and signal trigger system. It takes a list of leads in CSV format, sends each one to Claude (Anthropic's API) with a structured ICP rubric, receives a Hot/Warm/Cold score with a one-sentence rationale, and for Hot leads, automatically drafts a personalized first-touch email grounded in the lead's specific context.

The system makes three decisions automatically:

1. **Tier assignment** — Is this lead worth prioritizing? Based on title authority, industry fit, company size, current solution, and buying signals.
2. **Reasoning** — Why did this lead get this score? Every output includes an explicit rationale, not just a label.
3. **First-touch email** — For Hot leads, a personalized email that references the specific company, role, signal, and pain point — not a template with `{{first_name}}` filled in.

All results are saved to `outputs/scored_leads.csv` for review, CRM upload, or downstream automation. The source data is never touched.

---

## Design Decisions & Why

**1. Claude API for scoring, not hardcoded if/else logic.**
A rules engine would score on individual attributes in isolation. A language model reasons across all signals simultaneously — it can recognize that a Facilities Manager at a 300-person manufacturer who just posted a job for a Maintenance Coordinator and has 47 website visits is a different situation than one who has none of those signals, even if both match on title and industry. That compound reasoning is where the value lives.

**2. Model: claude-opus-4-6.**
This is a prioritization and personalization task, not a classification task. Cheaper/faster models would score correctly on easy cases but miss nuance — wrong-level titles, borderline industries, signals that only matter in context. At the MVP stage, output quality matters more than cost-per-call. Speed can be optimized later.

**3. Scoring criteria embedded in the prompt, not in code.**
The ICP evolves. What counts as a buying signal changes as the sales team learns. By keeping the scoring rubric in a prompt rather than in conditional logic, a GTM manager can update the criteria without touching code. This is a deliberate choice to keep the system maintainable by non-engineers.

**4. Personalized email drafts triggered automatically for Hot leads only.**
Writing emails for Warm leads at this stage is premature — Warm leads need a different motion (nurture, not outreach). Automating email drafts for Cold leads would be wasteful and potentially counterproductive. Hot leads are the highest-leverage use of AI-generated personalization because the stakes of a bad first impression are highest when the lead is actually winnable.

---

## What I Would Build Next

**Iteration 2 — Live signal enrichment (Week 1-2)**
Connect to real data sources: LinkedIn job postings via scraping or an enrichment API (Clearbit, Apollo, Clay), BuiltWith for current tech stack, and intent data from Bombora or G2. Right now the system scores what's in the CSV. The next version would pull fresh signals at runtime, score leads on current state, and flag accounts that have moved from Cold to Hot since the last run. Business outcome: the scoring system stays current without manual data updates.

**Iteration 3 — CRM integration + rep workflow trigger (Week 3-4)**
Push scored results directly into HubSpot or Salesforce. Hot leads get auto-enrolled in the correct sequence, assigned to the right rep, and the drafted email lands in their outbox as a draft — not a sent email — so they can review and send with one click. Warm leads get tagged and queued for a follow-up scoring pass in 30 days. Cold leads get suppressed from active outreach. Business outcome: the scoring system stops being a report and starts being a workflow. Reps spend zero time on triage and all their time on conversations.

---

## Known Limitations

**Dummy data, not real pipeline.** The CSV is hand-crafted to be interesting. A production version needs to pull from a live CRM or enrichment tool, and the scoring prompt needs to be validated against real closed-won and closed-lost data.

**No feedback loop.** The model scores leads but doesn't learn from outcomes. If a lead scored Cold converts, or a Hot lead goes dark, that signal never improves the system. A production version needs a mechanism to log rep feedback and outcomes and use them to refine the scoring criteria.

**Email drafts are not reviewed for tone fit.** The personalization is contextually accurate but hasn't been calibrated to actual brand voice, sequence timing, or what messaging has historically worked. These drafts are a starting point, not a send-ready asset.

**No deduplication or CRM sync.** Running the script twice scores the same leads twice. A production version needs to check against existing CRM records before scoring and avoid creating duplicate outreach.

**Cost scales linearly.** At current API pricing, scoring 1,000 leads costs meaningfully more than scoring 10. This is acceptable for a prioritized batch process but would need optimization — caching, cheaper models for initial filter passes, or tiered scoring — before running against a full database.
