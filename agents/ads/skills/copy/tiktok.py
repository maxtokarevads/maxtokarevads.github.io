from typing import Any, Dict


def build_tiktok_copy_prompt(payload: Dict[str, Any]) -> str:
    product      = payload.get("product", "product")
    usp          = payload.get("usp", "")
    audience     = payload.get("audience", {})
    goal         = payload.get("goal", "conversions")
    tone         = payload.get("tone", "native, authentic, energetic")
    duration     = payload.get("duration", "15–30 sec")
    funnel_stage = payload.get("funnel_stage", "tofu")

    audience_text = ", ".join(f"{k}: {v}" for k, v in audience.items() if v) or "broad audience"
    usp_text      = f"\nUSP: {usp}" if usp else ""

    stage_hint = {
        "tofu": "Awareness — do not sell; entertain/surprise, build recognition through content",
        "mofu": "Consideration — demonstrate product in action, social proof, education",
        "bofu": "Conversion — direct offer, urgency, discount, clear CTA",
    }.get(funnel_stage.lower(), "")

    return f"""Platform: TikTok Ads — Video Scripts & Ad Copy
Product: {product}{usp_text}
Goal: {goal}
Video duration: {duration}
Audience: {audience_text}
Funnel stage: {funnel_stage.upper()} — {stage_hint}
Tone: {tone}

HARD LIMITS — violations are not acceptable:
- Caption MUST be ≤100 characters. Rewrite if needed. Show count [XX chars].
- Scripts for 9:16 VERTICAL video ONLY. Do not suggest horizontal concepts.
- First 1–3 seconds = scroll-stop moment. This is not optional — it is a platform requirement.
- Style: native UGC. Polished brand-ad copy does not work on TikTok.

KEY RULE: the first 1–3 seconds are everything. No hook = scroll.

TIKTOK ADS LIMITS:
- Format: 9:16 vertical ONLY, 1080×1920 px
- In-Feed Ad caption: ≤100 characters
- CTA Button: preset (Shop Now, Learn More, Download, etc.)
- Sound ON by default — audio hook in first seconds is critical
- Subtitles: mandatory (use Auto Caption or burn-in)

GENERATE 3 VIDEO SCRIPTS

SCRIPT 1 — Hook: SCROLL-STOP VISUAL + QUESTION

[0–1 sec] OPENING (on-screen text / voiceover / action):
"..." ← max 5–7 words, creates curiosity

[1–3 sec] HOOK (retention):
"..." ← why the viewer must keep watching

[3–8 sec] PROBLEM / SITUATION:
"..." ← audience recognises themselves

[8–20 sec] SOLUTION / DEMO:
"..." ← product in action, no filler

[20 sec – last 3 sec] CTA:
"..." ← clear action

Caption (≤100 chars): "..."
CTA Button: [...]
Audio hook: "..." ← what the viewer hears in second 1
Opening subtitle: "..."

---

SCRIPT 2 — Hook: PROVOCATIVE STATEMENT / FACT

[0–1 sec] OPENING: "..."
[1–3 sec] HOOK: "..."
[3–8 sec] BUILD: "..."
[8–20 sec] DEMO / PROOF: "..."
[20 sec – end] CTA: "..."
Caption (≤100 chars): "..."
CTA Button: [...]
Audio hook: "..."

---

SCRIPT 3 — Hook: BEFORE / AFTER or TRANSFORMATION

[0–1 sec] OPENING (show the "before"): "..."
[1–3 sec] HOOK (intrigue): "..."
[3–8 sec] PROBLEM (before state): "..."
[8–20 sec] TRANSFORMATION (after): "..."
[20 sec – end] CTA: "..."
Caption (≤100 chars): "..."
CTA Button: [...]
Audio hook: "..."

SHOOTING GUIDELINES
- Camera: handheld phone, vertical, good natural lighting (not studio)
- Edit pace: cut every 1–2 seconds
- Text overlay: large font, max 6 words per frame
- Subtitles: mandatory, lower third of screen
- Music: trending sound from TikTok Commercial Music Library

SPARK ADS (if boosting organic content)
- Which organic post is suitable for boost: selection criteria
- Additional caption text for the Spark version

CHECKLIST
— First 3 sec: scroll-stop moment present? ✓/✗
— Caption ≤100 characters? ✓/✗
— Subtitles included? ✓/✗
— Audio hook in second 1? ✓/✗
— Native UGC style (not ad-like)? ✓/✗
— Clear CTA in last 3 seconds? ✓/✗
"""
