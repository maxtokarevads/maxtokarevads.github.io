"""
Canon Rules — all 33 active rules extracted from Notion database.
Each rule: ID, Severity, Where, Rule, How to check, What to do, Rollback, Verify.
"""

CANON_RULES = [
    {
        "id": "GAC-0001",
        "severity": "P0",
        "where": "Tracking",
        "rule": "Auto-tagging must be enabled",
        "how_to_check": "Google Ads → Settings → Account settings → Auto-tagging. Red flag: disabled.",
        "what_to_do": "Enable auto-tagging. If GCLID conflicts with third-party tracking, coordinate with dev to pass both.",
        "verify": "Confirm GCLID appears in GA4 sessions within 24h.",
        "rollback": "Revert auto-tagging setting and document reason.",
        "lifecycle": "Setup | Incident",
        "objective_fit": "All",
    },
    {
        "id": "GAC-0002",
        "severity": "P0",
        "where": "Tracking",
        "rule": "At least one Primary conversion action must be active and receiving data",
        "how_to_check": "Goals → Conversions → Summary. Red flags: 0 conversions in last 7d, all actions are Secondary, no purchase/lead action marked Primary.",
        "what_to_do": "Promote the correct business outcome (purchase/qualified lead) to Primary. Investigate 0-conversion cause immediately.",
        "verify": "Primary conversion shows data within 24–48h. No sudden drop to 0.",
        "rollback": "Revert conversion action status changes and re-baseline.",
        "lifecycle": "Setup | Incident | Weekly",
        "objective_fit": "All",
    },
    {
        "id": "GAC-0003",
        "severity": "P0",
        "where": "Tracking",
        "rule": "Conversion deduplication must be configured to avoid double-counting",
        "how_to_check": "Goals → Conversions → open conversion action → Count. Red flags: 'Every' selected for purchases, or multiple tracking methods (tag + GA4 import) both set to Primary for same event.",
        "what_to_do": "Set Count to 'One' for purchase/lead. Remove duplicate Primary conversion actions. Use one tracking method as source of truth.",
        "verify": "Conv count matches GA4 purchase events within expected range after 7d.",
        "rollback": "Revert conversion action count settings.",
        "lifecycle": "Setup | Incident",
        "objective_fit": "All",
    },
    {
        "id": "GAC-0004",
        "severity": "P0",
        "where": "Policies",
        "rule": "Account-level policy violations must be resolved before any optimization",
        "how_to_check": "Tools → Policy manager / Account status. Red flags: account suspension, limited serving status, active policy issues.",
        "what_to_do": "Resolve the policy violation per Google guidance. Request review after fix. Document timeline.",
        "verify": "Account status returns to Good within review window.",
        "rollback": "Revert any content/targeting change that triggered violation.",
        "lifecycle": "Incident | Setup",
        "objective_fit": "All",
    },
    {
        "id": "GAC-0005",
        "severity": "P0",
        "where": "Merchant Center / Feed",
        "rule": "Merchant Center shipping settings must match live checkout prices",
        "how_to_check": "MC → Shipping → review shipping rules vs live checkout. Red flags: shipping mismatch disapprovals in Diagnostics, free shipping in MC but not on site.",
        "what_to_do": "Align MC shipping rules to match checkout exactly. Fix mismatches in Diagnostics.",
        "verify": "Shipping mismatch disapprovals resolve within 24–72h after Diagnostics update.",
        "rollback": "Revert shipping rule change and re-check Diagnostics.",
        "lifecycle": "Setup | Incident | Weekly",
        "objective_fit": "Ecommerce",
    },
    {
        "id": "GAC-0006",
        "severity": "P1",
        "where": "Search",
        "rule": "Negative keyword lists must be used for scalable exclusions",
        "how_to_check": "Tools → Shared library → Negative keyword lists. Red flags: no lists, or lists not applied to relevant campaigns.",
        "what_to_do": "Create standard lists (jobs, free, info, diy, competitors) → apply to all non-brand campaigns → review weekly via Search terms.",
        "verify": "Wasted spend on irrelevant terms decreases over 7–14d.",
        "rollback": "Remove the negative keyword or list and monitor search terms.",
        "lifecycle": "Setup | Weekly",
        "objective_fit": "All",
    },
    {
        "id": "GAC-0007",
        "severity": "P2",
        "where": "Search",
        "rule": "RSA must include enough unique headlines/descriptions; pinning should be minimal",
        "how_to_check": "Ads → RSA → asset count + pinning. Red flags: <5 unique headlines, heavy pinning across most assets.",
        "what_to_do": "Add unique intent-focused headlines/descriptions. Pin only compliance-critical elements.",
        "verify": "Ad Strength improves to Good/Excellent after 7–14d.",
        "rollback": "Revert the last change and re-check performance.",
        "lifecycle": "Setup | Monthly",
        "objective_fit": "All",
    },
    {
        "id": "GAC-0008",
        "severity": "P1",
        "where": "Tracking",
        "rule": "Conversion window must be set per conversion action to match the business cycle",
        "how_to_check": "Goals → Conversions → select action → Conversion window. Red flags: identical window for all actions despite different cycles.",
        "what_to_do": "Set window per action (purchase vs lead vs qualified lead). Document rationale. Re-baseline CPA/ROAS after change.",
        "verify": "Conv volume stabilizes within 7–14d. No unexpected CPA shift.",
        "rollback": "Revert to prior window and re-baseline.",
        "lifecycle": "Setup | Quarterly",
        "objective_fit": "All",
    },
    {
        "id": "GAC-0009",
        "severity": "P1",
        "where": "PMax | Search",
        "rule": "Brand exclusions must be applied to PMax when you need to prevent brand cannibalization",
        "how_to_check": "PMax campaign → Settings → Brand exclusions. Red flags: brand excluded nowhere while PMax shows strong performance but Search brand loses volume.",
        "what_to_do": "Create brand list → apply brand exclusions to PMax → keep brand Search separate.",
        "verify": "Brand Search volume stable. PMax non-brand metrics stable after 7–14d.",
        "rollback": "Revert the last change and re-check performance.",
        "lifecycle": "Setup | Monthly",
        "objective_fit": "Ecommerce | Lead gen",
    },
    {
        "id": "GAC-0010",
        "severity": "P0",
        "where": "Merchant Center / Feed",
        "rule": "Merchant Center automatic item updates should be enabled to reduce price/availability mismatches",
        "how_to_check": "MC → Products → Diagnostics (mismatches/disapprovals) + MC → Automations. Red flags: frequent mismatch disapprovals, automations disabled.",
        "what_to_do": "Enable automatic item updates (price/availability/condition) + ensure structured data includes required fields.",
        "verify": "Mismatch disapprovals decrease in MC Diagnostics within 24–72h.",
        "rollback": "Revert the feed/shipping setting change and re-check Diagnostics.",
        "lifecycle": "Setup | Incident | Weekly",
        "objective_fit": "Ecommerce",
    },
    {
        "id": "GAC-0011",
        "severity": "P1",
        "where": "Bidding & Learning",
        "rule": "Smart Bidding must have sufficient conversion volume before switching to tCPA/tROAS",
        "how_to_check": "Check conversion volume: ≥30–50 conv/month per campaign for tCPA; ≥50 conv/month for tROAS. Red flags: tCPA/tROAS set with <20 conv/month → underbidding/instability.",
        "what_to_do": "If insufficient data: use Maximize Conversions (no target) to build volume, then switch to tCPA after threshold. Document the switch date.",
        "verify": "Conv volume stable for 14d before and after switch. CPA within 20% of target.",
        "rollback": "Revert to Maximize Conversions if performance degrades >20% after switch.",
        "lifecycle": "Setup | Weekly",
        "objective_fit": "All",
    },
    {
        "id": "GAC-0012",
        "severity": "P1",
        "where": "Bidding & Learning",
        "rule": "Do not make major changes during Smart Bidding learning phase (first 7–14d after strategy change)",
        "how_to_check": "Check campaign status: 'Learning' or 'Limited — Learning' badge. Red flags: budget cuts, target changes, or major asset edits within 7d of strategy change.",
        "what_to_do": "Wait for learning phase to complete. If performance is catastrophic (P0 gate), escalate as incident rather than making micro-adjustments.",
        "verify": "Campaign exits 'Learning' status within 7–14d with stable metrics.",
        "rollback": "Revert the strategy change if performance is P0-level bad.",
        "lifecycle": "Weekly | Setup",
        "objective_fit": "All",
    },
    {
        "id": "GAC-0013",
        "severity": "P1",
        "where": "Account Hygiene",
        "rule": "Budget pacing must be monitored — neither overcapping nor underspending significantly",
        "how_to_check": "Campaigns → Budget column. Red flags: campaigns capped >3d/week, or campaigns spending <70% of budget consistently.",
        "what_to_do": "For capped: increase budget or reduce targets. For underspend: check eligibility, QS, targeting, bids.",
        "verify": "Budget utilization 85–100% within 7d.",
        "rollback": "Revert budget change if spend spikes unexpectedly.",
        "lifecycle": "Weekly | Monthly",
        "objective_fit": "All",
    },
    {
        "id": "GAC-0014",
        "severity": "P1",
        "where": "Search",
        "rule": "Search Terms must be reviewed and actioned at least weekly",
        "how_to_check": "Reports → Search terms (last 7–14d). Red flags: irrelevant terms with spend >$20 and 0 conv, brand terms in non-brand campaigns.",
        "what_to_do": "Add negative keywords for irrelevant terms. Consider adding high-intent terms as keywords. Document in Actions log.",
        "verify": "Wasted spend decreases over next 7d. No new irrelevant term spikes.",
        "rollback": "Remove incorrectly added negative if it blocks relevant traffic.",
        "lifecycle": "Weekly",
        "objective_fit": "All",
    },
    {
        "id": "GAC-0015",
        "severity": "P1",
        "where": "PMax",
        "rule": "PMax Final URL expansion must be controlled (ON with exclusions or OFF)",
        "how_to_check": "PMax campaign → Settings → Final URL expansion + URL exclusions. Red flags: traffic landing on irrelevant pages (blog/about/info), CVR drop.",
        "what_to_do": "If strict landing control needed → turn Final URL expansion OFF. If ON → add URL exclusions and consider page feed.",
        "verify": "Landing page CVR stable after change. No new irrelevant URL traffic.",
        "rollback": "Revert Final URL expansion to previous state and restore URL exclusions.",
        "lifecycle": "Setup | Weekly",
        "objective_fit": "All",
    },
    {
        "id": "GAC-0016",
        "severity": "P1",
        "where": "Attribution & Reporting | Account Hygiene",
        "rule": "Change History must be reviewed before attributing performance shifts to 'the market'",
        "how_to_check": "Campaigns → Change history. Compare date range + filters. Red flags: multiple major edits close to performance drop/spike.",
        "what_to_do": "Identify changes correlating with performance shift → rollback or adjust one variable at a time → annotate what changed and why.",
        "verify": "Performance stabilizes within 7–14d after adjustment.",
        "rollback": "Revert the last change and re-check performance.",
        "lifecycle": "Weekly | Incident",
        "objective_fit": "All",
    },
    {
        "id": "GAC-0017",
        "severity": "P2",
        "where": "Attribution & Reporting | Bidding & Learning",
        "rule": "Conversion value rules must only be used when you have a clear value model",
        "how_to_check": "Tools → Conversions → Value rules. Red flags: rules applied without documented logic, overlapping conditions, unexplained ROAS shifts.",
        "what_to_do": "Document the value model → implement minimal rules → validate via value rules report and ROAS trend over 2–4 weeks.",
        "verify": "ROAS trend stable after rule implementation. Value rules report shows expected multipliers.",
        "rollback": "Revert to prior conversion value config and re-baseline.",
        "lifecycle": "Quarterly | Setup",
        "objective_fit": "Ecommerce | Lead gen",
    },
    {
        "id": "GAC-0018",
        "severity": "P1",
        "where": "Attribution & Reporting | Tracking",
        "rule": "A GA4 property must be linked to Google Ads (and the right toggles enabled)",
        "how_to_check": "Tools → Data manager → 'Google Analytics (GA4) & Firebase' status. Red flags: not linked, or imports (audiences/metrics) disabled.",
        "what_to_do": "Link GA4 in Data manager → enable needed imports (audiences/metrics) → verify GA columns/audiences availability after linking.",
        "verify": "GA4 audiences appear in Audience manager within 24–48h.",
        "rollback": "Revert the last change and re-check performance.",
        "lifecycle": "Setup | Incident",
        "objective_fit": "All",
    },
    {
        "id": "GAC-0019",
        "severity": "P1",
        "where": "Tracking",
        "rule": "Imported GA4 conversions must be treated as Secondary by default and promoted to Primary intentionally",
        "how_to_check": "Goals → Conversions → find GA4-imported actions → check Action optimization (Primary/Secondary). Red flags: micro-events imported as Primary, key outcome left Secondary.",
        "what_to_do": "Import only business outcomes → switch the right ones to Primary → leave micro-events as Secondary → wait 24h and confirm data flows.",
        "verify": "Primary conversion data flows within 24h. Bidding signals update.",
        "rollback": "Revert conversion action status and re-baseline.",
        "lifecycle": "Monthly | Setup",
        "objective_fit": "All",
    },
    {
        "id": "GAC-0020",
        "severity": "P1",
        "where": "Merchant Center / Feed",
        "rule": "Merchant Center must include correct unique product identifiers (GTIN/brand/MPN) or omit them properly",
        "how_to_check": "MC → Products → item details/feed rules → verify gtin, brand, mpn. Red flags: empty identifiers for products that have them, or internal SKU used as GTIN.",
        "what_to_do": "Submit real identifiers. If no GTIN exists for custom goods → follow MC guidance. Never fabricate.",
        "verify": "Identifier errors decrease in MC Diagnostics within 24–72h.",
        "rollback": "Revert feed/feed rules change and re-check Diagnostics.",
        "lifecycle": "Setup | Monthly",
        "objective_fit": "Ecommerce",
    },
    {
        "id": "GAC-0021",
        "severity": "P1",
        "where": "Account Hygiene",
        "rule": "Campaign naming convention must be consistent for scalable reporting and filtering",
        "how_to_check": "Campaigns list → scan names for consistency. Red flags: mixed conventions, no type/geo/target info in name, duplicate/unclear names.",
        "what_to_do": "Adopt a naming template: [Brand/NB]_[Type]_[Geo]_[Objective]_[Date if needed]. Rename gradually — document in Changes log.",
        "verify": "Filter/segment by campaign name works correctly in Looker/GA4 after rename.",
        "rollback": "Revert rename if it breaks downstream reporting filters.",
        "lifecycle": "Setup | Quarterly",
        "objective_fit": "All",
    },
    {
        "id": "GAC-0022",
        "severity": "P1",
        "where": "PMax",
        "rule": "PMax Asset Groups must have enough assets and realistic Audience Signals",
        "how_to_check": "PMax campaign → Asset groups → Asset strength + Audience signals. Red flags: Asset strength 'Poor', fewer than 3 headlines/images, generic signals.",
        "what_to_do": "Add more unique assets per required type. Set audience signals based on actual customer data (CRM, website visitors, intent). Review asset performance report.",
        "verify": "Asset strength improves to 'Good' or 'Excellent' within 7–14d.",
        "rollback": "Revert asset changes that degraded performance.",
        "lifecycle": "Setup | Monthly",
        "objective_fit": "All",
    },
    {
        "id": "GAC-0023",
        "severity": "P2",
        "where": "Search | Policies",
        "rule": "Automatically created assets must be controlled (ON for scale or OFF for strict brand control)",
        "how_to_check": "Campaign Settings → automatically created assets/text customization settings. Red flags: not checked, brand messaging inconsistent with ACA output.",
        "what_to_do": "For strict compliance: Off. For performance scaling: ON, but monitor automated assets reporting and remove conflicts.",
        "verify": "CTR/CVR stable. No brand compliance violations after 7–14d.",
        "rollback": "Revert ACA setting to previous state.",
        "lifecycle": "Setup | Quarterly",
        "objective_fit": "Ecommerce | Lead gen",
    },
    {
        "id": "GAC-0024",
        "severity": "P0",
        "where": "Merchant Center / Feed | Policies",
        "rule": "After fixing Merchant Center issues, request a review when the option exists",
        "how_to_check": "MC → Products → Needs attention/Diagnostics → look for Request review option. Red flags: fix applied but review not requested, repeated disapprovals.",
        "what_to_do": "Fix the issue → request review → track review status. Avoid repeated requests without real fixes (review limits may apply).",
        "verify": "Diagnostics shows issue resolved within review window (24–72h typically).",
        "rollback": "Revert the fix if review escalates and causes new issues.",
        "lifecycle": "Incident | Weekly",
        "objective_fit": "Ecommerce",
    },
    {
        "id": "GAC-0025",
        "severity": "P1",
        "where": "Remarketing | Tracking",
        "rule": "Audience segments must meet minimum active-user thresholds to be eligible to serve",
        "how_to_check": "Tools → Audience manager → Your data segments → Size and Status. Red flags: 'Too small' status, <1000 active users for Search RLSA.",
        "what_to_do": "Confirm tag/data collection is working. Allow 48–72h for new segments. If still 'Too small', broaden rules or increase membership duration.",
        "verify": "Segment status changes from 'Too small' to active within 72h of fix.",
        "rollback": "Revert the last change and re-check audience size.",
        "lifecycle": "Setup | Weekly",
        "objective_fit": "All",
    },
    {
        "id": "GAC-0026",
        "severity": "P1",
        "where": "Account Hygiene",
        "rule": "Auto-apply recommendations must be OFF by default, enable only explicitly approved types",
        "how_to_check": "Recommendations → Auto-apply settings. Red flags: broad sets enabled (especially 'Maintain Your Ads') without documented scope/owner.",
        "what_to_do": "Disable all auto-apply by default → if enabling, allow only tightly scoped approved subset → review History monthly.",
        "verify": "No unexpected changes in Change History from auto-apply after setting review.",
        "rollback": "Disable the auto-apply type(s) and revert any unwanted changes.",
        "lifecycle": "Setup | Monthly",
        "objective_fit": "All",
    },
    {
        "id": "GAC-0027",
        "severity": "P1",
        "where": "Attribution & Reporting | Bidding & Learning | Tracking",
        "rule": "Use Data-Driven Attribution (DDA) where eligible, and treat attribution model changes as a 'signal change'",
        "how_to_check": "Goals → Conversions → open action → Attribution model. Also check Attribution reports → Switch to DDA eligibility. Red flags: Last click model despite DDA availability.",
        "what_to_do": "If eligible, switch to DDA → document change date → update tCPA/tROAS targets if needed → evaluate after 1–2 conversion cycles.",
        "verify": "Attribution model updated. CPA/ROAS re-baselined after 14d.",
        "rollback": "Revert to prior attribution model and re-baseline KPIs for 7–14d.",
        "lifecycle": "Quarterly | Incident",
        "objective_fit": "All",
    },
    {
        "id": "GAC-0028",
        "severity": "P1",
        "where": "Bidding & Learning | Tracking",
        "rule": "Conversion values must be configured intentionally (required for ROAS-based optimization)",
        "how_to_check": "Goals → Conversions → open action → Value. Red flags: purchase conv without dynamic value, static value without value model for leadgen.",
        "what_to_do": "For purchases: ensure dynamic value is passed (tag/server) with correct currency. For leads: set static value only with validated value model.",
        "verify": "Conv value/cost stable after 7–14d. ROAS reporting reflects real revenue.",
        "rollback": "Revert conversion value config and re-baseline for 7–14d.",
        "lifecycle": "Setup | Monthly",
        "objective_fit": "Ecommerce | Lead gen",
    },
    {
        "id": "GAC-0029",
        "severity": "P0",
        "where": "Merchant Center / Feed | Account Hygiene",
        "rule": "Merchant Center must be linked to Google Ads via Data manager",
        "how_to_check": "Tools → Data manager → Google Merchant Center. Also in MC: linked Google Ads account. Red flags: not linked, or Shopping campaigns not serving.",
        "what_to_do": "Link correct MC account (admin access on both sides) → confirm connection status → document account IDs.",
        "verify": "MC link status shows 'Connected' within 24h. Shopping campaigns resume serving.",
        "rollback": "Revert the feed/shipping setting change and re-check Diagnostics.",
        "lifecycle": "Setup | Incident",
        "objective_fit": "Ecommerce",
    },
    {
        "id": "GAC-0030",
        "severity": "P1",
        "where": "Tracking | Account Hygiene",
        "rule": "Account-default conversion goals must reflect the real business outcome",
        "how_to_check": "Goals → Conversions → Summary → review which goals are included by default. Red flags: micro-actions included as defaults for optimization.",
        "what_to_do": "Keep defaults aligned to primary business outcomes (purchase/qualified lead). Use campaign-specific goals only when justified.",
        "verify": "Conversion column reflects only primary business outcomes. CPA/ROAS stable.",
        "rollback": "Revert conversion setting/model config and re-baseline for 7–14d.",
        "lifecycle": "Setup | Quarterly",
        "objective_fit": "All",
    },
    {
        "id": "GAC-0031",
        "severity": "P1",
        "where": "Search | PMax",
        "rule": "Brand vs Non-Brand campaigns must be structurally separated",
        "how_to_check": "Campaigns list → verify brand keywords are in dedicated Brand campaign with brand match types. Red flags: brand keywords mixed with non-brand, no brand campaign.",
        "what_to_do": "Create dedicated Brand campaign. Exclude brand from non-brand campaigns via negative keywords. Report brand/non-brand separately.",
        "verify": "Brand traffic isolated in Brand campaign. Non-brand CPA/ROAS measurable independently.",
        "rollback": "Revert structural change if it causes serving issues.",
        "lifecycle": "Setup | Monthly",
        "objective_fit": "All",
    },
    {
        "id": "GAC-0032",
        "severity": "P1",
        "where": "Bidding & Learning",
        "rule": "Target CPA/ROAS must be set based on actual historical performance, not aspirational goals",
        "how_to_check": "Campaigns → check tCPA/tROAS vs actual CPA/ROAS (last 30d). Red flags: target >50% better than actual average with insufficient volume.",
        "what_to_do": "Set initial target at actual 30d average. Adjust by max 10–15% per week. Document each change.",
        "verify": "Conv volume maintains ±15% after target change within 7–14d.",
        "rollback": "Increase target back toward actual CPA/ROAS if volume drops >20%.",
        "lifecycle": "Setup | Weekly",
        "objective_fit": "All",
    },
    {
        "id": "GAC-0033",
        "severity": "P2",
        "where": "Account Hygiene",
        "rule": "Ad scheduling must be intentional (not default 24/7 unless justified)",
        "how_to_check": "Campaigns → Settings → Ad schedule. Red flags: 24/7 schedule without performance analysis, or heavily restricted schedule without testing data.",
        "what_to_do": "Analyze performance by hour/day (Reports → Predefined reports → Time → Hour of day). Apply scheduling only with clear data support.",
        "verify": "CPA/CVR stable or improved after schedule change. No unexpected impression drop.",
        "rollback": "Revert to previous schedule if performance degrades.",
        "lifecycle": "Monthly | Quarterly",
        "objective_fit": "All",
    },

    # ── Measurement 2026 (GAC-0034 – GAC-0037) ────────────────────────────────

    {
        "id": "GAC-0034",
        "severity": "P0",
        "where": "Consent Mode / Privacy",
        "rule": "Consent Mode v2 must be active for all EU/EEA traffic — without it, conversion modelling is disabled and ROAS inflates artificially",
        "how_to_check": (
            "Google Ads → Tools → Conversions → Diagnostics → Consent Mode status. "
            "Also check Tag Assistant or GA4 DebugView: every hit must carry "
            "ad_storage and analytics_storage consent signals. "
            "Red flags: no consent mode configured; 'unmodelled' conversions >20% of total; "
            "CMP installed but signals not passed to gtag/GTM; GA4 showing 'consent not granted' >30%."
        ),
        "what_to_do": (
            "Implement Consent Mode v2 via your CMP (Cookiebot, OneTrust, Usercentrics etc.) "
            "or directly via gtag: gtag('consent','default',{ad_storage:'denied',analytics_storage:'denied'}). "
            "Enable 'Google Consent Mode' toggle in CMP settings. "
            "Verify in Tag Assistant that gtag consent state updates to 'granted' after user accepts. "
            "Enable Conversion Modelling in Google Ads: Tools → Data Manager → Consent Mode."
        ),
        "verify": "Conversion diagnostics show ≥80% consented conversions. 'Modelled conversions' visible in reports. No 'consent mode not detected' warning in diagnostics.",
        "rollback": "Do not remove Consent Mode — non-compliance risk. If signals break, revert CMP config to last working version.",
        "lifecycle": "Setup | Quarterly",
        "objective_fit": "All",
    },
    {
        "id": "GAC-0035",
        "severity": "P0",
        "where": "Enhanced Conversions / Tracking",
        "rule": "Enhanced Conversions for Web must be active — required to recover signal lost to ITP/cookieless browsers and Consent Mode denials",
        "how_to_check": (
            "Google Ads → Tools → Conversions → select primary conversion → Settings → Enhanced Conversions. "
            "Check status: Active / Not verified / Inactive. "
            "Red flags: Enhanced Conversions Off; hashed email/phone not passing with conversion tag; "
            "match rate in diagnostics <40% (means user data not captured); "
            "conversion tag fires but no customer_email or customer_phone_number field detected."
        ),
        "what_to_do": (
            "Enable Enhanced Conversions in Google Ads conversion action settings. "
            "Pass hashed customer data with each conversion tag: "
            "user_data: {email_address: 'user@example.com', phone_number: '+1234567890', "
            "address: {first_name: 'John', last_name: 'Doe'}}. "
            "Google hashes automatically if raw data provided, or pre-hash with SHA-256. "
            "Verify via Tag Assistant: conversion tag must show 'Enhanced match' status."
        ),
        "verify": "Diagnostics show Enhanced Conversions Active and match rate ≥60%. Conversion volume increase of 5-15% typical after activation.",
        "rollback": "Disable Enhanced Conversions in settings if data privacy concern raised — does not break standard conversion tracking.",
        "lifecycle": "Setup",
        "objective_fit": "All",
    },
    {
        "id": "GAC-0036",
        "severity": "P1",
        "where": "Enhanced Conversions for Leads / B2B",
        "rule": "Enhanced Conversions for Leads must connect CRM data back to Google Ads clicks — without it, Smart Bidding optimises for raw form fills, not qualified leads",
        "how_to_check": (
            "Google Ads → Tools → Conversions: look for a 'Lead' conversion action with source 'Imported from CRM'. "
            "Red flags: only form-fill pixel conversions (no CRM import); "
            "Smart Bidding tCPA optimising on form fills when lead quality is low; "
            "sales team reporting high volume but low SQL rate; "
            "no GCLID capture in CRM (makes offline import impossible)."
        ),
        "what_to_do": (
            "1. Capture GCLID: add hidden form field (name='gclid') populated via JS (urlParam('gclid')). Store in CRM against each lead. "
            "2. Create offline conversion action in Google Ads: Conversions → New → Import → CRMs/other. "
            "3. Export GCLID + conversion_name + conversion_time CSV from CRM when lead becomes MQL or SQL. "
            "4. Upload via Google Ads UI or API (delay: 6h-90d from click). "
            "5. Set Smart Bidding target on the qualified-lead conversion, exclude raw form-fill from bidding column."
        ),
        "verify": "Offline conversions appear in Google Ads within 48h of upload. Smart Bidding tCPA target set to qualified lead cost, not form-fill cost.",
        "rollback": "If GCLID capture breaks form, use autotagging with landing page URL parameter fallback.",
        "lifecycle": "Setup | Monthly",
        "objective_fit": "Lead-gen | B2B",
    },
    {
        "id": "GAC-0037",
        "severity": "P1",
        "where": "Measurement / Incrementality",
        "rule": "Geo-lift or holdout incrementality test must run at least once per quarter — attributed ROAS overstates true ad impact by 20-60%",
        "how_to_check": (
            "Google Ads → Experiments → check for active or completed geo experiments. "
            "Red flags: no geo experiment in last 6 months; decision-making based solely on attributed conversions; "
            "ROAS target set without understanding true incremental contribution; "
            "budget decisions made by comparing platform-attributed vs GA4-attributed (both are attribution, neither is incremental)."
        ),
        "what_to_do": (
            "Google Ads Geo Experiment: create a campaign experiment splitting matched geographic markets into test vs control. "
            "Run for 4-6 weeks. Measure: (test-region CVR − control-region CVR) / control = incremental lift%. "
            "Adjust ROAS targets: true ROAS = attributed ROAS × incremental lift%. "
            "Alternative: use Conversion Lift study via Google Ads (requires ≥$50k/mo). "
            "Minimum: compare branded-search volume in test vs control regions as a proxy."
        ),
        "verify": "Geo experiment complete with statistically significant result (p<0.1 acceptable for directional decisions). Incrementality factor documented and applied to ROAS targets.",
        "rollback": "Restore full targeting to both regions after experiment. Document incrementality factor in account notes.",
        "lifecycle": "Quarterly",
        "objective_fit": "All",
    },

    # ── B2B / Lead-gen depth (GAC-0038 – GAC-0041) ───────────────────────────

    {
        "id": "GAC-0038",
        "severity": "P1",
        "where": "Smart Bidding / Lead Quality",
        "rule": "Smart Bidding must optimise on qualified leads (MQL/SQL), not raw form fills — raw-fill optimisation attracts low-quality traffic and inflates volume metrics",
        "how_to_check": (
            "Check bidding conversion column: Tools → Conversions → which actions are 'Include in conversions' (bidding column). "
            "Red flags: only form-fill or page-view events in bidding column; "
            "CRM shows <10% form-fills → MQL rate; "
            "paid traffic generating high form-fill volume but low close rate vs organic; "
            "no offline conversion import configured (see GAC-0036)."
        ),
        "what_to_do": (
            "Tiered approach based on lead volume: "
            "Volume ≥30 qualified leads/month → tCPA on qualified lead conversion (GAC-0036 import). "
            "Volume 10-30/month → value-based bidding: assign conversion values (form-fill=1, MQL=5, SQL=20, Won=100) + target ROAS. "
            "Volume <10/month → optimise on micro-conversion (e.g. pricing page visit, demo request) while building qualified lead history. "
            "Never mix form-fill + qualified-lead in same bidding column — creates conflicting signals."
        ),
        "verify": "MQL rate from paid search ≥ organic MQL rate. CPA per qualified lead improving or stable MoM. Smart Bidding not in Learning Limited due to low qualified-lead volume.",
        "rollback": "If qualified lead volume drops below 10/month causing Learning Limited: temporarily revert to micro-conversion bidding, rebuild volume.",
        "lifecycle": "Setup | Monthly",
        "objective_fit": "Lead-gen | B2B",
    },
    {
        "id": "GAC-0039",
        "severity": "P1",
        "where": "CRM Integration / Closed Loop",
        "rule": "CRM closed-loop reporting must connect Google Ads clicks to revenue stages (MQL → SQL → Won) — without this, budget decisions are made on proxy metrics",
        "how_to_check": (
            "Ask: can you trace a Google Ads click → CRM lead → deal stage → closed-won? "
            "Red flags: CRM has no GCLID field; lead source in CRM is 'Web' with no channel breakdown; "
            "sales team and marketing team use different conversion definitions; "
            "reporting shows CPL only, no CPA-per-qualified-lead or CAC."
        ),
        "what_to_do": (
            "1. CRM field setup: add GCLID, UTM_source, UTM_campaign, UTM_medium, LP_URL to every lead record (hidden form fields). "
            "2. Stage export schedule: weekly export of leads that reached MQL/SQL/Won stage in last 7 days, with original GCLID. "
            "3. Upload to Google Ads as offline conversions (GAC-0036). "
            "4. Build reporting view: Google Ads cost → # clicks → # form fills → # MQLs → # SQLs → # Won → Revenue. "
            "5. Set account-level CPA target based on CAC (Revenue/Won × gross margin, worked backwards through funnel)."
        ),
        "verify": "Dashboard exists showing full funnel from paid click to closed revenue. At least MQL import flowing into Google Ads. CAC target documented.",
        "rollback": "GCLID capture can be added without changing form UX (hidden field). No rollback risk.",
        "lifecycle": "Setup | Quarterly",
        "objective_fit": "Lead-gen | B2B",
    },
    {
        "id": "GAC-0040",
        "severity": "P2",
        "where": "Value-based Bidding / B2B",
        "rule": "Assign differentiated conversion values across lead stages to unlock value-based Smart Bidding — flat-value bidding leaves significant efficiency gains untapped",
        "how_to_check": (
            "Tools → Conversions: check if conversion values differ across lead stage actions or if all set to value=1. "
            "Red flags: all conversions set to same value (e.g. 1); only one conversion action in bidding column; "
            "using tCPA when lead value varies significantly by source/intent/keyword."
        ),
        "what_to_do": (
            "Map conversion values to business impact (index: form-fill = 1): "
            "Form-fill / Demo request: 1 | MQL (sales-accepted): 5–10 | SQL (opportunity): 20–50 | Closed-Won: 100–500 (use avg deal value). "
            "Enter values in conversion action settings. Switch bidding to Maximise Conversion Value or target ROAS. "
            "Google will automatically shift budget to keywords/audiences generating higher-value leads. "
            "Minimum: 30 value-attributed conversions/month needed for tROAS learning."
        ),
        "verify": "Value-per-conversion metric rising. Lead quality score (MQL rate, SQL rate) stable or improving as Smart Bidding learns value signals.",
        "rollback": "Revert to tCPA if value-based bidding causes volume drop >30% — insufficient data signal.",
        "lifecycle": "Monthly | Quarterly",
        "objective_fit": "Lead-gen | B2B",
    },
    {
        "id": "GAC-0041",
        "severity": "P2",
        "where": "Audience / B2B Targeting",
        "rule": "B2B campaigns must layer customer-match and in-market B2B audiences — keyword intent alone misses the decision-maker targeting layer",
        "how_to_check": (
            "Ad Groups → Audiences: check if any B2B-specific audiences are applied. "
            "Red flags: no Customer Match audience from CRM; no In-Market: Business & Industrial segments; "
            "no RLSA from CRM list of existing customers (for exclusion + lookalike); "
            "no observation-mode audience data to inform B2B bid adjustments."
        ),
        "what_to_do": (
            "1. Customer Match: upload CRM list (all customers + lost deals) → exclude existing customers from prospecting; "
            "use as seed for Similar Audiences. "
            "2. In-Market B2B: Tools → Audience Manager → add 'Business Professionals', 'Business Technology', "
            "industry-specific In-Market segments in observation mode first; bid up if CPA favourable. "
            "3. LinkedIn match (if ≥$500/day budget): link LinkedIn Insight Tag → Google Customer Match via CRM export. "
            "4. Remarketing from CRM: upload MQL/SQL list → bid +30% on these (they've self-qualified); "
            "upload Won-customers → exclude from all acquisition campaigns."
        ),
        "verify": "CRM-based Customer Match audience shows ≥1,000 matched users. In-market B2B segments in observation show CPA difference vs non-audience traffic. Exclusion list suppressing existing customers.",
        "rollback": "Remove audience bid adjustments if CPA worsens. Keep audiences in observation mode if targeting mode underperforms.",
        "lifecycle": "Setup | Quarterly",
        "objective_fit": "Lead-gen | B2B",
    },
]


def get_rules_by_severity(severity: str):
    return [r for r in CANON_RULES if r["severity"] == severity]

# Total rules: auto-derived from list length — do not hardcode counts in comments.


def get_rules_for_audit(account_type: str = "") -> str:
    """Format Canon Rules for inclusion in audit prompt."""
    is_ecom = "ecom" in account_type.lower()

    def _fits(objective_fit: str) -> bool:
        """Return True if this rule applies to the account type.

        objective_fit is a pipe-separated string, e.g. "Ecommerce | Lead gen".
        Matching is done against normalised tokens so substring accidents are impossible.
        """
        tokens = {t.strip().lower() for t in objective_fit.split("|")}
        if "all" in tokens:
            return True
        ecom_tokens  = {"ecommerce", "ecom"}
        lead_tokens  = {"lead gen", "lead-gen", "lead", "b2b"}
        if is_ecom:
            return bool(tokens & ecom_tokens)
        return bool(tokens & lead_tokens)

    lines = ["## Canon Rules — Checklist\n"]
    lines.append("Apply EVERY applicable rule. Mark: ✓ OK | ✗ FAIL | ? Missing data\n")

    for sev in ["P0", "P1", "P2"]:
        sev_rules = [
            r for r in CANON_RULES
            if r["severity"] == sev and _fits(r["objective_fit"])
        ]
        lines.append(f"\n### {sev} Rules\n")
        for r in sev_rules:
            lines.append(f"**{r['id']}** [{r['where']}] {r['rule']}")
            lines.append(f"  How to check: {r['how_to_check']}")
            lines.append(f"  What to do: {r['what_to_do']}")
            lines.append(f"  Verify: {r['verify']}")
            lines.append("")

    return "\n".join(lines)
