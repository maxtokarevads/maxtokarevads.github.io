from typing import Any, Dict


def build_google_abtest_prompt(payload: Dict[str, Any]) -> str:
    product       = payload.get("product", "product")
    what_to_test  = payload.get("what_to_test", "")
    current_perf  = payload.get("current_performance", {})
    campaign_type = payload.get("campaign_type", "Search")
    budget        = payload.get("budget", 0)

    perf_text = ""
    if current_perf:
        perf_text = "\nCurrent performance:\n" + "\n".join(f"  {k}: {v}" for k, v in current_perf.items())

    test_hint = f"What to test: {what_to_test}" if what_to_test else \
        "What to test: determine based on current structure analysis"

    return f"""Platform: Google Ads — A/B Test Design
Product: {product}
Campaign type: {campaign_type}
Test budget: ${budget}/mo
{test_hint}{perf_text}

Task — develop a structured A/B testing plan:

1. GOOGLE ADS TESTING TOOLS

   A) Ad Variations:
   — Tests: headlines, descriptions, URL paths in RSA
   — Works at the existing campaign level (no copy needed)
   — Traffic split: 50/50 automatically
   — Minimum: 100–200 clicks for statistical significance
   — Use for: single ad element changes

   B) Drafts & Experiments:
   — Tests: bidding strategy, targeting, schedule, audiences
   — Works by creating a Draft campaign → launching as an Experiment
   — Split: configurable % of traffic (recommend 50/50)
   — Key: traffic split at auction level (cookie-based), not by time

2. WHAT AND HOW TO TEST (prioritised)

   HIGH PRIORITY — fast ROI:

   Test 1: BIDDING STRATEGY
   — Control: current strategy (e.g. Maximize Clicks)
   — Variant: Target CPA / Target ROAS
   — Tool: Drafts & Experiments
   — Duration: 4–6 weeks (need ≥100 conversions per branch)
   — Win metric: CPA reduced by ≥10% at stable volume

   Test 2: RSA HEADLINES (Ad Variations)
   — Control: current headlines
   — Variant A: headline with price / number
   — Variant B: question headline
   — Variant C: brand / trust signal headline
   — Duration: 2–4 weeks, ≥500 clicks per variant
   — Win metric: CTR increased by ≥15%

   MEDIUM PRIORITY:

   Test 3: KEYWORD MATCH TYPES
   — Control: Exact Match
   — Variant: Broad Match (with smart bidding) vs Phrase Match
   — Tool: Drafts & Experiments (separate campaign)
   — Duration: 6–8 weeks
   — Metric: conversion volume and CPA

   Test 4: LANDING PAGE (if multiple LPs available)
   — Control: current landing page
   — Variant: new LP version (A/B via Final URL in ad)
   — Tool: Ad Variations with different URLs
   — Win metric: CVR increased by ≥20%

   Test 5: PERFORMANCE MAX vs SEARCH
   — Control: dedicated Search campaign
   — Variant: Performance Max
   — Tool: Drafts & Experiments or parallel campaigns
   — Duration: 8 weeks (PMax needs time to learn)

3. STATISTICAL SIGNIFICANCE AND SAMPLE SIZE

   Required sample size formula (per branch, proportions):
     n = 16 × p × (1 − p) / δ²
   Where:
     p = baseline CVR (or CTR) as a decimal  (e.g. 2% = 0.02)
     δ = MDE in absolute terms  (e.g. 20% relative shift from 0.02 = 0.004)
   Parameters: 95% confidence (z_α = 1.96), 80% power (z_β = 0.84)

   Quick reference (sessions per branch):
   | Baseline CVR | MDE 10% (rel) | MDE 20% (rel) | MDE 30% (rel) |
   |---|---|---|---|
   | 1%  | ~30,800 | ~7,700 | ~3,400 |
   | 2%  | ~15,300 | ~3,800 | ~1,700 |
   | 3%  | ~10,000 | ~2,500 | ~1,100 |
   | 5%  | ~5,900  | ~1,500 | ~650   |
   | 10% | ~2,700  | ~680   | ~300   |

   Steps BEFORE launching a test:
   1. Establish baseline CVR from historical data (minimum 30 days)
   2. Set the MDE: typically 15–25% relative for Google
   3. Calculate n → determine test duration given current traffic
   4. If required traffic is unachievable: raise MDE or use a higher-volume event

   Practical rules:
   — Conversions: ≥100 events per branch — absolute minimum
   — CTR tests: ≥1,000 clicks per branch
   — Calculator: built into Google Ads Experiments or abtestguide.com
   — Do NOT stop early — early stopping = false result
   — Sequential testing: Google's automatic winner detection is acceptable

4. TEST STRUCTURE RULES
   — Test ONE variable at a time
   — Do not change bids, budgets, or schedules during the test
   — Exclude seasonal events (sales, holidays) from the test window

5. RESULT DOCUMENTATION
   For each test:
   — Hypothesis: "If we change X, then Y will improve by Z%"
   — Control and Variant: exact settings
   — Start / end date
   — Result: winner / loser / neutral
   — Next step: apply / reject / iterate
"""
