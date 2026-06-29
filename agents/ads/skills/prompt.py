from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional

from .plan.google    import build_google_prompt
from .plan.meta      import build_meta_prompt
from .plan.tiktok    import build_tiktok_prompt

from .analyze.google  import build_google_analyze_prompt
from .analyze.meta    import build_meta_analyze_prompt
from .analyze.tiktok  import build_tiktok_analyze_prompt

from .copy.google    import build_google_copy_prompt
from .copy.meta      import build_meta_copy_prompt
from .copy.tiktok    import build_tiktok_copy_prompt

from .retargeting.google  import build_google_retargeting_prompt
from .retargeting.meta    import build_meta_retargeting_prompt
from .retargeting.tiktok  import build_tiktok_retargeting_prompt

from .ab_test.google  import build_google_abtest_prompt
from .ab_test.meta    import build_meta_abtest_prompt
from .ab_test.tiktok  import build_tiktok_abtest_prompt

from .budget.allocator     import build_budget_prompt
from .canon.audit          import build_google_audit_prompt
from .canon.meta_audit     import build_meta_audit_prompt
from .canon.tiktok_audit   import build_tiktok_audit_prompt
from .landing.audit        import build_landing_audit_prompt
from .research.google      import build_google_research_prompt
from .research.meta        import build_meta_research_prompt
from .research.tiktok      import build_tiktok_research_prompt
from .forecast.planner     import build_forecast_prompt


# platform → { mode → builder }
_ROUTER: Dict[str, Dict[str, Callable]] = {
    "google": {
        "plan":        build_google_prompt,
        "analyze":     build_google_analyze_prompt,
        "audit":       build_google_audit_prompt,
        "copy":        build_google_copy_prompt,
        "retargeting": build_google_retargeting_prompt,
        "ab_test":     build_google_abtest_prompt,
        "research":    build_google_research_prompt,
    },
    "meta": {
        "plan":        build_meta_prompt,
        "analyze":     build_meta_analyze_prompt,
        "audit":       build_meta_audit_prompt,
        "copy":        build_meta_copy_prompt,
        "retargeting": build_meta_retargeting_prompt,
        "ab_test":     build_meta_abtest_prompt,
        "research":    build_meta_research_prompt,
    },
    "tiktok": {
        "plan":        build_tiktok_prompt,
        "analyze":     build_tiktok_analyze_prompt,
        "audit":       build_tiktok_audit_prompt,
        "copy":        build_tiktok_copy_prompt,
        "retargeting": build_tiktok_retargeting_prompt,
        "ab_test":     build_tiktok_abtest_prompt,
        "research":    build_tiktok_research_prompt,
    },
}

# Platform aliases
_PLATFORM_ALIASES: Dict[str, str] = {
    "google_ads": "google",
    "facebook":   "meta",
    "instagram":  "meta",
    "fb":         "meta",
}

SUPPORTED_PLATFORMS = sorted(_ROUTER.keys())
SUPPORTED_MODES     = [
    "plan", "analyze", "audit", "copy",
    "retargeting", "ab_test", "budget",
    "research", "landing", "forecast",
]


def _resolve_platform(raw: str) -> Optional[str]:
    p = raw.lower().strip()
    return _PLATFORM_ALIASES.get(p, p) if p else None


@dataclass
class AdsRequest:
    """
    Typed, normalised payload for AdsAgent.run().

    Call AdsRequest.from_dict(raw_payload) to get a normalised object,
    then .to_dict() to pass back to build_ads_prompt (merging with the
    original payload preserves unknown keys the Canon audit needs).
    """
    # ── Core ──────────────────────────────────────────────────────────────────
    mode:     str   = "plan"
    platform: str   = ""
    product:  str   = ""
    goal:     str   = "conversions"
    budget:   float = 0.0
    market:   str   = ""
    context:  str   = ""

    # ── Canon audit ──────────────────────────────────────────────────────────
    command:      str = ""        # /audit /weekly /monthly …
    project:      str = ""        # client/project name
    account_type: str = ""        # ecom | lead-gen | app
    date_range:   str = ""        # "last 30 days"
    notes:        str = ""

    # ── Mode-specific optional ────────────────────────────────────────────────
    metrics:             Dict[str, Any] = field(default_factory=dict)
    inputs:              Dict[str, Any] = field(default_factory=dict)
    campaign_type:       str  = ""
    funnel_stage:        str  = "mofu"
    what_to_test:        str  = ""
    current_performance: Dict[str, Any] = field(default_factory=dict)
    platforms:           List[str]      = field(default_factory=list)
    seed_keywords:       str  = ""
    competitors:         str  = ""
    url:                 str  = ""
    device:              str  = "mobile"
    months:              int  = 3

    def __post_init__(self) -> None:
        self.mode = (self.mode or "plan").lower().strip()
        if self.platform:
            self.platform = _resolve_platform(self.platform) or self.platform

    def to_dict(self) -> Dict[str, Any]:
        """Return only non-empty fields so callers can do {**raw, **req.to_dict()}."""
        result = {}
        for k, v in self.__dict__.items():
            if v or v == 0:
                result[k] = v
        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AdsRequest":
        allowed = {f.name for f in cls.__dataclass_fields__.values()}  # type: ignore[attr-defined]
        return cls(**{k: v for k, v in data.items() if k in allowed})


def build_ads_prompt(payload: Dict[str, Any]) -> str:
    mode     = str(payload.get("mode", "plan")).lower().strip()
    platform = _resolve_platform(str(payload.get("platform", "")))

    # Cross-platform modes — no specific platform required
    if mode == "budget":
        return build_budget_prompt(payload)

    if mode == "forecast":
        return build_forecast_prompt(payload)

    if mode == "landing":
        return build_landing_audit_prompt(payload)

    # Platform-specific modes
    if not platform or platform not in _ROUTER:
        known_p = ", ".join(SUPPORTED_PLATFORMS)
        known_m = ", ".join(SUPPORTED_MODES)
        product = payload.get("product", "product")
        budget  = payload.get("budget", "not specified")
        return (
            f"Product: {product}\nBudget: {budget}\n"
            f"Platform: '{platform or 'not specified'}' — not supported.\n"
            f"Supported platforms: {known_p}\n"
            f"Supported modes: {known_m}\n\n"
            "Recommend an ad platform and provide a launch strategy."
        )

    mode_map = _ROUTER[platform]

    if mode not in mode_map:
        supported = sorted(mode_map.keys())
        return (
            f"ERROR: mode '{mode}' is not supported for platform '{platform}'.\n"
            f"Supported modes for {platform}: {', '.join(supported)}\n"
            f"All supported modes: {', '.join(SUPPORTED_MODES)}"
        )

    return mode_map[mode](payload)
