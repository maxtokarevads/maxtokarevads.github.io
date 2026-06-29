from typing import Any, Dict


def build_meta_prompt(payload: Dict[str, Any]) -> str:
    product       = payload.get("product", "product")
    budget        = payload.get("budget", "not specified")
    audience      = payload.get("audience", {})
    goal          = payload.get("goal", "conversions")
    placement     = payload.get("placement", "")

    audience_lines = []
    if audience.get("age"):      audience_lines.append(f"age: {audience['age']}")
    if audience.get("location"): audience_lines.append(f"geo: {audience['location']}")
    if audience.get("interest"): audience_lines.append(f"interests: {audience['interest']}")
    audience_text = ", ".join(audience_lines) if audience_lines else "broad audience"

    placement_hint = f"Placement: {placement}" if placement else \
        "Placement: Advantage+ (automatic Meta selection)"

    return f"""Platform: Meta Ads (Facebook / Instagram)
Product: {product}
Budget: {budget}
Goal: {goal}
Audience: {audience_text}
{placement_hint}

Task — deliver a concrete campaign launch plan:

1. Campaign Objective:
   - Awareness: Brand Awareness, Reach
   - Consideration: Traffic, Engagement, Lead Generation, Video Views
   - Conversion: Sales, Catalog Sales (DPA)
   - Advantage+ Shopping Campaign (ASC) — for ecom

2. Account structure (Campaign → Ad Set → Ad):
   - Number of Ad Sets and split logic (by audience / placement)
   - Budget: CBO (Campaign Budget Optimization) vs ABO

3. Targeting (Ad Set level):
   - Core Audience: demographics, interests, behaviours
   - Custom Audiences: Pixel (website), Customer List, Video Engagement
   - Lookalike: 1–3% (cold traffic), 3–7% (scale)
   - Advantage+ Audience: when to use instead of manual targeting

4. Ad formats:
   - Single Image/Video — Feed (1:1 or 4:5)
   - Carousel — up to 10 cards, each with its own CTA
   - Collection + Instant Experience — mobile shopping
   - Stories / Reels — 9:16, first 3 seconds critical, sound on
   - Lead Form — embedded form without leaving the app

5. Bidding strategy:
   - Lowest Cost (uncapped) — for launch and learning
   - Cost Cap — hold CPA ≤ target
   - ROAS Target — for ecom with conversion history
   - Learning phase: ≥50 conversions in 7 days to exit

6. Creative:
   - Recommended cadence: 10–20 new assets per week
   - Creative shelf life: 2–4 weeks before fatigue (frequency >3–4)
   - Advantage+ Creative: automatic enhancements (brightness, music, text overlay)
   - 3 ad copy variants with different hooks (question / number / pain point)

7. KPIs and benchmarks (ecom, EU/US 2026):
   - CPM: $8–18 / CTR Feed: 0.9–1.8% / CVR: 0.9–2.2%
   - CPA, ROAS, Frequency (target ≤3 per 7 days)
   - Attribution: 7-day click / 1-day view
"""
