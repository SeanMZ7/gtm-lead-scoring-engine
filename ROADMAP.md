# ROADMAP.md — GTM Brain Product Roadmap

## Current State — V1 (Shipped March 2026)

A fully working AI-powered GTM intelligence layer running on mock data with a five-page Flask web UI. Addresses four of five brief challenges through a single connected architecture.

**What works today:**
- ICP fit scoring for inbound and outbound leads using Claude AI reasoning across title, industry, company size, offer type, channel source, buying signals, and geography
- Two-dimensional trial user scoring on ICP fit AND behavioral engagement using mocked Mixpanel signals
- Four-tier routing engine: AE fast-track via ChiliPiper, BDR sequence via Outreach, CS monitoring, suppression
- Personalized outreach drafts for BDR-routed leads referencing specific signals and behavioral data
- Speed-to-lead urgency flagging for Demo Request leads
- Unified full-funnel report across leads and trial users
- Non-technical ICP settings editor — no code required
- Export to CSV from every results page

---

## V2 — Live Data Integration (Weeks 1-2 post-hire)

**Goal:** Replace CSV inputs with live API connections. The scoring logic, routing decisions, and email drafts are already production-ready. The only change is the data pipe.

**CRM webhook integration**
- Trigger score_leads.py automatically on every new MQL created in HubSpot
- Write scoring results and routing action back to the HubSpot contact record as custom properties
- Hot leads auto-enrolled in ChiliPiper booking flow
- Warm leads auto-enrolled in Outreach BDR sequence
- Cold leads suppressed from active outreach automatically

**Mixpanel export integration**
- Nightly Mixpanel export feeds score_trials.py with real trial user behavioral data
- Trial users scored automatically each morning
- AE fast-track results trigger ChiliPiper booking invitation to the trial user
- BDR sequence results push personalized email draft to rep outbox in Outreach as a draft — not sent automatically, rep reviews and sends with one click

**ZoomInfo enrichment layer**
- Enrich inbound leads at scoring time with ZoomInfo firmographic data: employee count, revenue, tech stack, recent funding
- Eliminates reliance on self-reported company size and industry from form fills
- Scoring accuracy improves significantly with verified data

**Salesforce sync**
- Write scoring results to Salesforce lead and contact records
- Routing action becomes a Salesforce field visible to AEs and BDRs in their existing workflow
- No new tool adoption required from the sales team

---

## V3 — Intelligence Layer Expansion (Weeks 3-6)

**Goal:** Extend the system from reactive scoring to proactive signal detection.

**Intent signal monitoring**
- Connect HG Insights technographic data to identify accounts currently running legacy CMMS competitors (IBM Maximo, SAP PM, Hippo CMMS)
- Flag accounts where the tech stack signals an active evaluation window
- Feed these signals into the lead scoring prompt as additional buying intent indicators

**MadKudu displacement**
- Current MadKudu scoring is static ML model trained on historical data
- GTM Brain replaces MadKudu with Claude-based reasoning that evaluates compound signal combinations the way a sharp SDR would
- Advantage: scoring criteria update in minutes via prompt edit, not weeks via model retraining
- Implement A/B comparison: run both systems in parallel for 30 days, measure SAO conversion rate by scoring source

**Channel efficiency reporting**
- Addresses Challenge 5 from the brief: marketing spend efficiency
- Pull Google Ads, LinkedIn Ads, and Bing Ads performance data via API
- Score each channel and campaign against SAO conversion rate, not just CPL
- Surface anomalies automatically: campaigns with high spend and low SAO conversion flagged for budget reallocation
- Add a sixth page to the Flask UI: Channel Intelligence

**Feedback loop**
- Log rep acceptance and rejection of BDR email drafts
- Log deal outcomes tied back to lead scores
- Use outcome data to refine ICP scoring prompt automatically over time
- System gets smarter with every rep interaction

---

## V4 — Autonomous GTM Agent (Month 2-3)

**Goal:** Move from a decision-support system to an autonomous execution layer.

**Orchestration via n8n**
- Replace subprocess calls with n8n workflow orchestration
- Workflows trigger on CRM events, time schedules, and behavioral thresholds
- Visual workflow editor gives non-engineers visibility into what the system is doing and why

**Multi-touch sequence personalization**
- V1 drafts one email per lead
- V4 drafts the full multi-touch sequence: email 1 (first touch), email 2 (follow-up with new angle), LinkedIn connection request, email 3 (breakup)
- Each touch references what happened since the last one — opened but didn't reply, visited pricing page, attended webinar

**Voice agent integration**
- High-priority Demo Request leads trigger an AI voice agent call within 5 minutes of form submission
- Agent qualifies the lead, answers basic product questions, and books the AE meeting
- Addresses the speed-to-lead problem at a level no human BDR team can match

**Self-optimizing ICP**
- System monitors its own scoring accuracy against closed-won and closed-lost data
- Proposes ICP criteria updates based on what actually converted
- GTM manager reviews and approves changes in the settings page
- ICP definition evolves with the market automatically

---

## Success Metrics

| Metric | V1 Baseline | V2 Target | V3 Target |
|---|---|---|---|
| Time to score new MQL | Manual | < 30 seconds | < 10 seconds |
| BDR time on triage | ~40% of day | < 10% of day | < 5% of day |
| Demo request speed-to-lead | Variable | < 2 hours | < 5 minutes |
| Trial-to-SAO conversion | Known gap | +20% lift | +40% lift |
| Scoring consistency | 0% (manual) | 100% | 100% |

---

## Guiding Principles

**Prompt over code.** Scoring logic lives in prompts, not conditional statements. Non-engineers can update criteria without engineering support.

**Reps review, systems route.** Automation handles triage and drafting. Humans handle relationships and judgment calls. The system never sends an email without rep review.

**One operator, full-funnel visibility.** The goal is one GTM engineer running intelligence across the entire funnel — inbound leads, outbound targets, and trial users — from a single interface.

**Build for the stack you have.** Every integration in this roadmap uses tools already in the GTM stack. No new vendor relationships required for V2 or V3.
