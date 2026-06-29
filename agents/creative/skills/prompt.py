from typing import Any, Dict, List


SUPPORTED_MODES = [
    "concept",   # creative concept: 3 variants, core message, visual direction (default)
    "copy",      # platform ad copy with char counts
    "script",    # video script: hook -> problem -> solution -> CTA
    "ugc_brief", # UGC creator brief: talking points, shot list, dos/don'ts
]

# ── Platform specs ─────────────────────────────────────────────────────────────

_PLATFORM_SPECS: Dict[str, str] = {
    "google": (
        "Google RSA: headlines ≤30 chars (up to 15), descriptions ≤90 chars (up to 4). "
        "Include keyword in at least 1 headline. CTA in last headline or first description. "
        "Aim for 'Excellent' Ad Strength. Avoid over-pinning."
    ),
    "meta": (
        "Meta Feed: primary text ≤125 chars, headline ≤40 chars, description ≤30 chars. "
        "Stories/Reels: primary text ≤72 chars visible. "
        "Video: 9:16 for Stories/Reels, 1:1 for feed. "
        "85% viewed without sound — captions mandatory. Hook in first 1-3 sec."
    ),
    "facebook": (
        "Meta Facebook Feed: primary text ≤125 chars, headline ≤40 chars. "
        "Hook in first 5 words. Sound-off assumption: add captions."
    ),
    "instagram": (
        "Instagram: caption ≤125 chars visible before 'more'. "
        "Reels: 9:16, sound-on by default. First 3 seconds critical for retention."
    ),
    "tiktok": (
        "TikTok In-Feed/TopView: caption ≤100 chars, CTA button ≤12 chars. "
        "Video: 9:16, 15-60 sec (sweet spot 21-34 sec). "
        "Hook Rate target >25% (first 3 sec). Sound ON by default — use trending audio. "
        "Native UGC (lo-fi) outperforms polished 2-4x in 2026. "
        "Text overlay: mandatory, ≤30% of screen."
    ),
    "youtube": (
        "YouTube In-Stream: skippable at 5 sec — state value prop before skip. "
        "Non-skippable: ≤15 sec. Skippable: 60-90 sec optimal. "
        "Bumper: ≤6 sec, non-skippable. "
        "Thumbnail: face + emotion + readable text = 50% of clicks."
    ),
    "linkedin": (
        "LinkedIn: primary text ≤150 chars before 'see more'. Headline ≤70 chars. "
        "Data-led hooks ('67% of B2B buyers...') outperform lifestyle. "
        "Thought leadership tone beats promotional."
    ),
}

_STAGE_CONTEXT: Dict[str, str] = {
    "tofu": "TOFU — cold audience. Activate curiosity or aspiration. Soft CTA ('Learn more').",
    "mofu": "MOFU — warm audience. Activate desire and FOMO. Medium CTA ('See how it works').",
    "bofu": "BOFU — hot audience. Activate urgency and confidence. Hard CTA ('Buy' / 'Start free').",
}


def _common_context(payload: Dict[str, Any]) -> str:
    product  = payload.get("product", "product")
    usp      = payload.get("usp", "")
    industry = payload.get("industry", "")
    audience = payload.get("audience", {})
    tone     = payload.get("tone", "persuasive, modern")
    platform = str(payload.get("platform", "")).lower().strip()
    stage    = str(payload.get("funnel_stage", "mofu")).lower()

    audience_parts = [f"{k}: {v}" for k, v in audience.items() if v]
    audience_text  = ", ".join(audience_parts) if audience_parts else "broad audience"

    lines = [f"Product: {product}", f"Tone: {tone}", f"Audience: {audience_text}"]
    if usp:      lines.append(f"USP: {usp}")
    if industry: lines.append(f"Industry: {industry}")

    spec = _PLATFORM_SPECS.get(platform, "")
    if platform and spec:
        lines.append(f"Platform: {platform.capitalize()}")
        lines.append(f"Platform specs: {spec}")
    elif platform:
        lines.append(f"Platform: {platform.capitalize()}")

    stage_hint = _STAGE_CONTEXT.get(stage, "")
    if stage_hint:
        lines.append(f"Funnel stage: {stage_hint}")

    return "\n".join(lines)


# ── Mode builders ──────────────────────────────────────────────────────────────

def build_concept_prompt(payload: Dict[str, Any]) -> str:
    """Creative concept: 3 variants, core message, visual direction."""
    fmt      = payload.get("format", "")
    fmt_list = payload.get("formats", [])
    formats_text = fmt or (", ".join(fmt_list) if fmt_list else "headline, description, CTA")

    return f"""Creative Brief
{_common_context(payload)}
Formats: {formats_text}

Develop a creative concept and ready-to-use materials:

1. CORE MESSAGE
   — Single key sentence: what should the person remember after seeing the ad
   — Emotional hook: which pain or desire we are activating
   — Rational proof: fact / number / social proof that supports the claim

2. THREE CREATIVE CONCEPTS (different hook approaches)
   For each:
   — Concept name
   — Idea in one sentence
   — Hook type: pain / result / story / provocation / comparison / social proof
   — Visual idea: what is shown in the frame / image
   — Why this approach fits the audience

3. READY COPY BY FORMAT
   For each format in: {formats_text}
   — Variant A: finished copy respecting platform limits
   — Variant B: alternative with a different hook

4. HEADLINES AND CTAS
   — 5 headline variants (question / number / verb / pain / benefit)
   — 3 CTA variants

5. VISUAL DIRECTION
   — Colour mood and palette
   — Content type: photo / video / illustration / UGC / screenshot
   — What appears in first 3 seconds (for video)
   — Text overlays: position and content

6. A/B TEST PAIRS
   — 2 test pairs: what changes and why
   — Win metric per pair (CTR / Hook Rate / CVR)
"""


def build_copy_prompt(payload: Dict[str, Any]) -> str:
    """Platform-specific ad copy with character counts."""
    platform = str(payload.get("platform", "")).lower().strip()
    count    = payload.get("variant_count", 5)
    keywords = payload.get("keywords", [])
    offer    = payload.get("offer", "")

    keyword_line = f"\nKeywords to include: {', '.join(keywords)}" if keywords else ""
    offer_line   = f"\nOffer/promotion: {offer}" if offer else ""
    spec         = _PLATFORM_SPECS.get(platform, "Check official platform docs for current limits.")

    return f"""Ad Copy Generation
{_common_context(payload)}{keyword_line}{offer_line}

Platform character limits:
{spec}

Generate {count} copy variants with different hook strategies.

For EACH variant provide:
— Hook type (e.g. urgency / social_proof / problem_solution / result / provocation)
— Headline: finished text + exact character count
— Primary text / description: finished text + exact character count
— CTA: button text or call to action
— Compliance check: confirm every element is within platform limits

Then:
— FLAG any variant where a field exceeds the platform limit (mark as NON-COMPLIANT)
— List the 2 variants you recommend testing first and why
— Suggest one A/B pair (change only one element between A and B)
"""


def build_script_prompt(payload: Dict[str, Any]) -> str:
    """Video script: hook -> problem -> solution -> CTA."""
    duration = payload.get("duration", 30)
    platform = str(payload.get("platform", "tiktok")).lower().strip()
    style    = payload.get("style", "ugc")  # ugc / talking_head / voiceover / animation
    count    = payload.get("script_count", 3)

    spec     = _PLATFORM_SPECS.get(platform, "")
    spec_line = f"\nPlatform: {platform.capitalize()}\nPlatform notes: {spec}" if spec else ""

    return f"""Video Script
{_common_context(payload)}{spec_line}
Duration: {duration} seconds
Style: {style} (ugc / talking_head / voiceover / animation)
Scripts to generate: {count}

For EACH script provide:

[SCRIPT LABEL & HOOK TYPE]
Hook type: [pain / result / pov / question / controversy / social_proof]

Timecoded script:
[0-3s]   HOOK: [exact words / action / text overlay]
[3-8s]   PROBLEM: [specific pain point in viewer's language]
[8-{duration-8}s] SOLUTION: [product demo or transformation reveal]
[{duration-10}-{duration-5}s] PROOF: [number / testimonial / result]
[{duration-5}-{duration}s] CTA: [single clear action]

Delivery notes:
— Tone of voice and energy level
— Key word to emphasise
— Visual / B-roll recommendation per section
— Text overlays: what and when

After all scripts:
— HOOK RATE PREDICTION: rank scripts 1-{count} by expected hook rate
— A/B test recommendation: which two to test first and what metric decides the winner
"""


def build_ugc_brief_prompt(payload: Dict[str, Any]) -> str:
    """UGC creator brief: talking points, shot list, dos/don'ts."""
    platform     = str(payload.get("platform", "tiktok")).lower().strip()
    creator_type = payload.get("creator_type", "customer")
    duration     = payload.get("duration", 30)
    num_briefs   = payload.get("brief_count", 2)

    spec      = _PLATFORM_SPECS.get(platform, "")
    spec_line = f"\nPlatform: {platform.capitalize()}\nPlatform notes: {spec}" if spec else ""

    return f"""UGC Creator Brief
{_common_context(payload)}{spec_line}
Creator type: {creator_type} (customer / nano-influencer / in-house talent)
Video duration: {duration} seconds
Number of brief variants: {num_briefs}

Generate {num_briefs} UGC briefs, each with a DIFFERENT hook approach.

For EACH brief:

BRIEF [#] — [Hook approach name]
Goal: [what this video needs to achieve]
Hook (first 3 sec): [exact words or action the creator should open with]

TALKING POINTS (3-5 bullets):
— [Exact claim or message — creator can phrase in their own words]
— [...]

REQUIRED SHOT LIST:
1. [Scene description + approximate duration]
2. [...]

DOS:
— [Tone, energy, specific actions to include]

DON'TS:
— [Claims to avoid, competitor mentions, banned words, format mistakes]

REFERENCE:
— Hook rate benchmark for {platform}: target >25% (first 3 sec watch-through)
— Example video style: [describe reference ad style, do not name specific brands]

After all briefs:
— Which brief to prioritise and why
— What data / metrics to collect from the creator for performance prediction
"""
