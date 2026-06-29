"""
Meta Ads Canon Playbooks (SOPs) — 10 playbooks.
Structure mirrors Google Ads Canon SOPs for consistency.
"""

META_SOPS = {
    "Account Audit (Full)": {
        "id": "SOP-M001",
        "lifecycle": "Setup | Quarterly",
        "modules": "Pixel | CAPI | Audiences | Creative | Feed | Account",
        "steps": """
Step 1 — Context & success definition
  Inputs: Business context brief, account objectives
  Define: primary KPI (CPA/ROAS/CPL), geo, margins, attribution window, what counts as a conversion
  Output: 5-10 lines of context + KPI targets

Step 2 — Measurement sanity gate (Pixel + CAPI + GA4)
  Inputs: Events Manager event list, Event Match Quality scores, GA4 conversions
  Check: primary event active, EMQ ≥6.0, no duplicate counting, CAPI active
  Evidence: verify 1-3 recent orders appear in Events Manager AND backend
  Red flags: 0 purchase events; EMQ <6; events only from browser (no server); GA4 orders >> Meta purchases
  Output: tracking notes → if issue → add to Fixlist as P0 (MAC-0001 through MAC-0006)

Step 3 — Account health check
  Inputs: Account Quality, Policy violations log, Business Manager settings
  Check: account standing, payment method, BM verification, admin access
  Red flags: any active violations, single admin user, pixel owned by personal account
  Output: account health status + P0 items if any

Step 4 — Campaign structure audit
  Inputs: All active campaigns list, budget allocation, learning phase statuses
  Check: CBO vs ABO usage, ad sets per campaign, learning phase statuses, budget distribution
  Red flags: Learning Limited on key ad sets, ABO with 5+ ad sets, budget concentration >80% on one ad set
  Output: structure recommendations + P1 items

Step 5 — Audience quality audit
  Inputs: Audience list (custom + lookalike + interest), overlap tool results
  Check: source sizes, staleness, overlap %, exclusions in place, frequency by ad set
  Red flags: LAL source <1000, WCA not updating, no customer exclusions in prospecting, frequency >3
  Output: audience action plan

Step 6 — Creative performance audit
  Inputs: Last 30d performance by ad, creative fatigue indicators
  Check: CTR trend, frequency, hook rate (video), top/bottom performers
  Red flags: <3 active creative variants, no new creative in 21+ days, frequency >4
  Output: creative refresh plan with specific assets needed

Step 7 — Feed / Catalog audit (ecom only)
  Inputs: Commerce Manager Diagnostics, catalog disapproval rate, feed freshness
  Check: disapproval rate, price accuracy, availability accuracy, feed refresh schedule
  Red flags: >5% disapproved, feed refresh >24h old, DPA campaigns with outdated prices
  Output: feed fixlist

Step 8 — Synthesis: Fixlist + priorities
  Format: P0 (fix immediately) → P1 (fix this week) → P2 (fix this sprint)
  Each item: Rule ID | Issue | Action | Owner | Verify by | Rollback
""",
    },
    "Pixel & CAPI Health Check": {
        "id": "SOP-M002",
        "lifecycle": "Setup | Incident | Weekly",
        "modules": "Pixel | CAPI | Events Manager",
        "steps": """
Step 1 — Live pixel test
  Tool: Meta Pixel Helper (Chrome extension) on all key pages
  Pages to check: Homepage, Product/Service page, Cart/Lead form, Order confirmation/Thank you
  Expected: PageView fires on all pages; Purchase/Lead fires on confirmation only
  Red flags: No events, duplicate Purchase fires, wrong event parameters

Step 2 — Events Manager historical check
  Dashboard: Events Manager → Data Sources → Pixel → Event History (last 7d)
  Check: event volume trend (no sudden drops), event names match expected set
  Red flags: 0 events in last 24h, event names changed/missing, volume drop >50%

Step 3 — Event Match Quality (EMQ) audit
  Dashboard: Events Manager → EMQ tab per event
  Target: EMQ ≥7.0 for Purchase/Lead; ≥6.0 minimum
  Check each parameter passed: em, ph, fn, ln, ct, zp, country, fbc, fbp
  Action if low: add missing parameters, hash PII correctly (SHA-256 lowercase)

Step 4 — CAPI server events check
  Dashboard: Events Manager → event breakdown by Browser vs Server
  Target: ≥60% of events from Server (CAPI)
  Red flags: 0 server events, CAPI connected but not firing
  Action: re-check CAPI integration, test via API endpoint

Step 5 — Deduplication verification
  Check: event_id passed in both browser and CAPI for same event
  Tool: Events Manager → Diagnostics → Deduplication
  Red flags: Duplicated events > 5% of total
  Action: implement event_id matching (same UUID for browser + server event of same purchase)

Step 6 — Attribution window verification
  Settings: Ads Manager → Columns → Customize → Attribution settings
  Recommended: 7-day click, 1-day view for ecom; 7-day click for lead-gen
  Red flags: Only 1-day click (misses assisted conversions), view attribution off
  Output: tracking health report with pass/fail for each check
""",
    },
    "Weekly Optimization Loop": {
        "id": "SOP-M003",
        "lifecycle": "Weekly",
        "modules": "Campaigns | Creative | Audiences | Budget",
        "steps": """
Step 1 — Performance snapshot (15 min)
  Period: last 7 days vs previous 7 days
  Metrics: Spend, Impressions, CPM, CTR, CVR, CPA/ROAS, Frequency
  Flag: any metric moved >20% week-over-week

Step 2 — Learning Phase check
  Check all ad sets for Learning Limited status
  If Learning Limited: diagnose reason (budget/conv volume/too many changes)
  Action: consolidate ad sets or increase budget before making other changes

Step 3 — Budget performance review
  Check: ROAS/CPA by campaign; identify over- and under-performing campaigns
  Action: shift budget from campaigns with ROAS <1.5× to ROAS >3×
  Rule: never change CBO budget by >20% in one edit (resets learning)

Step 4 — Creative fatigue scan
  Check: Frequency >3 per ad set; CTR declining trend; top creative age >21 days
  Action: rotate new creative into fatigued ad sets; pause ads with frequency >5

Step 5 — Audience & frequency action
  Check: audience overlap >30% between ad sets; CPM spike vs. last week
  Action: refresh exclusion lists; add new Lookalike if prospecting CPM rose >25%

Step 6 — Quick wins (P2 hygiene)
  Check: UTMs present on all new ads, naming convention followed, copy within limits
  Fix: any missing items found in audit

Step 7 — Weekly summary
  Document: what changed, expected impact, metrics to monitor next week
  Output: 1-paragraph summary with 3 actions taken + 3 metrics to watch
""",
    },
    "Creative Refresh Playbook": {
        "id": "SOP-M004",
        "lifecycle": "Weekly | Monthly",
        "modules": "Creative | Ad",
        "steps": """
Step 1 — Creative fatigue diagnosis
  Signals: Frequency >3 (7d), CTR declining 2+ consecutive weeks, ROAS dropping with stable budget
  Urgency levels: Frequency >5 = urgent refresh; Frequency 3-5 = plan refresh this week

Step 2 — Audit current creative inventory
  List all active creatives by: format, age, performance (CTR, CVR, ROAS), frequency
  Identify: top performers (keep), underperformers (pause), fatigued (replace)

Step 3 — Brief new creative
  For each new asset specify: format (image/video/carousel), hook type, offer/angle, target placement
  Minimum batch: 5-10 new assets per refresh
  Test matrix: 1 control + 3 challengers per variable (hook / format / CTA)

Step 4 — Video creative checklist (if video)
  Hook (0-3s): visual or verbal pattern interrupt, show product/result
  Body (3-15s): problem → solution or demo
  CTA (last 5s): clear action + offer
  Technical: 9:16 for Reels/Stories, 1:1 or 4:5 for Feed, captions on, ≤60s

Step 5 — Launch new creative
  Upload to existing ad sets (don't create new ad sets — avoids resetting learning)
  Enable Dynamic Creative to auto-test combinations
  Enable Advantage+ Creative for Meta auto-optimizations

Step 6 — Monitor new creative (days 3-7)
  Check: Delivery status (learning?), initial CTR vs. control, frequency reset
  Decision threshold: after 300+ impressions → keep vs pause decision
  Winner criteria: CTR ≥ control AND ROAS ≥ control after 500+ impressions
""",
    },
    "Scaling Playbook": {
        "id": "SOP-M005",
        "lifecycle": "Monthly",
        "modules": "Budget | Campaigns | Audiences",
        "steps": """
Step 1 — Scale readiness check
  Prerequisites: ROAS ≥ 2.5× for ≥14 consecutive days, Learning Phase complete, no P0/P1 issues
  If not ready: fix underlying issues before scaling (don't scale a broken campaign)

Step 2 — Identify scaling lever
  Vertical scale: increase budget on best-performing campaign (max +20%/day to avoid reset)
  Horizontal scale: duplicate winning ad set with new audience (LAL 2-5%, broad interest expansion)
  New campaign scale: launch new campaign type (ASC, if not running)

Step 3 — Budget scaling rules
  Rule: max budget increase 20% per 3-day period (larger = learning reset risk)
  CBO campaigns: adjust at campaign level; let Meta rebalance ad sets
  If daily spend drops after budget increase: revert, wait 3 days, try again

Step 4 — Audience expansion for scale
  Add Lookalike tiers: 1% → 2-3% → 4-7% (test separately)
  Add Broad targeting (no interests, just demographics) alongside interest-based
  Launch Advantage+ Audience to let Meta find new segments automatically

Step 5 — Monitor scaling metrics
  Week 1 after scale: check daily ROAS, CPM trend, frequency
  Red flags: CPM rises >30%, ROAS drops >20%, frequency spikes
  Action if degraded: reduce budget to pre-scale level, diagnose CPM spike source

Step 6 — Document scale ceiling
  Track: at what budget level does ROAS begin degrading?
  This is the account's current scale ceiling → audience saturation signal
  Solution at ceiling: new creative angles, new audience pools, new markets/geo
""",
    },
    "Audience Strategy & Refresh": {
        "id": "SOP-M006",
        "lifecycle": "Monthly | Quarterly",
        "modules": "Audiences | Custom | Lookalike",
        "steps": """
Step 1 — Audience inventory audit
  List all audiences: type, size, last updated, campaigns using it
  Check: staleness (>90d for lists, pixel-based auto-updates), size trends, overlap

Step 2 — Custom Audience refresh
  Re-upload customer list: all purchasers, high-LTV segment, email subscribers
  Segment by value: VIP (top 20% LTV), Regular, One-time buyer
  Use value-based custom audiences (LTV column) for Value-Based Lookalike

Step 3 — Lookalike strategy review
  Audit LAL performance by tier: 1%, 2-3%, 4-7%
  Check source quality: ≥5000 seed for strong signal (minimum: 1000)
  Update: create new LAL from refreshed customer list + last 90d purchasers

Step 4 — Retargeting audience review
  Funnel layers: Top (all visitors 30d), Middle (product views 14d), Bottom (cart abandon 7d), Purchasers (180d)
  Exclusions: always exclude lower funnel from upper funnel targeting
  Size check: retargeting audiences <1000 → expand lookback window

Step 5 — Prospecting audience testing plan
  Test 2-3 new interest audiences per month
  Structure: each in its own ad set with equal budget for fair test
  Duration: ≥7 days, ≥3000 impressions before decision
  Winner: CPA ≤ target × 1.2, ROAS ≥ floor

Step 6 — Advantage+ Audience evaluation
  Compare Advantage+ Audience performance vs manual audiences over 30 days
  If Advantage+ wins: consolidate manual ad sets into A+ Audience
  If manual wins: document which signals/interests outperform Meta's algorithm
""",
    },
    "Advantage+ Shopping Campaign Setup": {
        "id": "SOP-M007",
        "lifecycle": "Setup | Monthly",
        "modules": "ASC | Catalog | Creative",
        "steps": """
Step 1 — Eligibility check
  Requirements: pixel with ≥500 purchase events (last 30d), product catalog connected, ecom objective
  BM must own pixel and catalog; catalog must have <5% disapproved items

Step 2 — ASC campaign creation
  Objective: Sales → Advantage+ Shopping Campaign (not manual Sales campaign)
  Budget: start with 20-30% of total Meta budget for the account
  Geo: same as best-performing manual campaign for fair comparison

Step 3 — Existing customer budget cap
  Set to 10% (conservative) to keep ASC focused on prospecting
  Existing customer definition: pixel purchasers last 180d + customer list
  Revisit after 30d: if existing customer conversions >30% of ASC conv → lower cap

Step 4 — Creative setup for ASC
  Upload minimum 10 creative assets: mix of formats (image, video, carousel)
  Include: lifestyle images, product-on-white, testimonial, UGC
  ASC uses all assets dynamically — more variety = better optimization

Step 5 — Catalog integration
  Connect product catalog to ASC for automatic DPA (Dynamic Product Ads)
  Verify catalog is healthy: <5% disapproved (MAC-0015)
  ASC will use catalog + creative assets together for best combination

Step 6 — Learning period (14 days)
  Do NOT make changes in first 14 days (reset learning)
  Monitor: delivery status (learning phase expected), spend ramp-up
  After 14d: evaluate ROAS vs manual campaigns; scale if competitive
""",
    },
    "Incident Response (Sudden Drop)": {
        "id": "SOP-M008",
        "lifecycle": "Incident",
        "modules": "Pixel | Account | Campaigns | Feed",
        "steps": """
Step 1 — Define the incident
  What dropped? ROAS / CPA / Conversions / Spend / Reach / CTR
  When did it start? (check hourly/daily chart to pinpoint)
  Magnitude: >30% drop = P0 incident; 15-30% = P1; <15% = normal variance

Step 2 — Check Pixel / CAPI first (MAC-0001 through MAC-0006)
  Events Manager: any drop in Purchase/Lead events at same time as performance drop?
  If yes: pixel/CAPI incident → run SOP-M002 (Pixel & CAPI Health Check)
  This is the most common cause of sudden conversion drops

Step 3 — Account quality check (MAC-0004)
  Account Quality dashboard: any new policy violations or restrictions?
  If yes: resolve per Meta policy guidance before any other action

Step 4 — Change history review
  Ads Manager → Campaigns → Change History (last 72h)
  Check: budget changes, bid strategy changes, audience edits, creative pauses/adds
  Hypothesis: what change correlates with the drop?

Step 5 — Platform / external factors
  Meta system status (status.meta.com): any active incidents?
  iOS update / ATT changes: check if drop correlates with OS update pattern
  Seasonality: is this period typically lower? Check same period last year

Step 6 — Diagnosis and fix
  If pixel issue: fix pixel, document data gap (conversions will be underreported for gap period)
  If account violation: resolve and request review; do not run ads during resolution
  If campaign change: revert the change that correlates with drop; monitor 48h
  If external: document, adjust budget/bids, communicate to client

Step 7 — Post-incident report
  What happened, root cause, fix applied, verify timeline, prevention measures
  Update Fixlist with MAC rule violated, add to recurring checklist
""",
    },
    "Campaign Launch Checklist": {
        "id": "SOP-M009",
        "lifecycle": "Setup",
        "modules": "Pixel | Campaign | Creative | Audiences | Tracking",
        "steps": """
Step 1 — Pre-launch: Measurement gate (MAC-0001 through MAC-0006)
  □ Pixel fires on all key pages (use Pixel Helper)
  □ Primary conversion event active and receiving data
  □ CAPI active with EMQ ≥6.0
  □ Deduplication configured (event_id passed)
  □ Attribution window set: 7-day click / 1-day view

Step 2 — Account hygiene gate (MAC-0004, MAC-0007)
  □ Account in Good Standing (no violations)
  □ Business Manager verified
  □ Payment method valid and charged
  □ Admin access: ≥2 admins in BM

Step 3 — Campaign structure
  □ Correct objective selected (Awareness/Traffic/Leads/Sales)
  □ CBO enabled for ≥3 ad sets
  □ Budget: CPA target × 5-7 = minimum daily budget per ad set
  □ Schedule: appropriate start/end dates (or always-on)
  □ Naming convention applied (MAC-0024)

Step 4 — Audiences
  □ Prospecting: Lookalike 1% + interest-based (500K–5M)
  □ Customer exclusions added to prospecting ad sets (MAC-0014)
  □ Retargeting: separate campaign/ad set from prospecting
  □ Audience overlap checked (<30%)

Step 5 — Creative
  □ Minimum 3 ad variants per ad set
  □ All placements previewed (Feed, Stories, Reels)
  □ Copy within character limits (MAC-0023)
  □ UTMs on all destination URLs (MAC-0018)
  □ Advantage+ Creative enabled (MAC-0025)
  □ Video: captions added, hook in first 3s

Step 6 — Final check & launch
  □ Spend limit set (campaign level) for first 48h to prevent overspend
  □ All ads reviewed and approved (not "In Review" blocking delivery)
  □ Notification set: alert if daily spend exceeds 150% of target
  □ Launch → monitor first 24h for delivery issues
  □ Check Events Manager for conversion tracking after first conversions
""",
    },
    "Retargeting Funnel Setup": {
        "id": "SOP-M010",
        "lifecycle": "Setup | Monthly",
        "modules": "Audiences | Campaigns | Creative",
        "steps": """
Step 1 — Funnel architecture
  Top of Funnel (TOF): All website visitors 30d (exclude purchasers 180d)
  Middle of Funnel (MOF): Product/service page viewers 14d (exclude purchasers 180d)
  Bottom of Funnel (BOF): Cart abandoners / Lead form openers 7d (exclude purchasers 180d)
  Win-back: Purchasers 181d-365d (exclude purchasers 0-180d)

Step 2 — Audience size check
  Each funnel stage must have ≥1000 people for delivery
  If TOF <10K: expand to 60d window; consider adding Facebook/Instagram engagers
  If BOF <1000: extend to 14d; add all checkout starters

Step 3 — Campaign structure
  Option A (separate campaigns): TOF/MOF/BOF each in own campaign with own budget
  Option B (consolidated): 1 retargeting campaign, 3 ad sets with exclusion stacking
  Recommended: Option B with CBO; let Meta allocate between funnel stages

Step 4 — Creative strategy by funnel stage
  TOF: Brand awareness, social proof, testimonials — "remind" them of the brand
  MOF: Product-specific content, comparison, benefits over competition
  BOF: Cart recovery offer (discount/urgency), FAQ objection handling, strong CTA
  Win-back: Re-engagement offer, new products/collections, loyalty message

Step 5 — Exclusion stacking (critical)
  TOF excludes: recent purchasers (180d), current MOF/BOF audiences
  MOF excludes: recent purchasers (180d), BOF audiences
  BOF excludes: recent purchasers (180d)
  Win-back excludes: purchasers 0-180d (only shows to older buyers)

Step 6 — Performance benchmarks
  BOF retargeting ROAS should be 3-5× prospecting ROAS (warm audience)
  If BOF ROAS < 2×: landing page problem or wrong offer
  If TOF retargeting ROAS < prospecting ROAS: audiences too cold or too small

Step 7 — Refresh cadence
  Creative: refresh every 14d (retargeting audiences see ads more frequently)
  Audiences: auto-update (pixel-based) — verify pixel is firing monthly
  Offers: test new offer quarterly (discount %, free shipping, bonus)
""",
    },
    "Measurement & Privacy Setup": {
        "id": "SOP-M011",
        "lifecycle": "Setup | Quarterly",
        "modules": "Pixel | CAPI | Consent | Events Manager",
        "steps": """
Step 1 — Consent configuration audit (MAC-0026)
  Check: is Meta Pixel consent mode active for EU/EEA?
  Tool: Facebook Pixel Helper — submit/reject cookie consent → does pixel fire change?
  Red flags: pixel fires regardless of consent; no cookie banner; Events Manager data restriction warnings
  Action: implement fbq('consent','revoke') as default; fbq('consent','grant') on CMP acceptance
  Output: consent status documented (Active / Partial / Missing) + P0 Fixlist item if missing

Step 2 — CAPI status and EMQ (MAC-0027)
  Check: Events Manager → Source column (Browser vs Server vs Both) + EMQ score
  Target: EMQ ≥7.0 | server events ≥60% of total | deduplication <5%
  Red flags: Browser-only for primary events; EMQ <6.0; dedup >10%
  Action: if CAPI missing → implement via native integration (Shopify/WooCommerce) or CAPI Gateway
  Output: EMQ score documented; server event % documented

Step 3 — Event match quality deep-dive
  For each primary event: check matched signals (email, phone, fbp, fbc, ip)
  Target: ≥3 matched signals per event
  Action: pass additional hashed fields to CAPI (em + ph + ip + ua = 4 signals)
  Output: matched signal count per event type

Step 4 — Incrementality baseline (MAC-0029)
  Check: any holdout experiment in last 6 months?
  If no: schedule holdout test (10% holdout, 14 days minimum)
  Calculate: blended MER = Total Revenue / Total Meta Spend (compare to attributed ROAS)
  Output: incrementality factor (or 'unknown — schedule test')

Done criteria:
  - [ ] Consent mode status confirmed (EU/EEA)
  - [ ] CAPI active with EMQ ≥7.0
  - [ ] Deduplication rate <5%
  - [ ] Incrementality test status: active / planned / none
  - [ ] All P0 measurement issues in Fixlist
""",
    },
    "B2B & Lead-gen Closed Loop": {
        "id": "SOP-M012",
        "lifecycle": "Setup | Monthly",
        "modules": "Lead Ads | Offline Conversions | CRM | Creative",
        "steps": """
Step 1 — Lead Ads to CRM sync (MAC-0030)
  Check: how quickly do Lead Ad submissions appear in CRM?
  Test: submit test form → check CRM → time to appear?
  Red flags: >5 min delay; manual CSV download; no CRM integration configured
  Action: connect CRM natively (Business Manager → Integrations) or via Zapier webhook
  Target: lead in CRM within 2 minutes; automated follow-up email within 5 minutes
  Output: sync speed documented; integration type noted

Step 2 — Offline conversion setup (MAC-0028)
  Check: Events Manager → offline event set exists and receiving data?
  Test: upload 5 historical qualified leads with fbclid → verify appear in Events Manager
  If missing: create offline event set; build CRM export → upload workflow
  Action: set campaign optimization goal to qualified-lead offline event (not form fill)
  Output: offline event set created and verified; optimization event updated

Step 3 — Lead quality baseline
  From CRM: measure form-fill → MQL rate from Meta paid traffic
  Target benchmark: MQL rate ≥15% from B2B targeting
  Red flags: MQL rate <5% → wrong audience or offer mismatch
  Output: MQL rate documented; CAC per qualified lead calculated

Step 4 — B2B targeting audit (MAC-0031)
  Review active Ad Set targeting layers
  Check: job-function, industry, company-size or CRM lookalike present?
  Action: add in observation mode: job titles + industries + 'Business decision makers'
  Upload CRM decision-maker list → 1% lookalike
  Output: B2B audience layers added; audience size documented

Step 5 — Creative audit for B2B (MAC-0033)
  Review active creatives: do they address business outcomes or consumer benefits?
  Check: is there social proof (client logos, named testimonials with title)?
  Action: create/test social-proof variant vs ROI-headline variant
  Output: B2B creative test plan with hypothesis and win metric

Step 6 — Value-based bidding readiness (MAC-0032)
  Check: ≥50 qualified-lead events/week flowing? If yes → switch to value-based
  If not: document volume needed; set interim optimization on MQL event
  Output: bidding strategy updated or volume target documented

Done criteria:
  - [ ] Lead Ads → CRM sync working (<2 min delay)
  - [ ] Offline conversion set up and verified
  - [ ] MQL rate documented
  - [ ] B2B audience layers in observation
  - [ ] B2B creative test active
  - [ ] Bidding on qualified leads (not raw form fills)
""",
    },
}


def get_meta_sop_steps(command: str) -> str:
    """Map Telegram command to Meta SOP and return steps."""
    mapping = {
        "/audit":        "Account Audit (Full)",
        "/tracking":     "Pixel & CAPI Health Check",
        "/weekly":       "Weekly Optimization Loop",
        "/monthly":      "Weekly Optimization Loop",
        "/creative":     "Creative Refresh Playbook",
        "/scale":        "Scaling Playbook",
        "/audiences":    "Audience Strategy & Refresh",
        "/asc":          "Advantage+ Shopping Campaign Setup",
        "/incident":     "Incident Response (Sudden Drop)",
        "/launch":       "Campaign Launch Checklist",
        "/retargeting":  "Retargeting Funnel Setup",
        "/attribution":  "Pixel & CAPI Health Check",
        "/ios14":        "Pixel & CAPI Health Check",
        "/dpa":          "Campaign Launch Checklist",
        "/abtest":       "Creative Refresh Playbook",
        "/seasonal":     "Scaling Playbook",
        "/measurement":  "Measurement & Privacy Setup",
        "/b2b":          "B2B & Lead-gen Closed Loop",
        "/crm":          "B2B & Lead-gen Closed Loop",
        "/leadgen":      "B2B & Lead-gen Closed Loop",
        "/fixlist":      "Account Audit (Full)",
    }
    sop_name = mapping.get(command)
    if not sop_name:
        return (
            f"## No dedicated SOP for {command}\n"
            "Run /audit for a full account review, or /creative for creative-specific guidance."
        )
    sop = META_SOPS.get(sop_name, {})
    return (
        f"## {sop_name} [{sop.get('id', '')}]\n"
        f"Lifecycle: {sop.get('lifecycle', '')}\n"
        f"Modules: {sop.get('modules', '')}\n\n"
        f"### Steps\n{sop.get('steps', '').strip()}"
    )
