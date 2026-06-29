from typing import Any, Dict


def build_meta_copy_prompt(payload: Dict[str, Any]) -> str:
    product      = payload.get("product", "product")
    usp          = payload.get("usp", "")
    audience     = payload.get("audience", {})
    goal         = payload.get("goal", "conversions")
    format_type  = payload.get("format", "feed image/video")
    tone         = payload.get("tone", "persuasive, conversational")
    funnel_stage = payload.get("funnel_stage", "mofu")
    landing_page = payload.get("landing_page", "")

    audience_text = ", ".join(f"{k}: {v}" for k, v in audience.items() if v) or "broad audience"
    usp_text      = f"\nUSP: {usp}" if usp else ""
    lp_text       = f"\nLanding Page: {landing_page}" if landing_page else ""

    stage_hint = {
        "tofu": "Cold audience — focus on awareness, pain/intrigue, do not sell directly",
        "mofu": "Warm audience — demonstrate value, social proof, key benefits",
        "bofu": "Hot audience — offer, urgency, concrete reason to buy now",
    }.get(funnel_stage.lower(), "")

    return f"""Platform: Meta Ads (Facebook/Instagram) — Ad Copywriting
Product: {product}{usp_text}
Goal: {goal}
Format: {format_type}
Audience: {audience_text}
Funnel stage: {funnel_stage.upper()} — {stage_hint}
Tone: {tone}{lp_text}

HARD LIMITS — violations are not acceptable:
- Primary Text MUST be ≤125 visible characters (rest is hidden behind "See more"). Rewrite if needed.
- Headline MUST be ≤40 characters (Feed/Reels). Stories headline ≤27 chars — note format in output.
- Description MUST be ≤30 characters. Show count [XX chars] for both headline and description.
- Output only final copy that fits — never "can be shortened" placeholders.

META ADS CHARACTER LIMITS:
- Primary Text: ≤125 characters (truncated at "See more")
- Headline: ≤40 characters (Feed / Reels) | ≤27 characters (Stories)
- Description (below headline): ≤30 characters
- CTA Button: preset options (Shop Now, Learn More, Sign Up, Get Quote, etc.)

GENERATE 3 COMPLETE AD VARIANTS

Each variant uses a different HOOK approach:

VARIANT 1 — Hook: PAIN / PROBLEM
Primary Text [≤125 chars]:
"..."
Headline [≤40 chars Feed / ≤27 chars Stories]: "..."
Description [≤30 chars]: "..."
CTA Button: [...]
Hook strategy: open with a problem the audience recognises in themselves

VARIANT 2 — Hook: NUMBER / RESULT
Primary Text [≤125 chars]:
"..."
Headline [≤40 chars Feed / ≤27 chars Stories]: "..."
Description [≤30 chars]: "..."
CTA Button: [...]
Hook strategy: open with a specific number or outcome the audience wants

VARIANT 3 — Hook: QUESTION / INTRIGUE
Primary Text [≤125 chars]:
"..."
Headline [≤40 chars Feed / ≤27 chars Stories]: "..."
Description [≤30 chars]: "..."
CTA Button: [...]
Hook strategy: ask a question the audience wants to answer "yes" to

FOR VIDEO / REELS
For each variant, additionally provide:
- First 3 seconds text (voice/on-screen text): "..." ← most critical element
- Opening subtitle (≤8 words, large font): "..."
- Audio hook (what the viewer hears in second 1): "..."

CAROUSEL (if format = carousel)
- Card 1 (hook): headline ≤40 chars, description ≤30 chars
- Cards 2–5: sequential story / benefits revealed one per card
- Last card: CTA + offer

CHECKLIST
— Primary Text ≤125 characters? ✓/✗
— Headline ≤40 chars (Feed) / ≤27 chars (Stories)? ✓/✗
— Description ≤30 characters? ✓/✗
— Hook in first 3–5 words of Primary Text? ✓/✗
— CTA button matches campaign goal? ✓/✗
— Different hooks across all 3 variants? ✓/✗
"""
