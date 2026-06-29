"""
SQLite-backed persistence for Telegram bot chat states.

All reads/writes go through this module. The bot's in-memory dict is the
primary read path (fast); this DB is the write-through store (durable).
On restart, load_all_states() restores the in-memory dict from disk.
"""
import json
import logging
import os
import sqlite3
from typing import Any, Dict, List

logger = logging.getLogger(__name__)

DB_PATH = os.getenv("DB_PATH", "bot_state.db")


def _connect() -> sqlite3.Connection:
    # check_same_thread=False: each call creates its own connection, safe from multiple threads.
    # WAL mode allows concurrent readers while a writer is active — reduces lock contention.
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def init_db() -> None:
    """Create tables if they don't exist. Call once on startup."""
    with _connect() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS chat_state (
                chat_id    INTEGER PRIMARY KEY,
                state      TEXT    NOT NULL DEFAULT '{}',
                updated_at TEXT    DEFAULT (datetime('now'))
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS chat_history (
                chat_id    INTEGER PRIMARY KEY,
                history    TEXT    NOT NULL DEFAULT '[]',
                updated_at TEXT    DEFAULT (datetime('now'))
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS usage_log (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                ts            TEXT    DEFAULT (datetime('now')),
                model         TEXT    DEFAULT '',
                agent         TEXT    DEFAULT '',
                mode          TEXT    DEFAULT '',
                input_tokens  INTEGER DEFAULT 0,
                output_tokens INTEGER DEFAULT 0,
                cache_read    INTEGER DEFAULT 0,
                cache_write   INTEGER DEFAULT 0
            )
        """)
    logger.info("Storage ready: %s", DB_PATH)


def load_all_states() -> Dict[int, Dict[str, Any]]:
    """Return {chat_id: state_dict} for all persisted chats. Call on startup."""
    with _connect() as conn:
        rows = conn.execute("SELECT chat_id, state FROM chat_state").fetchall()
    result: Dict[int, Dict[str, Any]] = {}
    for row in rows:
        try:
            result[int(row["chat_id"])] = json.loads(row["state"])
        except (json.JSONDecodeError, ValueError):
            pass
    logger.info("Loaded %d chat states from disk", len(result))
    return result


def has_explicit_platform(chat_id: int) -> bool:
    """Return True if this chat ever called /setup platform explicitly."""
    try:
        with _connect() as conn:
            row = conn.execute(
                "SELECT state FROM chat_state WHERE chat_id = ?", (chat_id,)
            ).fetchone()
        if not row:
            return False
        state = json.loads(row["state"])
        return bool(state.get("platform_set_explicitly"))
    except Exception:
        return False


def save_state(chat_id: int, state: Dict[str, Any]) -> None:
    """Write-through: persist one chat's state. Upsert on chat_id."""
    try:
        with _connect() as conn:
            conn.execute(
                """
                INSERT INTO chat_state (chat_id, state, updated_at)
                VALUES (?, ?, datetime('now'))
                ON CONFLICT(chat_id) DO UPDATE SET
                    state      = excluded.state,
                    updated_at = excluded.updated_at
                """,
                (chat_id, json.dumps(state)),
            )
    except Exception as exc:
        logger.error("Failed to persist state for chat %s: %s", chat_id, exc)


# ── Conversation history ──────────────────────────────────────────────────────

def load_all_histories() -> Dict[int, List[Dict[str, Any]]]:
    """Return {chat_id: history_list} for all persisted chats.
    Rows with invalid schema are silently dropped to prevent 400 errors on replay."""
    with _connect() as conn:
        rows = conn.execute("SELECT chat_id, history FROM chat_history").fetchall()
    result: Dict[int, List[Dict[str, Any]]] = {}
    dropped = 0
    for row in rows:
        try:
            history = json.loads(row["history"])
            # Validate: must be a list of {role, content} dicts
            if not isinstance(history, list):
                raise ValueError("not a list")
            valid = all(
                isinstance(m, dict) and "role" in m and "content" in m
                for m in history
            )
            if not valid:
                raise ValueError("invalid message schema")
            result[int(row["chat_id"])] = history
        except (json.JSONDecodeError, ValueError):
            dropped += 1
    if dropped:
        logger.warning("Dropped %d malformed history rows on load", dropped)
    logger.info("Loaded %d chat histories from disk", len(result))
    return result


def save_history(chat_id: int, history: List[Dict[str, Any]]) -> None:
    """Persist conversation history for one chat."""
    try:
        with _connect() as conn:
            conn.execute(
                """
                INSERT INTO chat_history (chat_id, history, updated_at)
                VALUES (?, ?, datetime('now'))
                ON CONFLICT(chat_id) DO UPDATE SET
                    history    = excluded.history,
                    updated_at = excluded.updated_at
                """,
                (chat_id, json.dumps(history)),
            )
    except Exception as exc:
        logger.error("Failed to persist history for chat %s: %s", chat_id, exc)


def log_usage(model: str, usage: Dict[str, Any], agent: str = "", mode: str = "") -> None:
    """Record token usage for one API call. Best-effort — never raises."""
    try:
        with _connect() as conn:
            conn.execute(
                """INSERT INTO usage_log
                       (model, agent, mode, input_tokens, output_tokens, cache_read, cache_write)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (
                    model, agent, mode,
                    usage.get("input_tokens", 0),
                    usage.get("output_tokens", 0),
                    usage.get("cache_read_input_tokens", 0),
                    usage.get("cache_creation_input_tokens", 0),
                ),
            )
    except Exception as exc:
        logger.warning("Failed to log usage: %s", exc)


def get_usage_summary(limit: int = 100) -> List[Dict[str, Any]]:
    """Return recent usage rows newest-first."""
    try:
        with _connect() as conn:
            rows = conn.execute(
                """SELECT ts, model, agent, mode,
                          input_tokens, output_tokens, cache_read, cache_write
                   FROM usage_log ORDER BY ts DESC LIMIT ?""",
                (limit,),
            ).fetchall()
        return [dict(r) for r in rows]
    except Exception:
        return []


def delete_history(chat_id: int) -> None:
    """Delete conversation history for one chat (called on /clear)."""
    try:
        with _connect() as conn:
            conn.execute("DELETE FROM chat_history WHERE chat_id = ?", (chat_id,))
    except Exception as exc:
        logger.error("Failed to delete history for chat %s: %s", chat_id, exc)
