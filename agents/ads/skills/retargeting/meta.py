from typing import Any, Dict
from .._shared import get_stage_hint


def build_meta_retargeting_prompt(payload: Dict[str, Any]) -> str:
    product      = payload.get("product", "product")
    usp          = payload.get("usp", "")
    funnel_stage = payload.get("funnel_stage", "mofu")
    goal         = payload.get("goal", "conversions")
    has_pixel    = payload.get("has_pixel", True)
    has_crm      = payload.get("has_crm_list", False)
    catalog      = payload.get("has_catalog", False)

    usp_text     = f"\nUSP: {usp}" if usp else ""
    pixel_text   = "Meta Pixel: installed" if has_pixel else "Meta Pixel: NOT installed — fix immediately"
    crm_text     = "Customer List: available" if has_crm else "Customer List: not provided"
    catalog_text = "Product Catalog: available (DPA possible)" if catalog else "Product Catalog: none"
    stage_hint   = get_stage_hint(funnel_stage, "meta")

    return f"""Platform: Meta Ads (Facebook/Instagram) — Remarketing Strategy
Product: {product}{usp_text}
Goal: {goal}
Funnel stage: {funnel_stage.upper()} — {stage_hint}
{pixel_text}
{crm_text}
{catalog_text}

Task — develop a complete remarketing strategy using Pixel audiences:

1. PIXEL AUDIENCE ARCHITECTURE (Custom Audiences)

   A) Website Custom Audiences (requires Meta Pixel):
   — All site visitors: 30 / 60 / 90 days
   — Key page visitors (product pages, pricing): 14 / 30 days
   — ViewContent: viewed products (30 days)
   — AddToCart: added to cart (14 days) ← warm
   — InitiateCheckout: started checkout (7 days) ← hot
   — Purchase: buyers (180 days) ← upsell / exclusion
   Exclusion from cold campaigns: all buyers in last 30 days

   B) Engagement Custom Audiences:
   — Video Views: 25% / 50% / 75% / 95% completion (30 / 90 days)
   — Page Engagement: interacted with Facebook/Instagram page (30 / 60 days)
   — Lead Form: opened / submitted form (30 days)
   — Instagram Profile: visited profile / saved posts

   C) Customer List:
   — Upload email/phone from CRM (minimum 1,000 records for matching)
   — Segments: all customers, active (<90 days), lapsed (>90 days), VIP (LTV >X)

   D) Lookalike (from best-performing audiences):
   — LAL 1% from buyers (most precise)
   — LAL 1–3% from AddToCart (more volume, slightly less precise)
   — LAL 1% from Customer List VIP segment

2. DYNAMIC PRODUCT ADS (DPA) — if catalog available
   — Broad Audience DPA: show products similar to what the user viewed across the web
   — Retargeting DPA: show the exact product the user viewed or added to cart
   — Cross-sell DPA: show complementary products to recent buyers
   — Requirements: Meta Product Catalog + Pixel with ViewContent, AddToCart, Purchase events

3. STRATEGY BY FUNNEL STAGE

   MOFU (visited site, browsed):
   — Audience: All Website Visitors 30d — minus buyers
   — Format: Carousel (top 5 products) or Video (demo/testimonial)
   — Message: social proof, benefits, "take another look"
   — Bidding: Cost Cap or Lowest Cost
   — Frequency cap: ≤5 per 7 days

   BOFU (cart / checkout):
   — Audience: AddToCart + InitiateCheckout — minus Purchase (7–14 days)
   — Format: Single Image/Video with dynamic product (DPA) or manual offer
   — Message: urgency ("Item waiting in your cart"), discount, free shipping
   — Bidding: Cost Cap with strict CPA limit
   — Frequency cap: ≤7 per 7 days (hot audience tolerates higher frequency)

   POST-PURCHASE (Upsell / Cross-sell):
   — Audience: Purchase in last 30–90 days
   — Format: DPA cross-sell or manual ad with related product
   — Message: "You might also love...", loyalty bonus for repeat purchase

4. CAMPAIGN STRUCTURE
   — Separate campaign per temperature: MOFU / BOFU / Post-purchase
   — Budget: CBO or ABO with priority on BOFU (highest ROAS)
   — Objective: Sales / Catalog Sales (DPA) / Traffic (for awareness retargeting)

5. AD COPY BY SEGMENT
   — AddToCart reminder: "You left something behind..." + product + urgency
   — MOFU reminder: real buyer testimonial + CTA
   — Lapsed customers: "We've missed you" + special offer

6. MEASUREMENT
   — Attribution: 7-day click / 1-day view (Meta standard)
   — Compare remarketing ROAS vs cold traffic — remarketing is typically 3–5× higher
   — Audience overlap: use Audience Overlap Tool for exclusions
"""
