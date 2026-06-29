"""
Canon Playbooks (SOPs) — all 12 SOPs from Notion database.
Source: Playbooks (SOP) database, Google Ads Canon workspace.
"""

SOPS = {
    "Account Audit (Full)": {
        "id": "SOP-0002",
        "lifecycle": "Setup | Quarterly",
        "modules": "Search | PMax | Tracking | MC",
        "steps": """
Step 1 — Context & success definition
  Inputs: Business context brief
  Define: primary KPI (CPA/ROAS), geo, margins/constraints, seasonality, what counts as a conversion
  Output: 5–10 lines of context + KPI targets

Step 2 — Measurement sanity gate (Ads ↔ GA4 ↔ Shopify/CRM)
  Inputs: Ads Conversions summary, GA4 Conversions summary, GA4 DebugView, Shopify Orders
  Check: conversion lists, Primary/Secondary, value/currency, counting, windows, imports
  Evidence: 1–3 recent orders/leads → find end-to-end traces in GA4 and Ads
  Red flags: Shopify has orders, GA4/Ads = 0; duplicate purchase; wrong value/currency
  Output: tracking alignment notes → if problem → add to Fixlist as P0

Step 3 — Change-history context (7–30 days)
  Inputs: Ads Change history
  Check: major changes (budget, bidding, goals, PMax settings, feed/MC changes)
  Red flags: KPI dropped immediately after a change
  Output: list of changes + hypothesis "what could have shifted KPI"

Step 4 — Account-level hygiene & guardrails
  Check: auto-tagging, account-default goals, location options, auto-apply recommendations
  Red flags: auto-tagging OFF, bidding optimizes to wrong conversion, auto-apply enabling risky changes
  Output: Fixlist (P0/P1) + guardrails

Step 5 — Search performance audit (structure → queries → ads)
  Inputs: Campaigns performance, Search terms (30d)
  Scan: spend/conversions/value by campaigns, devices, geo; brand vs non-brand share
  Search terms: Winners / Waste / Irrelevant → negatives plan + keyword add list
  Output: Search block + specific actions (max 5–10 items)

Step 6 — PMax audit (control surfaces + goals)
  Check: campaign goals vs account goals, URL expansion, brand exclusions, asset governance
  Gate: if ecom and MC P0 issues exist → MC triage first, then PMax
  Output: PMax block + 1–3 "safe" changes per iteration + verify plan

Step 7 — Merchant Center health (if ecom)
  Inputs: MC Diagnostics, Product status sample, Shipping settings, Feed rules/transformations
  Classify: account issues vs item issues; P0 (price/shipping/availability) vs P1
  Output: Feed/MC fixlist + what blocks impressions/ROAS

Step 8 — Synthesis & prioritization
  Consolidate: everything from previous steps → one Fixlist
  Rule: P0 (data/impressions/policies) → P1 (systematically hurts KPI) → P2 (quality/optimization)
  Output: Audit + Fixlist (priority, owner, effort)

Step 9 — Minimal change set + verification schedule
  Choose: 1–3 changes with highest impact and lowest risk
  Log: Actions log (what, why, expected impact)
  Verify: 24–72h (tracking/MC), 7–14 days (KPI)
  Output: next-14-days plan + verify thresholds

Done criteria:
  - Audit summary: what is OK, what is broken, what blocks growth (P0/P1/P2)
  - Tracking alignment Ads ↔ GA4 ↔ (Shopify/CRM) with evidence from min 2 systems
  - Fixlist with priorities (P0/P1/P2), Owner, Effort (S/M/L), Verify after, Rollback per item
  - Actions log: what was changed during audit + date/who/why
  - Separate insight blocks: Search, PMax, Merchant Center, Tracking
  - Next 14 days plan: 1–3 changes in first iteration + KPI/verify thresholds
""",
    },

    "Tracking QA + Incident Response": {
        "id": "SOP-0005",
        "lifecycle": "Incident",
        "modules": "Tracking",
        "steps": """
Step 1 — Define the incident
  Goal: document exactly what broke and when it started
  Check: which conversion/campaign/geo/device is affected; what we see in Ads/GA4/Shopify
  Red flags: 0 conversions, drop >50% with stable traffic, Shopify has orders but Ads/GA4 = 0

Step 2 — Collect minimum evidence (1–3 examples)
  Inputs: GA4 DebugView/Realtime, Shopify Orders (if ecom), Ads Change history
  Check: for 1–3 recent orders/leads find traces: GA4 event, purchase/value/currency, Ads conversion
  Red flags: Shopify/CRM has data, GA4 doesn't; GA4 has data, Ads doesn't; value/currency missing

Step 3 — Google Ads conversion goals sanity
  Inputs: Ads → Tools → Conversions → Summary
  Check: Primary/Secondary, Status, Account-default goals, Source (Website/GA4 import)
  Red flags: wrong Primary for bidding, disabled conversion, default goals are incorrect

Step 4 — Conversion action settings
  Inputs: Ads Conversions summary (settings)
  Check: Counting (One/Every), Window, Value settings
  Red flags: Every instead of One for leads, window too short/long, value/currency mismatch

Step 5 — Linkage / tagging sanity
  Check: GA4 linked to Ads, auto-tagging enabled, GA4 imports didn't accidentally become Primary
  Red flags: no link, auto-tagging OFF, GA4 imports became Primary unintentionally

Step 6 — Classify root cause
  Classes: Consent/Tag, GA4 import/config, duplicate events, checkout/site change, outage
  Decision: choose 1–2 most likely root causes (not 10), document hypotheses

Step 7 — Apply minimal fix + contain damage
  Action: apply minimal necessary change (settings/tag/link)
  If outage: create Data exclusion window for the period of "broken" data

Step 8 — Verify after change
  Inputs: GA4 DebugView, Ads conversions
  Check: test/real conversion passes end-to-end (GA4 → Ads)
  Red flags: event appears in only one system

Step 9 — Close incident
  Output: Incident report + Fixlist (with verify + rollback per item)

Done criteria:
  - Impact window (start/end) and what was affected
  - Evidence from at least 2 systems (Ads+GA4 or Shopify+GA4)
  - Fixlist: each item has Owner, Verify after, Rollback
  - If outage/broken data: Data exclusion window created or explicitly noted why not needed
""",
    },

    "Weekly Optimization Loop": {
        "id": "SOP-0007",
        "lifecycle": "Weekly",
        "modules": "Search | PMax | MC",
        "steps": """
Step 1 — Weekly health gates (15 min)
  Inputs: Campaigns+Ad groups mapping, MC Diagnostics (if ecom)
  Check: no sharp anomalies (0 conv, spend spike, disapprovals)
  Decision: if P0 → stop optimization, run Incident/MC triage

Step 2 — Budget & pacing
  Check: spend vs budget, campaigns with under/overspend, limited by budget
  Action: redistribute budget only with clear ROI/CPA rationale
  Output: 1–3 budget changes (if needed) + log

Step 3 — Performance scan by campaign type
  Inputs: Campaigns+Ad groups mapping
  Check: ROAS/CPA, CVR, AOV/value, device, geo
  Output: list "Scale / Hold / Fix / Pause" per campaign

Step 4 — Search terms cleanup (30d rolling)
  Inputs: Search terms export
  Action: add winners as keywords, add waste as negatives, update exceptions
  Output: Negative updates + Keyword add list (if relevant)

Step 5 — PMax governance mini-check
  Check: goals, URL expansion, brand exclusions, assets governance, last changes
  Rule: no major changes every week without reason
  Output: 0–1 change or "no change, monitor"

Step 6 — Test/iteration decision
  Choose: 1 hypothesis per week (offer/landing/structure/bidding)
  Define: KPI, success threshold, verification date

Step 7 — Log & verify plan
  Output: Weekly report (1-page) + Fixlist update + Actions log
  Verify: next week check effect of each change (after learning/lag)

Done criteria:
  - Weekly Report filled: what changed WoW, what got better/worse and why
  - Health gates checked: tracking sanity + MC P0 issues (if ecom)
  - 1–3 changes per week (not 10), all in Actions log with Verify after + Rollback
  - Fixlist updated: closed/added tasks, priorities
  - Next-week verification plan (KPI + thresholds)
""",
    },

    "Search Terms Cleanup": {
        "id": "SOP-0009",
        "lifecycle": "Weekly",
        "modules": "Search",
        "steps": """
Step 1 — Prepare export
  Inputs: Ads export: Search terms (30d)
  Check: columns Campaign, Ad group, Search term, Match type, Cost, Clicks, Conversions, Conv value
  Red flags: no conversion/value columns or no campaign/ad group mapping

Step 2 — Segment terms
  Buckets: Winners / Neutral / Waste / Irrelevant / Info intent / Competitor
  Red flags: high spend with 0 conv, systemic "info intent" spend

Step 3 — Winners → keyword add list
  Rule: terms with conversions and acceptable KPI → add as phrase/exact to correct ad groups
  Output: Keyword add list (keyword, match, target, rationale)

Step 4 — Waste → negative updates
  Rule: irrelevant/empty spend → negatives at right level (AG/Campaign/List)
  Red flags: risk of blocking useful queries → add Exceptions/Conditions
  Output: Negative list updates

Step 5 — Hygiene checks (optional)
  Check: Search Partners / Display expansion / auto-apply recs (if applicable)
  Decision: disable only with clear reason, otherwise log as "to test"

Step 6 — Log + verify
  Verify: after 3–7 days: waste spend ↓, CPA/ROAS ↑, coverage didn't collapse
  Output: Search terms report + verify plan

Done criteria:
  - 3 artifacts created: Search terms report, Negative list updates, Keyword add list
  - Each recommendation backed by metrics (Cost, Conversions, Conv value) and period
  - Risky negatives have Exceptions/Conditions
  - Verify date/threshold set (3–7 days) with pass/fail criteria
""",
    },

    "Merchant Center Triage": {
        "id": "SOP-0010",
        "lifecycle": "Weekly | Incident",
        "modules": "Feed | MC",
        "steps": """
Step 1 — Snapshot diagnostics
  Inputs: MC Diagnostics + Product status sample
  Classify: Account issues vs Item issues; impacted products %
  Output: list of issues with severity (P0/P1/P2)

Step 2 — P0 triage first
  P0 typically: price mismatch, availability mismatch, shipping issues, account suspension, policy blocks
  Action: select 1–3 P0 root causes (not 10)
  Output: P0 shortlist + hypothesis of source (feed/site/shipping settings)

Step 3 — Identify source of truth
  Inputs: Feed rules/transformations, Shipping settings, site (if accessible)
  Check: where price/availability/shipping comes from, any discrepancy between feed and site
  Red flags: shipping rate missing/doesn't cover countries, site prices differ from feed

Step 4 — Apply fixes (minimal, testable)
  Fix options: feed rules, shipping settings, site fixes, GTIN/identifiers, structured data
  Guardrail: don't break other attributes; 1–3 changes per iteration
  Output: Feed fixlist (what changes, where, expected impact)

Step 5 — Reprocess & request review (if needed)
  Action: trigger fetch/reprocess (where available), or wait for auto refresh
  If review required: complete Review request checklist and submit
  Output: review request timestamp + what was submitted

Step 6 — Validate recovery
  Inputs: Product status sample + Diagnostics after update
  Check: issue count ↓, approved items ↑, "eligible" status
  Output: Validation notes + re-check date (24–72h)

Step 7 — Ads impact mitigation (if urgent)
  If many disapprovals: temporarily reduce budgets/put hold on PMax optimizations
  Output: actions logged + recovery plan

Done criteria:
  - All issues classified: Account vs Item, P0 vs P1 vs P2
  - P0 issues (price/shipping/availability/policy) either closed or have Feed fixlist with Owner + ETA
  - If review needed: Review request checklist completed and submitted
  - Validation notes: what was checked after fix (reprocess/feed fetch, product status sample)
  - Ads impact documented and mitigation plan until full recovery
""",
    },

    "Quarterly Optimization Review": {
        "id": "SOP-0001",
        "lifecycle": "Quarterly",
        "modules": "Attribution | Reporting | Tracking | Search | PMax | MC | Feed",
        "steps": """
Step 1 — Data quality gate (don't start optimization blind)
  Input: Looker, Campaigns perf, Search terms, Change history, GA4 conv summary, Shopify orders, MC diagnostics
  Check: all must-haves present, period = full quarter, metrics consistent across sources
  Red flags: missing must-haves, period <60 days, Shopify has orders but Ads/GA4 = 0
  Action: if missing → work in "partial review" mode, explicitly note Missing inputs and limitations
  Output: Quarterly Report → Data quality, Missing inputs list

Step 2 — Tracking & attribution gate (P0 blocks optimization)
  Input: Ads conversions settings + GA4 conversions summary
  Check: primary conversion correct, counting/values/windows adequate, auto-tagging ON, no duplicates
  Red flags: "No recent conversions", primary = micro, sharp attribution gap, duplicates
  Action: if P0 → Fixlist P0, stop "optimization" until measurement stabilizes
  Output: Findings + Fixlist (P0) + Tracking section

Step 3 — KPI snapshot (Quarter vs Previous Quarter)
  Input: Looker Studio / Ads summary (Spend, Conv, Value, CPA, ROAS, CVR, CPC)
  Check: QoQ trends, where it dropped/grew, whether KPI matches goals
  Red flags: spend↑ with ROAS↓/CPA↑, conv/value dropping without explanation
  Action: classify problem: Demand / Auction / Structure / Tracking / Feed
  Output: KPI table + Summary (3 main changes)

Step 4 — Budget & spend allocation
  Input: Ads export: Campaigns (performance)
  Check: top campaigns by spend, share of spend, efficiency
  Red flags: 1–2 campaigns consumed most budget without KPI, scattered budget without focus
  Output: Findings + Fixlist (P1/P2) + reallocation proposal

Step 5 — Change history correlation (causality)
  Input: Ads Change history + business context changes
  Check: whether KPI shifts correlate with specific changes
  Red flags: major changes without plan/validation, frequent bid/goal changes → learning reset
  Output: Findings + Incident timeline if clear before/after

Step 6 — Search terms & intent quality
  Input: Search terms (30d/Quarter) + Campaign mapping
  Check: share of relevant queries, negatives hygiene, brand vs non-brand
  Output: Fixlist + Experiments (semantic tests)

Step 7 — PMax control surfaces
  Input: PMax settings + asset group performance
  Check: URL control, brand exclusions, assets coverage, learning stability
  Output: Findings + Fixlist + Experiments

Step 8 — Feed / Merchant Center (if Shopping/PMax feed-driven)
  Input: MC Diagnostics
  Check: disapprovals, price/availability mismatch, GTIN issues, policy/account issues
  Output: Findings + Fixlist (P0/P1) + Feed section

Step 9 — Quarter conclusions: Stop / Start / Continue
  Input: all findings
  Action: finalize plan for next quarter (Now/Next/Later)
  Output: Action plan + Fixlist with Verify after

Step 10 — Experiments roadmap (next quarter)
  Input: growth opportunities + quarter failures
  Check: 3–7 hypotheses with success metrics and decision rules
  Output: Experiments table

Step 11 — Context Delta
  Input: project context, constraints, promo/seasonality, margin, goals
  Check: what changed and what impacts next quarter
  Output: Context Delta block

Done criteria:
  - KPI table: quarter vs previous quarter
  - Data quality block: what was/wasn't available
  - Tracking/Attribution gate checked (P0): primary conversion, counting, windows, auto-tagging
  - Min 5 Findings with evidence (references/numbers)
  - Fixlist with Priority P0/P1/P2, Owner, Verify after
  - Experiments backlog with min 3 hypotheses for next quarter
  - Change history analysis: what could have caused shifts
  - "Stop / Start / Continue" conclusion on key directions
  - Context Delta filled (what changed in business/goals/constraints)
""",
    },

    "Quarterly Reporting": {
        "id": "SOP-0011",
        "lifecycle": "Quarterly",
        "modules": "Reporting | Attribution",
        "steps": """
Step 1 — Define period & baseline
  Define: quarter (dates), KPI targets, what counts as a conversion
  Output: report frame

Step 2 — Data integrity & attribution notes
  Inputs: GA4 Conversions summary, Ads Conversions settings, Change history
  Check: whether goals/conversions/attribution changed, any data gaps
  Output: Data quality section

Step 3 — Executive summary (1 page)
  Inputs: Looker Studio + Campaigns (performance)
  Summarize: spend, conv, revenue/value, CPA, ROAS + QoQ delta
  Output: top-line table + 3 conclusions

Step 4 — Breakdown: channel / campaign type / product category
  Inputs: Campaigns performance, MC Diagnostics (context), Shopify orders (validation)
  Analyze: what drives revenue/CPA, where it is declining
  Output: 2–4 charts/tables + commentary

Step 5 — Search insights
  Inputs: Search terms export
  Output: winners/waste, key opportunities, negatives plan (if relevant)

Step 6 — PMax / Shopping insights (if used)
  Check: major changes, learning events, feed health gates
  Output: what worked, what didn't, what control changes are needed

Step 7 — Recommendations & next-quarter plan
  Choose: 3–7 actions (priorities P0/P1/P2), owners, timeline
  Define: Verify after (7–14d/30d) + KPI thresholds
  Output: plan section

Done criteria:
  - Quarterly Report with QoQ comparison, main KPIs and conclusions
  - Data quality block: tracking/attribution/conversion changes
  - Breakdown by campaign type/channel, geo/device (top drivers at minimum)
  - 3–5 insights "what drove growth/decline" with change history references
  - Next-quarter plan: 3–7 priority actions + expected effect + what to measure
""",
    },

    "Launch Checklist": {
        "id": "SOP-0012",
        "lifecycle": "Setup",
        "modules": "Search | Tracking",
        "steps": """
Step 1 — Define success & constraints
  Inputs: Business context brief
  Define: KPI (CPA/ROAS), geo, budget, what is primary conversion, margins/CPA cap
  Output: launch brief

Step 2 — Measurement foundation
  Check: Ads↔GA4 link, auto-tagging ON, conversions correctly set up
  (Primary/Secondary, counting, windows, value/currency)
  Evidence: DebugView/Realtime + test/real conversion
  Output: tracking QA notes (OK or P0)

Step 3 — Merchant Center gate (if ecom)
  Inputs: MC Shipping settings + Diagnostics
  Check: shipping coverage, policy status, product approvals, P0 issues
  Decision: if P0 → MC triage first, then launch
  Output: MC gate status

Step 4 — Account hygiene & guardrails
  Check: time zone, billing, access, naming convention, auto-apply recommendations (off or controlled)
  Output: guardrails list

Step 5 — Campaign build QA (Search / PMax)
  Search: structure, match types, base negatives, RSA assets, landing relevance
  PMax: goals, URL expansion, brand exclusions, asset settings, final URL policy
  Output: build QA checklist

Step 6 — Go-live checklist
  Check: budgets, start date, bid strategy, conversion goal set, approvals/policies
  Action: enable campaigns, log launch in Actions log
  Output: go-live timestamp + baseline metrics (day 0)

Step 7 — Week-1 monitoring plan
  Define: daily checks (spend, conv, MC issues), thresholds,
  what to do if 0 conv / high spend
  Output: First-week monitoring plan

Done criteria:
  - Launch checklist completed (all critical items checked)
  - Tracking verified end-to-end: test or real conversion visible in GA4 and Ads
  - For ecom: MC account has no P0 blockers (or clear MC triage plan before launch)
  - Campaigns have: correct goals, budgets, geo, ad schedule, brand safety/URL controls (PMax)
  - First-week monitoring plan with thresholds (spend, CTR, CVR, conversions, disapprovals)
""",
    },

    "Performance Max Control Playbook": {
        "id": "SOP-0006",
        "lifecycle": "Weekly | Monthly",
        "modules": "PMax | MC | Tracking",
        "steps": """
Step 1 — Snapshot control surfaces
  Inputs: PMax settings snapshot
  Check: Final URL expansion, URL exclusions, Brand exclusions, Goals
  Red flags: URL expansion ON without control, no brand exclusions, goals optimizing to wrong conversion

Step 2 — Goals sanity (bidding truth)
  Inputs: Ads Conversions summary (settings)
  Check: which conversions are Primary, account-default goals vs campaign goals
  Red flags: PMax optimizing to secondary/incorrect conversion

Step 3 — Change-history context (7–14 days)
  Inputs: Ads Change history
  Check: budget/bid strategy/goals/assets changes
  Red flags: drop/spike started immediately after a change

Step 4 — Asset governance
  Inputs: PMax settings snapshot
  Check: Automatically created assets, brand/compliance constraints
  Red flags: auto-assets diluting offer or creating brand compliance risk

Step 5 — Feed health gate (if ecom)
  Inputs: Merchant Center Diagnostics
  Check: P0 issues (price/shipping/availability), mass disapprovals
  Decision: if P0 in MC → MC triage first, then PMax optimization

Step 6 — Choose actions (max 1–3)
  Rule: 1–3 changes per iteration
  Output: Actions log (what changes, why, expected impact)

Step 7 — Learning protection
  Check: were there "major changes" recently
  Decision: lock learning window 7–14 days without additional changes if major change made

Step 8 — Verify plan
  Define: KPIs, success/failure thresholds, check date
  Output: PMax control checklist + Test plan (if needed)

Done criteria:
  - Final URL expansion, Brand exclusions, Goals verified and documented
  - Any change logged in Actions log with Verify after + Rollback
  - If ecom: MC P0 issues closed or Feed fixlist exists and PMax changes deferred
  - No "many changes at once" without Test plan
""",
    },

    "Conversions Checks (Tracking Sanity)": {
        "id": "SOP-0003",
        "lifecycle": "Weekly | Incident",
        "modules": "Attribution | Tracking",
        "steps": """
Step 1 — Define the symptom & time window
  Inputs: brief description of problem + period
  Classify: 0 conversions, drop >50%, spike/double counting, value/currency mismatch
  Output: 2–3 sentences "what exactly broke"

Step 2 — Ads conversion goals sanity
  Inputs: Ads → Tools → Conversions → Summary
  Check: Primary/Secondary, account-default goals, status ("No recent conversions" etc.)
  Red flags: Primary = micro-conversion, disabled/deleted conversions, wrong goal set

Step 3 — GA4 key events sanity
  Inputs: GA4 → Admin → Key events/Events
  Check: which events are key events, any duplicates (purchase counted twice)
  Red flags: purchase not a key event, extra key events, duplication

Step 4 — End-to-end evidence (1–3 fresh cases)
  Inputs: GA4 DebugView/Realtime, Shopify Orders or CRM lead log
  Check: for 1–3 conversions find: GA4 event → params (value/currency/transaction_id) → Ads conversion
  Red flags: only in one system, no transaction_id, value=0/wrong currency

Step 5 — Settings deep check (counting, windows, value)
  Inputs: Ads conversion action settings + GA4 event settings
  Check: Counting (One/Every), Conversion window, Value rules/Settings
  Red flags: Every for lead, window too short/long, value rules breaking business logic

Step 6 — Linkage / tagging sanity
  Check: Ads↔GA4 link, auto-tagging, GA4 imports didn't accidentally become Primary
  Red flags: no link, auto-tagging OFF, duplicate import + website tag both as Primary

Step 7 — Change-history correlation
  Inputs: Ads Change history (7–14 days)
  Check: what changed in goals/conversions/bidding/tags/site
  Output: 1–2 most likely root causes

Step 8 — Decision & next action
  If OK: document baseline and monitoring thresholds
  If Degraded: Fixlist (P1) + Verify after 24–72h
  If Incident: Incident report + Data exclusion window (if needed)
  Output: Incident report or Tracking sanity notes

Done criteria:
  - Mapping table: Shopify/CRM event → GA4 event/key event → Ads conversion action (what is Primary)
  - Verified and documented: value/currency, counting, windows, attribution import/source
  - Evidence on 1–3 fresh conversions (DebugView/Realtime + Ads conversions)
  - Decision: OK / Degraded / Incident + clear next steps
  - If Incident: Incident report + Fixlist with Owner, Verify after, Rollback
""",
    },

    "Mini Audit (48h)": {
        "id": "SOP-0004",
        "lifecycle": "Setup",
        "modules": "Search | Tracking | PMax",
        "steps": """
Step 1 — Rapid context capture
  Inputs: Business context brief + Looker Studio link
  Define: KPI, budget, geo, what we sell/AOV, what was "wrong" before engagement
  Output: 5 lines of context

Step 2 — Measurement quick sanity
  Inputs: Ads Conversions summary, GA4 Conversions summary, Shopify Orders (if ecom)
  Check: Primary goals, basic alignment, value/currency
  Red flags: 0 conversions with existing orders, duplicate purchase
  Output: OK / P0 issue (add to Fixlist)

Step 3 — Top-level performance scan (last 7/30 days)
  Inputs: Campaigns performance + Looker Studio
  Check: spend, conv, value, CPA/ROAS; major outliers by campaigns/devices/geo
  Output: 3–5 key observations

Step 4 — Search terms: waste vs winners (30d)
  Inputs: Search terms export
  Bucket: Winners / Waste / Irrelevant / Info intent
  Output: quick negatives plan + keyword add list (obvious ones only)

Step 5 — PMax controls quick check
  Check: goals, URL expansion, brand exclusions, last changes (Change history)
  Decision: 1 "safe" change or "don't touch until MC/Tracking P0 is closed"
  Output: PMax notes + action candidate

Step 6 — Prioritize & propose first iteration
  Rule: 1–3 changes max
  Output: Audit + Fixlist (P0/P1/P2) + Actions log + Verify plan (24–72h and 7–14d)

Done criteria:
  - Measurement gate checked (Ads ↔ GA4 ↔ Shopify/CRM) on 1–3 examples
  - Top-5 findings with priority (P0/P1/P2) and brief "why"
  - Fixlist + Actions log (if anything changed) with Verify after + Rollback
  - 1–3 recommended changes for first iteration + KPI check date
""",
    },

    "Semantic Mining from 0": {
        "id": "SOP-0008",
        "lifecycle": "Setup",
        "modules": "Search",
        "steps": """
Step 1 — Extract seed keywords, core commercial intent
  Input: product/service description, landing page URL, competitors list
  Check: what exactly is being sold, main use case, core value proposition
  Red flags: starting with informational keywords, no clarity on offer
  Action: define 5–15 core commercial seeds (buy, price, order, service, geo if relevant)
  Output: seed list

Step 2 — Expand via Keyword Planner, volume is not priority
  Input: Google Keyword Planner export
  Check: search volume, competition level, CPC as proxy for intent
  Red flags: focusing only on high volume, ignoring CPC as intent signal
  Action: extract commercial clusters, separate brand vs non-brand, generic vs specific
  Output: raw keyword pool

Step 3 — Validate through SERP reality check
  Input: manual SERP review for top queries per cluster, screenshots/notes
  Check: what Google thinks the intent is, ads type, shopping presence, informational dominance
  Red flags: SERP shows blog results but we plan direct sales
  Action: reclassify cluster as Commercial / Informational / Navigational
  Output: intent labels

Step 4 — Competitor mining
  Input: competitor domains
  Check: ad messaging themes, category structure, recurring offer angles
  Red flags: competitor dominates with strong differentiation we ignore
  Action: extract message angles and structural insights
  Output: messaging notes

Step 5 — Intent clustering
  Input: full keyword pool
  Check: grouped by user intent, not just word similarity
  Red flags: mixing hot and cold intent in one group
  Action:
    Cluster A: High commercial (buy, price, order)
    Cluster B: Problem aware
    Cluster C: Research, comparison
  Output: cluster table

Step 6 — Negative framework
  Input: keyword pool, SERP analysis
  Check: irrelevant modifiers (DIY, free, jobs, education, wrong locations/languages)
  Red flags: broad match without negative foundation
  Action: create base negative list (account level + campaign level)
  Output: negative list draft

Step 7 — Campaign structure design
  Input: clusters and objectives
  Check: does each cluster need separate budget and control?
  Red flags: mixing different CPA tolerance segments
  Action:
    High intent → dedicated Search campaign
    Mid intent → separate campaign
    Brand → isolated if relevant
  Output: campaign map

Step 8 — Test design
  Input: final structure
  Check: each launch has a clear hypothesis and decision rule
  Red flags: launching without experiment logic
  Action: define hypothesis, KPI, decision rule (e.g. 20 conversions or 14 days)
  Output: experiments table

Done criteria:
  - Seed list created and validated against the offer
  - Keyword pool expanded and classified by intent
  - Competitor insights captured, messaging angles noted
  - Base negative list produced (account level + campaign level)
  - Campaign map created from clusters
  - Experiments table with KPI and decision rules
""",
    },
}


SOPS["Measurement & Privacy Setup"] = {
    "id": "SOP-0013",
    "lifecycle": "Setup | Quarterly",
    "steps": """
Step 1 — Consent Mode v2 audit (GAC-0034)
  Check: is Consent Mode v2 active for EU/EEA traffic?
  Tool: Tag Assistant → check gtag consent state on page load and after CMP interaction
  Red flags: no consent signals; ad_storage always 'granted' (bypassed); CMP not passing to gtag
  Action: implement Consent Mode v2 via CMP or directly in gtag with default='denied'
  Evidence: Tag Assistant shows consent state update from denied → granted after user accepts
  Output: Consent Mode status documented (Active / Partial / Not implemented) + P0 if missing

Step 2 — Enhanced Conversions for Web (GAC-0035)
  Check: EC active and match rate ≥60% in conversion diagnostics
  Tool: Google Ads → Conversions → select action → Diagnostics → Enhanced Conversions
  Red flags: Inactive; match rate <40%; no customer_email detected in tag
  Action: enable EC in conversion settings; verify hashed PII passing via Tag Assistant
  Evidence: 'Enhanced match' status in Tag Assistant conversion tag
  Output: EC status + match rate documented

Step 3 — Server-side measurement health
  Check: is any conversion measured server-side? (Google Ads Conversion API or server-side GTM)
  Tool: Conversions → check if any action has source 'Google Ads API' or 'Server-side'
  Recommended for: high-value conversions, purchases, lead forms on SPAs
  Action if missing: evaluate server-side GTM or direct Conversion API for primary conversion
  Output: server-side coverage % of total conversions

Step 4 — Consent vs conversion gap analysis
  Compare: conversions this month vs same period last year (or 6 months ago before iOS/cookie changes)
  Check: are 'modelled conversions' appearing? What % of total?
  If modelled >30%: consent coverage is low; prioritise Consent Mode v2 implementation
  Output: modelled conversion % documented

Step 5 — Incrementality baseline (GAC-0037)
  Check: any geo-lift experiment in last 6 months?
  If no: schedule geo experiment for next 4-6 weeks to establish true ROAS multiplier
  Output: incrementality factor estimate (or 'unknown — schedule test')

Done criteria:
  - [ ] Consent Mode status confirmed
  - [ ] EC status + match rate documented
  - [ ] Server-side coverage assessed
  - [ ] Modelled conversion % noted
  - [ ] Incrementality test status: active / planned / none
""",
}

SOPS["B2B & Lead-gen Closed Loop"] = {
    "id": "SOP-0014",
    "lifecycle": "Setup | Monthly",
    "steps": """
Step 1 — GCLID capture audit (prerequisite for everything else)
  Check: does your CRM store GCLID from each inbound lead?
  Test: submit a test form → check CRM record → look for gclid field
  Red flags: no gclid field; field present but empty; using only UTMs (insufficient for offline import)
  Fix: add hidden form field (name='gclid') auto-populated via JS: document.getElementById('gclid').value = getParam('gclid')
  Output: GCLID capture status (Yes / No / Broken)

Step 2 — Lead quality baseline
  Measure current funnel from paid search:
  - Form fills / week (Google Ads conversions)
  - MQL rate: form fills → marketing qualified leads (from CRM)
  - SQL rate: MQLs → sales qualified (from CRM)
  - Close rate: SQLs → Won (from CRM)
  - Average deal value
  Red flags: MQL rate <5% from paid; CAC > LTV; no CRM funnel data at all
  Output: funnel conversion rates documented; CAC calculated

Step 3 — Offline conversion import setup (GAC-0036)
  1. Create conversion action: Google Ads → Conversions → New → Import → Other data sources → CRMs
  2. Download template CSV or use API
  3. Test upload: 5 historical leads with GCLID + conversion_time + conversion_name
  4. Verify: conversions appear in Google Ads within 48h
  5. Schedule: weekly export from CRM of leads that reached MQL+ in last 7 days → upload
  Output: offline conversion action created and verified with test data

Step 4 — Smart Bidding migration (GAC-0038)
  Current state: what conversion action is in 'bidding column'?
  Target state based on volume:
    ≥30 qualified leads/month → tCPA on qualified-lead conversion
    10-30/month → value-based (form=1, MQL=5, SQL=20) + Maximise Conversion Value
    <10/month → stay on micro-conversion, build history over 60-90 days
  Action: update 'Include in conversions' setting; set tCPA or tROAS target
  Output: bidding strategy updated; target CPA/ROAS documented (based on CAC target)

Step 5 — CRM closed-loop reporting (GAC-0039)
  Build or verify this reporting view exists:
  Google Ads cost → Clicks → Form fills → MQLs → SQLs → Won → Revenue → ROI
  Tools: Google Ads API + CRM export → Google Sheets / Looker Studio
  Minimum viable: monthly manual export + join on GCLID in spreadsheet
  Output: reporting view link or template documented

Step 6 — B2B audience layers (GAC-0041)
  Add in observation mode first (not targeting mode):
  - Customer Match from CRM list
  - In-Market: Business & Industrial, B2B Technology, Consulting
  - RLSA from existing customer CRM upload (for exclusion)
  Run 30 days in observation → if CPA diff ≥15% → promote to targeting bid adjustment
  Output: audiences added to observation; CPA data after 30 days

Done criteria:
  - [ ] GCLID capture confirmed working
  - [ ] Funnel conversion rates documented
  - [ ] Offline conversion import live with ≥1 test conversion
  - [ ] Smart Bidding target set based on qualified lead, not raw fill
  - [ ] Closed-loop reporting view exists
  - [ ] B2B audiences in observation mode
""",
}


def get_sop_steps(command: str) -> str:
    """Return SOP steps for a given command."""
    command_to_sop = {
        "/audit":        "Account Audit (Full)",
        "/tracking":     "Conversions Checks (Tracking Sanity)",
        "/incident":     "Tracking QA + Incident Response",
        "/weekly":       "Weekly Optimization Loop",
        "/monthly":      "Weekly Optimization Loop",
        "/searchterms":  "Search Terms Cleanup",
        "/feed":         "Merchant Center Triage",
        "/pmax":         "Performance Max Control Playbook",
        "/quarterly":    "Quarterly Optimization Review",
        "/launch":       "Launch Checklist",
        "/fixlist":      "Mini Audit (48h)",
        "/semantic":     "Semantic Mining from 0",
        "/measurement":  "Measurement & Privacy Setup",
        "/b2b":          "B2B & Lead-gen Closed Loop",
        "/crm":          "B2B & Lead-gen Closed Loop",
        "/leadgen":      "B2B & Lead-gen Closed Loop",
    }
    sop_name = command_to_sop.get(command)
    if not sop_name:
        return (
            f"## No dedicated SOP for {command}\n"
            "Run /audit for a full account review, or /weekly for the weekly optimisation cycle."
        )
    sop = SOPS.get(sop_name, {})
    if not sop:
        return ""
    return f"\n## SOP: {sop_name} ({sop['id']})\nLifecycle: {sop['lifecycle']}\n{sop['steps']}"
