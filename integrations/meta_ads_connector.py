"""
Meta Ads connector — pulls live account data for Canon audits via Meta Marketing API.

Required .env vars:
    META_ACCESS_TOKEN   — long-lived user/system-user access token
    META_ACCOUNT_ID     — ad account ID, e.g. act_1234567890

Setup:
    1. Create a Meta App at developers.facebook.com
    2. Add Marketing API product
    3. Generate a long-lived access token with ads_read + ads_management permissions
    4. Find your Ad Account ID in Meta Business Manager → Ad Accounts
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

_GRAPH_BASE = "https://graph.facebook.com/v19.0"
_RETRY_MAX  = 3
_RETRY_BASE = 1.0
_RETRY_CAP  = 30.0


# ─── Auth helpers ─────────────────────────────────────────────────────────────

def _token() -> str:
    t = os.getenv("META_ACCESS_TOKEN", "")
    if not t:
        raise ValueError("META_ACCESS_TOKEN not set in .env")
    return t


def _account_id(override: str = "") -> str:
    raw = override or os.getenv("META_ACCOUNT_ID", "")
    if not raw:
        raise ValueError("META_ACCOUNT_ID not set in .env (format: act_1234567890)")
    return raw if raw.startswith("act_") else f"act_{raw}"


def is_configured() -> bool:
    return bool(os.getenv("META_ACCESS_TOKEN") and os.getenv("META_ACCOUNT_ID"))


# ─── HTTP helpers ──────────────────────────────────────────────────────────────

def _get(endpoint: str, params: dict) -> dict:
    """GET with exponential backoff on 429 / 503."""
    params = {**params, "access_token": _token()}
    url = f"{_GRAPH_BASE}/{endpoint}"
    for attempt in range(_RETRY_MAX + 1):
        try:
            resp = requests.get(url, params=params, timeout=30)
            if resp.status_code == 429 or (resp.status_code >= 500 and attempt < _RETRY_MAX):
                delay = min(_RETRY_BASE * (2 ** attempt) + random.uniform(0, 0.5), _RETRY_CAP)
                logger.warning("Meta API %d — retrying in %.1fs (attempt %d/%d)",
                               resp.status_code, delay, attempt + 1, _RETRY_MAX)
                time.sleep(delay)
                continue
            resp.raise_for_status()
            data = resp.json()
            if "error" in data:
                raise RuntimeError(f"Meta API error: {data['error']}")
            return data
        except requests.RequestException as exc:
            if attempt < _RETRY_MAX:
                delay = min(_RETRY_BASE * (2 ** attempt) + random.uniform(0, 0.5), _RETRY_CAP)
                logger.warning("Meta API request failed — retrying in %.1fs: %s", delay, exc)
                time.sleep(delay)
                continue
            raise
    raise RuntimeError("Meta API: max retries exceeded")


def _date_range(days: int = 30):
    end   = datetime.today()
    start = end - timedelta(days=days)
    return start.strftime("%Y-%m-%d"), end.strftime("%Y-%m-%d")


# ─── Individual data fetchers ──────────────────────────────────────────────────

def fetch_account_info(account_id: str = "") -> Dict:
    """Fetch account name, currency, timezone, status."""
    aid = _account_id(account_id)
    data = _get(aid, {
        "fields": "name,currency,timezone_name,account_status,business,spend_cap,amount_spent",
    })
    status_map = {1: "ACTIVE", 2: "DISABLED", 3: "UNSETTLED", 7: "PENDING_RISK_REVIEW",
                  8: "PENDING_SETTLEMENT", 9: "IN_GRACE_PERIOD", 100: "PENDING_CLOSURE",
                  101: "CLOSED", 201: "ANY_ACTIVE", 202: "ANY_CLOSED"}
    return {
        "name":       data.get("name", ""),
        "currency":   data.get("currency", "USD"),
        "timezone":   data.get("timezone_name", ""),
        "status":     status_map.get(data.get("account_status", 0), str(data.get("account_status"))),
        "spend_cap":  data.get("spend_cap", "0"),
        "spent_total": round(int(data.get("amount_spent", 0)) / 100, 2),
    }


def fetch_campaign_performance(account_id: str = "", days: int = 30) -> List[Dict]:
    """Fetch campaigns with spend, impressions, clicks, CPM, CPC, CTR, conversions, ROAS."""
    aid = _account_id(account_id)
    start, end = _date_range(days)

    data = _get(f"{aid}/campaigns", {
        "fields": (
            "id,name,status,objective,"
            "insights.fields(spend,impressions,clicks,ctr,cpc,cpm,reach,frequency,"
            "actions,action_values,purchase_roas,cost_per_action_type)"
            f".time_range({{'since':'{start}','until':'{end}'}})"
        ),
        "limit": 50,
    })

    rows = []
    for c in data.get("data", []):
        ins = c.get("insights", {}).get("data", [{}])[0] if c.get("insights") else {}
        spend = float(ins.get("spend", 0))

        def _action_val(actions: list, action_type: str) -> float:
            for a in (actions or []):
                if a.get("action_type") == action_type:
                    return float(a.get("value", 0))
            return 0.0

        actions     = ins.get("actions", [])
        conv_vals   = ins.get("action_values", [])
        purchases   = _action_val(actions, "purchase")
        leads       = _action_val(actions, "lead")
        conversions = purchases or leads
        rev         = _action_val(conv_vals, "purchase")
        roas_list   = ins.get("purchase_roas", [])
        roas        = float(roas_list[0].get("value", 0)) if roas_list else (rev / spend if spend > 0 else 0)

        rows.append({
            "id":          c["id"],
            "name":        c.get("name", ""),
            "status":      c.get("status", ""),
            "objective":   c.get("objective", ""),
            "spend":       round(spend, 2),
            "impressions": int(ins.get("impressions", 0)),
            "clicks":      int(ins.get("clicks", 0)),
            "ctr":         round(float(ins.get("ctr", 0)), 3),
            "cpc":         round(float(ins.get("cpc", 0)), 3),
            "cpm":         round(float(ins.get("cpm", 0)), 2),
            "reach":       int(ins.get("reach", 0)),
            "frequency":   round(float(ins.get("frequency", 0)), 2),
            "conversions": round(conversions, 1),
            "revenue":     round(rev, 2),
            "roas":        round(roas, 2),
        })
    return rows


def fetch_adset_performance(account_id: str = "", days: int = 30) -> List[Dict]:
    """Fetch ad sets with targeting summary and performance."""
    aid = _account_id(account_id)
    start, end = _date_range(days)

    data = _get(f"{aid}/adsets", {
        "fields": (
            "id,name,status,optimization_goal,billing_event,bid_amount,"
            "targeting{age_min,age_max,genders,geo_locations},"
            "insights.fields(spend,impressions,clicks,ctr,cpc,frequency,actions)"
            f".time_range({{'since':'{start}','until':'{end}'}})"
        ),
        "limit": 50,
    })

    rows = []
    for s in data.get("data", []):
        ins      = s.get("insights", {}).get("data", [{}])[0] if s.get("insights") else {}
        targeting = s.get("targeting", {})
        geo       = targeting.get("geo_locations", {})
        countries = [c.get("country_code") for c in geo.get("countries", [])]

        rows.append({
            "id":           s["id"],
            "name":         s.get("name", ""),
            "status":       s.get("status", ""),
            "objective":    s.get("optimization_goal", ""),
            "billing":      s.get("billing_event", ""),
            "age_min":      targeting.get("age_min"),
            "age_max":      targeting.get("age_max"),
            "genders":      targeting.get("genders", []),
            "countries":    countries,
            "spend":        round(float(ins.get("spend", 0)), 2),
            "impressions":  int(ins.get("impressions", 0)),
            "clicks":       int(ins.get("clicks", 0)),
            "ctr":          round(float(ins.get("ctr", 0)), 3),
            "cpc":          round(float(ins.get("cpc", 0)), 3),
            "frequency":    round(float(ins.get("frequency", 0)), 2),
        })
    return rows


def fetch_pixel_events(account_id: str = "") -> List[Dict]:
    """Fetch Meta Pixel IDs and their recent event counts (conversion tracking check)."""
    aid = _account_id(account_id)
    data = _get(f"{aid}/adspixels", {
        "fields": "id,name,last_fired_time,is_unavailable",
        "limit": 20,
    })
    return [
        {
            "id":             p.get("id"),
            "name":           p.get("name", ""),
            "last_fired":     p.get("last_fired_time"),
            "is_unavailable": p.get("is_unavailable", False),
        }
        for p in data.get("data", [])
    ]


def fetch_creative_performance(account_id: str = "", days: int = 30) -> List[Dict]:
    """Fetch top/bottom ads by hook rate (ThruPlay) and CTR."""
    aid = _account_id(account_id)
    start, end = _date_range(days)

    data = _get(f"{aid}/ads", {
        "fields": (
            "id,name,status,"
            "insights.fields(spend,impressions,clicks,ctr,video_play_actions,"
            "video_thruplay_watched_actions,actions)"
            f".time_range({{'since':'{start}','until':'{end}'}})"
        ),
        "limit": 50,
    })

    rows = []
    for ad in data.get("data", []):
        ins = ad.get("insights", {}).get("data", [{}])[0] if ad.get("insights") else {}
        if not ins or float(ins.get("spend", 0)) < 1:
            continue

        impressions = int(ins.get("impressions", 0))

        def _action_val(key: str) -> float:
            for a in ins.get(key, []):
                if a.get("action_type") in ("video_view", "video_thruplay_watched"):
                    return float(a.get("value", 0))
            return 0.0

        plays     = _action_val("video_play_actions")
        thruplays = _action_val("video_thruplay_watched_actions")
        hook_rate = round((plays / impressions * 100) if impressions > 0 else 0, 1)

        rows.append({
            "id":          ad["id"],
            "name":        ad.get("name", ""),
            "status":      ad.get("status", ""),
            "spend":       round(float(ins.get("spend", 0)), 2),
            "impressions": impressions,
            "ctr":         round(float(ins.get("ctr", 0)), 3),
            "hook_rate":   hook_rate,
            "thruplays":   int(thruplays),
        })

    rows.sort(key=lambda r: r["spend"], reverse=True)
    return rows[:20]


# ─── Canon audit payload builder ──────────────────────────────────────────────

def build_audit_payload(
    account_id:   str = "",
    project:      str = "",
    account_type: str = "",
    days:         int = 30,
    command:      str = "/audit",
) -> Dict[str, Any]:
    """Fetch live Meta data and return a payload dict for build_meta_audit_prompt()."""
    aid = _account_id(account_id)
    logger.info("Fetching Meta Ads data for account %s...", aid)

    def safe(fn, *args, default=None, **kwargs):
        try:
            return fn(*args, **kwargs)
        except Exception as exc:
            logger.warning("Meta fetch failed (%s): %s", fn.__name__, exc)
            return default if default is not None else []

    info       = safe(fetch_account_info, aid, default={})
    campaigns  = safe(fetch_campaign_performance, aid, days)
    adsets     = safe(fetch_adset_performance, aid, days)
    pixels     = safe(fetch_pixel_events, aid, default=[])
    creatives  = safe(fetch_creative_performance, aid, days)

    total_spend = sum(c["spend"] for c in campaigns)
    total_conv  = sum(c["conversions"] for c in campaigns)
    total_clicks= sum(c["clicks"] for c in campaigns)
    total_impr  = sum(c["impressions"] for c in campaigns)
    avg_roas    = round(sum(c["roas"] for c in campaigns) / len(campaigns), 2) if campaigns else 0
    avg_ctr     = round(total_clicks / total_impr * 100, 3) if total_impr > 0 else 0
    avg_cpa     = round(total_spend / total_conv, 2) if total_conv > 0 else "N/A"
    avg_freq    = round(sum(c["frequency"] for c in campaigns) / len(campaigns), 2) if campaigns else 0

    pixel_summary = (
        "; ".join(f"{p['name']} (last_fired: {p.get('last_fired','never')})" for p in pixels[:3])
        or "No pixels found — conversion tracking may be missing"
    )

    campaign_summary = "\n".join(
        f"  {c['name']} ({c['objective']}): "
        f"${c['spend']}/mo, CTR {c['ctr']}%, ROAS {c['roas']}x, "
        f"freq {c['frequency']}x, {c['conversions']} conv"
        for c in campaigns[:8]
    ) or "No active campaigns"

    creative_summary = "\n".join(
        f"  '{a['name']}': ${a['spend']} spend, hook {a['hook_rate']}%, CTR {a['ctr']}%"
        for a in creatives[:5]
    ) or "No creative data available"

    high_freq = [c for c in campaigns if c["frequency"] > 3.5]
    freq_warning = (
        f"{len(high_freq)} campaign(s) with freq > 3.5x: "
        + ", ".join(f"{c['name']} ({c['frequency']}x)" for c in high_freq[:3])
    ) if high_freq else "Frequency within normal range (<3.5x)"

    inputs = {
        "META__Pixel__Status":              pixel_summary,
        "META__Campaigns__Performance":     campaign_summary,
        "META__Creative__Performance":      creative_summary,
        "META__Frequency__Check":           freq_warning,
        "META__Account__Status":            info.get("status", "unknown"),
    }

    metrics = {
        "spend_30d":      f"${total_spend:,.0f}",
        "clicks_30d":     f"{total_clicks:,}",
        "conversions_30d": f"{total_conv:.0f}",
        "avg_cpa":        f"${avg_cpa}",
        "avg_ctr":        f"{avg_ctr}%",
        "avg_roas":       f"{avg_roas}x",
        "avg_frequency":  f"{avg_freq}x",
        "campaigns_count": len(campaigns),
        "adsets_count":   len(adsets),
        "currency":       info.get("currency", "USD"),
        "timezone":       info.get("timezone", ""),
    }

    return {
        "platform":     "meta",
        "mode":         "audit",
        "command":      command,
        "project":      project or info.get("name", f"Account {aid}"),
        "account_type": account_type,
        "date_range":   f"last {days} days",
        "inputs":       inputs,
        "metrics":      metrics,
    }


# ─── Tool definitions for agentic loop ────────────────────────────────────────

META_ADS_TOOLS = [
    {
        "name": "get_meta_account_info",
        "description": (
            "Fetch Meta ad account info: name, currency, timezone, account status. "
            "Call this FIRST — a DISABLED or IN_GRACE_PERIOD account status is a P0 gate."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "account_id": {"type": "string", "description": "Meta ad account ID, e.g. act_1234567890"}
            },
            "required": ["account_id"],
            "additionalProperties": False,
        },
    },
    {
        "name": "get_meta_campaigns",
        "description": (
            "Fetch Meta campaign performance: spend, impressions, clicks, CTR, CPC, CPM, "
            "reach, frequency, conversions, revenue, ROAS per campaign. "
            "Use to identify top/bottom performers and frequency issues."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "account_id": {"type": "string"},
                "days": {"type": "integer", "description": "Lookback window in days (default 30)"},
            },
            "required": ["account_id"],
            "additionalProperties": False,
        },
    },
    {
        "name": "get_meta_pixels",
        "description": (
            "Fetch Meta Pixel IDs and their last_fired_time. "
            "P0 gate: a pixel that never fired or hasn't fired in 7+ days = broken tracking."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "account_id": {"type": "string"},
            },
            "required": ["account_id"],
            "additionalProperties": False,
        },
    },
    {
        "name": "get_meta_adsets",
        "description": (
            "Fetch ad set targeting details and performance: age, gender, countries, "
            "optimization goal, billing event, frequency. "
            "Use to audit audience overlap, broad-vs-narrow, and frequency caps."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "account_id": {"type": "string"},
                "days": {"type": "integer"},
            },
            "required": ["account_id"],
            "additionalProperties": False,
        },
    },
    {
        "name": "get_meta_creatives",
        "description": (
            "Fetch ad creative performance: hook rate (video_play/impressions), "
            "ThruPlay rate, CTR, spend per ad. "
            "Use to identify creative fatigue and underperforming assets."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "account_id": {"type": "string"},
                "days": {"type": "integer"},
            },
            "required": ["account_id"],
            "additionalProperties": False,
        },
    },
]


def execute_tool(name: str, inputs: dict) -> Any:
    """Map tool name to Meta Ads API function."""
    aid  = inputs.get("account_id", _account_id())
    days = int(inputs.get("days", 30))

    if name == "get_meta_account_info":
        return fetch_account_info(aid)
    if name == "get_meta_campaigns":
        return fetch_campaign_performance(aid, days)
    if name == "get_meta_pixels":
        return fetch_pixel_events(aid)
    if name == "get_meta_adsets":
        return fetch_adset_performance(aid, days)
    if name == "get_meta_creatives":
        return fetch_creative_performance(aid, days)
    return {"error": f"Unknown tool: {name}"}


# ─── Quick CLI test ────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import sys
    aid = sys.argv[1] if len(sys.argv) > 1 else os.getenv("META_ACCOUNT_ID")
    if not aid:
        print("Usage: python meta_ads_connector.py <account_id>")
        print("Or set META_ACCOUNT_ID in .env")
        sys.exit(1)

    print(f"Fetching Meta Ads data for account: {aid}")
    payload = build_audit_payload(aid, project="Test")
    print(f"\nPayload ready:")
    print(f"  Project:    {payload['project']}")
    print(f"  Spend 30d:  {payload['metrics']['spend_30d']}")
    print(f"  Campaigns:  {payload['metrics']['campaigns_count']}")
    print(f"  ROAS:       {payload['metrics']['avg_roas']}")
    print(f"  Frequency:  {payload['metrics']['avg_frequency']}")
    print(f"\nReady to run Meta Canon audit!")
