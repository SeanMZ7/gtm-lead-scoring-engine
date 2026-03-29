# PROBLEM_STATEMENT.md

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

The GTM Brain is an AI-powered GTM intelligence layer. It addresses four challenges through a single connected architecture:

**1. Lead quality scoring.** Inbound and outbound leads are scored Hot/Warm/Cold against a structured ICP rubric — title authority, industry fit, company size, current solution, offer type, channel source, and buying signals — using Claude AI reasoning. Every output includes an explicit rationale, not just a label.

**2. Outbound personalization.** For Hot leads, the system automatically drafts a personalized first-touch email grounded in the lead's specific context: company name, role, signal, and pain point. No template with `{{first_name}}` filled in.

**3. Trial conversion routing.** Free trial users are scored on two dimensions simultaneously — ICP fit AND behavioral engagement using Mixpanel signals. The system routes each user to one of four actions: AE fast-track via ChiliPiper, BDR sequence via Outreach, CS monitoring, or suppression. Trial users who score high on engagement but low on ICP fit are identified as product-led growth candidates rather than discarded.

**4. Unified full-funnel view.** A single orchestrator runs both scoring scripts in sequence and produces a unified report across leads and trial users. One GTM operator can see the full funnel — inbound leads, outbound targets, and trial users — from a single interface.

All results are saved to `outputs/` for review, CRM upload, or downstream automation. Source data is never touched.

---

## Design Decisions & Why

**1. Claude API for scoring, not hardcoded if/else logic.**
A rules engine would score on individual attributes in isolation. A language model reasons across all signals simultaneously — it can recognize that a Facilities Manager at a 300-person manufacturer who just posted a job for a Maintenance Coordinator and has 47 website visits is a different situation than one who has none of those signals, even if both match on title and industry. That compound reasoning is where the value lives.

**2. Model: claude-sonnet-4-6.**
This is a prioritization and personalization task, not a classification task. Cheaper/faster models would score correctly on easy cases but miss nuance — wrong-level titles, borderline industries, signals that only matter in context. At the MVP stage, output quality matters more than cost-per-call. Speed can be optimized later.

**3. Scoring criteria embedded in the prompt and config file, not in code.**
The ICP evolves. What counts as a buying signal changes as the sales team learns. By keeping the scoring rubric in a prompt and in `config/icp_config.json` rather than in conditional logic, a GTM manager can update the criteria without touching code.

**4. Flask web UI — non-technical GTM operators can run the system without touching the terminal.**
Scoring scripts that only run from the terminal create a dependency on engineers. The Flask UI removes that dependency entirely. Any GTM operator can run a scoring pass, view results in a sortable table, and export to CSV from a browser. The system is self-service from day one.

**5. ICP Settings page — scoring criteria are maintainable without engineering support.**
A dedicated settings page backed by `config/icp_config.json` means a GTM manager can update industries, company size ranges, ideal titles, and disqualifiers through a form. No code deployment required. The criteria evolve with the market, not with the engineering sprint cycle.

**6. Personalized email drafts triggered automatically for Hot leads only.**
Writing emails for Warm leads at this stage is premature — Warm leads need a different motion (nurture, not outreach). Automating email drafts for Cold leads would be wasteful and potentially counterproductive. Hot leads are the highest-leverage use of AI-generated personalization because the stakes of a bad first impression are highest when the lead is actually winnable.

**7. Two-dimensional trial scoring.**
A trial user who is a poor ICP fit but highly engaged is not the same as one who is a poor ICP fit and disengaged. The two-dimensional model identifies product-led growth candidates that a one-dimensional score would miss, and avoids routing PLG users into an enterprise AE motion that won't convert them.

---

## What I Would Build Next

See [ROADMAP.md](ROADMAP.md) for the full V2 through V4 plan.

The short version: V2 replaces CSV inputs with live API connections to HubSpot, Mixpanel, ZoomInfo, and Salesforce. The scoring logic, routing decisions, and email drafts are already production-ready — the only change is the data pipe. V3 expands into proactive signal detection and MadKudu displacement. V4 moves from decision support to autonomous execution.

---

## Known Limitations

**Dummy data, not real pipeline.** The CSVs are hand-crafted to be interesting. A production version needs to pull from a live CRM or enrichment tool, and the scoring prompt needs to be validated against real closed-won and closed-lost data.

**No feedback loop.** The model scores leads but doesn't learn from outcomes. If a lead scored Cold converts, or a Hot lead goes dark, that signal never improves the system. A production version needs a mechanism to log rep feedback and outcomes and use them to refine the scoring criteria.

**Email drafts are not reviewed for tone fit.** The personalization is contextually accurate but hasn't been calibrated to actual brand voice, sequence timing, or what messaging has historically worked. These drafts are a starting point, not a send-ready asset.

**No deduplication or CRM sync.** Running the script twice scores the same leads twice. A production version needs to check against existing CRM records before scoring and avoid creating duplicate outreach.

**Cost scales linearly.** At current API pricing, scoring 1,000 leads costs meaningfully more than scoring 10. This is acceptable for a prioritized batch process but would need optimization — caching, cheaper models for initial filter passes, or tiered scoring — before running against a full database.

**Subprocess architecture is MVP-appropriate, not production-grade.** Flask calling scripts via subprocess works fine for a demo. A production version replaces this with direct function calls or a task queue (Celery, RQ) to handle concurrency, timeouts, and error recovery properly.
