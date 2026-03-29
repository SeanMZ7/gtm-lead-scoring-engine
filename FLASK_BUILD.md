I have a working GTM intelligence system built in Python. I need you to build a clean, professional Flask web UI on top of it. Here is everything you need to know before writing a single line of code.

THE EXISTING SYSTEM
The repo is called gtm-lead-scoring-engine. The structure is:
gtm-lead-scoring-engine/
├── data/
│   ├── dummy_leads.csv
│   └── dummy_trials.csv
├── outputs/
│   ├── scored_leads.csv
│   └── scored_trials.csv
│   └── gtm_intelligence_report.csv
├── scripts/
│   ├── score_leads.py
│   ├── score_trials.py
│   └── run_gtm_engine.py
Each script reads from the data/ folder, calls the Claude API, and writes results to outputs/. They already work and run clean. The Flask app must not modify these scripts. It wraps them.

WHAT TO BUILD
A Flask web app with 5 pages. Batch execution only — no streaming. Run the script, wait for results, display them. Reliability over animation.
FILE STRUCTURE TO CREATE
gtm-lead-scoring-engine/
├── app.py
├── config/
│   └── icp_config.json
├── templates/
│   ├── base.html
│   ├── dashboard.html
│   ├── leads.html
│   ├── trials.html
│   ├── funnel.html
│   └── settings.html
└── static/
    └── style.css

PAGE 1: DASHBOARD (route: /)
The home page. Shows the state of the last full run:

Page title: "GTM Brain"
Subtitle: "AI-powered GTM intelligence layer"
Four stat cards in a row: AE Fast-Track, BDR Sequence, CS Monitor, Suppressed — each showing count and percentage of total
A horizontal stacked bar showing routing distribution visually
Last run timestamp (read from gtm_intelligence_report.csv modified time, or "No run yet" if file doesn't exist)
Two large buttons: "Run Lead Engine" and "Run Trial Engine" — each triggers the corresponding script and redirects to that results page
One button: "Run Full Funnel" — runs run_gtm_engine.py and redirects to the funnel page
If no output files exist yet, show a clean empty state with a prompt to run the engine

PAGE 2: LEAD SCORING (route: /leads)

Button at top: "Run Lead Engine" — executes score_leads.py, refreshes page
Results table with columns: Company, Contact, Title, Industry, Score, Routing Action, Reason
Color-coded rows: green background for Hot/AE fast-track, purple for Warm/BDR, gray for Cold/Suppress
For any row with a BDR routing action: show a small "View email draft" toggle. Clicking it expands a text area below the row showing the full outreach_draft content
Summary line below table: Hot X | Warm X | Cold X
If no output file exists: show empty state with run button

PAGE 3: TRIAL CONVERSION (route: /trials)

Button at top: "Run Trial Engine" — executes score_trials.py, refreshes page
Results table with columns: Company, Contact, Title, Industry, Fit Score, Engagement Score, Routing Action, Reason
Same color coding as leads page but mapped to routing_action field
For BDR sequence rows: expandable email draft same as leads page
Summary line: AE Fast-Track X | BDR Sequence X | CS Monitor X | Suppressed X
If no output file exists: show empty state with run button

PAGE 4: FULL FUNNEL (route: /funnel)

Button at top: "Run Full Funnel Engine" — executes run_gtm_engine.py, refreshes page
Results table showing all 22 records with columns: Lead Type, Company, Contact, Title, Routing Action, Reason
Lead Type column shows "Lead" or "Trial" with a small badge
Same color coding
Expandable email drafts for BDR rows
Summary bar at top: Total Scored, AE Fast-Track, BDR Sequence, CS Monitor, Suppressed
If no output file exists: show empty state

PAGE 5: ICP SETTINGS (route: /settings)
This page lets a non-technical user update ICP criteria without touching code.

Load current settings from config/icp_config.json on page load
Form with these editable fields:

Target industries (textarea, one per line)
Target titles (textarea, one per line)
Company size min (number input)
Company size max (number input)
Buying signals (textarea, one per line)
Disqualifier industries (textarea, one per line)
Disqualifier titles (textarea, one per line)


Save button: writes form values back to config/icp_config.json
Show a green success message on save: "ICP settings saved. Next run will use updated criteria."
Default values in config/icp_config.json should match the current ICP in score_leads.py exactly

Default icp_config.json:
json{
  "target_industries": ["Manufacturing", "Facilities Management", "Healthcare", "Logistics / Warehousing", "Food and Beverage", "Energy / Utilities"],
  "target_titles": ["Operations Manager", "Facilities Director", "Maintenance Manager", "Plant Manager", "VP of Operations", "Reliability Engineer", "Director of Facilities", "Head of Facilities", "Head of Manufacturing Ops"],
  "company_size_min": 100,
  "company_size_max": 2500,
  "buying_signals": ["Job posting for maintenance role", "CMMS vendor evaluation", "RFP posted", "LinkedIn activity about maintenance pain", "Attended webinar or content", "High website engagement (30+ visits/30 days)"],
  "disqualifier_industries": ["Retail", "SaaS / Technology", "Consumer", "Government / Utilities"],
  "disqualifier_titles": ["HR", "Finance", "IT", "Customer Success", "Individual Contributor"]
}

NAVIGATION
Base template nav bar with links to all 5 pages. Active state on current page. Clean, minimal. No heavy CSS frameworks. Write plain CSS in static/style.css.

DESIGN REQUIREMENTS

Clean, professional, dark-sidebar or top-nav layout — your choice, but it must look like a real internal tool not a tutorial project
Color coding for routing actions must be consistent across all pages:

AE fast-track: green (#1a7a4a background, white text)
BDR sequence: purple (#5b3fa0 background, white text)
CS monitoring: amber (#b45309 background, white text)
Suppress: gray (#4b5563 background, white text)


Tables must be readable: alternating row shading, proper padding, no horizontal scroll on standard screen
Responsive enough to present on a laptop screen
No external CSS frameworks, no CDN dependencies. Everything must work fully offline during a live demo

EXECUTION REQUIREMENTS

Scripts are executed via Python subprocess from app.py
The ANTHROPIC_API_KEY must be passed from the environment into the subprocess. Do not hardcode it.
Each script run should show a loading state on the page ("Running engine, please wait...") before results appear
Handle errors gracefully: if a script fails, show the error message on the page rather than crashing
All output CSVs are read from the outputs/ directory after each run
The app runs on localhost:5000 with debug=False

START COMMAND
bash
python3 app.py

IMPORTANT

Plan the full structure before writing any code
Build app.py first, then base.html, then each page in order
Test that the app starts and each route returns a 200 before moving to the next page
Do not modify any existing scripts in the scripts/ folder
Do not hardcode any API keys anywhere