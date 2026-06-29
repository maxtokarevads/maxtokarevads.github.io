"""
PageSpeed Insights API client.

Fetches real Core Web Vitals (field data) and performance scores for a URL.
API key is optional — without it, requests are rate-limited to ~25/day.
Set PAGESPEED_API_KEY in .env for higher quota.

Docs: https://developers.google.com/speed/docs/insights/v5/get-started
"""
import logging
import os
from typing import Any, Dict, Optional

import httpx

logger = logging.getLogger(__name__)

_BASE_URL  = "https://www.googleapis.com/pagespeedonline/v5/runPagespeed"
_TIMEOUT   = 30.0

# Core Web Vitals thresholds (2026)
_CWV_THRESHOLDS = {
    "lcp":  {"good": 2000,  "poor": 4000,  "unit": "ms", "name": "LCP (Largest Contentful Paint)"},
    "fcp":  {"good": 1800,  "poor": 3000,  "unit": "ms", "name": "FCP (First Contentful Paint)"},
    "cls":  {"good": 0.1,   "poor": 0.25,  "unit": "",   "name": "CLS (Cumulative Layout Shift)"},
    "inp":  {"good": 200,   "poor": 500,   "unit": "ms", "name": "INP (Interaction to Next Paint) — PRIMARY 2026"},
    "ttfb": {"good": 800,   "poor": 1800,  "unit": "ms", "name": "TTFB (Time to First Byte)"},
    "si":   {"good": 3400,  "poor": 5800,  "unit": "ms", "name": "Speed Index"},
}


def _score_cwv(metric: str, value: float) -> str:
    t = _CWV_THRESHOLDS.get(metric)
    if not t:
        return "unknown"
    if value <= t["good"]:
        return "GOOD ✅"
    if value <= t["poor"]:
        return "NEEDS IMPROVEMENT ⚠️"
    return "POOR ❌"


def fetch_pagespeed(url: str, strategy: str = "mobile") -> Dict[str, Any]:
    """
    Fetch PageSpeed Insights for a URL.

    Args:
        url: Full URL to test
        strategy: "mobile" (default) or "desktop"

    Returns:
        Dict with performance scores and CWV metrics.
        On error: {"error": "...", "url": url}
    """
    if not url.startswith(("http://", "https://")):
        url = "https://" + url

    api_key = os.getenv("PAGESPEED_API_KEY", "")
    params: Dict[str, str] = {
        "url":      url,
        "strategy": strategy,
        "category": "performance",
    }
    if api_key:
        params["key"] = api_key

    try:
        resp = httpx.get(_BASE_URL, params=params, timeout=_TIMEOUT)
        resp.raise_for_status()
        data = resp.json()
    except httpx.TimeoutException:
        return {"url": url, "error": "PageSpeed API timeout (30s)", "strategy": strategy}
    except httpx.HTTPStatusError as exc:
        return {"url": url, "error": f"PageSpeed API {exc.response.status_code}", "strategy": strategy}
    except Exception as exc:
        logger.warning("PageSpeed fetch failed for %s: %s", url, exc)
        return {"url": url, "error": str(exc), "strategy": strategy}

    result: Dict[str, Any] = {"url": url, "strategy": strategy}

    # Lighthouse performance score
    categories = data.get("lighthouseResult", {}).get("categories", {})
    perf = categories.get("performance", {})
    result["performance_score"] = round((perf.get("score") or 0) * 100)

    # Audits — individual metrics
    audits = data.get("lighthouseResult", {}).get("audits", {})

    def _ms(audit_key: str) -> Optional[float]:
        a = audits.get(audit_key, {})
        return a.get("numericValue")

    lcp_ms  = _ms("largest-contentful-paint")
    fcp_ms  = _ms("first-contentful-paint")
    cls_val = _ms("cumulative-layout-shift")
    inp_ms  = _ms("interaction-to-next-paint")
    ttfb_ms = _ms("server-response-time")
    si_ms   = _ms("speed-index")

    result["lcp_ms"]     = round(lcp_ms)  if lcp_ms  is not None else None
    result["fcp_ms"]     = round(fcp_ms)  if fcp_ms  is not None else None
    result["cls"]        = round(cls_val, 3) if cls_val is not None else None
    result["inp_ms"]     = round(inp_ms)  if inp_ms  is not None else None
    result["ttfb_ms"]    = round(ttfb_ms) if ttfb_ms is not None else None
    result["si_ms"]      = round(si_ms)   if si_ms   is not None else None

    # Status per metric
    if result["lcp_ms"]  is not None: result["lcp_status"]  = _score_cwv("lcp",  result["lcp_ms"])
    if result["cls"]     is not None: result["cls_status"]   = _score_cwv("cls",  result["cls"])
    if result["inp_ms"]  is not None: result["inp_status"]   = _score_cwv("inp",  result["inp_ms"])
    if result["fcp_ms"]  is not None: result["fcp_status"]   = _score_cwv("fcp",  result["fcp_ms"])
    if result["ttfb_ms"] is not None: result["ttfb_status"]  = _score_cwv("ttfb", result["ttfb_ms"])

    # Field data (Chrome UX Report) — more representative than lab
    crux = data.get("loadingExperience", {})
    metrics_crux = crux.get("metrics", {})

    def _crux_metric(key: str) -> Optional[Dict]:
        m = metrics_crux.get(key, {})
        if not m:
            return None
        return {
            "category":   m.get("category", ""),
            "percentile": m.get("percentile"),
        }

    result["field_data"] = {
        "lcp":  _crux_metric("LARGEST_CONTENTFUL_PAINT_MS"),
        "cls":  _crux_metric("CUMULATIVE_LAYOUT_SHIFT_SCORE"),
        "inp":  _crux_metric("INTERACTION_TO_NEXT_PAINT"),
        "fcp":  _crux_metric("FIRST_CONTENTFUL_PAINT_MS"),
        "ttfb": _crux_metric("EXPERIMENTAL_TIME_TO_FIRST_BYTE"),
    }
    result["field_data_available"] = bool(crux.get("metrics"))

    # Top opportunities (what to fix)
    opportunities = []
    for key, audit in audits.items():
        if audit.get("score") is not None and audit.get("score", 1) < 0.9:
            savings = audit.get("details", {}).get("overallSavingsMs", 0)
            if savings and savings > 100:
                opportunities.append({
                    "id":          key,
                    "title":       audit.get("title", key),
                    "savings_ms":  round(savings),
                    "description": audit.get("description", "")[:200],
                })
    result["top_opportunities"] = sorted(
        opportunities, key=lambda x: -x["savings_ms"]
    )[:5]

    logger.info(
        "PageSpeed %s %s: score=%d LCP=%s INP=%s CLS=%s",
        strategy, url, result["performance_score"],
        result.get("lcp_ms"), result.get("inp_ms"), result.get("cls"),
    )
    return result


def format_pagespeed_for_prompt(data: Dict[str, Any]) -> str:
    """Format PageSpeed data as a structured block for prompt injection."""
    if data.get("error"):
        return f"PageSpeed Insights: FAILED — {data['error']}"

    strategy = data.get("strategy", "mobile").upper()
    lines = [
        f"## Real Data — PageSpeed Insights ({strategy})",
        f"Performance Score: {data.get('performance_score')}/100 "
        f"({'✅ Good' if data.get('performance_score',0) >= 90 else '⚠️ Needs work' if data.get('performance_score',0) >= 50 else '❌ Poor'})",
        "",
        "### Core Web Vitals (Lab Data)",
    ]

    cwv_map = [
        ("LCP", "lcp_ms", "ms", "lcp_status", "PRIMARY — target <2,000ms"),
        ("INP", "inp_ms", "ms", "inp_status", "PRIMARY 2026 — target <200ms"),
        ("CLS", "cls",   "",   "cls_status", "target <0.10"),
        ("FCP", "fcp_ms", "ms", "fcp_status", "target <1,800ms"),
        ("TTFB","ttfb_ms","ms","ttfb_status","target <800ms"),
    ]
    for name, key, unit, status_key, note in cwv_map:
        val = data.get(key)
        status = data.get(status_key, "")
        if val is not None:
            lines.append(f"- {name}: {val}{unit} — {status} ({note})")
        else:
            lines.append(f"- {name}: not measured")

    # Field data
    fd = data.get("field_data", {})
    if data.get("field_data_available"):
        lines.append("\n### Field Data (Chrome UX Report — real users)")
        for metric, label in [("lcp","LCP"), ("inp","INP"), ("cls","CLS"), ("fcp","FCP")]:
            m = fd.get(metric)
            if m:
                cat = m.get("category", "")
                p75 = m.get("percentile")
                status = "✅" if cat == "FAST" else ("⚠️" if cat == "AVERAGE" else "❌")
                lines.append(f"- {label}: {status} {cat} (p75: {p75})")
    else:
        lines.append("\n⚠️ Field data (CrUX): not available for this URL")

    # Opportunities
    opps = data.get("top_opportunities", [])
    if opps:
        lines.append("\n### Top Opportunities to Improve Performance")
        for opp in opps:
            lines.append(f"- {opp['title']}: saves {opp['savings_ms']}ms")

    return "\n".join(lines)
