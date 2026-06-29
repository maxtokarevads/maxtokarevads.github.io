from typing import Any, Dict


def build_tiktok_analyze_prompt(payload: Dict[str, Any]) -> str:
    product   = payload.get("product", "product")
    metrics   = payload.get("metrics", {})
    objective = payload.get("goal", "conversions")

    cpm              = metrics.get("cpm", None)
    ctr              = metrics.get("ctr", None)
    cpc              = metrics.get("cpc", None)
    cpa              = metrics.get("cpa", None)
    roas             = metrics.get("roas", None)
    spend            = metrics.get("spend", None)
    impressions      = metrics.get("impressions", None)
    clicks           = metrics.get("clicks", None)
    conversions      = metrics.get("conversions", None)
    cvr              = metrics.get("cvr", None)
    hook_rate        = metrics.get("hook_rate", None)
    video_completion = metrics.get("video_completion_rate", None)
    watch_time       = metrics.get("avg_watch_time", None)
    engagement_rate  = metrics.get("engagement_rate", None)

    def fmt(v, suffix=""):
        return f"{v}{suffix}" if v is not None else "not specified"

    context = payload.get("context", "") or payload.get("notes", "")
    if not any(v is not None for v in metrics.values()):
        if context:
            return (
                f"Platform: TikTok Ads — Campaign Analysis\n"
                f"Product/Project: {product}\n\n"
                f"Context provided by user:\n{context}\n\n"
                "Task — analyse the situation described above:\n"
                "1. Identify the most likely root cause (hook rate, creative fatigue, attribution, learning phase)\n"
                "2. Compare to TikTok 2026 benchmarks "
                "(Hook Rate ≥30%, CTR ≥1%, Video Completion ≥25%, CPM $3–8 normal)\n"
                "3. List 3–5 prioritised actions with expected impact\n"
                "4. Note what additional data would sharpen the diagnosis "
                "(Hook Rate and Video Completion Rate are priority asks for TikTok)\n"
            )
        return (
            f"Platform: TikTok Ads — Campaign Analysis\n"
            f"Product: {product}\n\n"
            "No metrics provided.\n\n"
            "To run a diagnosis, request the following data:\n"
            "- CPM, CTR, CPC, CPA, ROAS (core metrics)\n"
            "- Hook Rate (% who watched the first 3 sec) — the key TikTok signal\n"
            "- Video Completion Rate and Average Watch Time (sec)\n"
            "- Impressions, Clicks, Conversions, Spend\n"
            "- Learning phase status (in learning / completed)\n\n"
            "Do not fabricate a diagnosis without data."
        )

    return f"""Platform: TikTok Ads — Campaign Analysis
Product: {product}
Campaign objective: {objective}

## Diagnostic Examples (use as reasoning reference)

Example A — Hook Failure:
Symptom: Hook Rate 12% (benchmark ≥30%), CTR 0.4%, high CPM
Root cause: First 3 seconds too slow — no pattern interrupt, no text overlay
Action: Rewrite hook, add bold text overlay at second 0, test 3 hook variants
Result: Hook Rate → 28%, CTR → 1.1%, CPA -35%

Example B — Over-Attribution (CRITICAL EDGE CASE):
Symptom: TikTok dashboard ROAS 4.2x, GA4 shows 1.8x, backend shows 2.1x
Root cause: TikTok over-attributes 35–55% (standard for platform), 7d click / 1d view window too wide
Action: Run incrementality/holdout test, implement Events API (CAPI), tighten attribution window
Flag: NEVER recommend budget scale when TikTok vs GA4 ROAS gap >50%

Example C — Spark Ads vs In-Feed comparison:
Benchmark: Spark Ads CTR 2.4% (2.4× In-Feed 0.61%), CVR 2.6% (+44% vs In-Feed)
If In-Feed CTR <0.8%: test same message as Spark Ad with creator partnership
Expected lift: 1.5–2.5× CTR, 30–50% lower CPA

Metrics:
- CPM: ${fmt(cpm)}
- CTR: {fmt(ctr, "%")}
- CPC: ${fmt(cpc)}
- CPA: ${fmt(cpa)}
- ROAS: {fmt(roas, "x")}
- CVR: {fmt(cvr, "%")}
- Spend: ${fmt(spend)}
- Impressions: {fmt(impressions)}
- Clicks: {fmt(clicks)}
- Conversions: {fmt(conversions)}
- Hook Rate (3-sec view): {fmt(hook_rate, "%")}
- Video Completion Rate: {fmt(video_completion, "%")}
- Avg Watch Time: {fmt(watch_time, " sec")}
- Engagement Rate: {fmt(engagement_rate, "%")}

Task — run a detailed diagnostic analysis:

1. METRIC DIAGNOSIS
   TikTok Ads benchmarks (2026, EU/US):
   - CPM: $3–8 normal (prospecting) / >$12 = audience overheated
   - CTR: 1–3% normal for In-Feed / <0.5% = weak creative or irrelevant audience
   - CVR: 0.4–1.4% (lower than Meta — normal for discovery platform)
   - Hook Rate (3-sec): ≥30% good / <20% = hook not working — primary issue
   - Video Completion Rate: ≥25% good / <10% = content not holding attention
   - Avg Watch Time: ≥3–5 sec for a 15-sec video = acceptable

2. CREATIVE ANALYSIS (CRITICAL FOR TIKTOK)
   Hook Rate is the primary signal:
   - Hook Rate <20%: first 1–3 seconds not stopping the scroll
     → Recommendations: new scroll-stop opening, strong visual hook,
       question / provocation / unexpected action in frame 1
   - Low Watch Time with good Hook Rate: video drops off mid-way
     → Cut to 9–15 sec, remove pauses, increase pace
   - High Completion Rate but low CTR: missing a strong CTA
     → Add CTA at 75% mark + text overlay throughout

3. FUNNEL DIAGNOSIS
   - Normal CPM, low CTR: creative issue (not native, too polished/ad-like)
   - Good CTR, low CVR: landing page problem or expectation mismatch
   - High CPA with normal CVR: wrong audience or wrong objective

4. ATTRIBUTION & OVER-ATTRIBUTION
   - TikTok over-reports conversions by ~35–55%
   - Recommended: cross-validate with GA4 / backend / CAPI
   - Events API (CAPI) status: connected or not — critical for data quality
   - Use incrementality tests for true lift measurement

5. LEARNING PHASE
   - Maximum Delivery: budget ≥10× average CPA — met?
   - Cost Cap: budget ≥10× bid — aligned?
   - Learning window: 7–14 days; no structural changes during this period

6. CREATIVE REFRESH REQUIREMENT
   - TikTok typically requires 15–30 new assets/week to maintain performance
   - Assess: how many weeks are current ads running — rotation needed?

7. PRIORITISED ACTIONS
   Format: Problem → Root cause → Action → Expected impact

8. FORECAST
   Expected changes to Hook Rate, CVR, and CPA after implementing recommendations

9. CONFIDENCE ASSESSMENT
   For each recommendation above, state:
   - Confidence: High (have all data) / Medium (some data missing) / Low (assumption-based)
   - Missing data: what additional metrics would sharpen this diagnosis
   - Key assumptions made (especially re: over-attribution)
"""
