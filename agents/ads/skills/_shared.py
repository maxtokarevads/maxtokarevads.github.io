"""
Shared helpers reused across multiple skill modules:
- FUNNEL_STAGES: TOFU/MOFU/BOFU descriptions per platform
- get_stage_hint: returns stage context string for prompt builders
- parse_stage: normalises funnel_stage input
"""
from typing import Dict

# ─── Funnel stage descriptions ────────────────────────────────────────────────

_STAGE_DESCRIPTIONS: Dict[str, Dict[str, str]] = {
    "tofu": {
        "google":  "TOFU — cold audience; never visited the site, no prior intent signal.",
        "meta":    "TOFU — saw content or ads but has not visited the site.",
        "tiktok":  "TOFU — saw organic content or ads but has not visited the site.",
        "default": "TOFU — top of funnel, cold traffic, awareness stage.",
    },
    "mofu": {
        "google":  "MOFU — visited the site, engaged with content, not yet converted.",
        "meta":    "MOFU — visited the site or watched video 50%+, did not convert.",
        "tiktok":  "MOFU — visited the site or watched video 50%+, did not convert.",
        "default": "MOFU — middle of funnel, warm audience, consideration stage.",
    },
    "bofu": {
        "google":  "BOFU — high intent: product pages, cart, checkout abandonment.",
        "meta":    "BOFU — ViewContent / AddToCart / high purchase intent without buying.",
        "tiktok":  "BOFU — ViewContent / AddToCart / high purchase intent without buying.",
        "default": "BOFU — bottom of funnel, hot audience, purchase intent stage.",
    },
}


def parse_stage(raw: str) -> str:
    """Normalise raw funnel_stage input to tofu | mofu | bofu."""
    s = raw.strip().lower()
    if s in ("tofu", "top", "cold", "awareness"):
        return "tofu"
    if s in ("mofu", "mid", "middle", "warm", "consideration"):
        return "mofu"
    if s in ("bofu", "bot", "bottom", "hot", "purchase", "conversion"):
        return "bofu"
    return s  # pass through if already valid or unknown


def get_stage_hint(stage: str, platform: str = "default") -> str:
    """Return a human-readable stage description for the given platform."""
    s = parse_stage(stage)
    platform_key = platform.lower()
    if platform_key in ("facebook", "instagram"):
        platform_key = "meta"
    stage_map = _STAGE_DESCRIPTIONS.get(s, {})
    return stage_map.get(platform_key, stage_map.get("default", stage.upper()))
