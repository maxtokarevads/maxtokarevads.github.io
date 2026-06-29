"""
Google Search Console API client.

Supports two auth methods:
1. Service Account JSON (recommended for production): set GSC_SERVICE_ACCOUNT_JSON env var
2. OAuth2 credentials file: set GSC_CREDENTIALS_FILE env var

Falls back gracefully if google-api-python-client is not installed.
Install: pip install google-api-python-client google-auth
"""
import json
import logging
import os
from datetime import date, timedelta
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

_SCOPES = ["https://www.googleapis.com/auth/webmasters.readonly"]


def _get_service():
    """Build GSC API service. Returns None if credentials not configured."""
    try:
        from googleapiclient.discovery import build
        from google.oauth2 import service_account
        from google.oauth2.credentials import Credentials
    except ImportError:
        logger.debug("google-api-python-client not installed. Run: pip install google-api-python-client google-auth")
        return None

    # Method 1: Service Account JSON
    sa_json = os.getenv("GSC_SERVICE_ACCOUNT_JSON", "")
    if sa_json:
        try:
            info = json.loads(sa_json) if sa_json.startswith("{") else json.load(open(sa_json))
            creds = service_account.Credentials.from_service_account_info(info, scopes=_SCOPES)
            return build("searchconsole", "v1", credentials=creds)
        except Exception as exc:
            logger.warning("GSC service account auth failed: %s", exc)

    # Method 2: OAuth2 credentials file (token.json)
    creds_file = os.getenv("GSC_CREDENTIALS_FILE", "gsc_token.json")
    if os.path.exists(creds_file):
        try:
            creds = Credentials.from_authorized_user_file(creds_file, _SCOPES)
            return build("searchconsole", "v1", credentials=creds)
        except Exception as exc:
            logger.warning("GSC OAuth2 auth failed: %s", exc)

    logger.debug("GSC: no credentials configured. Set GSC_SERVICE_ACCOUNT_JSON or GSC_CREDENTIALS_FILE.")
    return None


def get_search_analytics(
    site_url: str,
    days: int = 28,
    row_limit: int = 25,
    dimensions: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """
    Fetch Search Analytics data for a site.

    Args:
        site_url: verified property URL (e.g. "sc-domain:example.com" or "https://example.com/")
        days: lookback period in days (default: 28)
        row_limit: max rows to return (max: 25,000)
        dimensions: e.g. ["query", "page"] (default: ["query"])

    Returns:
        {
            "rows": [...],
            "period": "YYYY-MM-DD to YYYY-MM-DD",
            "site_url": site_url,
        }
        or {"error": "...", "site_url": site_url}
    """
    service = _get_service()
    if not service:
        return {"error": "GSC not configured", "site_url": site_url,
                "setup": "Set GSC_SERVICE_ACCOUNT_JSON or GSC_CREDENTIALS_FILE in .env"}

    end_date   = date.today() - timedelta(days=2)   # GSC has ~2 day lag
    start_date = end_date - timedelta(days=days)

    body = {
        "startDate":  start_date.isoformat(),
        "endDate":    end_date.isoformat(),
        "dimensions": dimensions or ["query"],
        "rowLimit":   min(row_limit, 25000),
        "dataState":  "all",
    }

    try:
        resp = (
            service.searchanalytics()
            .query(siteUrl=site_url, body=body)
            .execute()
        )
        rows = resp.get("rows", [])
        logger.info("GSC: %d rows for %s (%s → %s)", len(rows), site_url,
                    start_date.isoformat(), end_date.isoformat())
        return {
            "rows":     rows,
            "period":   f"{start_date.isoformat()} to {end_date.isoformat()}",
            "site_url": site_url,
            "row_count": len(rows),
        }
    except Exception as exc:
        logger.warning("GSC search analytics failed for %s: %s", site_url, exc)
        return {"error": str(exc), "site_url": site_url}


def get_top_queries(site_url: str, days: int = 28, limit: int = 20) -> Dict[str, Any]:
    """Return top queries by clicks with impressions, CTR, position."""
    result = get_search_analytics(
        site_url, days=days, row_limit=limit, dimensions=["query"]
    )
    if "error" in result:
        return result

    rows = sorted(result.get("rows", []), key=lambda r: -r.get("clicks", 0))[:limit]
    processed = []
    for row in rows:
        keys = row.get("keys", [])
        processed.append({
            "query":       keys[0] if keys else "",
            "clicks":      row.get("clicks", 0),
            "impressions": row.get("impressions", 0),
            "ctr":         round(row.get("ctr", 0) * 100, 2),
            "position":    round(row.get("position", 0), 1),
        })
    result["top_queries"] = processed
    return result


def get_top_pages(site_url: str, days: int = 28, limit: int = 20) -> Dict[str, Any]:
    """Return top pages by clicks."""
    result = get_search_analytics(
        site_url, days=days, row_limit=limit, dimensions=["page"]
    )
    if "error" in result:
        return result

    rows = sorted(result.get("rows", []), key=lambda r: -r.get("clicks", 0))[:limit]
    processed = []
    for row in rows:
        keys = row.get("keys", [])
        processed.append({
            "page":        keys[0] if keys else "",
            "clicks":      row.get("clicks", 0),
            "impressions": row.get("impressions", 0),
            "ctr":         round(row.get("ctr", 0) * 100, 2),
            "position":    round(row.get("position", 0), 1),
        })
    result["top_pages"] = processed
    return result


def get_overview(site_url: str, days: int = 28) -> Dict[str, Any]:
    """Return aggregated totals: clicks, impressions, avg CTR, avg position."""
    result = get_search_analytics(site_url, days=days, row_limit=1, dimensions=["date"])
    if "error" in result:
        return result

    # Re-fetch with date dimension for aggregate
    service = _get_service()
    if not service:
        return {"error": "GSC not configured"}

    end_date   = date.today() - timedelta(days=2)
    start_date = end_date - timedelta(days=days)

    try:
        resp = (
            service.searchanalytics()
            .query(siteUrl=site_url, body={
                "startDate":       start_date.isoformat(),
                "endDate":         end_date.isoformat(),
                "dimensions":      [],
                "rowLimit":        1,
                "aggregationType": "auto",
            })
            .execute()
        )
        rows = resp.get("rows", [{}])
        agg = rows[0] if rows else {}
        return {
            "period":      f"{start_date.isoformat()} to {end_date.isoformat()}",
            "clicks":      agg.get("clicks", 0),
            "impressions": agg.get("impressions", 0),
            "ctr":         round(agg.get("ctr", 0) * 100, 2),
            "position":    round(agg.get("position", 0), 1),
            "site_url":    site_url,
        }
    except Exception as exc:
        return {"error": str(exc), "site_url": site_url}


def format_gsc_for_prompt(queries: Dict, pages: Dict, overview: Dict) -> str:
    """Format GSC data as a structured block for prompt injection."""
    lines = ["## Real Data — Google Search Console"]

    if "error" in overview:
        lines.append(f"GSC Status: NOT CONNECTED — {overview['error']}")
        if "setup" in overview:
            lines.append(f"Setup: {overview['setup']}")
        return "\n".join(lines)

    lines += [
        f"Period: {overview.get('period')}",
        f"- Total Clicks: {overview.get('clicks', 0):,}",
        f"- Total Impressions: {overview.get('impressions', 0):,}",
        f"- Avg CTR: {overview.get('ctr', 0)}%",
        f"- Avg Position: {overview.get('position', 0)}",
        "",
        "### Top Queries (by clicks)",
    ]

    top_q = queries.get("top_queries", [])
    if top_q:
        lines.append("| Query | Clicks | Impressions | CTR | Position |")
        lines.append("|-------|--------|-------------|-----|----------|")
        for q in top_q[:15]:
            lines.append(
                f"| {q['query'][:50]} | {q['clicks']} | {q['impressions']} "
                f"| {q['ctr']}% | #{q['position']} |"
            )
    else:
        lines.append("No query data available")

    top_p = pages.get("top_pages", [])
    if top_p:
        lines += ["", "### Top Pages (by clicks)",
                  "| Page | Clicks | Impressions | CTR | Position |",
                  "|------|--------|-------------|-----|----------|"]
        for p in top_p[:10]:
            page_slug = p['page'].replace("https://", "")[:60]
            lines.append(
                f"| {page_slug} | {p['clicks']} | {p['impressions']} "
                f"| {p['ctr']}% | #{p['position']} |"
            )

    return "\n".join(lines)
