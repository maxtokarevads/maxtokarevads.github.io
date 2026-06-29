"""
SEO Payload Enricher — fetches real data and injects into agent payload.

Called by SEOAgent before building the prompt.
Falls back gracefully when APIs are unavailable.
"""
import logging
import os
from typing import Any, Dict, Tuple

logger = logging.getLogger(__name__)

# Modes that trigger URL inspection + PageSpeed
_URL_MODES    = {"technical", "content", "schema", "sxo", "audit"}
# Modes that use GSC data
_GSC_MODES    = {"seo", "technical", "cluster", "audit", "drift"}
# Modes where we run PageSpeed
_PSPEED_MODES = {"technical", "audit"}


def enrich_payload(mode: str, payload: Dict[str, Any]) -> Tuple[Dict[str, Any], str]:
    """
    Fetch real data for the given mode and inject it into payload.

    Returns:
        (enriched_payload, real_data_block)
        real_data_block is a Markdown string prepended to the prompt.
    """
    skip_enrichment = os.getenv("SEO_SKIP_ENRICHMENT", "false").lower() == "true"
    if skip_enrichment:
        return payload, ""

    url     = payload.get("url", payload.get("site", ""))
    site    = payload.get("site", url)
    blocks  = []

    # ── URL Inspection ────────────────────────────────────────────────────────
    if mode in _URL_MODES and url:
        try:
            from integrations.url_inspector import inspect_url, format_inspection_for_prompt
            logger.info("SEO enricher: inspecting URL %s", url)
            inspection = inspect_url(url)
            payload["_url_inspection"] = inspection
            blocks.append(format_inspection_for_prompt(inspection))
        except ImportError:
            logger.warning("URL inspection skipped: url_inspector not available")
            blocks.append(
                "## URL Inspection\n"
                "Status: NOT AVAILABLE — url_inspector integration not installed.\n"
                "Note: Indexability and crawlability data will be based on your input only."
            )
        except Exception as exc:
            logger.warning("URL inspection failed: %s", exc)
            blocks.append(
                f"## URL Inspection\n"
                f"Status: FAILED — {exc}\n"
                f"Note: Indexability check skipped. Verify manually: Google Search Console → URL Inspection."
            )

    # ── PageSpeed Insights ────────────────────────────────────────────────────
    if mode in _PSPEED_MODES and url:
        pspeed_key = os.getenv("PAGESPEED_API_KEY", "")
        if not pspeed_key:
            logger.warning("PageSpeed skipped: PAGESPEED_API_KEY not set")
            blocks.append(
                "## PageSpeed Insights\n"
                "Status: NOT CONFIGURED — PAGESPEED_API_KEY is missing from .env\n"
                "Note: Core Web Vitals data unavailable. Set the key and re-run for real LCP/INP/CLS scores."
            )
        else:
            try:
                from integrations.pagespeed_client import fetch_pagespeed, format_pagespeed_for_prompt
                logger.info("SEO enricher: fetching PageSpeed for %s", url)
                mobile  = fetch_pagespeed(url, strategy="mobile")
                desktop = fetch_pagespeed(url, strategy="desktop")
                payload["_pagespeed_mobile"]  = mobile
                payload["_pagespeed_desktop"] = desktop
                blocks.append(format_pagespeed_for_prompt(mobile))
                if not desktop.get("error"):
                    blocks.append(f"\n**Desktop score:** {desktop.get('performance_score')}/100 "
                                   f"(LCP: {desktop.get('lcp_ms')}ms, INP: {desktop.get('inp_ms')}ms)")
                elif desktop.get("error"):
                    logger.warning("PageSpeed desktop failed: %s", desktop.get("error"))
            except Exception as exc:
                logger.warning("PageSpeed failed: %s", exc)
                blocks.append(
                    f"## PageSpeed Insights\n"
                    f"Status: FAILED — {exc}\n"
                    f"Note: Core Web Vitals data unavailable. Check PAGESPEED_API_KEY validity."
                )

    # ── Google Search Console ─────────────────────────────────────────────────
    if mode in _GSC_MODES and site:
        # Normalize site URL to sc-domain format if needed
        gsc_site = _normalize_gsc_site(site)
        gsc_creds = os.getenv("GSC_CREDENTIALS_FILE", "")
        if not gsc_creds:
            logger.warning("GSC skipped: GSC_CREDENTIALS_FILE not set")
            blocks.append(
                "## Google Search Console\n"
                "Status: NOT CONFIGURED — GSC_CREDENTIALS_FILE is missing from .env\n"
                "Note: Impressions, CTR, and ranking data unavailable. Run setup_gsc_oauth.py to connect."
            )
        else:
            try:
                from integrations.gsc_client import (
                    get_top_queries, get_top_pages, get_overview,
                    format_gsc_for_prompt,
                )
                logger.info("SEO enricher: fetching GSC data for %s", gsc_site)
                overview = get_overview(gsc_site)
                if "error" not in overview:
                    queries  = get_top_queries(gsc_site, limit=20)
                    pages    = get_top_pages(gsc_site, limit=10)
                    payload["_gsc_overview"] = overview
                    payload["_gsc_queries"]  = queries
                    payload["_gsc_pages"]    = pages
                    blocks.append(format_gsc_for_prompt(queries, pages, overview))
                else:
                    # GSC connected but this property not verified — still show status
                    blocks.append(
                        f"## Google Search Console\n"
                        f"Status: NOT CONNECTED — {overview.get('error')}\n"
                        f"Note: Property '{gsc_site}' may not be verified in GSC. "
                        f"Connect GSC for real impressions, CTR, and ranking data."
                    )
            except Exception as exc:
                logger.warning("GSC data failed: %s", exc)
                blocks.append(
                    f"## Google Search Console\n"
                    f"Status: FAILED — {exc}\n"
                    f"Note: GSC data unavailable. Check credentials file and property permissions."
                )

    real_data_block = ""
    if blocks:
        real_data_block = (
            "# REAL DATA (fetched live — use this instead of assumptions)\n\n"
            + "\n\n---\n\n".join(blocks)
            + "\n\n---\n\n"
        )

    return payload, real_data_block


def _normalize_gsc_site(site: str) -> str:
    """
    Return GSC property URL. Tries URL-prefix format first (most common),
    falls back to sc-domain format.
    GSC has two property types:
      - URL prefix: https://example.com/  (must match exactly incl. trailing slash)
      - Domain:     sc-domain:example.com
    """
    site = site.strip()
    if site.startswith("sc-domain:"):
        return site
    # Ensure https:// and trailing slash (URL-prefix format)
    if not site.startswith("http"):
        site = "https://" + site
    if not site.endswith("/"):
        site = site + "/"
    return site
