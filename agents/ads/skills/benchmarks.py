"""
Central benchmark library for all ad platforms.
Numbers are industry averages — use as orientation, not guarantees.
Last updated: 2026-Q2. Numbers reflect 2026 auction conditions.
"""

# ─── Google Ads ──────────────────────────────────────────────────────────────

GOOGLE = {
    # CPM / CPC
    "cpm_display":        (1.0,  4.0,   "USD"),   # Display / YouTube
    "cpc_search":         (1.0,  5.0,   "USD"),   # standard industries
    "cpc_search_high":    (5.0,  15.0,  "USD"),   # legal / finance / saas
    # CTR
    "ctr_search_good":    3.0,   # % — good
    "ctr_search_bad":     2.0,   # % — below this needs work
    "ctr_display_good":   0.35,  # %
    "ctr_display_bad":    0.10,  # %
    # Conversions
    "cvr_ecom":           (2.0,  5.0,   "%"),
    "cvr_leadgen":        (1.0,  3.0,   "%"),
    "roas_ecom_target":   3.0,   # x
    "roas_leadgen_min":   2.0,   # x
    # Quality & structure
    "quality_score_good": 7,     # points
    "quality_score_bad":  5,     # points — below needs work
    "impression_share_target": 70.0,  # %
    # Learning phase
    "learning_conv_min":  50,    # conversions to exit learning
    "learning_days":      14,    # days
    # Budget minimums (per month)
    "budget_min_usd":     1500,
    "budget_scale_usd":   5000,
}

# ─── Meta Ads ─────────────────────────────────────────────────────────────────

META = {
    # CPM
    "cpm_feed_normal":    (8.0,  18.0,  "USD"),
    "cpm_feed_hot":       25.0,          # above this → overheated auction
    "cpm_stories":        (5.0,  12.0,  "USD"),
    # CTR
    "ctr_link_good":      1.8,   # %
    "ctr_link_normal":    (0.9,  1.8,  "%"),
    "ctr_link_bad":       0.5,   # % — below this is a creative problem
    # Conversions
    "cvr_ecom":           (0.9,  2.2,  "%"),
    "cvr_leadgen":        (1.5,  4.0,  "%"),
    "roas_ecom_target":   2.5,   # x
    "roas_leadgen_min":   1.5,   # x
    # Engagement
    "frequency_normal":   3.0,   # per 7 days — above 5 → fatigue
    "frequency_warning":  5.0,
    "hook_rate_good":     25.0,  # % (3-sec video views / impressions)
    "hook_rate_bad":      15.0,  # %
    "video_completion_good": 15.0,  # % (plays to end)
    # EMQ
    "emq_minimum":        6.0,
    "emq_target":         7.0,
    # Learning phase
    "learning_conv_min":  50,    # conversions to exit learning
    "learning_days":      7,     # days (faster than Google)
    # Budget minimums (per month)
    "budget_min_usd":     2000,
    "budget_scale_usd":   8000,
    # CAPI
    "capi_match_rate_good": 80.0,   # %
    "capi_match_rate_bad":  60.0,   # %
}

# ─── TikTok Ads ───────────────────────────────────────────────────────────────

TIKTOK = {
    # CPM
    "cpm_infeed_normal":  (3.0,  8.0,   "USD"),
    "cpm_peak":           15.0,          # Q4 / competitive auctions
    # CTR
    "ctr_infeed_good":    2.5,   # %
    "ctr_infeed_normal":  (1.0,  2.5,  "%"),
    "ctr_infeed_bad":     0.5,   # %
    # Conversions
    "cvr_ecom":           (0.5,  1.5,  "%"),   # lower than Meta (intent gap)
    "roas_ecom_target":   2.0,   # x
    # Creative — TikTok targets are higher than Meta (algorithm rewards strong hooks more aggressively)
    "hook_rate_good":     30.0,  # % (3-sec views / impressions) — TikTok standard
    "hook_rate_warn":     20.0,  # % — below this = immediate refresh needed
    "hook_rate_bad":      15.0,  # % — critical
    "video_completion_good": 25.0,  # %
    "video_burnout_days": 14,    # creative fatigue typical window
    # Attribution
    "over_attribution":   (35,   55,   "%"),   # typical over-attribution range
    # Learning phase
    "learning_conv_min":  50,
    "learning_days":      7,
    # Budget minimums (per month)
    "budget_min_usd":     1000,
    "budget_scale_usd":   3000,
    "budget_test_min":    1500,  # minimum for statistically meaningful test
    # Audience minimums
    "custom_audience_min": 1000, # users — below this targeting won't activate
}

# ─── Cross-platform comparison string ─────────────────────────────────────────

def benchmark_summary(platform: str) -> str:
    """Return a formatted benchmark reference block for inclusion in prompts."""
    p = platform.lower()
    if p in ("google", "google_ads"):
        b = GOOGLE
        return (
            "Platform benchmarks (Google Ads, industry avg 2026):\n"
            f"  Search CTR: ≥{b['ctr_search_good']}% good / <{b['ctr_search_bad']}% needs work\n"
            f"  Display CTR: ≥{b['ctr_display_good']}% good / <{b['ctr_display_bad']}% needs work\n"
            f"  CVR ecom: {b['cvr_ecom'][0]}–{b['cvr_ecom'][1]}%\n"
            f"  ROAS target (ecom): ≥{b['roas_ecom_target']}x\n"
            f"  Quality Score: ≥{b['quality_score_good']} good / <{b['quality_score_bad']} critical\n"
            f"  Impression Share target: ≥{b['impression_share_target']}%\n"
            f"  Learning phase: ≥{b['learning_conv_min']} conv / {b['learning_days']}d\n"
            f"  Budget min: ${b['budget_min_usd']:,}/mo  |  scale threshold: ${b['budget_scale_usd']:,}/mo\n"
        )
    elif p in ("meta", "facebook", "instagram"):
        b = META
        return (
            "Platform benchmarks (Meta Ads, industry avg 2026):\n"
            f"  CPM Feed: ${b['cpm_feed_normal'][0]}–${b['cpm_feed_normal'][1]}  |  >${b['cpm_feed_hot']} = overheated\n"
            f"  Link CTR: {b['ctr_link_normal'][0]}–{b['ctr_link_normal'][1]}%  |  <{b['ctr_link_bad']}% = creative problem\n"
            f"  CVR ecom: {b['cvr_ecom'][0]}–{b['cvr_ecom'][1]}%\n"
            f"  ROAS target (ecom): ≥{b['roas_ecom_target']}x\n"
            f"  Frequency: ≤{b['frequency_normal']}/7d normal  |  >{b['frequency_warning']} = fatigue\n"
            f"  Hook Rate (3s): ≥{b['hook_rate_good']}% good / <{b.get('hook_rate_warn', b['hook_rate_bad'])}% refresh needed / <{b['hook_rate_bad']}% critical\n"
            f"  EMQ: ≥{b['emq_minimum']} minimum  |  ≥{b['emq_target']} target\n"
            f"  Learning phase: ≥{b['learning_conv_min']} conv / {b['learning_days']}d\n"
            f"  Budget min: ${b['budget_min_usd']:,}/mo  |  scale threshold: ${b['budget_scale_usd']:,}/mo\n"
        )
    elif p in ("tiktok", "tiktok_ads"):
        b = TIKTOK
        return (
            "Platform benchmarks (TikTok Ads, industry avg 2026):\n"
            f"  CPM In-Feed: ${b['cpm_infeed_normal'][0]}–${b['cpm_infeed_normal'][1]}  |  up to ${b['cpm_peak']} peak\n"
            f"  CTR In-Feed: {b['ctr_infeed_normal'][0]}–{b['ctr_infeed_normal'][1]}%  |  <{b['ctr_infeed_bad']}% poor\n"
            f"  CVR ecom: {b['cvr_ecom'][0]}–{b['cvr_ecom'][1]}%  (lower intent than Meta/Google)\n"
            f"  ROAS target: ≥{b['roas_ecom_target']}x\n"
            f"  Hook Rate (3s): ≥{b['hook_rate_good']}%  |  Video Completion: ≥{b['video_completion_good']}%\n"
            f"  Creative burnout: ~{b['video_burnout_days']}d  |  Over-attribution: {b['over_attribution'][0]}–{b['over_attribution'][1]}%\n"
            f"  Learning phase: ≥{b['learning_conv_min']} conv / {b['learning_days']}d\n"
            f"  Budget min: ${b['budget_min_usd']:,}/mo  |  test minimum: ${b['budget_test_min']:,}/mo\n"
            f"  Custom Audience min size: {b['custom_audience_min']:,} users\n"
        )
    return ""
