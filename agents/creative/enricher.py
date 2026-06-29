"""
Creative Enricher — enriches payload with platform benchmarks, format intelligence,
and competitive context before prompt generation.

No external API calls required — enrichment is data-driven from embedded benchmark
tables and payload normalization logic. API-backed enrichment (TikTok Creative Center,
Meta Ad Library) can be added via the extension points below.

Numeric performance benchmarks (CTR, hook rate, CPM, ROAS) are imported from
agents.ads.skills.benchmarks — single source of truth for 2026 numbers.
Creative-specific data (char limits, best formats, sound rules) lives here.
"""
import logging
from typing import Any, Dict, Optional, Tuple

from agents.ads.skills.benchmarks import GOOGLE, META, TIKTOK

logger = logging.getLogger(__name__)

# ── Platform intelligence ──────────────────────────────────────────────────────
# Numeric values come from benchmarks.py (single source of truth).
# Creative-specific data (formats, char limits, production rules) lives here.

_PLATFORM_BENCHMARKS: Dict[str, Dict[str, Any]] = {
    "meta": {
        # Numeric values from benchmarks.py
        "hook_rate_target":         f"≥{META['hook_rate_good']}% (first 3 sec watch-through)",
        "video_completion_target":  f"≥{META['video_completion_good']}%",
        "ctr_benchmark":            f"{META['ctr_link_normal'][0]}–{META['ctr_link_normal'][1]}% Link CTR",
        "cpm_range":                f"${META['cpm_feed_normal'][0]}–{META['cpm_feed_normal'][1]} normal / >${META['cpm_feed_hot']} overheated",
        "creative_refresh_signal":  f"Frequency >{META['frequency_normal']} or CTR declining >2%/day",
        # Creative-specific data
        "best_formats_2026":        ["Reels 9:16", "Carousel (story-driven)", "UGC lo-fi"],
        "sound_off_rule":           "85% of Meta Feed is watched without sound — captions mandatory",
        "hook_window_sec":          3,
        "char_limits": {
            "headline":     40,   # Feed
            "primary_text": 125,
            "description":  30,
        },
    },
    "facebook": {
        "hook_rate_target":         "≥20%",
        "ctr_benchmark":            f"{META['ctr_link_bad']}–{META['ctr_link_normal'][1]}% Link CTR",
        "cpm_range":                f"${META['cpm_feed_normal'][0]}–15 normal",
        "creative_refresh_signal":  "Frequency >3.5",
        "best_formats_2026":        ["Single image (direct)", "Short video ≤15 sec", "Carousel"],
        "sound_off_rule":           "Sound off — add captions and text overlays",
        "hook_window_sec":          3,
        "char_limits": {
            "headline":     40,
            "primary_text": 125,
            "description":  30,
        },
    },
    "instagram": {
        "hook_rate_target":         "≥30%",
        "ctr_benchmark":            "1.0–1.5%",
        "best_formats_2026":        ["Reels 9:16 (sound-on)", "Stories", "Carousel exploration"],
        "sound_off_rule":           "Reels: sound-ON by default. Captions still recommended.",
        "hook_window_sec":          3,
        "char_limits": {
            "headline":     40,
            "primary_text": 125,
        },
    },
    "tiktok": {
        # Numeric values from benchmarks.py
        "hook_rate_target":         f"≥{TIKTOK['hook_rate_good']}% (critical — primary TikTok signal)",
        "video_completion_target":  f"≥{TIKTOK['video_completion_good']}%",
        "ctr_benchmark":            f"{TIKTOK['ctr_infeed_normal'][0]}–{TIKTOK['ctr_infeed_normal'][1]}% In-Feed CTR",
        "cpm_range":                f"${TIKTOK['cpm_infeed_normal'][0]}–{TIKTOK['cpm_infeed_normal'][1]} normal / >${TIKTOK['cpm_peak']} overheated",
        "creative_refresh_signal":  f"Performance drops after {TIKTOK['video_burnout_days']} days or Hook Rate <{TIKTOK['hook_rate_warn']}%",
        "over_attribution_note":    f"TikTok over-reports conversions {TIKTOK['over_attribution'][0]}–{TIKTOK['over_attribution'][1]}% — cross-validate with GA4",
        # Creative-specific data
        "best_formats_2026":        [
            "UGC lo-fi (outperforms polished 2-4x)",
            "Spark Ads (2.4× CTR vs In-Feed)",
            "Trending audio with text overlay",
        ],
        "sound_on_rule":            "TikTok is sound-ON by default — audio hook is critical",
        "hook_window_sec":          3,
        "char_limits": {
            "caption": 100,
            "cta":     12,
        },
    },
    "youtube": {
        "hook_rate_target":         "≥35% view-through at 5 sec (before skip)",
        "ctr_benchmark":            "2–5% (thumbnail + title)",
        "best_formats_2026":        ["Skippable In-Stream 60-90 sec", "Non-skippable ≤15 sec", "Bumper ≤6 sec"],
        "sound_on_rule":            "Sound ON — audio quality matters",
        "hook_window_sec":          5,
        "char_limits": {},
    },
    "google": {
        # Numeric values from benchmarks.py
        "ctr_benchmark":            f"≥{GOOGLE['ctr_search_good']}% Search CTR (good) / <{GOOGLE['ctr_search_bad']}% needs work",
        "best_formats_2026":        ["RSA (15 headlines, 4 descriptions)", "Responsive Display"],
        "char_limits": {
            "headline":     30,
            "description":  90,
        },
    },
    "linkedin": {
        "ctr_benchmark":            "0.4–0.6% (B2B average)",
        "best_formats_2026":        ["Thought leadership single image", "Video ≤30 sec", "Document ads"],
        "hook_window_sec":          3,
        "char_limits": {
            "headline":     70,
            "primary_text": 150,
        },
    },
}

_INDUSTRY_CREATIVE_SIGNALS: Dict[str, str] = {
    "saas":      "SaaS creative: lead with outcome (time/money saved), not features. Social proof = logos + usage numbers.",
    "ecom":      "E-commerce: product in use > product alone. Lifestyle + urgency (limited stock/offer) outperforms.",
    "leadgen":   "Lead gen: lead magnet hooks ('Free audit', 'See your score') outperform generic CTAs by 2-4x.",
    "app":       "App: screen recordings with finger taps outperform polished mockups. Show the 'aha moment' in first 3 sec.",
    "local":     "Local: faces of real staff + location signals outperform stock imagery. Google Business Profile imagery style.",
    "b2b":       "B2B: data-led hooks ('67% of sales teams report X') outperform lifestyle. LinkedIn-native tone.",
    "finance":   "Finance: trust signals first (regulation badges, years in business). Pain-led ('losing money on X?') over aspirational.",
    "health":    "Health: before/after (where allowed), testimonials from relatable people, avoid overclaiming.",
    "education": "Education: outcome-led ('get certified in 4 weeks'), instructor credibility, free trial hooks.",
}

_FUNNEL_CREATIVE_GUIDE: Dict[str, str] = {
    "tofu": (
        "TOFU creative: pattern interrupt, curiosity, pain activation. DO NOT show price or CTA 'Buy Now'. "
        "Hook = problem recognition, not solution. Soft CTA: 'Learn more', 'See how'."
    ),
    "mofu": (
        "MOFU creative: demonstrate value, social proof, comparison. Show product in context. "
        "Hook = desire activation. CTA: 'See how it works', 'Get the guide', 'Watch demo'."
    ),
    "bofu": (
        "BOFU creative: urgency, specificity, risk reversal (guarantee, free trial). "
        "Hook = why NOW. CTA: 'Start free', 'Buy now', 'Get quote'. Remove all friction."
    ),
}

_FORMAT_PRODUCTION_NOTES: Dict[str, str] = {
    "ugc":          "Film vertically 9:16. Natural lighting. No brand logo in first 3 sec. Authentic imperfections OK.",
    "talking_head": "Eye contact with camera = direct eye contact with viewer. Subtitles mandatory. Energy high.",
    "voiceover":    "Script at 130-150 wpm. Pause after hook (0.5 sec silence = emphasis). Mix B-roll.",
    "animation":    "Text appears ON the key spoken word, not before. Brand color consistency. Minimal text per frame.",
    "static_image": "Rule of thirds for product placement. Human face in frame = 38% higher CTR. Single CTA.",
    "carousel":     "Card 1 = hook (problem or intrigue). Cards 2-N = reveal/benefit. Last card = CTA.",
}

# ── Extension points for API-backed enrichment ─────────────────────────────────

def _fetch_tiktok_creative_center(product: str, industry: str) -> Optional[str]:
    """Stub: fetch trending hooks and formats from TikTok Creative Center.
    Requires TIKTOK_ACCESS_TOKEN env variable. Returns None if unavailable."""
    # TODO: implement with TikTok Marketing API v2
    # GET /open_api/v1.3/creative/template/list/ with filters
    return None


def _fetch_meta_ad_library(product: str, competitors: str) -> Optional[str]:
    """Stub: fetch competitor creative intelligence from Meta Ad Library.
    Requires META_ACCESS_TOKEN env variable. Returns None if unavailable."""
    # TODO: implement with Meta Ad Library API
    # GET /ads_archive with search_terms=product, ad_type=ALL
    return None


# ── Core enrichment ────────────────────────────────────────────────────────────

def enrich_creative_payload(
    mode: str,
    payload: Dict[str, Any],
) -> Tuple[Dict[str, Any], str]:
    """Enrich payload with platform intelligence and return (enriched_payload, data_block).

    data_block is a formatted string prepended to the prompt so the LLM has
    concrete benchmarks and signals without needing to recall them from training data.
    """
    platform  = str(payload.get("platform", "")).lower().strip()
    industry  = str(payload.get("industry", "")).lower().strip()
    funnel    = str(payload.get("funnel_stage", "mofu")).lower().strip()
    fmt       = str(payload.get("format", payload.get("style", ""))).lower().strip()
    competitors = payload.get("competitors", "")

    sections: list[str] = []

    # ── Platform intelligence ────────────────────────────────────────────────
    platform_data = _PLATFORM_BENCHMARKS.get(platform, {})
    if platform_data:
        lines = [f"## Platform Intelligence — {platform.capitalize()}"]

        if "hook_rate_target" in platform_data:
            lines.append(f"Hook Rate target: {platform_data['hook_rate_target']}")
        if "video_completion_target" in platform_data:
            lines.append(f"Video Completion target: {platform_data['video_completion_target']}")
        if "ctr_benchmark" in platform_data:
            lines.append(f"CTR benchmark: {platform_data['ctr_benchmark']}")
        if "cpm_range" in platform_data:
            lines.append(f"CPM range: {platform_data['cpm_range']}")
        if "creative_refresh_signal" in platform_data:
            lines.append(f"Refresh signal: {platform_data['creative_refresh_signal']}")
        if "sound_off_rule" in platform_data:
            lines.append(f"Sound: {platform_data['sound_off_rule']}")
        if "sound_on_rule" in platform_data:
            lines.append(f"Sound: {platform_data['sound_on_rule']}")
        if "over_attribution_note" in platform_data:
            lines.append(f"Attribution note: {platform_data['over_attribution_note']}")
        if "best_formats_2026" in platform_data:
            lines.append(f"Best formats 2026: {', '.join(platform_data['best_formats_2026'])}")

        char_limits = platform_data.get("char_limits", {})
        if char_limits:
            limit_parts = [f"{k} ≤{v} chars" for k, v in char_limits.items()]
            lines.append(f"Character limits: {', '.join(limit_parts)}")

        sections.append("\n".join(lines))

        # Inject char_limits into payload so prompt builders can reference them
        if char_limits and "platform_char_limits" not in payload:
            payload = dict(payload)
            payload["platform_char_limits"] = char_limits

    # ── Industry creative signals ────────────────────────────────────────────
    industry_signal = ""
    for key, signal in _INDUSTRY_CREATIVE_SIGNALS.items():
        if key in industry:
            industry_signal = signal
            break
    if industry_signal:
        sections.append(f"## Industry Creative Signal\n{industry_signal}")

    # ── Funnel creative guide ────────────────────────────────────────────────
    funnel_guide = _FUNNEL_CREATIVE_GUIDE.get(funnel, "")
    if funnel_guide:
        sections.append(f"## Funnel Stage Guidance\n{funnel_guide}")

    # ── Format production notes ──────────────────────────────────────────────
    format_note = ""
    for key, note in _FORMAT_PRODUCTION_NOTES.items():
        if key in fmt:
            format_note = note
            break
    if format_note:
        sections.append(f"## Format Production Notes\n{format_note}")

    # ── API-backed enrichment (non-blocking stubs) ───────────────────────────
    product = payload.get("product", "")
    tiktok_trends = None
    meta_intel    = None

    if platform == "tiktok" and mode in ("script", "ugc_brief", "concept"):
        tiktok_trends = _fetch_tiktok_creative_center(product, industry)
    if competitors and mode in ("concept", "copy"):
        meta_intel = _fetch_meta_ad_library(product, competitors)

    if tiktok_trends:
        sections.append(f"## TikTok Creative Center Trends\n{tiktok_trends}")
    if meta_intel:
        sections.append(f"## Meta Ad Library Competitive Intelligence\n{meta_intel}")

    data_block = ""
    if sections:
        data_block = "\n\n".join(sections) + "\n\n---\n\n"

    return payload, data_block
