"""
Google Ads API connector — pulls live account data for Canon audits.

Builds structured input dicts compatible with build_google_audit_prompt().
"""
import os
import logging
import random
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv
load_dotenv()

logger = logging.getLogger(__name__)

_RETRY_MAX   = 3
_RETRY_BASE  = 1.0
_RETRY_MAX_D = 30.0

def _with_retry(fn, *args, **kwargs):
    """Retry a Google Ads API call with exponential backoff on quota/rate errors."""
    for attempt in range(_RETRY_MAX + 1):
        try:
            return fn(*args, **kwargs)
        except Exception as exc:
            err = str(exc)
            retriable = any(k in err for k in ("RESOURCE_EXHAUSTED", "QUOTA_EXCEEDED", "429", "503", "UNAVAILABLE"))
            if retriable and attempt < _RETRY_MAX:
                delay = min(_RETRY_BASE * (2 ** attempt) + random.uniform(0, 0.5), _RETRY_MAX_D)
                logger.warning("Google Ads rate limit — retrying in %.1fs (attempt %d/%d)", delay, attempt + 1, _RETRY_MAX)
                time.sleep(delay)
                continue
            raise

# ─── Client factory ───────────────────────────────────────────────────────────

def _get_client():
    from google.ads.googleads.client import GoogleAdsClient
    config = {
        "developer_token":  os.getenv("GOOGLE_ADS_DEVELOPER_TOKEN"),
        "client_id":        os.getenv("GOOGLE_ADS_CLIENT_ID"),
        "client_secret":    os.getenv("GOOGLE_ADS_CLIENT_SECRET"),
        "refresh_token":    os.getenv("GOOGLE_ADS_REFRESH_TOKEN"),
        "use_proto_plus":   True,
    }
    missing = [k for k, v in config.items() if not v and k != "use_proto_plus"]
    if missing:
        raise ValueError(
            f"Missing Google Ads credentials in .env: {missing}. "
            "Run: python setup_google_ads_oauth.py"
        )
    return GoogleAdsClient.load_from_dict(config)


def is_configured() -> bool:
    required = ["GOOGLE_ADS_DEVELOPER_TOKEN", "GOOGLE_ADS_CLIENT_ID",
                "GOOGLE_ADS_CLIENT_SECRET",   "GOOGLE_ADS_REFRESH_TOKEN"]
    return all(os.getenv(k) for k in required)


# ─── Date helpers ─────────────────────────────────────────────────────────────

def _date_range(days: int = 30):
    end   = datetime.today()
    start = end - timedelta(days=days)
    return start.strftime("%Y-%m-%d"), end.strftime("%Y-%m-%d")


# ─── Individual data fetchers ─────────────────────────────────────────────────

def fetch_campaign_performance(customer_id: str, days: int = 30) -> List[Dict]:
    def _fetch():
        client = _get_client()
        ga_svc = client.get_service("GoogleAdsService")
        start, end = _date_range(days)
        query = f"""
            SELECT
                campaign.id,
                campaign.name,
                campaign.status,
                campaign.advertising_channel_type,
                campaign.bidding_strategy_type,
                metrics.impressions,
                metrics.clicks,
                metrics.cost_micros,
                metrics.conversions,
                metrics.conversions_value,
                metrics.ctr,
                metrics.average_cpc,
                metrics.search_impression_share,
                metrics.search_budget_lost_impression_share,
                metrics.search_rank_lost_impression_share
            FROM campaign
            WHERE segments.date BETWEEN '{start}' AND '{end}'
              AND campaign.status != 'REMOVED'
            ORDER BY metrics.cost_micros DESC
        """
        rows = []
        for row in ga_svc.search(customer_id=customer_id, query=query):
            m = row.metrics
            rows.append({
                "id":             row.campaign.id,
                "name":           row.campaign.name,
                "status":         row.campaign.status.name,
                "type":           row.campaign.advertising_channel_type.name,
                "bidding":        row.campaign.bidding_strategy_type.name,
                "impressions":    m.impressions,
                "clicks":         m.clicks,
                "cost":           round(m.cost_micros / 1_000_000, 2),
                "conversions":    round(m.conversions, 1),
                "conv_value":     round(m.conversions_value, 2),
                "ctr":            round(m.ctr * 100, 2),
                "avg_cpc":        round(m.average_cpc / 1_000_000, 2),
                "is":             round(m.search_impression_share * 100, 1) if m.search_impression_share else None,
                "lost_is_budget": round(m.search_budget_lost_impression_share * 100, 1) if m.search_budget_lost_impression_share else None,
                "lost_is_rank":   round(m.search_rank_lost_impression_share * 100, 1) if m.search_rank_lost_impression_share else None,
            })
        return rows
    return _with_retry(_fetch)


def fetch_conversion_actions(customer_id: str) -> List[Dict]:
    def _fetch():
        client = _get_client()
        ga_svc = client.get_service("GoogleAdsService")
        query = """
            SELECT
                conversion_action.id,
                conversion_action.name,
                conversion_action.status,
                conversion_action.type,
                conversion_action.primary_for_goal,
                conversion_action.include_in_conversions_metric,
                conversion_action.tag_snippets
            FROM conversion_action
            WHERE conversion_action.status != 'REMOVED'
        """
        rows = []
        for row in ga_svc.search(customer_id=customer_id, query=query):
            ca = row.conversion_action
            rows.append({
                "name":       ca.name,
                "status":     ca.status.name,
                "type":       ca.type_.name,
                "primary":    ca.primary_for_goal,
                "in_bidding": ca.include_in_conversions_metric,
            })
        return rows
    return _with_retry(_fetch)


def fetch_account_settings(customer_id: str) -> Dict:
    def _fetch():
        client = _get_client()
        ga_svc = client.get_service("GoogleAdsService")
        query = """
            SELECT
                customer.id,
                customer.descriptive_name,
                customer.currency_code,
                customer.time_zone,
                customer.auto_tagging_enabled,
                customer.conversion_tracking_setting.conversion_tracking_id,
                customer.conversion_tracking_setting.google_ads_conversion_customer
            FROM customer
            LIMIT 1
        """
        for row in ga_svc.search(customer_id=customer_id, query=query):
            c = row.customer
            return {
                "name":             c.descriptive_name,
                "currency":         c.currency_code,
                "timezone":         c.time_zone,
                "auto_tagging":     c.auto_tagging_enabled,
                "conv_tracking_id": c.conversion_tracking_setting.conversion_tracking_id,
            }
        return {}
    return _with_retry(_fetch)


def fetch_top_wasted_spend(customer_id: str, days: int = 30, limit: int = 20) -> List[Dict]:
    """Search terms with spend but 0 conversions — top wasted spend."""
    def _fetch():
        client = _get_client()
        ga_svc = client.get_service("GoogleAdsService")
        start, end = _date_range(days)
        query = f"""
            SELECT
                search_term_view.search_term,
                search_term_view.status,
                metrics.impressions,
                metrics.clicks,
                metrics.cost_micros,
                metrics.conversions
            FROM search_term_view
            WHERE segments.date BETWEEN '{start}' AND '{end}'
              AND metrics.cost_micros > 1000000
              AND metrics.conversions < 0.1
              AND search_term_view.status = 'NONE'
            ORDER BY metrics.cost_micros DESC
            LIMIT {limit}
        """
        rows = []
        for row in ga_svc.search(customer_id=customer_id, query=query):
            rows.append({
                "term":        row.search_term_view.search_term,
                "clicks":      row.metrics.clicks,
                "cost":        round(row.metrics.cost_micros / 1_000_000, 2),
                "conversions": row.metrics.conversions,
            })
        return rows
    return _with_retry(_fetch)


def fetch_quality_scores(customer_id: str) -> List[Dict]:
    def _fetch():
        client = _get_client()
        ga_svc = client.get_service("GoogleAdsService")
        # Note: metrics cannot be mixed with ad_group_criterion in the same query
        query = """
            SELECT
                ad_group_criterion.keyword.text,
                ad_group_criterion.quality_info.quality_score,
                ad_group_criterion.quality_info.creative_quality_score,
                ad_group_criterion.quality_info.post_click_quality_score,
                ad_group_criterion.quality_info.search_predicted_ctr
            FROM ad_group_criterion
            WHERE ad_group_criterion.type = 'KEYWORD'
              AND ad_group_criterion.status != 'REMOVED'
              AND ad_group_criterion.quality_info.quality_score IS NOT NULL
            LIMIT 100
        """
        rows = []
        for row in ga_svc.search(customer_id=customer_id, query=query):
            qs = row.ad_group_criterion.quality_info.quality_score
            rows.append({
                "keyword":     row.ad_group_criterion.keyword.text,
                "qs":          qs,
                "creative_qs": row.ad_group_criterion.quality_info.creative_quality_score.name,
                "lp_qs":       row.ad_group_criterion.quality_info.post_click_quality_score.name,
                "ctr_qs":      row.ad_group_criterion.quality_info.search_predicted_ctr.name,
            })
        return rows
    return _with_retry(_fetch)


# ─── Main builder — assembles Canon audit payload ────────────────────────────

def build_audit_payload(
    customer_id:  str,
    project:      str = "",
    account_type: str = "",
    days:         int = 30,
    command:      str = "/audit",
) -> Dict[str, Any]:
    """
    Fetch live data from Google Ads and return a payload dict
    ready for build_google_audit_prompt().
    """
    logger.info("Fetching Google Ads data for customer %s...", customer_id)

    def safe(fn, *args, default=None, **kwargs):
        try:
            return fn(*args, **kwargs)
        except Exception as e:
            logger.warning("Fetch failed (%s): %s", fn.__name__, e)
            return default if default is not None else []

    settings    = safe(fetch_account_settings, customer_id, default={})
    campaigns   = safe(fetch_campaign_performance, customer_id, days)
    conversions = safe(fetch_conversion_actions, customer_id)
    wasted      = safe(fetch_top_wasted_spend, customer_id, days)
    quality     = safe(fetch_quality_scores, customer_id)

    # ── Format inputs block ───────────────────────────────────────────────────

    auto_tag_status = "ON" if settings.get("auto_tagging") else "OFF — CRITICAL: auto-tagging disabled"

    conv_summary = "; ".join(
        f"{c['name']} ({c['type']}, primary={c['primary']}, in_bidding={c['in_bidding']})"
        for c in conversions[:5]
    ) or "No conversion actions found"

    total_spend = sum(c["cost"] for c in campaigns)
    total_conv  = sum(c["conversions"] for c in campaigns)
    total_clicks= sum(c["clicks"] for c in campaigns)
    avg_cpa     = round(total_spend / total_conv, 2) if total_conv > 0 else "N/A"
    avg_ctr     = round(sum(c["ctr"] for c in campaigns) / len(campaigns), 2) if campaigns else 0

    campaign_summary = "\n".join(
        f"  {c['name']} ({c['type']}): "
        f"${c['cost']}/mo, CTR {c['ctr']}%, "
        f"{c['conversions']} conv, IS {c['is']}%"
        for c in campaigns[:8]
    ) or "No active campaigns"

    wasted_summary = "\n".join(
        f"  '{w['term']}': ${w['cost']} spend, {w['clicks']} clicks, 0 conv"
        for w in wasted[:10]
    ) or "No wasted spend detected"

    low_qs = [k for k in quality if k["qs"] and k["qs"] < 6]
    qs_summary = (
        f"Avg QS: {round(sum(k['qs'] for k in quality if k['qs']) / max(len(quality),1), 1)}/10. "
        f"Low QS keywords (<6): {len(low_qs)} — "
        + (", ".join(f"'{k['keyword']}' ({k['qs']}/10)" for k in low_qs[:5]) or "none")
    ) if quality else "Quality Score data not available"

    avg_is = round(sum(c["is"] for c in campaigns if c["is"]) / max(len(campaigns), 1), 1) if campaigns else None
    avg_lost_budget = round(sum(c["lost_is_budget"] for c in campaigns if c["lost_is_budget"]) / max(len(campaigns),1), 1) if campaigns else None

    inputs = {
        "ADS__AutoTagging__Status":            auto_tag_status,
        "ADS__Conversions__Summary__Settings": conv_summary,
        "ADS__Export__Campaigns__Performance": campaign_summary,
        "ADS__SearchTerms__WastedSpend__30d":  wasted_summary,
        "ADS__QualityScore__Keywords":         qs_summary,
        "ADS__ImpressionShare__30d":           f"Avg IS: {avg_is}% | Lost IS (budget): {avg_lost_budget}%" if avg_is else "Not available",
    }

    metrics = {
        "spend_30d":      f"${total_spend:,.0f}",
        "clicks_30d":     f"{total_clicks:,}",
        "conversions_30d": f"{total_conv:.0f}",
        "avg_cpa":        f"${avg_cpa}",
        "avg_ctr":        f"{avg_ctr}%",
        "campaigns_count": len(campaigns),
        "currency":       settings.get("currency", "USD"),
        "timezone":       settings.get("timezone", ""),
    }

    return {
        "platform":     "google",
        "mode":         "audit",
        "command":      command,
        "project":      project or settings.get("name", f"Account {customer_id}"),
        "account_type": account_type,
        "date_range":   f"last {days} days",
        "inputs":       inputs,
        "metrics":      metrics,
    }


# ─── Tool definitions for agentic loop ───────────────────────────────────────

GOOGLE_ADS_TOOLS = [
    {
        "name": "get_account_settings",
        "description": (
            "Fetch Google Ads account settings: auto-tagging status, currency, timezone, "
            "conversion tracking ID. Call this FIRST — auto-tagging OFF is a P0 gate "
            "that blocks all attribution and must be checked before any optimization."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "customer_id": {"type": "string", "description": "10-digit Google Ads customer ID"}
            },
            "required": ["customer_id"],
            "additionalProperties": False,
        },
    },
    {
        "name": "get_campaigns",
        "description": (
            "Fetch campaign performance: spend, conversions, conversion value, CTR, CPC, "
            "Impression Share, Lost IS (budget/rank) for each campaign. "
            "Call this to understand which campaigns are driving results or causing issues. "
            "Also use to calculate total account CPA and ROAS."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "customer_id": {"type": "string"},
                "days": {"type": "integer", "description": "Lookback window in days (default 30)"},
            },
            "required": ["customer_id"],
            "additionalProperties": False,
        },
    },
    {
        "name": "get_conversion_actions",
        "description": (
            "Fetch all conversion actions: name, type, primary/secondary status, in_bidding flag. "
            "Call this to verify P0 tracking gate: at least one Primary conversion action must exist "
            "and be active. Also reveals duplicate counting or wrong Primary assignments."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "customer_id": {"type": "string"},
            },
            "required": ["customer_id"],
            "additionalProperties": False,
        },
    },
    {
        "name": "get_wasted_spend",
        "description": (
            "Fetch search terms with spend > $1 but 0 conversions — top wasted spend. "
            "Call this after verifying tracking is healthy, to find search term hygiene issues "
            "and negative keyword opportunities (GAC-0014)."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "customer_id": {"type": "string"},
                "days": {"type": "integer", "description": "Lookback window in days (default 30)"},
                "limit": {"type": "integer", "description": "Max results (default 20)"},
            },
            "required": ["customer_id"],
            "additionalProperties": False,
        },
    },
    {
        "name": "get_quality_scores",
        "description": (
            "Fetch keyword Quality Scores (1-10), landing page experience, expected CTR, "
            "and creative quality score for all active keywords. "
            "Call this when CTR is below benchmark or CPC is inflated, to diagnose QS issues (GAC-0007)."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "customer_id": {"type": "string"},
            },
            "required": ["customer_id"],
            "additionalProperties": False,
        },
    },
]


def execute_tool(name: str, inputs: dict) -> Any:
    """
    Map tool name to actual Google Ads API function.
    Returns a JSON-serialisable value.
    """
    cid  = inputs.get("customer_id", "")
    days = int(inputs.get("days", 30))

    if name == "get_account_settings":
        result = fetch_account_settings(cid)
        return result if result else {"error": "No account data returned"}

    if name == "get_campaigns":
        rows = fetch_campaign_performance(cid, days)
        return rows if rows else []

    if name == "get_conversion_actions":
        rows = fetch_conversion_actions(cid)
        return rows if rows else []

    if name == "get_wasted_spend":
        limit = int(inputs.get("limit", 20))
        rows = fetch_top_wasted_spend(cid, days, limit)
        return rows if rows else []

    if name == "get_quality_scores":
        rows = fetch_quality_scores(cid)
        return rows if rows else []

    return {"error": f"Unknown tool: {name}"}


# ─── Quick CLI test ───────────────────────────────────────────────────────────

if __name__ == "__main__":
    import sys
    cid = sys.argv[1] if len(sys.argv) > 1 else os.getenv("GOOGLE_ADS_CUSTOMER_ID")
    if not cid:
        print("Usage: python google_ads_connector.py <customer_id>")
        print("Or set GOOGLE_ADS_CUSTOMER_ID in .env")
        sys.exit(1)

    print(f"Fetching data for customer: {cid}")
    payload = build_audit_payload(cid, project="Test")
    print(f"\nPayload ready:")
    print(f"  Project:    {payload['project']}")
    print(f"  Spend 30d:  {payload['metrics']['spend_30d']}")
    print(f"  Campaigns:  {payload['metrics']['campaigns_count']}")
    print(f"  Auto-tag:   {payload['inputs']['ADS__AutoTagging__Status']}")
    print(f"\nReady to run Canon audit!")
