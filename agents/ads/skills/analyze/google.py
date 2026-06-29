from typing import Any, Dict


def build_google_analyze_prompt(payload: Dict[str, Any]) -> str:
    product       = payload.get("product", "product")
    metrics       = payload.get("metrics", {})
    campaign_type = payload.get("campaign_type", "Search")

    ctr              = metrics.get("ctr", None)
    cpc              = metrics.get("cpc", None)
    cpa              = metrics.get("cpa", None)
    roas             = metrics.get("roas", None)
    impressions      = metrics.get("impressions", None)
    clicks           = metrics.get("clicks", None)
    conversions      = metrics.get("conversions", None)
    spend            = metrics.get("spend", None)
    quality_score    = metrics.get("quality_score", None)
    impression_share = metrics.get("impression_share", None)
    lost_is_budget   = metrics.get("lost_is_budget", None)
    lost_is_rank     = metrics.get("lost_is_rank", None)
    ad_strength      = metrics.get("ad_strength", None)

    def fmt(v, suffix=""):
        return f"{v}{suffix}" if v is not None else "not specified"

    context = payload.get("context", "") or payload.get("notes", "")
    if not any(v is not None for v in metrics.values()):
        if context:
            # Free-text mode: user passed context instead of structured metrics
            return (
                f"Platform: Google Ads — Campaign Analysis\n"
                f"Product/Project: {product}\n\n"
                f"Context provided by user:\n{context}\n\n"
                "Task — analyse the situation described above:\n"
                "1. Identify the most likely root cause\n"
                "2. Compare stated metrics to Google Ads 2026 benchmarks "
                "(CTR ≥3% Search, QS ≥7, IS ≥70%, ROAS ≥3x ecom / ≥2x lead-gen)\n"
                "3. List 3–5 prioritised actions with expected impact\n"
                "4. Note what additional data would sharpen the diagnosis\n"
            )
        return (
            f"Platform: Google Ads — Campaign Analysis\n"
            f"Product: {product}\n\n"
            "No metrics provided.\n\n"
            "To run a diagnosis, paste your metrics after the command:\n"
            "/analyze CTR dropped from 3.5% to 1.8%, CPA up from $40 to $67, QS avg 4.2\n\n"
            "Or provide structured metrics and try again."
        )

    return f"""Platform: Google Ads — Campaign Analysis
Product: {product}
Campaign type: {campaign_type}

## Diagnostic Examples (use as reasoning reference)

Example A — Low CTR (happy path):
Symptom: Search CTR 1.8% (benchmark 3.52% avg, 4.1% e-com)
Root cause: "Learn more" CTA underperforms "Get started" 2.3x in copy tests
Action: Replace 40% of ad variants with high-intent CTAs
Result: CTR → 2.9%, CPA -18%

Example B — Smart Bidding Failure (EDGE CASE):
Symptom: tCPA set at $35, actual CPA $68, spend erratic, Learning status permanent
Root cause: Only 18 conversions/month — insufficient for tCPA (need ≥30–50)
Action: Switch to Maximize Conversions until 50+ conv/month, then re-enable tCPA
Flag: NEVER switch to Smart Bidding with <30 conversions/month

Example C — PMax Brand Cannibalization:
Symptom: Brand keyword costs doubled, PMax taking credit for branded searches
Root cause: PMax not excluded from brand terms, competing with Search campaign
Action: Add brand exclusions to PMax, monitor branded search IS separately

Metrics:
- CTR: {fmt(ctr, "%")}
- CPC: ${fmt(cpc)}
- CPA: ${fmt(cpa)}
- ROAS: {fmt(roas, "x")}
- Impressions: {fmt(impressions)}
- Clicks: {fmt(clicks)}
- Conversions: {fmt(conversions)}
- Spend: ${fmt(spend)}
- Quality Score: {fmt(quality_score, "/10")}
- Search Impression Share: {fmt(impression_share, "%")}
- Lost IS (budget): {fmt(lost_is_budget, "%")}
- Lost IS (rank): {fmt(lost_is_rank, "%")}
- Ad Strength: {fmt(ad_strength)}

Task — run a detailed diagnostic analysis:

1. METRIC DIAGNOSIS
   Google Ads benchmarks (Search, 2026):
   - CTR: ≥3–5% normal for Search / <1% = relevance problem
   - Quality Score: ≥7 good / ≤4 = urgent fix (CTR, relevance, landing page)
   - ROAS: ≥3x ecom / ≥2x lead-gen minimum
   - Impression Share: <70% = losing significant auction volume

2. QUALITY SCORE BREAKDOWN (if provided)
   Three components: Expected CTR / Ad Relevance / Landing Page Experience
   - What is dragging QS down and how it inflates CPC
   - Concrete steps to reach QS 7+

3. IMPRESSION SHARE ANALYSIS
   - Lost IS (budget): increase daily budget or narrow targeting
   - Lost IS (rank): raise bids or improve QS
   - Acceptable loss: up to 20–25% combined Lost IS

4. BIDDING STRATEGY DIAGNOSIS
   - Is the current strategy justified? Enough data for Smart Bidding (≥30–50 conv/mo)?
   - Recommendations: move to tCPA / tROAS / Maximize Conversions
   - If data is thin: Maximize Clicks with CPC cap as starting point

5. PROBLEMS AND PRIORITISED ACTIONS
   Format: Problem → Root cause → Concrete action → Expected impact

6. FORECAST
   If recommendations are implemented: expected CTR / CPA / ROAS improvement in 2–4 weeks

7. CONFIDENCE ASSESSMENT
   For each recommendation above, state:
   - Confidence: High (have all data) / Medium (some data missing) / Low (assumption-based)
   - Missing data: what additional metrics or context would sharpen this diagnosis
   - Key assumptions made
"""
