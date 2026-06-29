"""
TikTok Ads Canon Rules — 25 active rules (TAC-XXXX).
Structure mirrors Meta Ads Canon (MAC-XXXX) and Google Ads Canon (GAC-XXXX).

Severity:
  P0 — breaks measurement/policy/spend. Stop optimization, fix first.
  P1 — significant KPI impact. Fix within 24-48h.
  P2 — hygiene/optimization. Address in weekly cycle.

TikTok-specific context:
  - Algorithm-first platform: content targeting drives reach, not just demographics
  - Creative fatigue is 2-3x faster than Meta (1-2 week shelf life)
  - Hook Rate (3-sec view rate) is the primary creative health signal
  - Events API (CAPI equivalent) is less mature — over-attribution 35-55% is norm
  - Learning phase: 50 conversions / 7 days per Ad Group
"""

TIKTOK_CANON_RULES = [
    # ── P0: Measurement & Policy (7 rules) ──────────────────────────────────
    {
        "id": "TAC-0001",
        "severity": "P0",
        "where": "Pixel / Tracking",
        "rule": "TikTok Pixel must be firing on all conversion pages (purchase, lead, add-to-cart)",
        "how_to_check": (
            "TikTok Ads Manager → Assets → Events → Web Events → Test Events (real-time). "
            "Check: PageView fires on all pages; Purchase/Lead fires on confirmation page only. "
            "Red flags: Purchase/Lead missing in last 7d, 0 events on key pages, "
            "ViewContent fires but Purchase doesn't, mismatched event counts vs backend orders."
        ),
        "what_to_do": (
            "Re-verify pixel base code on all pages. Use TikTok Pixel Helper (Chrome extension). "
            "Check Purchase event fires exclusively on order confirmation / thank-you page. "
            "If tag manager (GTM): verify trigger fires on transaction page, not all pages. "
            "Test via Events Manager → Test Events in real time before any campaign launch."
        ),
        "verify": "Purchase/Lead event appears in Events Manager within 24h. Test Events confirms live fire.",
        "rollback": "Revert pixel code changes; restore previous GTM container version if used.",
        "lifecycle": "Setup | Incident",
        "objective_fit": "All",
    },
    {
        "id": "TAC-0002",
        "severity": "P0",
        "where": "Pixel / Tracking",
        "rule": "Primary conversion event must be active and receiving data (≥1 event in 7 days)",
        "how_to_check": (
            "Events Manager → Web Events → Activity tab. "
            "Red flags: 0 purchase/lead events in last 7d, event status 'Inactive', "
            "only micro-events (ViewContent, AddToCart) with no macro event (Purchase/Lead) as primary. "
            "Compare pixel event count vs backend order count — divergence >30% = problem."
        ),
        "what_to_do": (
            "Set the business-outcome event (Purchase for e-com, Lead/CompleteRegistration for lead-gen) "
            "as primary optimization event in Ad Group settings. "
            "If 0 events: check pixel fire, Events API connection, URL changes. "
            "Fallback: temporarily optimize on AddToCart if Purchase volume is too low (<10/week)."
        ),
        "verify": "Primary event count >0 in Events Manager after 24h. No sudden drop vs baseline.",
        "rollback": "Revert event priority; document baseline event counts before change.",
        "lifecycle": "Setup | Incident | Weekly",
        "objective_fit": "All",
    },
    {
        "id": "TAC-0003",
        "severity": "P0",
        "where": "Pixel / Events API",
        "rule": "No duplicate conversion counting — Pixel and Events API must deduplicate via event_id",
        "how_to_check": (
            "Events Manager → Web Events → check 'Deduplicated' column in event breakdown. "
            "Red flags: event_id not passed in both pixel and Events API calls, "
            "total pixel events >> actual orders (dedup not working), "
            "ROAS appears 2-3× higher than GA4 / backend reality, "
            "Purchase event count is double the actual order count."
        ),
        "what_to_do": (
            "Implement deduplication: pass matching event_id in both browser pixel and Events API server call. "
            "TikTok deduplicates on event_id + event_name match within 48h window. "
            "Use Shopify/WooCommerce TikTok integration which handles dedup automatically. "
            "Manual: generate UUID per order and pass identically in pixel and server event."
        ),
        "verify": "Duplicate event % < 5% in Events Manager. Conv count matches actual backend orders ±15%.",
        "rollback": "Disable server-side Events API temporarily if dedup can't be implemented immediately.",
        "lifecycle": "Setup | Incident",
        "objective_fit": "All",
    },
    {
        "id": "TAC-0004",
        "severity": "P0",
        "where": "Policies / Account",
        "rule": "Ad account must be in Good Standing — no active policy violations, restrictions, or payment holds",
        "how_to_check": (
            "TikTok Ads Manager → Account → Account Health (top-right notification bell). "
            "Red flags: account disabled or restricted, payment hold, "
            "active policy violations in notification center, ads stuck 'Under Review' > 48h, "
            "creative disapprovals affecting >20% of active ads."
        ),
        "what_to_do": (
            "Resolve violations per TikTok Advertising Policies guidance. "
            "Appeal in Ads Manager → Help → Appeal Center. "
            "For payment holds: verify billing info, update payment method. "
            "For creative violations: remove flagged elements (claims, restricted categories, audio). "
            "Do not duplicate violating ads before appeal is resolved."
        ),
        "verify": "Account Health shows no active issues. Ads serving normally within review window (24-72h).",
        "rollback": "Revert any creative/targeting changes that triggered the violation before appeal.",
        "lifecycle": "Setup | Incident",
        "objective_fit": "All",
    },
    {
        "id": "TAC-0005",
        "severity": "P0",
        "where": "Events API / Tracking",
        "rule": "Events API must be active alongside Pixel for signal resilience and iOS tracking",
        "how_to_check": (
            "Events Manager → Web Events → event breakdown by Source (Browser vs. Server). "
            "Red flags: only 'Browser' events shown (no server events), "
            "Events API connected but 0 server events in last 7d, "
            "conversion volume drops >30% post iOS 14.5 update without server-side fallback."
        ),
        "what_to_do": (
            "Activate Events API: use TikTok's native Shopify/WooCommerce integration, "
            "or implement server-side API directly. "
            "Pass customer data hashed with SHA-256: email (em), phone (ph), "
            "IP address (ip), user_agent (ua), external_id (external_id). "
            "Target: ≥50% of conversion events reported via server."
        ),
        "verify": "Server events appear in Events Manager within 48h. Server event % ≥ 50% of total.",
        "rollback": "Disable Events API if it causes duplicate counting until dedup (TAC-0003) is implemented.",
        "lifecycle": "Setup | Incident",
        "objective_fit": "All",
    },
    {
        "id": "TAC-0006",
        "severity": "P0",
        "where": "Creative / Format",
        "rule": "All In-Feed video ads must be 9:16 vertical format at 1080×1920px resolution",
        "how_to_check": (
            "Ads Manager → Ads → Preview each active ad. "
            "Red flags: horizontal (16:9) video uploaded, resolution <720px, "
            "black bars on sides (letterboxed), important content in top/bottom 15% (cut off by UI). "
            "TikTok rejects non-vertical or sub-720p assets at upload."
        ),
        "what_to_do": (
            "Export video in 9:16 (1080×1920px). "
            "If only horizontal footage: crop or use template with branded borders (not ideal). "
            "Safe zone: keep key content between y=15% and y=85% (avoid TikTok UI overlap). "
            "File: MP4 or MOV, ≤500MB, 5–60 sec, 23–60 FPS."
        ),
        "verify": "Ad preview shows full-screen vertical video without letterboxing. No safe-zone violations.",
        "rollback": "Pause ads using non-compliant format; revert to last approved creative.",
        "lifecycle": "Setup | Incident",
        "objective_fit": "All",
    },
    {
        "id": "TAC-0007",
        "severity": "P0",
        "where": "Business Center / Account",
        "rule": "TikTok Business Center ownership and admin access must be verified and documented",
        "how_to_check": (
            "Business Center → Settings → Business Info: check verification status. "
            "Red flags: Business Verification not completed (limits spend and some ad formats), "
            "only one admin user (lockout risk), pixel/catalog owned outside Business Center, "
            "ad account not linked to Business Center."
        ),
        "what_to_do": (
            "Complete Business Verification (required for spend limits >$1500/day and branded formats). "
            "Add ≥2 admin users to Business Center to prevent lockout. "
            "Transfer pixel and catalog ownership to Business Center (not personal account). "
            "Link all ad accounts to Business Center for centralized management."
        ),
        "verify": "Business Verification badge visible in Business Center. All assets owned by BC, not personal.",
        "rollback": "N/A — verification is additive.",
        "lifecycle": "Setup",
        "objective_fit": "All",
    },

    # ── P1: Performance (10 rules) ────────────────────────────────────────────
    {
        "id": "TAC-0008",
        "severity": "P1",
        "where": "Campaign / Learning Phase",
        "rule": "Each Ad Group must reach ≥ 50 optimization events per 7 days to exit Learning Phase",
        "how_to_check": (
            "Ads Manager → Ad Groups → Delivery Status column: look for 'Learning' badge. "
            "Red flags: Ad Group stuck in 'Learning' >7 days, "
            "budget too low (<10× daily CPA target), too many Ad Groups splitting budget, "
            "conversion event too rare (<10/week even for BOFU)."
        ),
        "what_to_do": (
            "Consolidate Ad Groups: merge similar audiences into fewer, larger Ad Groups. "
            "Increase budget: each Ad Group needs ~7× daily CPA to hit 50 conv/week. "
            "Switch to higher-volume event if purchases rare: AddToCart (≥50/week) → Purchase. "
            "Consider Smart+ Campaign (TikTok's ASC equivalent) if manual learning phase fails. "
            "Do NOT change bid, budget, audience, or creative during learning — resets the clock."
        ),
        "verify": "Learning badge disappears from Ad Group within 7 days of reaching 50 events/week.",
        "rollback": "Revert Ad Group merges/budget changes if performance drops post-consolidation.",
        "lifecycle": "Weekly | Setup",
        "objective_fit": "All",
    },
    {
        "id": "TAC-0009",
        "severity": "P1",
        "where": "Creative / Fatigue",
        "rule": "Creative must be refreshed when CTR drops ≥ 20% week-over-week at stable CPM",
        "how_to_check": (
            "Ads Manager → Ads → compare CTR last 7d vs prior 7d per creative. "
            "Red flags: CTR drop ≥20% while CPM is flat or rising (not external CPM spike), "
            "creative age >10 days with declining trend, "
            "Hook Rate dropping below 20% on previously healthy creative."
        ),
        "what_to_do": (
            "Refresh hook first: re-shoot or re-edit first 1–3 seconds with new angle/text/sound. "
            "TikTok-specific: try different trending audio/sound on same visual content. "
            "Introduce new creative variant alongside fatigued ad (don't pause immediately). "
            "Cadence: plan new creative every 7–14 days for active campaigns with >$50/day spend."
        ),
        "verify": "New creative achieves CTR ≥ fatigued creative baseline within 3–5 days.",
        "rollback": "Re-enable fatigued creative if new creative CTR is ≥30% worse after 500 impressions.",
        "lifecycle": "Weekly",
        "objective_fit": "All",
    },
    {
        "id": "TAC-0010",
        "severity": "P1",
        "where": "Creative / Video",
        "rule": "Hook Rate (3-sec view rate) must be ≥ 30% — below 20% requires immediate hook revision",
        "how_to_check": (
            "Ads Manager → Columns → Video → '3-Second Video Views' ÷ Impressions × 100. "
            "Red flags: Hook Rate <20%, video autoplay skipped before 3s, "
            "average watch time <3s (even on 15s video), "
            "high impressions but low CTR despite good CPM."
        ),
        "what_to_do": (
            "Rewrite hook (first 1–3 seconds): "
            "• Pain-point question: 'Why is your store not converting?' "
            "• Shock stat: '73% of store owners make this mistake...' "
            "• Bold claim: 'I spent $50k on ads and here's what I learned' "
            "• Pattern interrupt: unexpected motion, sound, or text overlay on frame 1. "
            "Text overlay on first frame is mandatory — many users watch before sound kicks in."
        ),
        "verify": "Hook Rate ≥30% on new creative after ≥500 impressions.",
        "rollback": "Test previous hook version if new one scores <15% Hook Rate after 300 impressions.",
        "lifecycle": "Weekly",
        "objective_fit": "All",
    },
    {
        "id": "TAC-0011",
        "severity": "P1",
        "where": "Creative / Video",
        "rule": "Video Completion Rate must be ≥ 25% for videos ≤15 sec; ≥ 15% for videos 16–30 sec",
        "how_to_check": (
            "Ads Manager → Columns → Video → ThruPlay count ÷ Impressions × 100. "
            "Or: Average Watch Time ÷ Video Duration × 100. "
            "Red flags: Completion Rate <15% for short video, average watch time <4 sec, "
            "viewers dropping off sharply at same timestamp (check retention curve in Creative Center)."
        ),
        "what_to_do": (
            "Shorten video: trim to strongest 9–12 seconds. "
            "Add pattern interrupts every 3–5 seconds: text change, zoom, cut, sound effect. "
            "Eliminate slow middle section (most drop-off happens at sec 4–8). "
            "Test shorter 6–9 sec version with same hook — often outperforms on TikTok. "
            "Add captions: keeps viewers engaged even without sound."
        ),
        "verify": "Completion Rate ≥25% for ≤15s video after creative revision.",
        "rollback": "Revert to original duration if edited version drops Hook Rate below baseline.",
        "lifecycle": "Weekly",
        "objective_fit": "All",
    },
    {
        "id": "TAC-0012",
        "severity": "P1",
        "where": "Campaign / Budget",
        "rule": "Bid strategy must match campaign maturity and optimization event data volume",
        "how_to_check": (
            "Ads Manager → Ad Group → Bid & Optimization. "
            "Red flags: Cost Cap used with <50 conv/week (causes under-delivery), "
            "Bid Cap set too low (Ad Group not spending available budget), "
            "Maximum Delivery used on account with no conversion history (overspend risk), "
            "Minimum ROAS set but campaign has <100 purchases/month."
        ),
        "what_to_do": (
            "Progression: "
            "New campaign → Maximum Delivery (no cap) for data gathering. "
            "After 50+ conv/week → Cost Cap (set 20-30% above actual CPA). "
            "After 100+ conv/month with stable ROAS → Minimum ROAS (set 20% below actual ROAS). "
            "Bid Cap: only for strict CPC/CPM control — risk of under-delivery."
        ),
        "verify": "Ad Group delivery improves; CPA/ROAS stabilizes within 7 days of strategy change.",
        "rollback": "Switch to Maximum Delivery if Cost Cap causes severe under-delivery (spending <70% of budget).",
        "lifecycle": "Weekly | Monthly",
        "objective_fit": "All",
    },
    {
        "id": "TAC-0013",
        "severity": "P1",
        "where": "Audiences / Custom",
        "rule": "Custom Audiences used for targeting or Lookalike source must have ≥ 1000 users",
        "how_to_check": (
            "Ads Manager → Assets → Audiences → check size column for each Custom Audience. "
            "Red flags: Retargeting audience <1000 users (TikTok minimum for delivery), "
            "Lookalike source <1000 seed users (weak signal), "
            "Customer File audience showing 0 matches (email/phone format issue)."
        ),
        "what_to_do": (
            "Expand retargeting window: 7d → 14d → 30d to grow audience size. "
            "For Lookalike: use pixel-based Purchase audience (180d) as seed instead of small list. "
            "Customer File: ensure phone numbers include country code, emails are lowercase. "
            "Minimum viable for Lookalike: 1000; optimal: 10000+ for strong signal."
        ),
        "verify": "Custom Audience size shows ≥1000 in Assets panel. Lookalike source ≥1000 seed users.",
        "rollback": "Pause campaigns using under-threshold audiences; revert to broad targeting.",
        "lifecycle": "Setup | Monthly",
        "objective_fit": "All",
    },
    {
        "id": "TAC-0014",
        "severity": "P1",
        "where": "Audiences / Exclusions",
        "rule": "Existing customers and recent purchasers must be excluded from cold-prospecting Ad Groups",
        "how_to_check": (
            "Ads Manager → Ad Group → Targeting → Exclusions section. "
            "Red flags: prospecting Ad Groups show 0 exclusions, "
            "conversion rate suspiciously high in 'prospecting' (likely hitting existing customers), "
            "customer list not uploaded or not excluded."
        ),
        "what_to_do": (
            "Add to exclusions in prospecting Ad Groups: "
            "(1) Pixel Custom Audience: Purchase event, last 180d. "
            "(2) Customer File: full purchaser list from CRM. "
            "(3) Engagement audience: recent TikTok profile visitors (optional). "
            "For Lead Gen: exclude existing leads from CRM list."
        ),
        "verify": "Prospecting Ad Group audience size decreases after adding exclusions (confirms it works).",
        "rollback": "Remove exclusions if audience size drops below delivery minimum.",
        "lifecycle": "Setup | Monthly",
        "objective_fit": "All",
    },
    {
        "id": "TAC-0015",
        "severity": "P1",
        "where": "Catalog / Feed",
        "rule": "Product catalog must have < 5% disapproved items in active Shopping Ads campaigns",
        "how_to_check": (
            "TikTok Ads Manager → Assets → Catalog → Diagnostics. "
            "Red flags: >5% products disapproved, 'price mismatch' or 'image violation' errors, "
            "Shopping Ads spending but showing wrong/outdated prices, "
            "catalog not refreshed in >24h (price/stock stale)."
        ),
        "what_to_do": (
            "Fix P0 feed errors first: price mismatch vs landing page, unavailable items, image policy violations. "
            "Set feed refresh schedule: every 4–6h for e-com with frequent price/stock changes. "
            "Use TikTok Catalog Manager feed rules to transform problematic fields. "
            "Exclude permanently unavailable products from catalog."
        ),
        "verify": "Disapproval rate <5% in Catalog Diagnostics within 24h of feed fix.",
        "rollback": "Revert feed transformation rules if they cause new disapprovals.",
        "lifecycle": "Weekly | Incident",
        "objective_fit": "Ecom",
    },
    {
        "id": "TAC-0016",
        "severity": "P1",
        "where": "Campaign / Structure",
        "rule": "Smart+ Campaign must be considered for e-com accounts with ≥ 50 conv/week and stable CPA",
        "how_to_check": (
            "Ads Manager → check if Smart+ Campaigns exist. "
            "Red flags: no Smart+ for e-com account with strong conversion history, "
            "only manual campaigns — missing TikTok algorithm full automation signal, "
            "ROAS plateau despite budget increases."
        ),
        "what_to_do": (
            "Launch 1 Smart+ Campaign alongside existing manual campaigns (budget 20-30%). "
            "Smart+ setup: no manual audience (algorithm handles), "
            "upload 5–10 creative assets (video + images), connect catalog for Shopping. "
            "Let Smart+ run ≥14 days before evaluating. "
            "Smart+ typically outperforms manual for e-com at scale (>$5k/month)."
        ),
        "verify": "Smart+ CPA ≤ manual campaigns CPA after 14-day learning window.",
        "rollback": "Pause Smart+ if budget is cannibalized from better-performing manual campaigns.",
        "lifecycle": "Monthly | Quarterly",
        "objective_fit": "Ecom",
    },
    {
        "id": "TAC-0017",
        "severity": "P1",
        "where": "Audiences / Lookalike",
        "rule": "Lookalike Audience must use seed with ≥ 1000 users; 1–3% tier for cold prospecting",
        "how_to_check": (
            "Assets → Audiences → Lookalike → check seed size and Lookalike tier. "
            "Red flags: LAL seed <1000 users, using email list with <500 contacts as seed, "
            "LAL 5-10% used as main prospecting (too broad, diluted signal), "
            "LAL source not refreshed in >90 days."
        ),
        "what_to_do": (
            "Build seed from Pixel Purchase audience (180d) — typically largest and highest signal. "
            "Tiers: 1–3% for cold prospecting (precision), 5–10% for scale. "
            "Refresh seed: re-generate LAL from updated customer list every 30–60d. "
            "Test Creator Lookalike (audience similar to specific TikToker's followers) for niche products."
        ),
        "verify": "LAL source ≥1000 users. LAL 1-3% campaign ROAS ≥ broad prospecting ROAS.",
        "rollback": "Pause LAL campaigns using under-threshold seed; revert to broad targeting.",
        "lifecycle": "Setup | Monthly",
        "objective_fit": "All",
    },

    # ── P2: Hygiene & Optimization (8 rules) ─────────────────────────────────
    {
        "id": "TAC-0018",
        "severity": "P2",
        "where": "Tracking / URLs",
        "rule": "All ads must have UTM parameters for cross-platform attribution in GA4",
        "how_to_check": (
            "Ads Manager → Ads → URL column: check for UTM parameters. "
            "Red flags: missing utm_source, utm_medium, utm_campaign on destination URLs, "
            "GA4 shows high 'direct' traffic on conversion pages, "
            "no way to attribute TikTok sessions in analytics."
        ),
        "what_to_do": (
            "Add UTM template at Ad level or via Campaign URL settings: "
            "utm_source=tiktok&utm_medium=paid_social&utm_campaign={{campaign_name}}&utm_content={{ad_name}}. "
            "TikTok supports dynamic parameters: __CAMPAIGN_ID__, __ADGROUP_ID__, __AD_ID__. "
            "Also add TikTok Click ID (__CLICKID__) to URL for enhanced matching."
        ),
        "verify": "GA4 shows tiktok/paid_social sessions. Direct traffic on key pages decreases.",
        "rollback": "Remove UTM if GA4 shows inflated session counts (double-counting issue).",
        "lifecycle": "Setup | Monthly",
        "objective_fit": "All",
    },
    {
        "id": "TAC-0019",
        "severity": "P2",
        "where": "Creative / Refresh",
        "rule": "Minimum 3 active creative variants per Ad Group; new creative added at least every 14 days",
        "how_to_check": (
            "Ads Manager → Ads tab: count active ads per Ad Group. "
            "Red flags: <3 active ad variants per Ad Group, "
            "no new creative added in >14 days for campaigns with >$30/day spend, "
            "all ads using same hook style or same audio."
        ),
        "what_to_do": (
            "Maintain creative pipeline: minimum 4–6 new assets per month for active campaigns. "
            "Framework: 1 control + 3 challengers varying hook (different first 3 sec). "
            "TikTok-specific: test organic-style (selfie camera, talking head) vs. edited/motion graphic. "
            "Rotate audio: trending TikTok sound often boosts CTR even with same visual."
        ),
        "verify": "CTR stabilizes or improves after new creative added. No single ad over 70% of spend.",
        "rollback": "Reactivate paused top-performing creative if new batch underperforms.",
        "lifecycle": "Weekly",
        "objective_fit": "All",
    },
    {
        "id": "TAC-0020",
        "severity": "P2",
        "where": "Creative / Copy",
        "rule": "Ad caption must be ≤ 100 characters with a clear CTA; subtitles mandatory on all video ads",
        "how_to_check": (
            "Ads Manager → Ads → Preview each active ad. "
            "Red flags: caption >100 chars (truncated in feed), no CTA in caption, "
            "video has no on-screen subtitles (loses viewers who watch muted), "
            "hashtags used as substitutes for CTA."
        ),
        "what_to_do": (
            "Caption formula: [Emotional hook]. [Key benefit]. [CTA] #[niche] #[product] #fyp "
            "Keep caption ≤100 chars including hashtags. "
            "Subtitles: add via TikTok Auto Captions (in Ads Manager) or burn into video. "
            "CTA button: choose from preset (Shop Now / Learn More / Sign Up / Download). "
            "Test caption CTA variants: urgency ('Today only') vs. benefit ('Free shipping')."
        ),
        "verify": "Caption displays in full without truncation. Video has visible subtitles.",
        "rollback": "Revert to previous caption if new version lowers CTR by >20% after 500 impressions.",
        "lifecycle": "Setup | Weekly",
        "objective_fit": "All",
    },
    {
        "id": "TAC-0021",
        "severity": "P2",
        "where": "Account / Structure",
        "rule": "Naming convention must be consistent: [Objective]-[Audience]-[Date] at campaign, Ad Group, and Ad level",
        "how_to_check": (
            "Ads Manager → scan campaign, Ad Group, and ad names. "
            "Red flags: names like 'Campaign 1', 'Ad Group - Copy', no date stamp, "
            "no audience or objective identifier — impossible to analyze at scale."
        ),
        "what_to_do": (
            "Adopt convention: "
            "Campaign: [Product]-[Objective]-[Market]-[YYYYMM] (e.g. Shoes-CONV-UA-202601). "
            "Ad Group: [Audience type]-[Tier/Size]-[Age] (e.g. LAL1pct-Purchase-18-34). "
            "Ad: [Format]-[Hook type]-[Version] (e.g. UGC-Pain-v2). "
            "Rename all active items; document convention in team wiki."
        ),
        "verify": "All active campaigns/Ad Groups/Ads follow convention after rename.",
        "rollback": "N/A — naming is non-destructive.",
        "lifecycle": "Setup | Quarterly",
        "objective_fit": "All",
    },
    {
        "id": "TAC-0022",
        "severity": "P2",
        "where": "Creative / Spark Ads",
        "rule": "Spark Ads authorization from creator/account must be valid and not expired before launch",
        "how_to_check": (
            "Ads Manager → Creative → Spark Ads → Authorization status. "
            "Red flags: authorization expired (default: 30 days from creator grant), "
            "Spark Ad showing as 'Unauthorized', post deleted by creator after authorization, "
            "ad account not matching the account that received authorization."
        ),
        "what_to_do": (
            "Request fresh authorization from creator via Spark Ads auth code (valid 30 days). "
            "For own organic content: authorize via TikTok account settings → Spark Ads. "
            "If authorization expired mid-campaign: pause affected ads, re-authorize, re-launch. "
            "Document authorization dates and set calendar reminder for renewal."
        ),
        "verify": "Spark Ad shows 'Authorized' status in Creative panel. Post is still live and visible.",
        "rollback": "Switch from Spark Ad to regular In-Feed Ad with same creative if re-auth unavailable.",
        "lifecycle": "Setup | Monthly",
        "objective_fit": "All",
    },
    {
        "id": "TAC-0023",
        "severity": "P2",
        "where": "Tracking / Attribution",
        "rule": "TikTok over-attribution (35-55%) must be monitored; cross-validate with GA4 and backend data",
        "how_to_check": (
            "Compare: TikTok Ads Manager reported conversions vs. GA4 TikTok-attributed conversions vs. backend orders. "
            "Red flags: TikTok reports 2× more conversions than GA4 (over-attribution), "
            "ROAS in TikTok 3× higher than blended ROAS from backend, "
            "no regular cross-check cadence in place."
        ),
        "what_to_do": (
            "Set up weekly triangulation: TikTok Manager conv ÷ GA4 TikTok conv = attribution ratio. "
            "Acceptable ratio: 1.35–1.55 (35-55% over-attribution is normal). "
            "If ratio >2.0: investigate duplicate counting (TAC-0003), view-through attribution inflation. "
            "Adjust internal ROAS target upward by over-attribution factor when evaluating TikTok performance."
        ),
        "verify": "Attribution ratio TikTok/GA4 stays between 1.3 and 1.6 consistently.",
        "rollback": "Disable View-through attribution if ratio >2.0 to reduce over-attribution.",
        "lifecycle": "Weekly | Monthly",
        "objective_fit": "All",
    },
    {
        "id": "TAC-0024",
        "severity": "P2",
        "where": "Audiences / Targeting",
        "rule": "Interest-based audience size must be 500K–10M per Ad Group for optimal delivery",
        "how_to_check": (
            "Ads Manager → Ad Group → Audience size estimate. "
            "Red flags: audience <200K (too narrow, CPM spikes, poor delivery), "
            ">50M (too broad, algorithm gets less signal from narrow interest layers), "
            "multiple overlapping interest categories causing redundancy."
        ),
        "what_to_do": (
            "Narrow (<500K): add secondary interest categories or expand geo. "
            "Too broad (>20M): add demographic filter (age, gender) or narrow to 1-2 specific interests. "
            "Optimal for conversion campaigns: 500K–5M. "
            "Optimal for Smart+ (no targeting): 1M+ country-level (algorithm finds own segments). "
            "Test Broad targeting (no interests) — often outperforms on TikTok for large budgets."
        ),
        "verify": "Audience size estimate falls in 500K–10M range. CPM stabilizes vs. narrow targeting.",
        "rollback": "Revert targeting changes if reach drops below delivery minimum.",
        "lifecycle": "Setup | Monthly",
        "objective_fit": "All",
    },
    {
        "id": "TAC-0025",
        "severity": "P2",
        "where": "Tracking / Attribution",
        "rule": "Attribution window must be set to 7-day click / 1-day view as standard; document any deviation",
        "how_to_check": (
            "Ads Manager → Ad Group → Optimization & Measurement → Attribution setting. "
            "Red flags: only 1-day click selected (misses 80% of TikTok-influenced conversions), "
            "7-day view selected (inflates attribution by 2-3×), "
            "different windows used across Ad Groups (inconsistent comparison)."
        ),
        "what_to_do": (
            "Standard: 7-day click / 1-day view for conversion campaigns. "
            "Lead Gen: 7-day click / no view (view-through less relevant for form fills). "
            "If testing incrementality: disable view-through attribution and compare results. "
            "Document chosen window in campaign notes; don't change mid-flight."
        ),
        "verify": "Attribution window matches standard (7d click / 1d view) in all active Ad Groups.",
        "rollback": "Revert attribution window change; document data gap from mid-flight window change.",
        "lifecycle": "Setup | Quarterly",
        "objective_fit": "All",
    },
]


def get_tiktok_rules_for_audit(account_type: str = "") -> str:
    """Return all rules; filter by objective_fit when account_type is given.
    Consistent with Google Canon: include rule when obj=='All' OR account_type matches."""
    lines = []
    for r in TIKTOK_CANON_RULES:
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
