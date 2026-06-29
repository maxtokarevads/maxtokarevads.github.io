"""
Meta Ads Canon Rules — 25 active rules (MAC-XXXX).
Structure mirrors Google Ads Canon (GAC-XXXX) for consistency.

Severity:
  P0 — breaks measurement/policy/spend. Stop optimization, fix first.
  P1 — significant KPI impact. Fix within 24-48h.
  P2 — hygiene/optimization. Address in weekly cycle.
"""

META_CANON_RULES = [
    # ── P0: Measurement & Policy (7 rules) ──────────────────────────────────
    {
        "id": "MAC-0001",
        "severity": "P0",
        "where": "Pixel / Tracking",
        "rule": "Meta Pixel must be firing on all conversion pages (purchase, lead, add-to-cart)",
        "how_to_check": (
            "Events Manager → Data Sources → Pixel → Test Events (live) and Event History. "
            "Red flags: Purchase/Lead event missing in last 7d, 0 events on key pages, "
            "PageView fires but Purchase doesn't."
        ),
        "what_to_do": (
            "Re-verify pixel base code on all pages. Check Purchase event fires on order confirmation. "
            "Use Meta Pixel Helper Chrome extension for quick debug. "
            "If tag manager: verify GTM trigger fires on transaction page."
        ),
        "verify": "Purchase event appears in Events Manager within 24h. Test Events shows live fire.",
        "rollback": "Revert pixel code changes; restore previous GTM container version if used.",
        "lifecycle": "Setup | Incident",
        "objective_fit": "All",
    },
    {
        "id": "MAC-0002",
        "severity": "P0",
        "where": "Pixel / Tracking",
        "rule": "Primary conversion event must be active and receiving data (≥1 event in 7 days)",
        "how_to_check": (
            "Events Manager → Data Sources → Activity. "
            "Red flags: 0 purchase/lead events in last 7d, event status 'Inactive', "
            "all conversions are micro-events (ViewContent) with no macro (Purchase/Lead) as Primary."
        ),
        "what_to_do": (
            "Set the business-outcome event (Purchase for ecom, Lead/CompleteRegistration for lead-gen) "
            "as Primary in Ads Manager → Settings → Pixel → Manage Events. "
            "Investigate 0-event root cause: pixel fire, CAPI failure, or URL change."
        ),
        "verify": "Primary event count >0 in Events Manager after 24h. No sudden drop.",
        "rollback": "Revert event priority changes; document baseline event counts before change.",
        "lifecycle": "Setup | Incident | Weekly",
        "objective_fit": "All",
    },
    {
        "id": "MAC-0003",
        "severity": "P0",
        "where": "Pixel / CAPI",
        "rule": "No duplicate conversion counting — pixel and CAPI must not both report same event as Primary",
        "how_to_check": (
            "Events Manager → Data Sources → Pixel → Settings → Deduplication. "
            "Red flags: event_id not passed in both pixel and CAPI calls, "
            "total pixel events >> actual orders (dedup not working), "
            "ROAS looks 2-3× higher than reality."
        ),
        "what_to_do": (
            "Implement deduplication: pass matching event_id in both browser pixel and CAPI server event. "
            "Meta deduplicates on event_id + event_name + user_data match. "
            "Use Conversions API Gateway or partner integration (Shopify, WooCommerce) which handles dedup automatically."
        ),
        "verify": "Duplicated events % in Events Manager < 5%. Conv count matches actual backend orders ±10%.",
        "rollback": "Disable server-side event temporarily if dedup can't be implemented immediately.",
        "lifecycle": "Setup | Incident",
        "objective_fit": "All",
    },
    {
        "id": "MAC-0004",
        "severity": "P0",
        "where": "Policies / Account",
        "rule": "Ad account must be in Good Standing — no active policy violations, restrictions, or holds",
        "how_to_check": (
            "Ads Manager → Account Overview → Account Quality. "
            "Red flags: account disabled, payment hold, ad account restricted, "
            "active policy violations in Account Quality center."
        ),
        "what_to_do": (
            "Resolve violations per Meta's Account Quality recommendations. "
            "Request review in Account Quality → Request Review. "
            "For payment holds: verify billing info, update payment method. "
            "Document resolution timeline."
        ),
        "verify": "Account Quality shows no active issues. Ads serving normally within review window.",
        "rollback": "Revert any creative/targeting changes that triggered the violation.",
        "lifecycle": "Setup | Incident",
        "objective_fit": "All",
    },
    {
        "id": "MAC-0005",
        "severity": "P0",
        "where": "CAPI / Tracking",
        "rule": "Conversions API (CAPI) must be active alongside Pixel for signal resilience",
        "how_to_check": (
            "Events Manager → Data Sources → Pixel → Overview: check 'Server' activity in event breakdown. "
            "Red flags: only 'Browser' events shown, CAPI connected but 0 server events, "
            "Event Match Quality (EMQ) score < 6.0."
        ),
        "what_to_do": (
            "Activate CAPI: use Shopify/WooCommerce Meta integration (native), "
            "Conversions API Gateway (no-code), or direct API implementation. "
            "Pass customer data (email, phone, name) hashed with SHA-256 to maximize EMQ. "
            "Target EMQ ≥ 7.0."
        ),
        "verify": "Server events appear in Events Manager. EMQ score improves to ≥6.0 within 48h.",
        "rollback": "Disable CAPI if it causes duplicate counting until dedup is implemented.",
        "lifecycle": "Setup | Incident",
        "objective_fit": "All",
    },
    {
        "id": "MAC-0006",
        "severity": "P0",
        "where": "Tracking / Attribution",
        "rule": "Event Match Quality (EMQ) score must be ≥ 6.0 for primary conversion event",
        "how_to_check": (
            "Events Manager → Data Sources → Pixel → Event Match Quality tab. "
            "Red flags: EMQ < 6.0, missing email/phone match parameters, "
            "'No customer information' status on majority of events."
        ),
        "what_to_do": (
            "Pass more customer data: email (em), phone (ph), first_name (fn), last_name (ln), "
            "zip (zp), country (country). Hash all PII with SHA-256. "
            "For CAPI: pass fbp/fbc cookies alongside user data. "
            "Each parameter added improves EMQ by ~0.5–1.0 point."
        ),
        "verify": "EMQ improves to ≥6.0 within 72h of adding parameters.",
        "rollback": "Remove newly added parameters if they cause privacy compliance issues.",
        "lifecycle": "Setup | Quarterly",
        "objective_fit": "All",
    },
    {
        "id": "MAC-0007",
        "severity": "P0",
        "where": "Business Manager / Account",
        "rule": "Business Manager ownership and admin access must be verified and documented",
        "how_to_check": (
            "Business Manager → Business Settings → Business Info: check verification status. "
            "Red flags: Business Verification not completed, only one admin user, "
            "pixel/catalog owned by personal account not BM."
        ),
        "what_to_do": (
            "Complete Business Verification (required for larger spend and some objectives). "
            "Add 2+ admin users to prevent lockout. "
            "Transfer pixel and catalog ownership to Business Manager."
        ),
        "verify": "Business Verification badge visible. Assets owned by BM, not personal account.",
        "rollback": "N/A — verification is additive.",
        "lifecycle": "Setup",
        "objective_fit": "All",
    },

    # ── P1: Performance (10 rules) ────────────────────────────────────────────
    {
        "id": "MAC-0008",
        "severity": "P1",
        "where": "Campaign / Learning Phase",
        "rule": "Each ad set must reach ≥ 50 optimization events per week to exit Learning Phase",
        "how_to_check": (
            "Ads Manager → Ad Sets → Learning Phase column. "
            "Red flags: 'Learning Limited' status, ad sets with <50 conv/week, "
            "too many ad sets splitting budget below threshold."
        ),
        "what_to_do": (
            "Consolidate ad sets: merge audiences into fewer, larger ad sets. "
            "Increase budget: each ad set needs ~7× daily CPA budget to hit 50 conv/week. "
            "Consider switching to higher-volume conversion event (AddToCart → Purchase) "
            "if purchases are too rare. Switch to CBO to let Meta allocate."
        ),
        "verify": "Learning Phase status changes to 'Active' or disappears within 7 days.",
        "rollback": "Revert ad set merges and budget changes if performance drops post-consolidation.",
        "lifecycle": "Weekly | Setup",
        "objective_fit": "All",
    },
    {
        "id": "MAC-0009",
        "severity": "P1",
        "where": "Audiences / Ad Sets",
        "rule": "Audience overlap between ad sets must be < 30% to avoid internal competition",
        "how_to_check": (
            "Ads Manager → Ad Sets → select 2+ ad sets → Actions → Audience Overlap. "
            "Red flags: >30% overlap between prospecting ad sets, "
            "CPM rising rapidly across all ad sets simultaneously (internal auction competition)."
        ),
        "what_to_do": (
            "Use Audience Overlap tool to identify overlapping pairs. "
            "Options: (1) merge overlapping ad sets, (2) add audience exclusions, "
            "(3) use Campaign Budget Optimization (CBO) — Meta handles overlap internally. "
            "Advantage+ Audience eliminates overlap concern entirely."
        ),
        "verify": "Overlap % < 30% after adjustments. CPM stabilizes or improves.",
        "rollback": "Restore original audience definitions if consolidation harms performance.",
        "lifecycle": "Weekly | Monthly",
        "objective_fit": "All",
    },
    {
        "id": "MAC-0010",
        "severity": "P1",
        "where": "Creative / Frequency",
        "rule": "Frequency must stay ≤ 3x per 7-day window per ad set to prevent audience fatigue",
        "how_to_check": (
            "Ads Manager → Columns → Frequency. Set date range to last 7 days. "
            "Red flags: Frequency > 3, CTR dropping while CPM stays flat or rises, "
            "ROAS declining week-over-week with stable budget."
        ),
        "what_to_do": (
            "Rotate creative: add 3–5 new ad variants per ad set. "
            "Expand audience: add Lookalike, broaden interest targeting, "
            "or switch to Advantage+ Audience. "
            "Pause top-frequency ad and let new creative reset the curve."
        ),
        "verify": "Frequency drops below 3 within 7 days. CTR stabilizes or improves.",
        "rollback": "Re-enable paused ads if new creative underperforms significantly.",
        "lifecycle": "Weekly",
        "objective_fit": "All",
    },
    {
        "id": "MAC-0011",
        "severity": "P1",
        "where": "Campaign / Budget",
        "rule": "CBO must be used for campaigns with ≥3 ad sets; ABO only for testing phases",
        "how_to_check": (
            "Ads Manager → Campaign level → Budget type. "
            "Red flags: ABO with 5+ ad sets receiving unequal performance (Meta can't rebalance), "
            "one ad set spending 80%+ of budget while others starve."
        ),
        "what_to_do": (
            "Switch to CBO (Campaign Budget Optimization) for all campaigns with ≥3 ad sets. "
            "ABO is useful for: audience testing (equal spend per set), "
            "retargeting (prioritize specific segments). "
            "CBO + Advantage+ Audience is the current Meta best practice for scaling."
        ),
        "verify": "Budget distributes more evenly. ROAS improves as Meta finds best-performing audiences.",
        "rollback": "Switch back to ABO if CBO concentrates spend on one poor-performing ad set.",
        "lifecycle": "Setup | Monthly",
        "objective_fit": "All",
    },
    {
        "id": "MAC-0012",
        "severity": "P1",
        "where": "Audiences / Lookalike",
        "rule": "Lookalike source audience must have ≥ 1000 people for quality signal",
        "how_to_check": (
            "Ads Manager → Audiences → Custom Audiences → check source size. "
            "Red flags: Purchase-based Lookalike source has <1000 people, "
            "using email list with <500 contacts as LAL source."
        ),
        "what_to_do": (
            "Expand source: use Value-Based LAL (purchase value as signal) if available. "
            "Merge multiple lists (purchasers + high-LTV customers) to exceed 1000. "
            "Use pixel-based audiences (all purchasers last 180d) as source — typically larger. "
            "Minimum viable: 1000, optimal: 5000–10000+ for strong signal."
        ),
        "verify": "LAL source shows ≥1000 people. LAL campaigns show ROAS ≥ prospecting ROAS.",
        "rollback": "Pause LAL campaigns using under-threshold source; revert to broad targeting.",
        "lifecycle": "Setup | Monthly",
        "objective_fit": "All",
    },
    {
        "id": "MAC-0013",
        "severity": "P1",
        "where": "Audiences / Custom",
        "rule": "Custom Audiences must not be stale (last updated > 30 days for dynamic, > 90 days for static lists)",
        "how_to_check": (
            "Ads Manager → Audiences → last updated column. "
            "Red flags: Website Custom Audiences (WCA) not receiving new users (pixel broken), "
            "Customer list audience not refreshed in >90 days."
        ),
        "what_to_do": (
            "Dynamic audiences (pixel-based WCA): fix pixel if stale — they auto-update when pixel fires. "
            "Static lists: re-upload refreshed customer list with updated purchasers/subscribers. "
            "Set recurring calendar reminder: re-upload lists every 30–60 days."
        ),
        "verify": "Audience size grows or stays stable. 'Last updated' timestamp current.",
        "rollback": "Revert to previous customer list version if new upload causes audience size anomaly.",
        "lifecycle": "Monthly",
        "objective_fit": "All",
    },
    {
        "id": "MAC-0014",
        "severity": "P1",
        "where": "Audiences / Exclusions",
        "rule": "Existing customers must be excluded from cold-prospecting ad sets",
        "how_to_check": (
            "Ads Manager → Ad Set → Audiences → Exclusions. "
            "Red flags: prospecting campaigns show 0 exclusions, "
            "high conversion rate in 'prospecting' campaigns (likely retargeting existing customers), "
            "customer list not uploaded or expired."
        ),
        "what_to_do": (
            "Add to exclusions: (1) Customer List Custom Audience, "
            "(2) Website purchasers last 180d (pixel WCA), "
            "(3) Facebook Page engagers if they're existing customers. "
            "For lead-gen: exclude existing leads from CRM list."
        ),
        "verify": "Prospecting ad set audience size decreases after adding exclusions (confirms it works).",
        "rollback": "Remove exclusions if audience size drops too low for delivery.",
        "lifecycle": "Setup | Monthly",
        "objective_fit": "All",
    },
    {
        "id": "MAC-0015",
        "severity": "P1",
        "where": "Catalog / Feed",
        "rule": "Product catalog must have < 5% disapproved items in active DPA/Catalog campaigns",
        "how_to_check": (
            "Commerce Manager → Catalog → Diagnostics → Issues. "
            "Red flags: >5% products disapproved, 'availability' or 'price' errors, "
            "DPA campaigns spending but showing wrong/outdated prices."
        ),
        "what_to_do": (
            "Fix P0 feed errors first: price mismatch, unavailability, image violations. "
            "Use feed rules in Commerce Manager to transform problematic fields. "
            "Set up feed refresh schedule: hourly for ecom (price/stock changes). "
            "Exclude permanently unavailable products from catalog."
        ),
        "verify": "Disapproval rate < 5% in Catalog Diagnostics within 24h of feed fix.",
        "rollback": "Revert feed transformation rules if they cause new disapprovals.",
        "lifecycle": "Weekly | Incident",
        "objective_fit": "Ecom",
    },
    {
        "id": "MAC-0016",
        "severity": "P1",
        "where": "Campaign / Bid Strategy",
        "rule": "Bid strategy must match optimization event data volume and campaign objective",
        "how_to_check": (
            "Ads Manager → Ad Sets → Optimization & Delivery. "
            "Red flags: using Cost Cap with <50 conv/week (causes under-delivery), "
            "ROAS Target set but campaign has <100 purchases/month, "
            "Lowest Cost with no cap when CPA is 3× target."
        ),
        "what_to_do": (
            "Progression: Lowest Cost (learning) → Cost Cap (stable, ≥50 conv/week) → ROAS Target (≥100 conv/month). "
            "For new accounts: always start with Lowest Cost to gather data. "
            "Cost Cap threshold: set 20–30% above actual CPA to prevent under-delivery. "
            "ROAS Target: set 20% below actual ROAS to allow flexibility."
        ),
        "verify": "Delivery improves; CPA/ROAS stabilizes within 7 days of strategy change.",
        "rollback": "Switch back to Lowest Cost if Cost Cap causes severe under-delivery.",
        "lifecycle": "Weekly | Monthly",
        "objective_fit": "All",
    },
    {
        "id": "MAC-0017",
        "severity": "P1",
        "where": "Campaign / Structure",
        "rule": "Advantage+ Shopping Campaign (ASC) must be considered for ecom accounts with ≥ 500 purchases/month",
        "how_to_check": (
            "Ads Manager → check if ASC campaigns exist. "
            "Red flags: no ASC for ecom account with strong purchase history, "
            "only manual campaigns with manual audiences — missing Meta automation signal."
        ),
        "what_to_do": (
            "Launch 1 ASC campaign alongside existing manual campaigns. "
            "ASC setup: existing customer budget cap 10–30% (Meta default 30%), "
            "broad creative set (10+ assets), no manual audience targeting. "
            "Let ASC run for ≥2 weeks before evaluating. "
            "ASC typically outperforms manual at scale for mature accounts."
        ),
        "verify": "ASC ROAS ≥ manual campaigns ROAS after 14-day learning window.",
        "rollback": "Pause ASC if budget is being cannibalized from better-performing manual campaigns.",
        "lifecycle": "Monthly | Quarterly",
        "objective_fit": "Ecom",
    },

    # ── P2: Hygiene & Optimization (8 rules) ─────────────────────────────────
    {
        "id": "MAC-0018",
        "severity": "P2",
        "where": "Tracking / URLs",
        "rule": "All ads must have UTM parameters for proper attribution in GA4 / analytics",
        "how_to_check": (
            "Ads Manager → Ads → URL Parameters column. "
            "Red flags: missing utm_source, utm_medium, utm_campaign, "
            "GA4 shows high 'direct' traffic on conversion pages."
        ),
        "what_to_do": (
            "Add UTM template at campaign level: "
            "utm_source=facebook&utm_medium=paid_social&utm_campaign={{campaign.name}}&utm_content={{ad.name}}. "
            "Use Campaign URL Builder or set at Ad Set level → URL Parameters. "
            "Dynamic parameters: {{campaign.id}}, {{adset.id}}, {{ad.id}} for granular tracking."
        ),
        "verify": "GA4 shows facebook/paid_social sessions. Direct traffic drops.",
        "rollback": "Remove UTM if GA4 shows inflated session counts (double-counting).",
        "lifecycle": "Setup | Monthly",
        "objective_fit": "All",
    },
    {
        "id": "MAC-0019",
        "severity": "P2",
        "where": "Creative / Ad",
        "rule": "Creative refresh must happen before frequency exceeds 3 — maintain 10+ active ad variants per campaign",
        "how_to_check": (
            "Ads Manager → check number of active ads per campaign. "
            "Red flags: <3 active ad variants, no new creative in >21 days, "
            "CTR declining trend over 2+ weeks."
        ),
        "what_to_do": (
            "Maintain creative pipeline: minimum 10 assets/month for active campaigns. "
            "Creative testing framework: 1 control + 3 challengers per variable (hook/format/offer). "
            "Use Dynamic Creative Optimization (DCO) to auto-test combinations. "
            "Creative lifecycle: 2–4 weeks before expected fatigue (frequency >3)."
        ),
        "verify": "CTR stabilizes or improves after new creative launch. Frequency stays ≤3.",
        "rollback": "Reactivate paused top performers if new creative underperforms.",
        "lifecycle": "Weekly",
        "objective_fit": "All",
    },
    {
        "id": "MAC-0020",
        "severity": "P2",
        "where": "Creative / Video",
        "rule": "Video hook rate (3-second view rate) must be ≥ 25% for video ads",
        "how_to_check": (
            "Ads Manager → Columns → Video → ThruPlay, 3-Second Video Views, Video Plays. "
            "3-sec view rate = 3-sec views / impressions × 100. "
            "Red flags: 3-sec view rate <15%, video >30s with <5% completion rate."
        ),
        "what_to_do": (
            "Rewrite video hook: first 3 seconds must show product benefit or create curiosity. "
            "Hook formulas: Pain point ('Tired of X?'), Bold claim ('We doubled sales with Y'), "
            "Curiosity gap ('The one thing brands get wrong about Z'). "
            "Test static/carousel alongside video if hook rate <15%. "
            "Caption all videos (85% of FB video watched without sound)."
        ),
        "verify": "3-sec view rate improves to ≥25% on new creative within first week.",
        "rollback": "Pause video ad and revert budget to static if video rate stays <15% after 500+ impressions.",
        "lifecycle": "Weekly",
        "objective_fit": "All",
    },
    {
        "id": "MAC-0021",
        "severity": "P2",
        "where": "Landing Page",
        "rule": "Landing page must load in < 3 seconds on mobile (Core Web Vitals LCP)",
        "how_to_check": (
            "PageSpeed Insights (https://pagespeed.web.dev/) → Mobile score. "
            "Red flags: LCP >3s, CLS >0.1, mobile score <50, "
            "CVR < 1% despite good CTR (indicates landing page friction)."
        ),
        "what_to_do": (
            "Priority fixes: compress images (use WebP), enable CDN, minimize render-blocking JS. "
            "Quick wins: lazy-load below-fold images, remove unused scripts, enable browser caching. "
            "Consider Instant Experience (Meta's fast-loading canvas) for mobile-first campaigns."
        ),
        "verify": "PageSpeed mobile score ≥60. LCP <3s. CVR improves within 14 days.",
        "rollback": "Revert site changes if load time gets worse or conversion errors appear.",
        "lifecycle": "Monthly | Quarterly",
        "objective_fit": "All",
    },
    {
        "id": "MAC-0022",
        "severity": "P2",
        "where": "Audiences / Targeting",
        "rule": "Interest-based audience size must be 500K–20M for optimal delivery (not too narrow, not too broad)",
        "how_to_check": (
            "Ads Manager → Ad Set → Audience size meter. "
            "Red flags: audience < 100K (too narrow, CPM spikes, under-delivery), "
            ">50M (too broad, wasted impressions, algorithm can't find buyers)."
        ),
        "what_to_do": (
            "Narrow: add more interests/behaviours to expand, or layer lookalike on top. "
            "Too broad: add demographic filters (age, income if available), "
            "or switch to Detailed Targeting Expansion OFF for tighter control. "
            "Optimal range: 500K–5M for conversion campaigns, up to 20M for awareness."
        ),
        "verify": "Audience size meter shows 'Defined' to 'Broad' (not 'Specific' or 'Very broad').",
        "rollback": "Revert targeting changes if reach drops below minimum delivery threshold.",
        "lifecycle": "Setup | Monthly",
        "objective_fit": "All",
    },
    {
        "id": "MAC-0023",
        "severity": "P2",
        "where": "Creative / Copy",
        "rule": "Ad copy must respect Meta character limits and follow platform best practices",
        "how_to_check": (
            "Ads Manager → Ads → Preview. "
            "Red flags: primary text truncated in Feed (>125 chars), "
            "headline > 40 chars (truncated on mobile), "
            "no clear CTA in description, all-caps or excessive punctuation triggering policy flags."
        ),
        "what_to_do": (
            "Character limits: Primary text ≤125 chars (above-fold), Headline ≤40 chars, "
            "Description ≤30 chars. "
            "Best practices: lead with benefit/hook in first line, "
            "use social proof (numbers, reviews), include clear CTA. "
            "Test 3 variants: problem-focused, benefit-focused, social proof-focused."
        ),
        "verify": "Ads preview without truncation across Feed, Stories, Reels placements.",
        "rollback": "Revert to previous copy if new versions show lower CTR after 300+ impressions.",
        "lifecycle": "Setup | Weekly",
        "objective_fit": "All",
    },
    {
        "id": "MAC-0024",
        "severity": "P2",
        "where": "Account / Structure",
        "rule": "Naming convention must be consistent: [Objective]-[Audience]-[Date] at campaign, ad set, and ad level",
        "how_to_check": (
            "Ads Manager → scan campaign/ad set/ad names. "
            "Red flags: names like 'Campaign 1', 'Ad Set - Copy', random emojis, "
            "no date stamp, no audience identifier — impossible to analyze at scale."
        ),
        "what_to_do": (
            "Adopt convention: "
            "Campaign: [Product]-[Objective]-[Market]-[YYYYMM] (e.g. Shoes-CONV-US-202601). "
            "Ad Set: [Audience type]-[Size]-[Age] (e.g. LAL1pct-Purchasers-25-44). "
            "Ad: [Format]-[Hook type]-[Version] (e.g. Video-Pain-v3). "
            "Rename all active items; set up template in Business Manager."
        ),
        "verify": "All active campaigns/ad sets/ads follow convention after rename.",
        "rollback": "N/A — naming is non-destructive.",
        "lifecycle": "Setup | Quarterly",
        "objective_fit": "All",
    },
    {
        "id": "MAC-0025",
        "severity": "P2",
        "where": "Creative / Advantage+",
        "rule": "Advantage+ Creative must be enabled on all active ad sets to unlock Meta's auto-optimizations",
        "how_to_check": (
            "Ads Manager → Ads → Edit → Advantage+ Creative section. "
            "Red flags: Advantage+ Creative off for all ads, "
            "missing music, brightness/contrast optimization, text overlay."
        ),
        "what_to_do": (
            "Enable Advantage+ Creative at ad level: automatic adjustments, "
            "add music for Reels/Stories, enable text overlay optimization. "
            "Caution: review auto-generated variations to ensure brand compliance. "
            "Disable specific enhancements that alter brand visual identity."
        ),
        "verify": "Advantage+ Creative shows 'On' in ad details. Check auto-variations in preview.",
        "rollback": "Disable Advantage+ Creative if auto-variations violate brand guidelines.",
        "lifecycle": "Setup | Monthly",
        "objective_fit": "All",
    },

    # ── Measurement 2026 (MAC-0026 – MAC-0029) ────────────────────────────────

    {
        "id": "MAC-0026",
        "severity": "P0",
        "where": "Privacy / Consent",
        "rule": "Consent signals must be passed to Meta Pixel for EU/EEA users — non-compliance risks ad account restrictions and invalidates attribution data",
        "how_to_check": (
            "Events Manager → Pixel → Settings → check consent configuration. "
            "Test with Facebook Pixel Helper: after CMP rejection, pixel should NOT fire standard events. "
            "Red flags: pixel fires all events regardless of consent choice; "
            "no CMP or cookie banner present on site; "
            "Events Manager showing restricted data use warnings."
        ),
        "what_to_do": (
            "Implement Meta Pixel Consent API: "
            "Default deny: fbq('consent','revoke') before CMP loads. "
            "After consent granted: fbq('consent','grant'). "
            "US states (CCPA etc.): fbq('dataProcessingOptions',['LDU'],1,1000) for California. "
            "For CAPI: include data_processing_options in server events matching pixel. "
            "Use your CMP's native Meta integration if available (OneTrust, Cookiebot, etc.)."
        ),
        "verify": "Pixel Helper shows consent state changes. No data restriction warnings in Events Manager. Events only fire after user grants consent (EU).",
        "rollback": "Do not remove consent gate — legal requirement. If pixel breaks: check fbq('consent','grant') call triggers on CMP acceptance.",
        "lifecycle": "Setup | Quarterly",
        "objective_fit": "All",
    },
    {
        "id": "MAC-0027",
        "severity": "P0",
        "where": "CAPI / Server-side",
        "rule": "Conversions API must send server-side events matching pixel events — iOS14+ and browser restrictions lose 30-50% of pixel-only conversions",
        "how_to_check": (
            "Events Manager → Data Sources → Events → Source column: Browser vs Server vs Both. "
            "EMQ score: target ≥7.0. Deduplication rate: target <5%. "
            "Red flags: only Browser source for Purchase/Lead; EMQ <6.0; "
            "Ads Manager conversions 40%+ below backend orders."
        ),
        "what_to_do": (
            "Implement CAPI via: Shopify Meta app / WooCommerce plugin (easiest) or "
            "CAPI Gateway in Events Manager (no-code server-side) or direct API. "
            "Pass hashed: email (em), phone (ph), ip, user_agent, fbp, fbc. "
            "Include event_id in both pixel and server event for deduplication. "
            "Target: EMQ ≥7.0 | server events ≥60% of total."
        ),
        "verify": "Both Browser and Server sources visible in Events Manager. Deduplication <5%. EMQ ≥7.0.",
        "rollback": "CAPI is additive. If deduplication fails (double-counting), fix event_id matching — do not remove CAPI.",
        "lifecycle": "Setup",
        "objective_fit": "All",
    },
    {
        "id": "MAC-0028",
        "severity": "P1",
        "where": "Offline Conversions / Lead-gen",
        "rule": "Offline Conversions API must close the loop from Meta leads to CRM qualified stages — form-fill optimisation produces high volume but low-quality leads",
        "how_to_check": (
            "Events Manager: look for offline event set. "
            "Red flags: Lead Ads high volume but low contact/MQL rate; "
            "no offline conversion event set in Events Manager; "
            "CRM has no fbclid field; optimising on instant form submission only."
        ),
        "what_to_do": (
            "Lead Ads: fbclid captured automatically — connect CRM via Lead Ads webhook. "
            "When lead reaches MQL/SQL/Won: upload to offline events: "
            "lead_id + event_name (Lead_Qualified / Opportunity / Purchase) + event_time. "
            "Use qualified-lead offline event as campaign optimization goal. "
            "Alternative: CAPI offline_events endpoint for server-side upload."
        ),
        "verify": "Offline event set shows data within 48h. Ads Manager offline column populated. Campaign optimization updated to qualified lead stage.",
        "rollback": "Offline events additive — no risk. If volume too low for optimization: use as secondary metric only.",
        "lifecycle": "Setup | Monthly",
        "objective_fit": "Lead-gen | B2B",
    },
    {
        "id": "MAC-0029",
        "severity": "P1",
        "where": "Measurement / Incrementality",
        "rule": "Meta-attributed ROAS overstates true incremental impact by 35-55% — holdout test required quarterly to calibrate true ad contribution",
        "how_to_check": (
            "Experiments → check for active or completed Holdout tests. "
            "Red flags: no holdout in last 6 months; blended MER (Total Revenue / Total Ad Spend) "
            "significantly lower than Meta-attributed ROAS."
        ),
        "what_to_do": (
            "Experiments → Create → Holdout Test. "
            "Holdout: 10-15% of audience sees no Meta ads. "
            "Duration: 14-21 days. "
            "Measure incremental lift: (exposed CVR - holdout CVR) / holdout CVR. "
            "True ROAS = Attributed ROAS × incremental lift factor. "
            "Apply factor to budget decisions and ROAS targets."
        ),
        "verify": "Holdout completed with ≥80% confidence. Incrementality factor documented and applied to ROAS targets.",
        "rollback": "Restore holdout audience to exposed after experiment.",
        "lifecycle": "Quarterly",
        "objective_fit": "All",
    },

    # ── B2B / Lead-gen (MAC-0030 – MAC-0033) ─────────────────────────────────

    {
        "id": "MAC-0030",
        "severity": "P1",
        "where": "Lead Ads / CRM",
        "rule": "Lead Ads must sync to CRM in real-time via webhook — manual CSV download delays follow-up and reduces contact rate by 50-80%",
        "how_to_check": (
            "Business Manager → Integrations → check for CRM connection. "
            "Test: submit lead form → how long until it appears in CRM? "
            "Red flags: leads downloaded manually; >1h delay before sales notified; contact rate <20%."
        ),
        "what_to_do": (
            "Connect CRM natively: HubSpot, Salesforce, Zoho, ActiveCampaign available in Business Manager → Integrations. "
            "Fallback: Zapier/Make webhook → CRM contact create. "
            "Minimum: email notification to sales within 5 minutes of form submit. "
            "Target: lead contacted within 5 minutes → contact rate 3-4× higher than 1-hour delay."
        ),
        "verify": "Test lead appears in CRM within 2 minutes. Automated sequence triggers. Contact rate ≥30% (industry avg for well-operated lead-gen).",
        "rollback": "Webhook can be paused independently. Manual CSV as backup.",
        "lifecycle": "Setup | Monthly",
        "objective_fit": "Lead-gen | B2B",
    },
    {
        "id": "MAC-0031",
        "severity": "P1",
        "where": "Targeting / B2B",
        "rule": "B2B campaigns must layer job-function and company-size targeting — interest-only targeting wastes budget on non-decision-makers",
        "how_to_check": (
            "Ad Set → Detailed Targeting: what layers are active? "
            "Red flags: only broad interests; no job-function or employer-size categories; "
            "high form volume but low MQL rate (<5%)."
        ),
        "what_to_do": (
            "Detailed Targeting additions: "
            "Job titles: 'Director', 'VP', 'C-Suite', role-specific (e.g. 'Marketing Manager'). "
            "Industries: Work → Industries → select relevant verticals. "
            "Behaviors: 'Business decision makers' as broad filter. "
            "Lookalike: upload CRM decision-maker list → 1% LAL. "
            "Note: Meta B2B targeting less precise than LinkedIn — expect 20-30% off-ICP audience."
        ),
        "verify": "MQL rate from B2B campaigns ≥15% (vs 3-8% general). CRM shows target job titles submitting forms.",
        "rollback": "Remove job-title targeting if audience <500K. Broaden one layer at a time.",
        "lifecycle": "Setup | Quarterly",
        "objective_fit": "Lead-gen | B2B",
    },
    {
        "id": "MAC-0032",
        "severity": "P2",
        "where": "Value-based Bidding / B2B",
        "rule": "Value-based optimization on qualified lead events unlocks Meta's ability to seek high-value leads — flat CPA treats CMO leads the same as intern leads",
        "how_to_check": (
            "Campaign optimization event: form submission or qualified lead? "
            "Red flags: optimising on form submission only; no conversion value differentiation; all leads valued equally."
        ),
        "what_to_do": (
            "Assign conversion values via offline events (MAC-0028): "
            "Form submit = 1 | MQL = 10 | SQL = 50 | Won = 200 (or actual deal value). "
            "Switch optimization to Conversion Value with Minimum ROAS target. "
            "Requires ≥50 value-attributed events/week for learning. "
            "If volume insufficient: use Lowest Cost on MQL event (not form fill)."
        ),
        "verify": "Value-per-lead trending up. MQL rate ≥15%. Meta shifting budget to higher-value creative/audience.",
        "rollback": "Revert to Lowest Cost if Learning Limited. Build qualified lead volume first.",
        "lifecycle": "Monthly | Quarterly",
        "objective_fit": "Lead-gen | B2B",
    },
    {
        "id": "MAC-0033",
        "severity": "P2",
        "where": "Creative / B2B",
        "rule": "B2B Meta creative must address decision-maker business outcomes — consumer-style hooks underperform for buyers evaluating ROI and organizational risk",
        "how_to_check": (
            "Review active creatives: do headlines speak to business outcomes (ROI, efficiency, risk reduction) "
            "or consumer benefits? "
            "Red flags: generic lifestyle imagery; no social proof from recognisable companies; "
            "no quantified business outcome; vague value proposition."
        ),
        "what_to_do": (
            "B2B creative formula: "
            "Hook: quantified outcome or peer validation ('How [Company] cut CAC by 40%'). "
            "Body: specific problem → mechanism → result (no vague claims). "
            "Social proof: client logos, named testimonials with title/company, industry data. "
            "CTA: low-friction awareness (Guide/Webinar) → high-intent BOFU (Demo/Trial/Quote). "
            "Format: static image with bold data point often beats video for B2B (decision-makers skim). "
            "Test: social-proof vs problem-led vs ROI-calculator CTA."
        ),
        "verify": "MQL rate ≥15%. CRM shows target job titles submitting. Hook Rate ≥20%.",
        "rollback": "A/B test; keep best-performing creative. Never pause all ads simultaneously.",
        "lifecycle": "Weekly | Monthly",
        "objective_fit": "Lead-gen | B2B",
    },
]


def get_meta_rules_for_audit(account_type: str = "") -> str:
    """Return all rules; filter by objective_fit when account_type is given.
    Consistent with Google Canon: include rule when obj=='All' OR account_type matches."""
    lines = []
    for r in META_CANON_RULES:
        obj = r.get("objective_fit", "All")
        if account_type and obj != "All" and account_type.lower() not in obj.lower():
            continue
        lines.append(
            f"[{r['id']}] {r['severity']} | {r['where']}\n"
            f"Rule: {r['rule']}\n"
            f"Check: {r['how_to_check']}\n"
            f"Fix: {r['what_to_do']}\n"
            f"Verify: {r['verify']}\n"
            f"Rollback: {r['rollback']}\n"
            f"Lifecycle: {r['lifecycle']}\n"
        )
    return "\n---\n".join(lines)
