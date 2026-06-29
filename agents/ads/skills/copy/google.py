from typing import Any, Dict


def build_google_copy_prompt(payload: Dict[str, Any]) -> str:
    product       = payload.get("product", "product")
    usp           = payload.get("usp", "")
    audience      = payload.get("audience", {})
    goal          = payload.get("goal", "conversions")
    keywords      = payload.get("keywords", [])
    landing_page  = payload.get("landing_page", "")
    campaign_type = payload.get("campaign_type", "Search RSA")
    tone          = payload.get("tone", "persuasive, professional")

    audience_text = ", ".join(f"{k}: {v}" for k, v in audience.items() if v) or "broad audience"
    kw_text       = ", ".join(keywords[:10]) if keywords else "not specified"
    usp_text      = f"\nUSP: {usp}" if usp else ""
    lp_text       = f"\nLanding Page: {landing_page}" if landing_page else ""

    return f"""Platform: Google Ads — Ad Copywriting
Product: {product}{usp_text}
Goal: {goal}
Audience: {audience_text}
Keywords: {kw_text}
Campaign type: {campaign_type}
Tone: {tone}{lp_text}

HARD LIMITS — violations are not acceptable:
- Every headline MUST be ≤30 characters including spaces. Rewrite if it doesn't fit.
- Every description MUST be ≤90 characters including spaces.
- Count characters for each piece of copy before outputting. Show the actual count [XX chars].
- Do not output copy with a note "can be shortened" — output the final version that fits.

GOOGLE ADS RSA LIMITS:
- Headlines: 15 total, each ≤30 characters
- Descriptions: 4 total, each ≤90 characters
- Google shows 3 headlines + 2 descriptions simultaneously — each must be self-contained

GENERATE:

1. HEADLINES (15 total, strictly ≤30 characters each)
   Grouped by purpose:
   — Keyword headlines (3–4): direct keyword insertion or close variant
   — USP headlines (3–4): primary benefit, numbers, facts
   — CTA headlines (2–3): action verb + object
   — Urgency / social proof (2–3): "10,000+ customers", "Free", deadline
   — Brand / trust (1–2)
   Format: #1 "text" [XX chars]

2. DESCRIPTIONS (4 total, strictly ≤90 characters each)
   — Description 1: audience pain point → solution
   — Description 2: key benefit + CTA
   — Description 3: social proof / trust / guarantee
   — Description 4: special offer / urgency
   Format: #1 "text" [XX chars]

3. PINNING RECOMMENDATIONS
   — Which headline to pin to position 1 (brand / primary keyword)
   — Which to pin to position 3 (CTA)
   — Which descriptions to pin vs leave in rotation

4. AD EXTENSIONS (Assets)
   — 4 Sitelinks: text ≤25 chars + 2 descriptions ≤35 chars each
   — 4 Callouts: ≤25 chars each
   — 2 Structured snippets: header (type) + 3–5 values
   — Call extension (if relevant): call-to-action text

5. DYNAMIC KEYWORD INSERTION (if appropriate)
   — Examples of using {{Keyword:Default Text}} in headlines

6. CHECKLIST
   — All headlines ≤30 chars? ✓/✗
   — All descriptions ≤90 chars? ✓/✗
   — CTA in at least 2 headlines? ✓/✗
   — At least 1 keyword headline? ✓/✗
"""
