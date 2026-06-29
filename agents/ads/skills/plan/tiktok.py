from typing import Any, Dict


def build_tiktok_prompt(payload: Dict[str, Any]) -> str:
    product       = payload.get("product", "product")
    budget        = payload.get("budget", "not specified")
    audience      = payload.get("audience", {})
    goal          = payload.get("goal", "conversions")
    campaign_type = payload.get("campaign_type", "")

    audience_lines = []
    if audience.get("age"):      audience_lines.append(f"age: {audience['age']}")
    if audience.get("location"): audience_lines.append(f"geo: {audience['location']}")
    if audience.get("interest"): audience_lines.append(f"interests: {audience['interest']}")
    audience_text = ", ".join(audience_lines) if audience_lines else "broad audience"

    campaign_hint = f"Campaign type: {campaign_type}" if campaign_type else \
        "Campaign type: choose from Standard / Smart+ / Shopping Ads"

    return f"""Platform: TikTok Ads
Product: {product}
Budget: {budget}
Goal: {goal}
Audience: {audience_text}
{campaign_hint}

Task — deliver a concrete campaign launch plan:

1. Campaign type and objective:
   - Awareness: Reach, Video Views
   - Consideration: Traffic, Community Interaction, App Installs
   - Conversion: Website Conversions, Lead Generation, App Events, Catalog Sales
   - Smart+ Campaign: Full Auto / Partial / Manual control tiers
   - Shopping Ads: placements in feed + search + shopping centre

2. Structure (Campaign → Ad Group → Ad):
   - Ad Group split logic: by audience or format
   - Daily budget per Ad Group: minimum $20–50 during learning

3. Bidding strategy:
   - Maximum Delivery — maximise conversions within budget
     (budget ≥ 10× average CPA over 7 days during learning)
   - Cost Cap — target CPA; budget ≥ 10× bid
   - Bid Cap — hard ceiling on bid amount
   - Minimum ROAS — for ecom accounts

4. Targeting:
   - Demographics: age, gender, language, geo
   - Interests & Behaviours: interest categories, video/profile engagement
   - Custom Audiences: Website Pixel, Customer File, App Activity, Engagement
   - Lookalike: 1–3% (precise), 5–10% (scale)
   - TikTok-specific: Hashtag Audience, Creator Lookalike

5. Ad formats (9:16 vertical only):
   - In-Feed Ads: 5–60 sec, autoplay in feed, CTA button
   - TopView: first thing user sees on app open, 3–60 sec
   - Brand Takeover: full-screen on launch, 3–5 sec
   - Branded Hashtag Challenge: UGC mechanic, min 6 days
   - Spark Ads: boost organic content (creator posts)
   - Shopping Ads: product cards from feed

6. Creative requirements:
   - Format: 9:16, 1080×1920 px, sound ON is default
   - Hook: first 1–3 seconds determine everything (scroll-stop moment)
   - Refresh cadence: 15–30 new assets per week
   - Style: native UGC beats polished brand ads on TikTok
   - Subtitles: mandatory (add via Auto Caption or burn-in)
   - Split test: audience, placement, bid strategy, budget, creative, catalog

7. KPIs and benchmarks (EU/US 2026):
   - CPM: $3–8 (prospecting) / CTR: 1–3%
   - CVR: 0.4–1.4% (lower than Meta — normal for discovery platform)
   - Video Completion Rate ≥ 25% — benchmark for strong creative
   - Hook Rate (3-sec views / impressions): ≥ 30% good / < 20% refresh needed
   - Attribution: Events API (maturing), recommend Pixel + CAPI
   - Over-attribution: ~35–55% — use incrementality tests for true measure

8. Budget guidance (EU/US SMB):
   - Minimum for meaningful data: $1,000–3,000/mo
   - Realistic SMB ceiling: $15,000–60,000/mo
"""
