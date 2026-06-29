"""
SEO Drift Monitoring — SQLite-based baseline tracking.

Captures ranking/traffic baselines at first analysis, then tracks delta
on subsequent runs. Alerts on significant drops vs baseline (not week-over-week).
"""
import json
import logging
import os
import sqlite3
from datetime import date
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

_DB_PATH = os.getenv("DB_PATH", "bot_state.db")


def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(_DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def init_drift_table() -> None:
    """Create seo_drift table if it doesn't exist."""
    try:
        with _connect() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS seo_drift (
                    id          INTEGER PRIMARY KEY AUTOINCREMENT,
                    site        TEXT NOT NULL,
                    snapshot_ts TEXT DEFAULT (datetime('now')),
                    snapshot_date TEXT,
                    metrics     TEXT NOT NULL DEFAULT '{}'
                )
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_seo_drift_site
                ON seo_drift (site, snapshot_date)
            """)
    except Exception as exc:
        logger.warning("Failed to init seo_drift table: %s", exc)


def save_baseline(site: str, metrics: Dict[str, Any]) -> None:
    """Save a snapshot of site metrics. Called on first or explicit baseline capture."""
    try:
        init_drift_table()
        today = date.today().isoformat()
        with _connect() as conn:
            conn.execute(
                "INSERT INTO seo_drift (site, snapshot_date, metrics) VALUES (?, ?, ?)",
                (site, today, json.dumps(metrics)),
            )
        logger.info("SEO baseline saved for %s (%s)", site, today)
    except Exception as exc:
        logger.warning("Failed to save SEO baseline: %s", exc)


def get_baseline(site: str) -> Optional[Dict[str, Any]]:
    """Return the earliest snapshot for a site (the original baseline)."""
    try:
        init_drift_table()
        with _connect() as conn:
            row = conn.execute(
                "SELECT metrics, snapshot_date FROM seo_drift WHERE site = ? ORDER BY id ASC LIMIT 1",
                (site,),
            ).fetchone()
        if row:
            return {"metrics": json.loads(row["metrics"]), "date": row["snapshot_date"]}
    except Exception as exc:
        logger.warning("Failed to get SEO baseline: %s", exc)
    return None


def get_history(site: str, limit: int = 12) -> List[Dict[str, Any]]:
    """Return recent snapshots for a site, newest first."""
    try:
        init_drift_table()
        with _connect() as conn:
            rows = conn.execute(
                "SELECT snapshot_date, metrics FROM seo_drift WHERE site = ? ORDER BY id DESC LIMIT ?",
                (site, limit),
            ).fetchall()
        return [{"date": r["snapshot_date"], "metrics": json.loads(r["metrics"])} for r in rows]
    except Exception as exc:
        logger.warning("Failed to get SEO history: %s", exc)
    return []


def compute_drift(baseline: Dict[str, Any], current: Dict[str, Any]) -> Dict[str, Any]:
    """
    Compare current metrics to baseline.
    Returns: {metric: {baseline, current, delta_pct, alert}}
    """
    result = {}
    _ALERT_THRESHOLD = 15.0  # % drop from baseline triggers alert

    for key, base_val in baseline.items():
        curr_val = current.get(key)
        if curr_val is None or not isinstance(base_val, (int, float)):
            continue
        try:
            base_val = float(base_val)
            curr_val = float(curr_val)
            delta = ((curr_val - base_val) / base_val * 100) if base_val != 0 else 0
            alert = delta <= -_ALERT_THRESHOLD
            result[key] = {
                "baseline": base_val,
                "current":  curr_val,
                "delta_pct": round(delta, 1),
                "alert": alert,
                "status": "⬇️ DROP" if alert else ("⬆️ GAIN" if delta >= 5 else "➡️ STABLE"),
            }
        except (TypeError, ValueError):
            continue
    return result


def build_drift_prompt(site: str, current_metrics: Dict[str, Any]) -> str:
    """Build an agent prompt for drift analysis — includes baseline comparison."""
    baseline_data = get_baseline(site)
    history       = get_history(site)

    baseline_block = ""
    drift_block    = ""

    if baseline_data:
        baseline_block = f"\n## Baseline (captured {baseline_data['date']})\n"
        baseline_block += "\n".join(f"- {k}: {v}" for k, v in baseline_data["metrics"].items())

        drift = compute_drift(baseline_data["metrics"], current_metrics)
        if drift:
            drift_block = "\n## Delta vs Baseline\n"
            for metric, d in drift.items():
                alert_tag = " ⚠️ ALERT" if d["alert"] else ""
                drift_block += (
                    f"- {metric}: {d['baseline']} → {d['current']} "
                    f"({d['delta_pct']:+.1f}%) {d['status']}{alert_tag}\n"
                )
    else:
        baseline_block = "\n## Baseline\nNo baseline found for this site. Current snapshot will be saved as baseline."

    history_block = ""
    if len(history) > 1:
        history_block = f"\n## Recent History ({len(history)} snapshots)\n"
        for snap in history[:6]:
            history_block += f"- {snap['date']}: {snap['metrics']}\n"

    current_block = "\n## Current Metrics\n"
    current_block += "\n".join(f"- {k}: {v}" for k, v in current_metrics.items())

    return f"""Platform: SEO — Drift Monitor
Site: {site}
{current_block}
{baseline_block}
{drift_block}
{history_block}

Analyze SEO performance drift:

1. ALERT SUMMARY
   — Which metrics show >15% drop vs baseline? (CRITICAL alerts)
   — Which show 5–15% drop? (WARNING alerts)
   — Which are stable or improving?

2. ROOT CAUSE ANALYSIS
   For each alerted metric:
   — Probable cause: algorithm update / competitor move / content change / technical issue / seasonal
   — Evidence supporting the diagnosis
   — What additional data would confirm the cause

3. TREND ASSESSMENT
   — Is this a one-time drop or consistent decline?
   — Recovery trajectory if no action taken?
   — Benchmark: where does current performance sit vs industry averages?

4. RECOVERY ACTIONS
   Format: Metric affected | Root cause | Action | Expected recovery timeline
   — Immediate (this week)
   — Short-term (this month)
   — Monitor only (watch, no action yet)

5. CONFIDENCE ASSESSMENT
   - Confidence per finding: High / Medium / Low
   - Data quality assessment: is the metrics data reliable?
   - Recommended monitoring cadence for this site
"""
