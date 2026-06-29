"""
TikTok Ads Canon Playbooks (SOPs) — 10 playbooks.
Structure mirrors Meta Ads Canon SOPs (SOP-M001..M010) for consistency.

TikTok-specific emphasis:
  - Hook Rate is the primary creative health signal (check before CTR)
  - Creative fatigue is 2-3× faster than Meta — refresh cadence 7-14 days
  - Learning phase: 50 conv / 7 days per Ad Group (do NOT touch during learning)
  - Over-attribution 35-55% is normal — always cross-validate with GA4/backend
"""

TIKTOK_SOPS = {
    "Account Audit (Full)": {
        "id": "SOP-T001",
        "lifecycle": "Setup | Quarterly",
        "modules": "Pixel | Events API | Audiences | Creative | Catalog | Account",
        "steps": """
Step 1 — Context & success definition
  Inputs: Business context brief, account objectives
  Define: primary KPI (CPA/ROAS/CPL), geo, margins, attribution window, what counts as a conversion
  TikTok-specific: note product's visual appeal, UGC availability, target age group (18-34 vs. 35+)
  Output: 5-10 lines of context + KPI targets

Step 2 — Measurement sanity gate (Pixel + Events API + GA4)
  Inputs: Events Manager event list, source breakdown (browser vs. server), GA4 conversions
  Check: primary event active, no duplicate counting, Events API active with ≥50% server events
  Evidence: verify 1-3 recent orders appear in Events Manager AND backend AND GA4
  Red flags: 0 purchase events; only browser events (no server); GA4 orders >> TikTok purchases by >2×
  Over-attribution check: TikTok conv ÷ GA4 conv — acceptable 1.35–1.55 (TAC-0023)
  Output: tracking notes → if issue → Fixlist as P0 (TAC-0001 through TAC-0005)

Step 3 — Account health check
  Inputs: Account Health panel, Policy violations log, Business Center settings
  Check: account standing, payment method, Business Center verification, admin access (≥2 admins)
  Red flags: active violations, single admin, pixel/catalog owned outside Business Center
  Output: account health status + P0 items if any

Step 4 — Campaign structure audit
  Inputs: All active campaigns list, budget allocation, Ad Group delivery statuses
  Check: learning phase statuses per Ad Group, CBO vs. Ad Group budget distribution, Smart+ presence
  Red flags: Ad Groups stuck in Learning >7 days, budget <10× daily CPA per Ad Group, no Smart+
  Output: structure recommendations + P1 items

Step 5 — Creative performance audit (most critical for TikTok)
  Inputs: Last 14d performance by Ad — Hook Rate, Completion Rate, CTR, CVR, creative age
  Check: Hook Rate ≥30%, Completion Rate ≥25%, CTR trend week-over-week, creative age vs. fatigue
  Red flags: Hook Rate <20%, CTR drop ≥20% WoW at stable CPM, any creative >14 days old with declining CTR
  Output: creative refresh plan with specific assets needed (hook rewrites, format changes)

Step 6 — Audience quality audit
  Inputs: Audience list (custom + lookalike + interest), delivery stats per Ad Group
  Check: source sizes (≥1000), staleness, exclusions in place, audience overlap between Ad Groups
  Red flags: LAL source <1000, no customer exclusions in prospecting, retargeting audience <1000
  Output: audience action plan

Step 7 — Feed / Catalog audit (e-com only)
  Inputs: Catalog → Diagnostics, disapproval rate, feed freshness timestamp
  Check: disapproval rate <5%, price accuracy, availability, feed refresh schedule
  Red flags: >5% disapproved, feed refresh >24h old, Shopping Ads with outdated prices
  Output: catalog fixlist

Step 8 — Synthesis: Fixlist + priorities
  Format: P0 (fix immediately) → P1 (fix this week) → P2 (fix this sprint)
  Each item: Rule ID | Issue | Action | Owner | Verify by | Rollback
""",
    },
    "Pixel & Events API Health Check": {
        "id": "SOP-T002",
        "lifecycle": "Setup | Incident | Weekly",
        "modules": "Pixel | Events API | Events Manager",
        "steps": """
Step 1 — Live pixel test
  Tool: TikTok Pixel Helper (Chrome extension) on all key pages
  Pages: Homepage, Product/Service page, Cart/Lead form, Order confirmation/Thank you
  Expected: PageView fires on all pages; Purchase/Lead fires on confirmation page only
  Red flags: no events, duplicate Purchase fires, wrong event parameters, event fires on wrong page

Step 2 — Events Manager historical check
  Dashboard: Assets → Events → Web Events → Activity tab (last 7d)
  Check: event volume trend (no sudden drops), event names correct, volume consistency
  Red flags: 0 events in last 24h, volume drop >50% vs previous week, event names changed

Step 3 — Source breakdown audit
  Dashboard: Events Manager → event breakdown by Source (Browser vs. Server)
  Target: ≥50% of events from Server (Events API)
  Red flags: 0 server events, Events API connected but not firing, all events browser-only

Step 4 — Deduplication verification (TAC-0003)
  Check: event_id passed consistently in both browser pixel and Events API for same event
  Tool: Events Manager → Diagnostics → check Deduplicated Events count
  Red flags: Duplicated events > 5% of total, purchase count 2× actual orders
  Action: implement event_id matching (same UUID in browser + server for same purchase)

Step 5 — Over-attribution cross-check (TAC-0023)
  Compare: TikTok Manager conversions vs. GA4 TikTok conversions vs. backend orders (same 7d period)
  Calculate: TikTok conv ÷ GA4 conv = attribution ratio
  Acceptable: 1.35–1.55 (35-55% over-attribution is TikTok norm)
  Red flags: ratio >2.0 → investigate duplicate counting or view-through inflation

Step 6 — Attribution window verification (TAC-0025)
  Settings: Ad Group → Optimization → Attribution window
  Standard: 7-day click / 1-day view for conversion campaigns
  Red flags: only 1-day click (misses conversions), 7-day view active (inflates attribution)
  Output: tracking health report with pass/fail for each check
""",
    },
    "Weekly Optimization Loop": {
        "id": "SOP-T003",
        "lifecycle": "Weekly",
        "modules": "Campaigns | Creative | Audiences | Budget",
        "steps": """
Step 1 — Performance snapshot (15 min)
  Period: last 7 days vs. previous 7 days
  Metrics: Spend, Impressions, CPM, Hook Rate, CTR, CVR, CPA/ROAS, Completion Rate
  Flag: any metric moved >20% week-over-week
  TikTok-first: check Hook Rate before CTR — Hook Rate drop often precedes CTR drop by 3-5 days

Step 2 — Learning Phase check
  Check all Ad Groups for 'Learning' delivery status
  If stuck in Learning >7 days: diagnose (budget/conv volume/too many changes in learning window)
  Action: consolidate Ad Groups or increase budget — do NOT change targeting/bids during learning

Step 3 — Creative fatigue scan (most important step for TikTok)
  Check: Hook Rate trend per ad, CTR WoW trend, creative age in days
  Rule: if Hook Rate drops >20% WoW at stable CPM → creative is fatiguing (TAC-0009)
  Action: queue new creative; test new hook first (not full new video) — fastest to produce
  TikTok cadence: active campaigns with >$50/day should get new creative every 7-14 days

Step 4 — Budget performance review
  Check: ROAS/CPA by campaign; identify over- and under-performing campaigns
  Action: shift budget from campaigns with ROAS <1.5× to campaigns with ROAS >3×
  Rule: never change budget by >20% in one edit (risks resetting Ad Group learning)

Step 5 — Attribution cross-check (brief)
  Quick triangulation: TikTok Manager conv vs. GA4 TikTok conv — ratio within 1.35–1.55?
  If ratio spikes >2.0 this week: check for pixel duplicate issue (run SOP-T002)

Step 6 — Quick wins (P2 hygiene)
  Check: UTMs on all new ads, naming convention, caption ≤100 chars, subtitles present
  Fix: any missing items found inline

Step 7 — Weekly summary
  Document: what changed, expected impact, metrics to watch next week
  Output: 1-paragraph summary with 3 actions taken + 3 metrics to monitor
""",
    },
    "Creative Refresh Playbook": {
        "id": "SOP-T004",
        "lifecycle": "Weekly | Monthly",
        "modules": "Creative | Ad",
        "steps": """
Step 1 — Creative fatigue diagnosis
  Primary signals (in priority order):
    1. Hook Rate drops >20% WoW at stable CPM → hook is fatiguing
    2. CTR drops >20% WoW → ad overall is fatiguing
    3. Completion Rate drops >5 pp → body/middle losing viewers
    4. Creative age >14 days for campaigns with >$50/day spend → proactive refresh
  Urgency: Hook Rate <20% = refresh this week; Hook Rate 20-30% = plan refresh this week

Step 2 — Audit current creative inventory
  List all active creatives: format, age (days), Hook Rate, Completion Rate, CTR, CVR, spend
  Categorize: top performers (keep + extend), underperformers (pause), fatigued (replace hook)

Step 3 — Fastest refresh: hook-only edit
  Re-shoot or re-edit first 1–3 seconds only (same body, new hook)
  TikTok hook variants to test:
    A. Pain-point question: 'Why is your [product] not [result]?'
    B. Shock stat: 'X% of people make this mistake...'
    C. Bold claim: 'I tried [action] and here's what I found'
    D. Pattern interrupt: unexpected motion, sound, or color on frame 1
  Adding trending TikTok audio to same visual often extends creative life 5-7 days

Step 4 — Full creative brief (when hook-only is not enough)
  For each new asset specify: format (UGC/studio/screen-rec), hook type, offer/angle, CTA
  Minimum batch: 3-5 new assets per refresh; test different styles (UGC vs. polished)
  TikTok video checklist:
    □ 9:16 format, 1080×1920px (TAC-0006)
    □ Hook delivers message in first 1 sec (text overlay mandatory)
    □ Duration 9-15 sec (sweet spot); 6 sec for awareness
    □ Sound-on design: voice, music, or sound effect prominent
    □ Subtitles burned in or via TikTok Auto Captions (TAC-0020)
    □ Pattern interrupt every 3-5 sec to maintain Completion Rate
    □ CTA in last 2-3 sec, repeated in caption

Step 5 — Launch and monitor new creative
  Add to existing Ad Group (don't create new Ad Group — avoids resetting learning)
  TikTok algorithm will auto-allocate spend toward better-performing creative
  Monitor: Hook Rate and CTR in first 48h (TikTok gives faster initial signal than Meta)

Step 6 — Decision thresholds (after ≥500 impressions)
  Keep: Hook Rate ≥30% AND CTR ≥ control baseline
  Test longer: Hook Rate 20-30% AND CTR within 20% of control
  Pause: Hook Rate <20% OR CTR >30% below control
""",
    },
    "Scaling Playbook": {
        "id": "SOP-T005",
        "lifecycle": "Monthly",
        "modules": "Budget | Campaigns | Audiences | Creative",
        "steps": """
Step 1 — Scale readiness check
  Prerequisites: ROAS ≥ target × 1.5 for ≥14 consecutive days, learning phase complete, no P0/P1 issues
  Creative health gate: Hook Rate ≥30% on at least 2 active creatives (scaling fatigued creative = waste)
  If not ready: fix creative or measurement first — don't scale a broken or fatiguing campaign

Step 2 — Identify scaling lever
  Vertical scale: increase budget on best-performing Ad Group (max +20%/day to avoid learning reset)
  Horizontal scale: duplicate winning Ad Group with new audience tier (LAL 1% → 3%, or Broad)
  New campaign scale: launch Smart+ Campaign if not already running (TAC-0016)
  Creative scale: multiply winning hook into 3-5 variations (same hook, different body/CTA/length)

Step 3 — Budget scaling rules
  Rule: max budget increase 20% per 3-day period (larger = learning reset risk for TikTok)
  Smart+ Campaigns: can tolerate faster budget increases (algorithm self-adjusts)
  If daily spend drops after budget increase: revert, wait 3 days, retry with smaller increment

Step 4 — Audience expansion for scale
  Tier 1 (current): LAL 1-3% purchasers → add LAL 3-5% in separate Ad Group
  Tier 2: Broad targeting (no interests, only demographics) — often outperforms on TikTok
  Tier 3: New geo markets with similar demographics to proven geo
  Smart+: no audience input needed — algorithm finds optimal segments automatically

Step 5 — Creative pipeline for scale
  Scale requires 2× creative volume: budget × 2 → fatigue × 2 faster without fresh creative
  Brief new creative batch before scaling: minimum 5 new assets ready to deploy
  TikTok-specific: test UGC / creator content at scale — converts better than polished video

Step 6 — Monitor scaling metrics (daily first week)
  Watch: CPM trend, Hook Rate stability, CPA/ROAS vs. pre-scale baseline
  Red flags: CPM rises >30% (audience saturation), ROAS drops >25%, Hook Rate declining faster
  Scale ceiling: when ROAS drops to target floor at maximum budget → new creative angle or geo required
""",
    },
    "Audience Strategy & Refresh": {
        "id": "SOP-T006",
        "lifecycle": "Monthly | Quarterly",
        "modules": "Audiences | Custom | Lookalike",
        "steps": """
Step 1 — Audience inventory audit
  List all audiences: type (Pixel/File/Engagement/LAL), size, last updated, campaigns using it
  Check: size ≥1000 (TAC-0013), staleness (File audiences need manual refresh every 30-60d)
  TikTok-specific: Engagement audiences (profile visitors, video viewers) update automatically

Step 2 — Custom Audience refresh
  Re-upload customer list: all purchasers, high-LTV segment, email/phone CRM export
  Format: phone with country code (+380...), email lowercase
  Segment by value: VIP (top 20% LTV), Regular, One-time buyer
  Pixel-based audiences: auto-update as long as pixel fires — verify pixel health first (SOP-T002)

Step 3 — Lookalike strategy review
  Tiers: 1-3% (precision cold prospecting) vs. 5-10% (scale)
  Best seed: Pixel Purchase audience 180d (largest + highest signal)
  Alternative seeds: Customer File top-LTV, High-retention video viewers (≥75% completion)
  Creator Lookalike: test audiences similar to followers of relevant TikTok creators
  Refresh LAL: regenerate from updated seed every 30-60 days

Step 4 — Retargeting audience review (TAC-0013, TAC-0014)
  Funnel layers:
    TOFU: Video viewers ≥75% completion (last 14d)
    MOFU: Website visitors (last 14d), exclude purchasers 180d
    BOFU: AddToCart / Lead Form openers not converted (last 7d)
    Retention: Purchasers 90-180d for LTV upsell
  Size check: any segment <1000 → expand window or combine with adjacent segment

Step 5 — Prospecting audience testing plan
  Test 2 new interest audience combinations per month
  Each in separate Ad Group with equal budget (TAC-0024: target 500K–10M size)
  Duration: ≥7 days, ≥3000 impressions before decision
  Broad targeting test: always include 1 Ad Group with no interest targeting — TikTok often rewards it

Step 6 — Smart+ Audience evaluation
  Compare Smart+ Campaign results vs. manual interest/LAL over 30 days
  If Smart+ wins on CPA: migrate budget from manual Ad Groups to Smart+
  If manual wins: document which specific interest clusters outperform algorithm's choices
""",
    },
    "Smart+ Campaign Setup": {
        "id": "SOP-T007",
        "lifecycle": "Setup | Monthly",
        "modules": "Smart+ | Catalog | Creative",
        "steps": """
Step 1 — Eligibility check
  Requirements: pixel with ≥50 conversion events/week (last 30d), conversion objective
  For Shopping Smart+: product catalog connected, <5% disapproved items (TAC-0015)
  Business Center verified (TAC-0007), Events API active (TAC-0005)

Step 2 — Smart+ Campaign creation
  Objective: Website Conversions → Smart+ Campaign (not Standard Campaign)
  Budget: start with 20-30% of total TikTok budget; Smart+ needs room to explore
  Geo: same as best-performing manual campaign for fair comparison
  No manual audience targeting: algorithm handles audience selection

Step 3 — Creative setup for Smart+
  Upload minimum 5-10 assets: mix of formats (UGC video, polished video, image)
  Variety is key: different hooks, durations (6s / 9s / 15s), aspect ratios (9:16 primary)
  Smart+ A/B tests assets automatically — more variety = better optimization signal
  Ensure all assets pass creative compliance (TAC-0006, TAC-0020)

Step 4 — Catalog integration (e-com)
  Connect product catalog to Smart+ for dynamic Shopping Ads capability
  Verify catalog health: <5% disapproved (TAC-0015)
  Smart+ will use catalog + creative assets in combination for product-level optimization

Step 5 — Learning period (14 days minimum)
  Do NOT change budget by >20%, creative set, or objective during first 14 days
  Monitor: delivery ramp-up (days 1-3 slow spend is normal), Ad Group delivery status
  After 14d: evaluate CPA vs. manual campaigns; require ≤10% CPA premium to justify keeping

Step 6 — Smart+ vs. Manual ongoing evaluation
  Monthly comparison: Smart+ CPA / ROAS vs. best manual campaign over same period
  Scale Smart+ if consistently ≤ manual CPA
  Keep manual campaigns for: A/B testing specific creatives, audience insights, budget control
""",
    },
    "Incident Response (Sudden Drop)": {
        "id": "SOP-T008",
        "lifecycle": "Incident",
        "modules": "Pixel | Account | Campaigns | Creative",
        "steps": """
Step 1 — Define the incident
  What dropped? ROAS / CPA / Conversions / Spend / Reach / CTR / Hook Rate
  When did it start? (check hourly/daily chart in Ads Manager to pinpoint timestamp)
  Magnitude: >30% drop = P0 incident; 15-30% = P1; <15% = normal variance

Step 2 — Check Pixel / Events API first (TAC-0001 through TAC-0005)
  Events Manager: any drop in Purchase/Lead events at same time as performance drop?
  Compare: TikTok conv vs. GA4 TikTok conv — sudden ratio change = tracking issue
  If yes: pixel/Events API incident → run SOP-T002 (Pixel & Events API Health Check)
  Most common cause of sudden conversion drops is tracking failure, not campaign issue

Step 3 — Account quality check (TAC-0004)
  Account Health panel: any new policy violations or restrictions since drop?
  If yes: resolve per TikTok policy guidance before any other action
  Check: any creative newly disapproved that was driving most conversions

Step 4 — Creative fatigue check (TAC-0009)
  Check: did Hook Rate drop first, then CTR, then conversions? (3-5 day lag)
  Timeline: if creatives are 10+ days old and Hook Rate has been declining → fatigue incident
  Action: emergency creative refresh (hook-only edit, minimum 48h turnaround)

Step 5 — Change history review
  Ads Manager → Campaign → Change History (last 72h)
  Check: budget changes, bid strategy changes, audience edits, creative pauses/adds, learning resets
  Hypothesis: what change correlates with the drop in timing?

Step 6 — Platform / external factors
  TikTok system status (ads.tiktok.com/help): any active incidents?
  iOS updates: CPM spikes often correlate with iOS ATT prompt waves
  Seasonality: same period last year / same weekday pattern (TikTok has strong day-of-week variance)
  Geo / macro events: holidays, elections, news events in target market

Step 7 — Diagnosis and fix
  If pixel issue: fix pixel, document data gap (conversions underreported for gap period)
  If account violation: resolve and appeal; pause affected ads during resolution
  If creative fatigue: emergency hook refresh + reactivate best-performing older creative
  If campaign change caused reset: revert change; accept 7-day re-learning window
  If external: document, adjust CPA targets for period, communicate to client/team

Step 8 — Post-incident report
  What happened, root cause, fix applied, verify timeline, prevention measures
  Update Fixlist with TAC rule violated; add check to recurring weekly SOP-T003
""",
    },
    "Campaign Launch Checklist": {
        "id": "SOP-T009",
        "lifecycle": "Setup",
        "modules": "Pixel | Campaign | Creative | Audiences | Tracking",
        "steps": """
Step 1 — Pre-launch: Measurement gate (TAC-0001 through TAC-0005)
  □ TikTok Pixel installed and tested via Test Events (real-time fire confirmed)
  □ Primary conversion event active and receiving data (≥1 event in last 7d)
  □ Events API active with ≥50% server events
  □ Deduplication configured (event_id passed in both pixel and server)
  □ Attribution window set: 7-day click / 1-day view (TAC-0025)
  □ UTM parameters added to all destination URLs (TAC-0018)

Step 2 — Account hygiene gate (TAC-0004, TAC-0007)
  □ Account in Good Standing (no active violations in Account Health)
  □ Business Center verified
  □ Payment method valid
  □ ≥2 admin users in Business Center
  □ Pixel owned by Business Center (not personal account)

Step 3 — Campaign structure
  □ Correct objective selected (Reach/Traffic/Lead Gen/Conversions/App/Shopping)
  □ Budget: CPA target × 10 = minimum daily budget per Ad Group (learning phase requirement)
  □ Naming convention applied: [Product]-[Objective]-[Market]-[YYYYMM] (TAC-0021)
  □ Smart+ Campaign created alongside manual (for e-com accounts, TAC-0016)

Step 4 — Audiences
  □ Prospecting: LAL 1-3% from Purchase seed OR Broad (no targeting) OR Interest 500K-10M
  □ Customer exclusions added to prospecting Ad Groups (TAC-0014)
  □ Retargeting: separate campaign from prospecting
  □ Audience sizes ≥1000 for Custom Audiences used in retargeting (TAC-0013)
  □ Lookalike seed ≥1000 users (TAC-0017)

Step 5 — Creative
  □ Minimum 3 ad variants per Ad Group (TAC-0019)
  □ All videos 9:16, 1080×1920px, MP4/MOV, 5-60 sec (TAC-0006)
  □ Hook delivers message in first 1-3 seconds; text overlay on frame 1
  □ Subtitles present (TAC-0020)
  □ Caption ≤100 chars with CTA (TAC-0020)
  □ If Spark Ads: authorization valid and not expired (TAC-0022)

Step 6 — Final check & launch
  □ Spend cap set at campaign level for first 48h (prevent overspend before learning)
  □ All ads reviewed and not stuck 'Under Review' (check 2h after submission)
  □ Test conversion event fires correctly after a test purchase/lead (if possible)
  □ Launch → monitor first 24h for delivery issues, policy flags, and event tracking
  □ Day 3 check: Hook Rate ≥30%, CPM within expected range, Events Manager showing conversions
""",
    },
    "Retargeting Funnel Setup": {
        "id": "SOP-T010",
        "lifecycle": "Setup | Monthly",
        "modules": "Audiences | Campaigns | Creative",
        "steps": """
Step 1 — Funnel architecture
  TOFU Warm: Video viewers ≥75% completion (last 14d) — engaged but unknown intent
  MOFU: Website visitors (last 14d) — exclude purchasers 180d
  BOFU: AddToCart / Lead Form opened but not completed (last 7d) — highest intent
  Retention: Purchasers 90-180d — LTV / upsell / cross-sell

Step 2 — Audience size check (TAC-0013)
  Each segment must have ≥1000 users for delivery
  If BOFU <1000: extend to 14d; add Checkout Initiated alongside AddToCart
  If MOFU <1000: extend to 30d; add TikTok Profile visitors
  If TOFU <5000: expand video view completion threshold from 75% to 50%

Step 3 — Campaign structure
  Option A (separate campaigns): MOFU/BOFU each in own campaign, own budget — full control
  Option B (consolidated): 1 retargeting campaign, 3 Ad Groups with exclusion stacking
  Recommended: Option B with shared budget for ≤$3000/month; Option A for larger budgets
  TikTok difference from Meta: retargeting audiences are smaller — expect lower volume than Meta

Step 4 — Creative strategy by funnel stage
  TOFU/MOFU: social proof (UGC reviews, testimonials), product demo, brand reminder
  BOFU cart abandoners: urgency + incentive (limited stock, discount code, free shipping)
  BOFU lead form openers: address objections, show case studies, strong benefit recap
  Retention: new products/collections, loyalty offer, upsell to complementary item
  Format: Spark Ads (boosted organic review) works exceptionally well for MOFU retargeting

Step 5 — Exclusion stacking (critical — same principle as Meta)
  MOFU excludes: recent purchasers (180d)
  BOFU excludes: recent purchasers (180d)
  TOFU-Warm excludes: MOFU audience + purchasers (180d)
  Retention excludes: purchasers 0-89d (only targets older buyers)

Step 6 — TikTok-specific retargeting nuances
  Engagement retargeting is unique to TikTok: 'Interacted with TikTok account' or 'Visited Profile'
  Use for MOFU: users who followed or engaged with organic content but didn't visit site
  View-through attribution inflates retargeting ROAS — cross-check with GA4 assisted conversions

Step 7 — Performance benchmarks
  BOFU ROAS should be 2-4× prospecting ROAS (warm audience, but TikTok retargeting smaller than Meta)
  If BOFU ROAS < 1.5× prospecting: landing page problem, wrong offer, or audience too small
  Creative refresh: retargeting users see ads more frequently — refresh creative every 7-10 days

Step 8 — Refresh cadence
  Audiences: pixel-based auto-update — verify pixel fires monthly
  Creative: refresh every 7-10 days (retargeting frequency is higher than prospecting)
  Offers: test new discount/incentive quarterly; rotate urgency messaging
""",
    },
}


def get_tiktok_sop_steps(command: str) -> str:
    """Map Telegram command to TikTok SOP and return steps."""
    mapping = {
        "/audit":        "Account Audit (Full)",
        "/tracking":     "Pixel & Events API Health Check",
        "/weekly":       "Weekly Optimization Loop",
        "/monthly":      "Weekly Optimization Loop",
        "/creative":     "Creative Refresh Playbook",
        "/hookrate":     "Creative Refresh Playbook",   # hook rate = creative health → SOP-T004
        "/scale":        "Scaling Playbook",
        "/audiences":    "Audience Strategy & Refresh",
        "/smartplus":    "Smart+ Campaign Setup",       # was incorrectly mapped as /smart
        "/incident":     "Incident Response (Sudden Drop)",
        "/launch":       "Campaign Launch Checklist",
        "/retargeting":  "Retargeting Funnel Setup",
    }
    sop_name = mapping.get(command)
    if not sop_name:
        return (
            f"## No SOP for {command}\n"
            "This command has no dedicated TikTok SOP. "
            "Run /audit for a full account review, or /creative for creative-specific guidance."
        )
    sop = TIKTOK_SOPS.get(sop_name, {})
    return (
        f"## {sop_name} [{sop.get('id', '')}]\n"
        f"Lifecycle: {sop.get('lifecycle', '')}\n"
        f"Modules: {sop.get('modules', '')}\n\n"
        f"### Steps\n{sop.get('steps', '').strip()}"
    )
