"""
TikTok Ads connector — pulls live account data for Canon audits via TikTok Business API v1.3.

Required .env vars:
    TIKTOK_ACCESS_TOKEN   — access token from TikTok Marketing API app
    TIKTOK_ADVERTISER_ID  — advertiser ID (numeric string)

Setup:
    1. Create a TikTok for Business app at business.tiktok.com/portal
    2. Apply for Marketing API access
    3. Generate access token with REPORTING + CAMPAIGN_MANAGEMENT scopes
    4. Find your Advertiser ID in TikTok Ads Manager → Account Info
"""
import logging
import os
import random
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import requests
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

_API_BASE   = "https://business-api.tiktok.com/open_api/v1.3"
_RETRY_MAX  = 3
_RETRY_BASE = 1.0
_RETRY_CAP  = 30.0


# ─── Auth helpers ──────────────────────────────────────────────────────────────

def _token() -> str:
    t = os.getenv("TIKTOK_ACCESS_TOKEN", "")
    if not t:
        raise ValueError("TIKTOK_ACCESS_TOKEN not set in .env")
    return t


def _advertiser_id(override: str = "") -> str:
    aid = override or os.getenv("TIKTOK_ADVERTISER_ID", "")
    if not aid:
        raise ValueError("TIKTOK_ADVERTISER_ID not set in .env")
    return str(aid)


def is_configured() -> bool:
    return bool(os.getenv("TIKTOK_ACCESS_TOKEN") and os.getenv("TIKTOK_ADVERTISER_ID"))


# ─── HTTP helpers ──────────────────────────────────────────────────────────────

def _post(endpoint: str, body: dict) -> dict:
    """POST with exponential backoff on 429 / 503."""
    url     = f"{_API_BASE}/{endpoint}"
    headers = {
        "Access-Token": _token(),
        "Content-Type": "application/json",
    }
    for attempt in range(_RETRY_MAX + 1):
        try:
            resp = requests.post(url, json=body, headers=headers, timeout=30)
            if resp.status_code == 429 or (resp.status_code >= 500 and attempt < _RETRY_MAX):
                delay = min(_RETRY_BASE * (2 ** attempt) + random.uniform(0, 0.5), _RETRY_CAP)
                logger.warning("TikTok API %d — retrying in %.1fs (attempt %d/%d)",
                               resp.status_code, delay, attempt + 1, _RETRY_MAX)
                time.sleep(delay)
                continue
            resp.raise_for_status()
            data = resp.json()
            code = data.get("code", 0)
            if code != 0:
                msg = data.get("message", "unknown error")
                if code in (40100, 40101) and attempt < _RETRY_MAX:
                    delay = min(_RETRY_BASE * (2 ** attempt), _RETRY_CAP)
                    logger.warning("TikTok rate limit (code %d) — retrying in %.1fs", code, delay)
                    time.sleep(delay)
                    continue
                raise RuntimeError(f"TikTok API error {code}: {msg}")
            return data.get("data", {})
        except requests.RequestException as exc:
            if attempt < _RETRY_MAX:
                delay = min(_RETRY_BASE * (2 ** attempt) + random.uniform(0, 0.5), _RETRY_CAP)
                logger.warning("TikTok request failed — retrying in %.1fs: %s", delay, exc)
                time.sleep(delay)
                continue
            raise
    raise RuntimeError("TikTok API: max retries exceeded")


def _date_range(days: int = 30):
    end   = datetime.today()
    start = end - timedelta(days=days)
    return start.strftime("%Y-%m-%d"), end.strftime("%Y-%m-%d")


# ─── Individual data fetchers ──────────────────────────────────────────────────

def fetch_advertiser_info(advertiser_id: str = "") -> Dict:
    """Fetch advertiser name, currency, timezone, status."""
    aid  = _advertiser_id(advertiser_id)
    data = _post("advertiser/info/", {
        "advertiser_ids": [aid],
        "fields": ["name", "currency", "timezone", "status", "balance"],
    })
    info_list = data.get("list", [])
    if not info_list:
        return {}
    info = info_list[0]
    return {
        "name":     info.get("name", ""),
        "currency": info.get("currency", "USD"),
        "timezone": info.get("timezone", ""),
        "status":   info.get("status", ""),
        "balance":  round(float(info.get("balance", 0)), 2),
    }


def fetch_campaign_performance(advertiser_id: str = "", days: int = 30) -> List[Dict]:
    """Fetch campaigns with spend, impressions, clicks, CTR, CPA, conversions."""
    aid        = _advertiser_id(advertiser_id)
    start, end = _date_range(days)

    data = _post("report/integrated/get/", {
        "advertiser_id": aid,
        "report_type":   "BASIC",
        "dimensions":    ["campaign_id"],
        "metrics": [
            "spend", "impressions", "clicks", "ctr", "cpc", "cpm",
            "reach", "frequency", "conversion", "cost_per_conversion",
            "real_time_conversion", "video_play_actions",
            "video_watched_2s", "video_watched_6s",
            "campaign_name", "campaign_status", "objective_type",
        ],
        "start_date": start,
        "end_date":   end,
        "page_size":  50,
    })

    rows = []
    for item in data.get("list", []):
        dims    = item.get("dimensions", {})
        metrics = item.get("metrics", {})
        impressions  = int(metrics.get("impressions", 0))
        plays        = int(metrics.get("video_play_actions", 0))
        watch_2s     = int(metrics.get("video_watched_2s", 0))
        hook_rate    = round(plays / impressions * 100, 1) if impressions > 0 else 0
        hold_rate_2s = round(watch_2s / plays * 100, 1) if plays > 0 else 0

        rows.append({
            "campaign_id":    dims.get("campaign_id", ""),
            "name":           metrics.get("campaign_name", ""),
            "status":         metrics.get("campaign_status", ""),
            "objective":      metrics.get("objective_type", ""),
            "spend":          round(float(metrics.get("spend", 0)), 2),
            "impressions":    impressions,
            "clicks":         int(metrics.get("clicks", 0)),
            "ctr":            round(float(metrics.get("ctr", 0)), 3),
            "cpc":            round(float(metrics.get("cpc", 0)), 3),
            "cpm":            round(float(metrics.get("cpm", 0)), 2),
            "reach":          int(metrics.get("reach", 0)),
            "frequency":      round(float(metrics.get("frequency", 0)), 2),
            "conversions":    round(float(metrics.get("conversion", 0)), 1),
            "cpa":            round(float(metrics.get("cost_per_conversion", 0)), 2),
            "hook_rate":      hook_rate,
            "hold_rate_2s":   hold_rate_2s,
            "video_plays":    plays,
        })
    return rows


def fetch_adgroup_performance(advertiser_id: str = "", days: int = 30) -> List[Dict]:
    """Fetch ad group performance with audience and placement info."""
    aid        = _advertiser_id(advertiser_id)
    start, end = _date_range(days)

    data = _post("report/integrated/get/", {
        "advertiser_id": aid,
        "report_type":   "BASIC",
        "dimensions":    ["adgroup_id"],
        "metrics": [
            "spend", "impressions", "clicks", "ctr", "cpc", "conversion",
            "cost_per_conversion", "frequency", "adgroup_name", "adgroup_status",
            "optimization_goal", "bid_type", "bid",
        ],
        "start_date": start,
        "end_date":   end,
        "page_size":  50,
    })

    rows = []
    for item in data.get("list", []):
        dims    = item.get("dimensions", {})
        metrics = item.get("metrics", {})
        rows.append({
            "adgroup_id":  dims.get("adgroup_id", ""),
            "name":        metrics.get("adgroup_name", ""),
            "status":      metrics.get("adgroup_status", ""),
            "objective":   metrics.get("optimization_goal", ""),
            "bid_type":    metrics.get("bid_type", ""),
            "bid":         round(float(metrics.get("bid", 0)), 3),
            "spend":       round(float(metrics.get("spend", 0)), 2),
            "impressions": int(metrics.get("impressions", 0)),
            "clicks":      int(metrics.get("clicks", 0)),
            "ctr":         round(float(metrics.get("ctr", 0)), 3),
            "cpc":         round(float(metrics.get("cpc", 0)), 3),
            "conversions": round(float(metrics.get("conversion", 0)), 1),
            "cpa":         round(float(metrics.get("cost_per_conversion", 0)), 2),
            "frequency":   round(float(metrics.get("frequency", 0)), 2),
        })
    return rows


def fetch_creative_performance(advertiser_id: str = "", days: int = 30) -> List[Dict]:
    """Fetch ad-level creative performance: hook rate, 2s hold, 6s hold, CTR."""
    aid        = _advertiser_id(advertiser_id)
    start, end = _date_range(days)

    data = _post("report/integrated/get/", {
        "advertiser_id": aid,
        "report_type":   "BASIC",
        "dimensions":    ["ad_id"],
        "metrics": [
            "spend", "impressions", "clicks", "ctr",
            "video_play_actions", "video_watched_2s", "video_watched_6s",
            "video_views_p25", "video_views_p50", "video_views_p75", "video_views_p100",
            "conversion", "cost_per_conversion",
            "ad_name", "ad_status",
        ],
        "start_date": start,
        "end_date":   end,
        "page_size":  50,
    })

    rows = []
    for item in data.get("list", []):
        dims    = item.get("dimensions", {})
        m       = item.get("metrics", {})
        impr    = int(m.get("impressions", 0))
        plays   = int(m.get("video_play_actions", 0))
        w2s     = int(m.get("video_watched_2s", 0))
        w6s     = int(m.get("video_watched_6s", 0))

        if impr == 0 or float(m.get("spend", 0)) < 1:
            continue

        rows.append({
            "ad_id":       dims.get("ad_id", ""),
            "name":        m.get("ad_name", ""),
            "status":      m.get("ad_status", ""),
            "spend":       round(float(m.get("spend", 0)), 2),
            "impressions": impr,
            "ctr":         round(float(m.get("ctr", 0)), 3),
            "hook_rate":   round(plays / impr * 100, 1) if impr > 0 else 0,
            "hold_2s":     round(w2s / plays * 100, 1) if plays > 0 else 0,
            "hold_6s":     round(w6s / plays * 100, 1) if plays > 0 else 0,
            "complete":    round(int(m.get("video_views_p100", 0)) / plays * 100, 1) if plays > 0 else 0,
            "conversions": round(float(m.get("conversion", 0)), 1),
            "cpa":         round(float(m.get("cost_per_conversion", 0)), 2),
        })

    rows.sort(key=lambda r: r["spend"], reverse=True)
    return rows[:20]


# ─── Canon audit payload builder ──────────────────────────────────────────────

def build_audit_payload(
    advertiser_id: str = "",
    project:       str = "",
    account_type:  str = "",
    days:          int = 30,
    command:       str = "/audit",
) -> Dict[str, Any]:
    """Fetch live TikTok data and return a payload dict for build_tiktok_audit_prompt()."""
    aid = _advertiser_id(advertiser_id)
    logger.info("Fetching TikTok Ads data for advertiser %s...", aid)

    def safe(fn, *args, default=None, **kwargs):
        try:
            return fn(*args, **kwargs)
        except Exception as exc:
            logger.warning("TikTok fetch failed (%s): %s", fn.__name__, exc)
            return default if default is not None else []

    info      = safe(fetch_advertiser_info, aid, default={})
    campaigns = safe(fetch_campaign_performance, aid, days)
    adgroups  = safe(fetch_adgroup_performance, aid, days)
    creatives = safe(fetch_creative_performance, aid, days)

    total_spend = sum(c["spend"] for c in campaigns)
    total_conv  = sum(c["conversions"] for c in campaigns)
    total_clicks= sum(c["clicks"] for c in campaigns)
    total_impr  = sum(c["impressions"] for c in campaigns)
    avg_cpa     = round(total_spend / total_conv, 2) if total_conv > 0 else "N/A"
    avg_ctr     = round(total_clicks / total_impr * 100, 3) if total_impr > 0 else 0
    avg_hook    = round(sum(c["hook_rate"] for c in campaigns) / len(campaigns), 1) if campaigns else 0
    avg_freq    = round(sum(c["frequency"] for c in campaigns) / len(campaigns), 2) if campaigns else 0

    campaign_summary = "\n".join(
        f"  {c['name']} ({c['objective']}): "
        f"${c['spend']}/mo, CTR {c['ctr']}%, hook {c['hook_rate']}%, "
        f"freq {c['frequency']}x, {c['conversions']} conv, CPA ${c['cpa']}"
        for c in campaigns[:8]
    ) or "No active campaigns"

    creative_summary = "\n".join(
        f"  '{a['name']}': hook {a['hook_rate']}%, hold_2s {a['hold_2s']}%, "
        f"hold_6s {a['hold_6s']}%, complete {a['complete']}%, CTR {a['ctr']}%"
        for a in creatives[:5]
    ) or "No creative data available"

    low_hook = [c for c in campaigns if c["hook_rate"] < 15 and c["spend"] > 10]
    hook_warning = (
        f"{len(low_hook)} campaign(s) with hook rate <15%: "
        + ", ".join(f"{c['name']} ({c['hook_rate']}%)" for c in low_hook[:3])
    ) if low_hook else "Hook rates within normal range (>15%)"

    high_freq = [c for c in campaigns if c["frequency"] > 3.0]
    freq_warning = (
        f"{len(high_freq)} campaign(s) with freq >3x: "
        + ", ".join(f"{c['name']} ({c['frequency']}x)" for c in high_freq[:3])
    ) if high_freq else "Frequency within normal range (<3x)"

    inputs = {
        "TIKTOK__Campaigns__Performance":  campaign_summary,
        "TIKTOK__Creative__Performance":   creative_summary,
        "TIKTOK__Hook__Rate__Check":       hook_warning,
        "TIKTOK__Frequency__Check":        freq_warning,
        "TIKTOK__Account__Status":         info.get("status", "unknown"),
    }

    metrics = {
        "spend_30d":       f"${total_spend:,.0f}",
        "clicks_30d":      f"{total_clicks:,}",
        "conversions_30d": f"{total_conv:.0f}",
        "avg_cpa":         f"${avg_cpa}",
        "avg_ctr":         f"{avg_ctr}%",
        "avg_hook_rate":   f"{avg_hook}%",
        "avg_frequency":   f"{avg_freq}x",
        "campaigns_count": len(campaigns),
        "adgroups_count":  len(adgroups),
        "currency":        info.get("currency", "USD"),
        "timezone":        info.get("timezone", ""),
    }

    return {
        "platform":     "tiktok",
        "mode":         "audit",
        "command":      command,
        "project":      project or info.get("name", f"Advertiser {aid}"),
        "account_type": account_type,
        "date_range":   f"last {days} days",
        "inputs":       inputs,
        "metrics":      metrics,
    }


# ─── Tool definitions for agentic loop ────────────────────────────────────────

TIKTOK_ADS_TOOLS = [
    {
        "name": "get_tiktok_advertiser_info",
        "description": (
            "Fetch TikTok advertiser info: name, currency, timezone, status, balance. "
            "Call this FIRST — account status and balance issues are P0 gates."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "advertiser_id": {"type": "string", "description": "TikTok advertiser ID (numeric)"}
            },
            "required": ["advertiser_id"],
            "additionalProperties": False,
        },
    },
    {
        "name": "get_tiktok_campaigns",
        "description": (
            "Fetch TikTok campaign performance: spend, impressions, clicks, CTR, CPC, CPM, "
            "reach, frequency, conversions, CPA, hook rate, 2s hold rate. "
            "Use to identify top/bottom performers, creative fatigue, frequency issues."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "advertiser_id": {"type": "string"},
                "days": {"type": "integer", "description": "Lookback window in days (default 30)"},
            },
            "required": ["advertiser_id"],
            "additionalProperties": False,
        },
    },
    {
        "name": "get_tiktok_adgroups",
        "description": (
            "Fetch ad group performance with bid strategy and optimization goal. "
            "Use to audit bidding setup, CPA targets, and audience structure."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "advertiser_id": {"type": "string"},
                "days": {"type": "integer"},
            },
            "required": ["advertiser_id"],
            "additionalProperties": False,
        },
    },
    {
        "name": "get_tiktok_creatives",
        "description": (
            "Fetch ad-level creative performance: hook rate (plays/impressions), "
            "2s hold rate, 6s hold rate, completion rate, CTR, conversions. "
            "TikTok benchmark: hook >20%, 2s hold >30%, completion >15%."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "advertiser_id": {"type": "string"},
                "days": {"type": "integer"},
            },
            "required": ["advertiser_id"],
            "additionalProperties": False,
        },
    },
]


def execute_tool(name: str, inputs: dict) -> Any:
    """Map tool name to TikTok Ads API function."""
    aid  = inputs.get("advertiser_id", _advertiser_id())
    days = int(inputs.get("days", 30))

    if name == "get_tiktok_advertiser_info":
        return fetch_advertiser_info(aid)
    if name == "get_tiktok_campaigns":
        return fetch_campaign_performance(aid, days)
    if name == "get_tiktok_adgroups":
        return fetch_adgroup_performance(aid, days)
    if name == "get_tiktok_creatives":
        return fetch_creative_performance(aid, days)
    return {"error": f"Unknown tool: {name}"}


# ─── Quick CLI test ────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import sys
    aid = sys.argv[1] if len(sys.argv) > 1 else os.getenv("TIKTOK_ADVERTISER_ID")
    if not aid:
        print("Usage: python tiktok_ads_connector.py <advertiser_id>")
        print("Or set TIKTOK_ADVERTISER_ID in .env")
        sys.exit(1)

    print(f"Fetching TikTok Ads data for advertiser: {aid}")
    payload = build_audit_payload(aid, project="Test")
    print(f"\nPayload ready:")
    print(f"  Project:    {payload['project']}")
    print(f"  Spend 30d:  {payload['metrics']['spend_30d']}")
    print(f"  Campaigns:  {payload['metrics']['campaigns_count']}")
    print(f"  Hook rate:  {payload['metrics']['avg_hook_rate']}")
    print(f"  Frequency:  {payload['metrics']['avg_frequency']}")
    print(f"\nReady to run TikTok Canon audit!")
