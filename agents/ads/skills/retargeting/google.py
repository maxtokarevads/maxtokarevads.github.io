from typing import Any, Dict
from .._shared import get_stage_hint


def build_google_retargeting_prompt(payload: Dict[str, Any]) -> str:
    product      = payload.get("product", "product")
    usp          = payload.get("usp", "")
    funnel_stage = payload.get("funnel_stage", "mofu")
    audience     = payload.get("audience", {})
    goal         = payload.get("goal", "conversions")
    has_crm      = payload.get("has_crm_list", False)
    landing_page = payload.get("landing_page", "")

    usp_text   = f"\nUSP: {usp}" if usp else ""
    lp_text    = f"\nLanding Page: {landing_page}" if landing_page else ""
    crm_text   = "CRM list: available" if has_crm else "CRM list: not provided"
    stage_hint = get_stage_hint(funnel_stage, "google")

    return f"""Platform: Google Ads — Remarketing Strategy
Product: {product}{usp_text}
Goal: {goal}
Funnel stage: {funnel_stage.upper()} — {stage_hint}
{crm_text}{lp_text}

Task — develop a complete remarketing strategy:

1. AUDIENCE ARCHITECTURE (Google Audiences)

   A) RLSA (Remarketing Lists for Search Ads):
   — "All site visitors" (30 days): bid +20%
   — "Key page visitors" (30 days): bid +35%
   — "Cart abandoners" (14 days): bid +60%, special offer
   — "Checkout page visitors" (7 days): bid +80%, urgency message
   — Exclusion: "Buyers in last 30 days" — exclude from conversion ads
   Minimum audience size for RLSA activation: 1,000 users per segment

   B) Display Remarketing (Google Display Network):
   — Site visitors 14 / 30 / 90 days with different creatives
   — Sequential remarketing: show ads in a defined order
   — Frequency cap: 5–7 impressions/day per user

   C) Customer Match:
   — Upload CRM email list to Google Ads (minimum 1,000 matches)
   — Segments: active customers, lapsed (no purchase >90 days), high-value (LTV >X)
   — Upsell / cross-sell ads for existing customers

   D) Similar Audiences (based on top converters):
   — Lookalike from Customer Match purchaser list
   — Lookalike from cart-abandoner remarketing audience

2. STRATEGY BY FUNNEL STAGE

   MOFU (visited but did not convert):
   — Display: product reminder with social proof (reviews, ratings)
   — Search RLSA: same queries + bid uplift + "You viewed X" headline
   — Message: "Come back and learn more", benefit demonstration

   BOFU (cart / checkout):
   — Search RLSA: maximum bid, urgency ("Only 2 left", "Offer expires soon")
   — Display: Dynamic Remarketing (DRA) — shows the exact products they viewed
   — Gmail Ads: personalised reminder with an offer
   — Message: "Complete your purchase", discount or bonus to recover

3. DYNAMIC REMARKETING (ecom only)
   — Requirements: Google Merchant Center, remarketing tag with Product ID
   — Ad templates: auto-populate product, price, image
   — Audiences: General Visitors, Product Viewers, Cart Abandoners, Past Buyers

4. CAMPAIGN SETTINGS
   — Campaign type: Display (remarketing) / Search with RLSA
   — Bidding: Target CPA (if enough data) / Enhanced CPC
   — Frequency cap: 3–5 impressions/day for Display
   — Audience membership duration: 7 / 14 / 30 / 90 days by segment

5. AD COPY BY SEGMENT
   — Cart abandoners: urgency + offer (discount, free shipping)
   — Page viewers: reminder + social proof
   — Lapsed customers: "We miss you" + new arrivals or loyalty bonus

6. MEASUREMENT
   — Key metrics: segment ROAS vs cold traffic ROAS, CPA by audience
   — Attribution: view-through conversion window for Display = 1 day
   — Exclude self-attribution: do not count organic conversions as remarketing
"""
