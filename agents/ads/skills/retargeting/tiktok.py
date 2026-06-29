from typing import Any, Dict
from .._shared import get_stage_hint


def build_tiktok_retargeting_prompt(payload: Dict[str, Any]) -> str:
    product      = payload.get("product", "product")
    usp          = payload.get("usp", "")
    funnel_stage = payload.get("funnel_stage", "mofu")
    goal         = payload.get("goal", "conversions")
    has_pixel    = payload.get("has_pixel", True)
    has_crm      = payload.get("has_crm_list", False)
    has_catalog  = payload.get("has_catalog", False)

    usp_text   = f"\nUSP: {usp}" if usp else ""
    pixel_text = "TikTok Pixel: installed" if has_pixel else "TikTok Pixel: NOT installed — critical to fix"
    crm_text   = "Customer File: available" if has_crm else "Customer File: not provided"
    cat_text   = "Product Catalog: available" if has_catalog else "Product Catalog: none"
    stage_hint = get_stage_hint(funnel_stage, "tiktok")

    return f"""Platform: TikTok Ads — Remarketing Strategy
Product: {product}{usp_text}
Goal: {goal}
Funnel stage: {funnel_stage.upper()} — {stage_hint}
{pixel_text}
{crm_text}
{cat_text}

TikTok context: remarketing audiences are smaller than Meta/Google.
TikTok users came for entertainment — direct "you forgot your cart" messaging works poorly.
Best approach: subtle reminder through native content + Spark Ads.

Task — develop a remarketing strategy suited to the platform:

1. REMARKETING AUDIENCE ARCHITECTURE

   A) Website Custom Audiences (via TikTok Pixel):
   — All site visitors: 7 / 14 / 30 days
   — ViewContent: viewed product pages (14 days)
   — AddToCart: added to cart (7 days)
   — InitiateCheckout: started checkout (7 days) ← highest intent
   — Purchase: buyers (180 days) ← exclude from acquisition + upsell
   Minimum size for remarketing: ~1,000 users

   B) Engagement Custom Audiences (no Pixel needed):
   — Video Viewers: 2 sec / 6 sec / 25% / 50% / 75% / 100% (7 / 14 / 30 days)
   — Profile Visitors: visited brand's TikTok profile (7 / 30 days)
   — Liked / Commented / Shared: engaged with videos (7 / 14 days)
   — Hashtag Participants: used brand hashtag
   — LIVE Viewers: watched brand LIVE stream

   C) Customer File:
   — Upload email/phone from CRM
   — Segments: all customers, active, lapsed, VIP

   D) Lookalike based on:
   — Buyers (LAL 1–3%)
   — 100% Video Completers (most engaged signal)
   — Customer File VIP

2. SPARK ADS — PRIMARY REMARKETING TOOL ON TIKTOK

   Concept: boost organic post (own or creator's) as paid ad
   Best remarketing scenario:
   — Show MOFU audience a UGC video testimonial from a real buyer via Spark Ads
   — Show a demo video in native format to those who watched the previous video >50%
   — Boost a UGC post to users who engaged with the profile

   Setup: requires author account authorisation (Creator Marketplace or direct)

3. STRATEGY BY FUNNEL STAGE

   MOFU (visited site, watched video >50%):
   — Audience: Website Visitors 30d + Video 50% completers — minus buyers
   — Format: Spark Ads (testimonial/demo) or In-Feed with social proof
   — Message: not "you forgot" — "here's what other buyers say"
   — Tone: native, non-salesy
   — Frequency cap: ≤4 per 7 days

   BOFU (AddToCart / InitiateCheckout):
   — Audience: AddToCart + Checkout — minus Purchase (7 days)
   — Format: In-Feed with clear offer — urgency, discount, free shipping
   — Message: more direct than MOFU, still native-style
   — Bidding: Cost Cap with target CPA

   POST-PURCHASE (Upsell):
   — Audience: Purchase in last 30–90 days
   — Format: Spark Ads from creator + cross-sell product
   — Tone: "how to get the most out of it", "what pairs well with your purchase"

4. SHOPPING REMARKETING (if catalog available)
   — TikTok Shopping Ads: retarget ViewContent / AddToCart with dynamic product cards
   — Placements: feed, search, shopping centre
   — Requires: TikTok Shop or Product Catalog in Ads Manager

5. IMPORTANT TIKTOK CONSTRAINTS
   — Audiences are smaller than Meta: minimum 1,000 for Custom Audiences
   — Events API (CAPI) recommended for attribution accuracy (still maturing)
   — Over-attribution ~35–55%: use holdout tests for true lift measurement
   — TikTok excels at discovery → primary conversions;
     Meta is stronger for returning users

6. MEASUREMENT
   — Attribution window: 7-day click / 1-day view
   — Compare remarketing ROAS vs cold traffic — if ≥2× difference, remarketing is working
   — Incrementality test: 10% holdout (no ads), compare CVR with exposed group
"""
