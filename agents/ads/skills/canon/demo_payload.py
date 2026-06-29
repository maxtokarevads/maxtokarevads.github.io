"""
Pre-loaded demo payloads for each platform.
Used by the /demo command to showcase the Canon audit system
without requiring the user to paste real account data.
"""

DEMO_GOOGLE = {
    "platform":     "google",
    "mode":         "audit",
    "command":      "/audit",
    "project":      "Demo Account — TechFlow SaaS",
    "account_type": "lead-gen",
    "date_range":   "last 30 days",
    "market":       "US / USD",
    "context":      "B2B SaaS, target: software teams, ACV $12k, sales cycle 45 days",
    "inputs": {
        "ADS__AutoTagging__Status":           "OFF — auto-tagging disabled",
        "ADS__Conversions__Summary__Settings": "1 conversion action: 'Form Submit' (form pixel). No Enhanced Conversions. No offline import.",
        "ADS__Conversions__Volume__30d":       "Form Submit: 142 conversions / 30d",
        "GA4__Conversions__30d":               "47 goal completions attributed to Google Ads (vs 142 in Ads Manager)",
        "ADS__Export__Campaigns__Performance": "3 active campaigns: Brand Search ($800/mo, ROAS 12x), Non-Brand Search ($3,200/mo, CPA $87), Display Remarketing ($600/mo, CPA $310)",
        "ADS__SearchTerms__30d":               "Top wasted spend terms: 'techflow salary' ($340), 'techflow jobs' ($210), 'what is saas software' ($180), 'crm free trial' ($290)",
        "ADS__QualityScore__Sample":           "Primary keywords QS: 'project management software' 4/10, 'team collaboration tool' 5/10, 'saas project tracker' 6/10",
        "ADS__ImpressionShare__30d":           "Search IS: 38%. Lost IS (budget): 31%. Lost IS (rank): 31%.",
        "ADS__ChangeHistory__30d":             "3 bid changes in last 7 days. Target CPA changed from $90 → $65 → $80 (oscillating).",
        "ADS__Conversions__ConsentMode":       "Not configured. No consent mode signals detected.",
        "ADS__EnhancedConversions__Status":    "Inactive — no Enhanced Conversions for Leads configured.",
    },
    "metrics": {
        "spend_30d":        "$4,600",
        "clicks_30d":       "2,847",
        "impressions_30d":  "41,200",
        "avg_cpc":          "$1.62",
        "ctr":              "6.9%",
        "conversions_30d":  "142 (form fills) / 47 (GA4 attributed)",
        "cpa_reported":     "$32.40 (Ads Manager) / $97.90 (GA4-attributed)",
        "quality_score":    "avg 5.1/10 across primary keywords",
        "impression_share": "38%",
        "lost_is_budget":   "31%",
        "lost_is_rank":     "31%",
    },
    "notes": (
        "Sales team reports avg 8% of form fills become MQLs. "
        "No GCLID stored in CRM. Monthly SQL target: 12. Currently hitting ~6."
    ),
}

DEMO_META = {
    "platform":     "meta",
    "mode":         "audit",
    "command":      "/audit",
    "project":      "Demo Account — StyleHouse Ecom",
    "account_type": "ecom",
    "date_range":   "last 30 days",
    "market":       "US / USD",
    "context":      "DTC fashion ecom, AOV $85, repeat purchase rate 28%",
    "inputs": {
        "META__Pixel__Status":              "Pixel firing. Purchase event confirmed.",
        "META__CAPI__Status":               "Not connected — browser-only pixel.",
        "META__EMQ__Score":                 "4.2 / 10 (low — email matching only, no phone/IP)",
        "META__ConsentMode__Status":        "Not configured for EU — data use restriction warning active.",
        "META__Campaigns__Summary":         "2 campaigns: ASC ($2,400/mo, ROAS 2.1x), Retargeting ($800/mo, ROAS 4.8x)",
        "META__Creative__Performance":      "Top creative: 18 days active. Hook Rate 14% (below 25% threshold). CTR 0.7% (below 0.9% norm).",
        "META__Frequency__7d":              "3.8x per 7 days (approaching fatigue threshold of 5x)",
        "META__Learning__Status":           "ASC: Active (exited learning). Retargeting Ad Set: Learning Limited — only 23 purchase events in 7d (need 50).",
        "META__Attribution__Check":         "Meta reported: 287 purchases. Shopify backend: 198 orders. Ratio: 1.45x (within 1.35-1.55 normal range).",
    },
    "metrics": {
        "spend_30d":     "$3,200",
        "purchases":     "287 (Meta) / 198 (Shopify)",
        "roas_meta":     "2.8x reported",
        "roas_true":     "~1.9x (adjusted for attribution ratio)",
        "cpm":           "$22.40 (above $18 norm)",
        "ctr_link":      "0.71%",
        "hook_rate":     "14%",
        "frequency_7d":  "3.8x",
        "cvr":           "1.1%",
    },
    "notes": "No new creative in 18 days. CAPI not implemented. EU consent warning.",
}

DEMO_TIKTOK = {
    "platform":     "tiktok",
    "mode":         "audit",
    "command":      "/audit",
    "project":      "Demo Account — FitGear Sports",
    "account_type": "ecom",
    "date_range":   "last 14 days",
    "market":       "US / USD",
    "context":      "Sports equipment DTC, AOV $120, target 18-35",
    "inputs": {
        "TIKTOK__Pixel__Status":             "Pixel installed. Purchase event firing.",
        "TIKTOK__EventsAPI__Status":         "Not connected — browser-only.",
        "TIKTOK__Creative__Performance":     "3 active ads: Ad A (21 days, Hook Rate 12%), Ad B (8 days, Hook Rate 31%), Ad C (5 days, Hook Rate 28%)",
        "TIKTOK__LearningPhase__Status":     "Ad Group 1: Learning (day 9, 31 conversions — need 50)",
        "TIKTOK__Attribution__Check":        "TikTok reported: 89 purchases. Shopify: 54 orders. Ratio: 1.65x (above 1.55 norm — possible duplicate counting).",
        "TIKTOK__Campaigns__Summary":        "1 campaign: Standard ($1,800/mo). No Smart+ tested.",
        "TIKTOK__Audience__Status":          "Interest targeting only. No Custom Audiences. No Lookalike.",
    },
    "metrics": {
        "spend_14d":       "$840",
        "purchases":       "89 (TikTok) / 54 (Shopify)",
        "roas_tiktok":     "2.1x reported",
        "cpm":             "$6.20",
        "ctr":             "1.8%",
        "hook_rate_avg":   "avg 24% (Ad A dragging down)",
        "video_completion": "Ad A: 11% / Ad B: 29% / Ad C: 26%",
    },
    "notes": "Ad A running 21 days — clear fatigue. Events API missing. Attribution ratio 1.65x slightly elevated.",
}


def get_demo_payload(platform: str) -> dict:
    """Return a pre-loaded demo audit payload for the given platform."""
    mapping = {
        "google":    DEMO_GOOGLE,
        "meta":      DEMO_META,
        "facebook":  DEMO_META,
        "instagram": DEMO_META,
        "tiktok":    DEMO_TIKTOK,
    }
    return mapping.get(platform.lower(), DEMO_GOOGLE)
