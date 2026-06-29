from typing import Any, Dict


def build_meta_analyze_prompt(payload: Dict[str, Any]) -> str:
    product   = payload.get("product", "product")
    metrics   = payload.get("metrics", {})
    objective = payload.get("goal", "conversions")

    cpm        = metrics.get("cpm", None)
    ctr        = metrics.get("ctr", None)
    cpc        = metrics.get("cpc", None)
    cpa        = metrics.get("cpa", None)
    roas       = metrics.get("roas", None)
    frequency  = metrics.get("frequency", None)
    reach      = metrics.get("reach", None)
    impressions= metrics.get("impressions", None)
    clicks     = metrics.get("clicks", None)
    conversions= metrics.get("conversions", None)
    spend      = metrics.get("spend", None)
    cvr        = metrics.get("cvr", None)
    relevance  = metrics.get("relevance_score", None)
    hook_rate  = metrics.get("hook_rate", None)
    video_rate = metrics.get("video_completion_rate", None)

    def fmt(v, suffix=""):
        return f"{v}{suffix}" if v is not None else "not specified"

    context = payload.get("context", "") or payload.get("notes", "")
    if not any(v is not None for v in metrics.values()):
        if context:
            return (
                f"Platform: Meta Ads — Campaign Analysis\n"
                f"Product/Project: {product}\n\n"
                f"Context provided:\n{context}\n\n"
                "Task — analyse the situation described above:\n"
                "1. Identify root cause (pixel, creative fatigue, audience, learning phase, bid)\n"
                "2. Compare to Meta 2026 benchmarks (Link CTR ≥0.9%, Hook Rate ≥25%, Frequency ≤5/7d, EMQ ≥6)\n"
                "3. List 3–5 prioritised actions with expected impact\n"
                "4. Note what additional data would sharpen the diagnosis\n"
            )
        return (
            f"Platform: Meta Ads — Campaign Analysis\n"
            f"Product: {product}\n\n"
            "No metrics provided.\n\n"
            "Paste metrics after the command:\n"
            "/analyze ROAS dropped from 3.2x to 1.8x, Frequency 5.4, Hook Rate 12%\n"
        )

    return f"""Platform: Meta Ads (Facebook/Instagram) — Campaign Analysis
Product: {product}
Campaign objective: {objective}

## Diagnostic Examples (use as reasoning reference)

Example A — Creative Fatigue:
Symptom: Frequency 3.2, CTR declining 2%/day, CPM rising 8%/day
Root cause: Same creative served to warm audience for 12 days
Action: Rotate creative, introduce 3 variants, cap frequency at 2.5
Result: CTR stabilized, CPM decreased 12%

Example B — Attribution Inflation (EDGE CASE):
Symptom: Meta ROAS 4.1x but GA4 shows only 1.9x
Root cause: TikTok/Meta over-attribution + view-through window too wide
Action: Cross-validate with GA4, implement CAPI, run incrementality test
Flag: NEVER recommend scale-up when platform vs analytics gap >30%

Example C — Learning Limited:
Symptom: "Learning Limited" status, CPM 40% above normal, delivery erratic
Root cause: Ad set getting <50 conversions/week — algorithm cannot optimise
Action: Consolidate ad sets, increase budget, or switch to higher-funnel event

Metrics:
- CPM: ${fmt(cpm)}
- CTR (Link): {fmt(ctr, "%")}
- CPC: ${fmt(cpc)}
- CPA: ${fmt(cpa)}
- ROAS: {fmt(roas, "x")}
- CVR: {fmt(cvr, "%")}
- Frequency: {fmt(frequency, "x per 7d")}
- Reach: {fmt(reach)}
- Impressions: {fmt(impressions)}
- Clicks: {fmt(clicks)}
- Conversions: {fmt(conversions)}
- Spend: ${fmt(spend)}
- Relevance Score: {fmt(relevance)}
- Hook Rate (3-sec): {fmt(hook_rate, "%")}
- Video Completion Rate: {fmt(video_rate, "%")}

Task — run a detailed diagnostic analysis:

1. METRIC DIAGNOSIS
   Meta Ads benchmarks (2026, EU/US):
   - CPM: $8–18 normal / >$25 = audience overheated or heavy competition
   - CTR (Link): 0.9–1.8% normal / <0.5% = creative or relevance problem
   - CVR: 0.9–2.2% ecom / lower = landing page or audience mismatch
   - ROAS: ≥2.5x minimum ecom / ≥1.5x lead-gen
   - Frequency: ≤3/7d normal / >5 = audience fatigue, refresh creative

2. AUDIENCE FATIGUE ANALYSIS (Frequency)
   - Frequency >3: signs — CTR dropping with stable or rising CPM
   - Actions: refresh creative, broaden audience, add Lookalike
   - Learning Limited: if active — causes and how to resolve (budget / conversions)

3. CREATIVE ANALYSIS (if Hook Rate / Video Completion Rate provided)
   - Hook Rate <25%: first 3 seconds not stopping scroll — hook recommendations
   - Video Completion Rate <15%: video too long or loses interest
   - What to change: script, format, copy

4. FUNNEL DIAGNOSIS (CPM → CTR → CVR → ROAS)
   - Where it breaks: cheap traffic but no conversion = landing page issue
   - High CPM = audience overheated or wrong objective
   - Attribution window: 7-day click / 1-day view — are post-view conversions counted?

5. LEARNING PHASE STATUS
   - Enough conversions (≥50 in 7 days) to exit Learning Phase?
   - Recommendations: consolidate Ad Sets, simplify structure

6. PRIORITISED ACTIONS
   Format: Problem → Root cause → Action → Expected impact

7. FORECAST
   Expected metric changes after implementing recommendations

8. CONFIDENCE ASSESSMENT
   For each recommendation above, state:
   - Confidence: High (have all data) / Medium (some data missing) / Low (assumption-based)
   - Missing data: what additional metrics or context would sharpen this diagnosis
   - Key assumptions made
"""
