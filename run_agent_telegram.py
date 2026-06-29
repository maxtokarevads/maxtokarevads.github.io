import logging
import os
import threading
import time
from datetime import datetime
from typing import Any, Dict, Optional, Set

import requests
from dotenv import load_dotenv

from agent import AdvertisingAnalyticsAgent
from agents.ads.reporting.pdf_builder import build_report_pdf
from agents.ads.skills.canon.demo_payload import get_demo_payload
from telegram_formatter import (
    format_for_telegram,
    extract_telegram_report,
    extract_full_fixlist,
    render_telegram_report,
)

# Google Ads live connector (only active when credentials are configured)
try:
    from integrations.google_ads_connector import (
        build_audit_payload as _gads_build_payload,
        is_configured as _gads_configured,
        GOOGLE_ADS_TOOLS,
        execute_tool as _gads_execute_tool,
    )
    GOOGLE_ADS_AVAILABLE = _gads_configured()
except Exception:
    GOOGLE_ADS_AVAILABLE = False
    _gads_build_payload   = None
    GOOGLE_ADS_TOOLS      = []
    _gads_execute_tool    = None

# Meta Ads live connector
try:
    from integrations.meta_ads_connector import (
        build_audit_payload as _meta_build_payload,
        is_configured as _meta_configured,
        META_ADS_TOOLS,
        execute_tool as _meta_execute_tool,
    )
    META_ADS_AVAILABLE = _meta_configured()
except Exception:
    META_ADS_AVAILABLE   = False
    _meta_build_payload  = None
    META_ADS_TOOLS       = []
    _meta_execute_tool   = None

# TikTok Ads live connector
try:
    from integrations.tiktok_ads_connector import (
        build_audit_payload as _tiktok_build_payload,
        is_configured as _tiktok_configured,
        TIKTOK_ADS_TOOLS,
        execute_tool as _tiktok_execute_tool,
    )
    TIKTOK_ADS_AVAILABLE = _tiktok_configured()
except Exception:
    TIKTOK_ADS_AVAILABLE  = False
    _tiktok_build_payload = None
    TIKTOK_ADS_TOOLS      = []
    _tiktok_execute_tool  = None

import storage

load_dotenv()

# ── Per-user rate limiter ─────────────────────────────────────────────────────
# Allows up to _RL_MAX_REQUESTS per _RL_WINDOW_SECONDS per chat_id.
# In-memory only — resets on restart. Prevents API budget abuse.
_RL_WINDOW_SECONDS = int(os.getenv("RATE_LIMIT_WINDOW", "60"))
_RL_MAX_REQUESTS   = int(os.getenv("RATE_LIMIT_MAX", "10"))
_rl_lock: threading.Lock = threading.Lock()
_rl_timestamps: Dict[int, list] = {}  # chat_id → [epoch timestamps]


_RL_CLEANUP_INTERVAL = 3600  # evict stale chat entries once per hour
_rl_last_cleanup     = 0.0


def _check_rate_limit(chat_id: int) -> bool:
    """Return True if request is allowed, False if rate limit exceeded."""
    global _rl_last_cleanup
    now = time.time()
    with _rl_lock:
        ts = _rl_timestamps.setdefault(chat_id, [])
        cutoff = now - _RL_WINDOW_SECONDS
        _rl_timestamps[chat_id] = [t for t in ts if t > cutoff]
        if len(_rl_timestamps[chat_id]) >= _RL_MAX_REQUESTS:
            return False
        _rl_timestamps[chat_id].append(now)
        # Periodically remove chats that have no recent activity (memory guard)
        if now - _rl_last_cleanup > _RL_CLEANUP_INTERVAL:
            stale = [cid for cid, ts_list in _rl_timestamps.items()
                     if not any(t > cutoff for t in ts_list)]
            for cid in stale:
                del _rl_timestamps[cid]
            _rl_last_cleanup = now
        return True


def _friendly_error(exc: Exception, command: str = "") -> str:
    """Convert raw exception into a user-friendly Telegram message."""
    t = type(exc).__name__
    msg = str(exc)
    if "ReadTimeout" in t or "Timeout" in t:
        return f"Request timed out — the model took too long. Try again or use a simpler command."
    if "PERMISSION_DENIED" in msg or "AuthenticationError" in msg:
        return "API authentication error. Contact the administrator."
    if "RESOURCE_EXHAUSTED" in msg or "429" in msg:
        return "Rate limit reached. Please wait 30 seconds and try again."
    if "RateLimitError" in msg:
        return "Rate limit reached. Please wait 30 seconds and try again."
    logger.error("Unhandled error in %s: %s: %s", command, t, msg)
    return f"Something went wrong running {command}. Please try again in a moment."

class _SecretRedactFilter(logging.Filter):
    """Redacts known secret patterns from log records before they are emitted."""

    _SECRETS: list = []

    @classmethod
    def register(cls, secret: str) -> None:
        if secret and secret not in cls._SECRETS:
            cls._SECRETS.append(secret)

    def filter(self, record: logging.LogRecord) -> bool:
        msg = record.getMessage()
        for secret in self._SECRETS:
            if secret in msg:
                record.msg    = record.msg.replace(secret, f"{secret[:4]}***")
                record.args   = ()
        return True


def _setup_logging() -> logging.Logger:
    """Configure logging. Set LOG_FORMAT=json in .env for structured JSON logs
    (recommended for production deployments with log aggregation tools).
    Default: human-readable plaintext for development.
    """
    redact_filter = _SecretRedactFilter()
    log_format    = os.getenv("LOG_FORMAT", "text").lower()

    if log_format == "json":
        try:
            from pythonjsonlogger.jsonlogger import JsonFormatter
            handler   = logging.StreamHandler()
            formatter = JsonFormatter(
                "%(asctime)s %(levelname)s %(name)s %(message)s",
                rename_fields={"asctime": "ts", "levelname": "level", "name": "logger"},
            )
            handler.setFormatter(formatter)
            handler.addFilter(redact_filter)
            logging.root.setLevel(logging.INFO)
            logging.root.handlers = [handler]
        except ImportError:
            # Fallback to plaintext if library not installed
            _setup_plaintext_logging(redact_filter)
    else:
        _setup_plaintext_logging(redact_filter)

    logging.getLogger("fontTools").setLevel(logging.ERROR)
    return logging.getLogger(__name__)


def _setup_plaintext_logging(redact_filter: logging.Filter) -> None:
    handler = logging.StreamHandler()
    handler.addFilter(redact_filter)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[handler],
        force=True,
    )


logger = _setup_logging()

# Register secrets for redaction after loading env
for _secret_key in ("TELEGRAM_BOT_TOKEN", "ANTHROPIC_API_KEY",
                    "META_ACCESS_TOKEN", "TIKTOK_ACCESS_TOKEN",
                    "GSC_CREDENTIALS_FILE", "PAGESPEED_API_KEY"):
    _val = os.getenv(_secret_key, "")
    if _val:
        _SecretRedactFilter.register(_val)

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
POLLING_TIMEOUT = int(os.getenv("TELEGRAM_POLLING_TIMEOUT", "30"))
DEFAULT_AGENT = os.getenv("TELEGRAM_DEFAULT_AGENT", "ads")

if not BOT_TOKEN:
    raise ValueError("TELEGRAM_BOT_TOKEN is not set — add it to your .env file")

# ── Auth allowlist ────────────────────────────────────────────────────────────
# Set ALLOWED_CHAT_IDS=123456789,987654321 in .env to restrict access.
# If not set → WARNING logged on every startup and on every unauthorised message.
_raw_ids = os.getenv("ALLOWED_CHAT_IDS", "").strip()
ALLOWED_CHAT_IDS: Set[int] = {
    int(x.strip()) for x in _raw_ids.split(",") if x.strip().lstrip("-").isdigit()
}
if not ALLOWED_CHAT_IDS:
    logger.warning(
        "⚠️  SECURITY: ALLOWED_CHAT_IDS is not set — bot is open to ANYONE. "
        "Set ALLOWED_CHAT_IDS=<your_telegram_id> in .env before exposing this bot. "
        "Get your Telegram ID from @userinfobot."
    )

BASE_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"

# Canon commands that invoke audit mode
# Google Canon: /audit /weekly /monthly /tracking /incident /feed /pmax /quarterly /searchterms /launch /semantic /fixlist
# Meta Canon:   /creative /scale /audiences /asc /retargeting /attribution /dpa /abtest /seasonal /ios14
# TikTok Canon: /smartplus /hookrate
LIVE_AUDIT_COMMAND = "/liveaudit"  # pulls real Google Ads data then runs Canon

CANON_COMMANDS = {
    # Google
    "/audit", "/weekly", "/monthly", "/tracking", "/incident",
    "/feed", "/pmax", "/quarterly", "/searchterms", "/launch", "/semantic", "/fixlist",
    # Meta
    "/creative", "/scale", "/audiences", "/asc", "/retargeting",
    "/attribution", "/dpa", "/abtest", "/seasonal", "/ios14",
    # TikTok
    "/smartplus", "/hookrate",
    # Cross-platform — Measurement 2026 & B2B
    "/measurement", "/b2b", "/crm", "/leadgen",
}

DEMO_COMMAND = "/demo"

# Skill commands: non-audit modes accessible directly from Telegram
# Format: /command → mode passed to AdsAgent.run()
SKILL_COMMANDS: Dict[str, str] = {
    "/plan":        "plan",
    "/analyze":     "analyze",
    "/copy":        "copy",
    "/retarget":    "retargeting",
    "/budget":      "budget",
    "/research":    "research",
    "/landing":     "landing",
    "/forecast":    "forecast",
}

SEO_COMMANDS: Dict[str, str] = {
    "/seo":       "seo",
    "/technical": "technical",
    "/content":   "content",
    "/cluster":   "cluster",
    "/aeo":       "aeo",
    "/schema":    "schema",
    "/backlinks": "backlinks",
    "/local":     "local",
    "/write":     "article",
    "/brief":     "brief",
    "/meta":      "meta",
    "/rewrite":   "rewrite",
}

STRATEGY_COMMANDS: Dict[str, str] = {
    "/strategy":    "general",
    "/gtm":         "gtm",
    "/positioning": "positioning",
    "/channelmix":  "channel_mix",
    "/kpi":         "kpi",
}

CREATIVE_COMMANDS: Dict[str, str] = {
    "/concept": "concept",
    "/script":  "script",
    "/ugc":     "ugc_brief",
    "/adcopy":  "copy",
}

# Max Telegram message length
TG_MAX_LEN = 4000


class TelegramAgentBot:
    def __init__(self):
        self.agent = AdvertisingAnalyticsAgent()
        if not self.agent.claude_enabled:
            raise RuntimeError("Claude API not available. Check ANTHROPIC_API_KEY in .env")

        # Persistence: init DB, restore states and conversation histories
        storage.init_db()
        self.chat_state: Dict[int, Dict[str, Any]] = storage.load_all_states()
        # Restore per-chat conversation histories into the ads agent
        histories = storage.load_all_histories()
        ads_agent = self.agent.agents.get_agent("ads")
        if ads_agent and histories:
            ads_agent.restore_histories(histories)

        # Per-chat lock: prevents two concurrent LLM calls for the same chat_id
        self._chat_locks: Dict[int, threading.Lock] = {}

        self.available_agents = list(self.agent.list_agents().keys())
        self.bot_info = self._get_bot_info()
        logger.info("Bot ready: @%s (%s)", self.bot_info.get("username"), self.bot_info.get("id"))

    # ── Telegram API helpers ─────────────────────────────────────────────────

    def _api(self, method: str, **kwargs) -> Optional[dict]:
        try:
            r = requests.post(f"{BASE_URL}/{method}", json=kwargs, timeout=30)
            data = r.json()
            if not data.get("ok"):
                logger.error("%s failed: %s", method, data)
            else:
                if method == "sendMessage":
                    logger.info("sendMessage OK → chat_id=%s len=%d",
                                kwargs.get("chat_id"), len(str(kwargs.get("text", ""))))
            return data
        except Exception as exc:
            logger.error("%s error: %s", method, exc)
            return None

    def send_message(self, chat_id: int, text: str, html: bool = False) -> None:
        """Send message, splitting if needed to stay within Telegram's 4096-char limit."""
        if not text:
            return
        chunks = self._split(text)
        kwargs = {"parse_mode": "HTML"} if html else {}
        for chunk in chunks:
            self._api("sendMessage", chat_id=chat_id, text=chunk, **kwargs)
            if len(chunks) > 1:
                time.sleep(0.3)

    def send_typing(self, chat_id: int) -> None:
        self._api("sendChatAction", chat_id=chat_id, action="typing")

    def send_document(self, chat_id: int, pdf_bytes: bytes,
                      filename: str, caption: str = "") -> None:
        """Send a PDF file as a Telegram document."""
        try:
            r = requests.post(
                f"{BASE_URL}/sendDocument",
                data={"chat_id": chat_id, "caption": caption},
                files={"document": (filename, pdf_bytes, "application/pdf")},
                timeout=60,
            )
            data = r.json()
            if not data.get("ok"):
                logger.error("sendDocument failed: %s", data)
        except Exception as exc:
            logger.error("sendDocument error: %s", exc)

    def _get_bot_info(self) -> dict:
        r = requests.get(f"{BASE_URL}/getMe", timeout=30)
        r.raise_for_status()
        return r.json().get("result", {})

    def get_updates(self, offset: Optional[int] = None):
        payload: dict = {"timeout": POLLING_TIMEOUT, "allowed_updates": ["message"]}
        if offset is not None:
            payload["offset"] = offset
        r = requests.get(f"{BASE_URL}/getUpdates", params=payload, timeout=POLLING_TIMEOUT + 10)
        r.raise_for_status()
        return r.json().get("result", [])

    @staticmethod
    def _split(text: str) -> list:
        """Split text into chunks ≤ TG_MAX_LEN, breaking on newlines."""
        if len(text) <= TG_MAX_LEN:
            return [text]
        chunks = []
        while text:
            if len(text) <= TG_MAX_LEN:
                chunks.append(text)
                break
            split_at = text.rfind("\n", 0, TG_MAX_LEN)
            if split_at == -1:
                split_at = TG_MAX_LEN
            chunks.append(text[:split_at])
            text = text[split_at:].lstrip("\n")
        return chunks

    # ── Chat state ────────────────────────────────────────────────────────────

    def _state(self, chat_id: int) -> dict:
        if chat_id not in self.chat_state:
            default = {
                "agent": DEFAULT_AGENT,
                "platform": "google",
                "project": "",
                "account_type": "",
            }
            self.chat_state[chat_id] = default
            storage.save_state(chat_id, default)
        return self.chat_state[chat_id]

    def get_chat_agent(self, chat_id: int) -> str:
        return self._state(chat_id).get("agent", DEFAULT_AGENT)

    def set_chat_agent(self, chat_id: int, agent_type: str) -> None:
        state = self._state(chat_id)
        state["agent"] = agent_type
        storage.save_state(chat_id, state)

    # ── Message router ────────────────────────────────────────────────────────

    def handle_message(self, message: dict) -> None:
        chat_id = message["chat"]["id"]
        user_id = message.get("from", {}).get("id", chat_id)

        # Auth: reject if allowlist is configured and neither chat nor user is on it
        if ALLOWED_CHAT_IDS and chat_id not in ALLOWED_CHAT_IDS and user_id not in ALLOWED_CHAT_IDS:
            logger.warning("Rejected unauthorised access: chat_id=%s user_id=%s", chat_id, user_id)
            self.send_message(chat_id, "Access denied. Contact the administrator.")
            return

        # Rate limiting: allow up to _RL_MAX_REQUESTS per _RL_WINDOW_SECONDS per chat
        if not _check_rate_limit(chat_id):
            logger.warning("Rate limit hit: chat_id=%s", chat_id)
            self.send_message(
                chat_id,
                f"Too many requests. Please wait {_RL_WINDOW_SECONDS} seconds and try again.",
            )
            return

        text = message.get("text", "").strip()
        if not text:
            self.send_message(chat_id, "Please send a text message.")
            return

        parts = text.split(maxsplit=1)
        cmd = parts[0].lower().split("@")[0]   # strip @botname suffix in group chats
        arg = parts[1].strip() if len(parts) > 1 else ""

        if cmd in ("/start", "/help"):
            self.send_welcome(chat_id)
        elif cmd == "/skills":
            self.send_skills_help(chat_id)
        elif cmd == LIVE_AUDIT_COMMAND:
            self._run_live_audit_async(chat_id, arg)
        elif cmd == DEMO_COMMAND:
            self._run_demo_async(chat_id, arg)
        elif cmd == "/agent":
            self.change_agent(chat_id, arg)
        elif cmd == "/list":
            self.send_agent_list(chat_id)
        elif cmd == "/clear":
            self._clear_history(chat_id)
        elif cmd == "/setup":
            self.handle_setup(chat_id, arg)
        elif cmd == "/status":
            self.send_status(chat_id)
        elif cmd == "/cost":
            self.send_cost(chat_id)
        elif cmd in CANON_COMMANDS:
            self._run_canon_async(chat_id, cmd, arg)
        elif cmd in SKILL_COMMANDS:
            self._run_skill_async(chat_id, cmd, SKILL_COMMANDS[cmd], arg)
        elif cmd in SEO_COMMANDS:
            self._run_other_agent_async(chat_id, "seo", cmd, SEO_COMMANDS[cmd], arg)
        elif cmd in STRATEGY_COMMANDS:
            self._run_other_agent_async(chat_id, "strategy", cmd, STRATEGY_COMMANDS[cmd], arg)
        elif cmd in CREATIVE_COMMANDS:
            self._run_other_agent_async(chat_id, "creative", cmd, CREATIVE_COMMANDS[cmd], arg)
        elif cmd.startswith("/"):
            self.send_message(chat_id, "Unknown command. Use /help or /skills for command list.")
        else:
            # Regular chat with current agent
            self._run_chat_async(chat_id, text)

    # ── Canon audit commands ──────────────────────────────────────────────────

    def _run_live_audit_async(self, chat_id: int, arg: str) -> None:
        """
        Agentic live audit — routes to Google / Meta / TikTok based on current platform,
        Claude fetches data iteratively via tools then produces Canon Fixlist + PDF.
        """
        state    = self._state(chat_id)
        platform = state.get("platform", "google")

        # ── Platform routing ──────────────────────────────────────────────────
        if platform == "google":
            if not GOOGLE_ADS_AVAILABLE:
                self.send_message(
                    chat_id,
                    "Google Ads API not configured.\n"
                    "Run: python setup_google_ads_oauth.py\n"
                    "Then set GOOGLE_ADS_CUSTOMER_ID in .env"
                )
                return
            account_id = os.getenv("GOOGLE_ADS_CUSTOMER_ID") or arg.strip()
            if not account_id:
                self.send_message(chat_id,
                    "Provide a Customer ID:\n/liveaudit 1234567890\n\n"
                    "Or set GOOGLE_ADS_CUSTOMER_ID in .env")
                return
            tools         = GOOGLE_ADS_TOOLS
            tool_executor = lambda name, inp: _gads_execute_tool(name, {**inp, "customer_id": account_id})
            system_hint   = (
                "Audit protocol:\n"
                "1. Start with get_account_settings (P0: auto-tagging must be ON).\n"
                "2. get_conversion_actions — verify Primary conversion exists.\n"
                "3. get_campaigns — performance overview.\n"
                "4. get_wasted_spend and get_quality_scores only if tracking gates pass.\n"
                "5. Fetch only what the situation requires."
            )
            tool_labels = {
                "get_account_settings":   "Checking account settings...",
                "get_campaigns":          "Fetching campaign performance...",
                "get_conversion_actions": "Checking conversion tracking...",
                "get_wasted_spend":       "Scanning for wasted spend...",
                "get_quality_scores":     "Fetching Quality Scores...",
            }

        elif platform == "meta":
            if not META_ADS_AVAILABLE:
                self.send_message(
                    chat_id,
                    "Meta Ads API not configured.\n"
                    "Set META_ACCESS_TOKEN and META_ACCOUNT_ID in .env\n"
                    "See .env.example for setup instructions."
                )
                return
            account_id = os.getenv("META_ACCOUNT_ID") or arg.strip()
            if not account_id:
                self.send_message(chat_id,
                    "Provide an Account ID:\n/liveaudit act_1234567890\n\n"
                    "Or set META_ACCOUNT_ID in .env")
                return
            tools         = META_ADS_TOOLS
            tool_executor = lambda name, inp: _meta_execute_tool(name, {**inp, "account_id": account_id})
            system_hint   = (
                "Audit protocol:\n"
                "1. Start with get_meta_account_info (P0: account must be ACTIVE).\n"
                "2. get_meta_pixels — verify Pixel is firing (P0 gate).\n"
                "3. get_meta_campaigns — performance, frequency, ROAS.\n"
                "4. get_meta_adsets — audience structure, frequency.\n"
                "5. get_meta_creatives — hook rate, CTR, creative fatigue.\n"
                "6. Fetch only what the situation requires."
            )
            tool_labels = {
                "get_meta_account_info": "Checking account info...",
                "get_meta_pixels":       "Checking Pixel tracking...",
                "get_meta_campaigns":    "Fetching campaign performance...",
                "get_meta_adsets":       "Fetching ad set data...",
                "get_meta_creatives":    "Analyzing creative performance...",
            }

        elif platform == "tiktok":
            if not TIKTOK_ADS_AVAILABLE:
                self.send_message(
                    chat_id,
                    "TikTok Ads API not configured.\n"
                    "Set TIKTOK_ACCESS_TOKEN and TIKTOK_ADVERTISER_ID in .env\n"
                    "See .env.example for setup instructions."
                )
                return
            account_id = os.getenv("TIKTOK_ADVERTISER_ID") or arg.strip()
            if not account_id:
                self.send_message(chat_id,
                    "Provide an Advertiser ID:\n/liveaudit 1234567890\n\n"
                    "Or set TIKTOK_ADVERTISER_ID in .env")
                return
            tools         = TIKTOK_ADS_TOOLS
            tool_executor = lambda name, inp: _tiktok_execute_tool(name, {**inp, "advertiser_id": account_id})
            system_hint   = (
                "Audit protocol:\n"
                "1. Start with get_tiktok_advertiser_info (P0: account must be ACTIVE).\n"
                "2. get_tiktok_campaigns — spend, CTR, hook rate, frequency, CPA.\n"
                "3. get_tiktok_creatives — hook rate, 2s/6s hold, completion rate.\n"
                "4. get_tiktok_adgroups — bid strategy, optimization goals.\n"
                "5. Fetch only what the situation requires."
            )
            tool_labels = {
                "get_tiktok_advertiser_info": "Checking advertiser info...",
                "get_tiktok_campaigns":       "Fetching campaign performance...",
                "get_tiktok_creatives":       "Analyzing creative performance...",
                "get_tiktok_adgroups":        "Fetching ad group data...",
            }

        else:
            self.send_message(chat_id, f"Live audit not supported for platform: {platform}")
            return

        project      = state.get("project") or f"Account {account_id}"
        account_type = state.get("account_type") or ""

        self.send_typing(chat_id)
        self.send_message(
            chat_id,
            f"Starting agentic audit on {platform.capitalize()} Ads — {account_id}...\n"
            f"Project: {project}\n\n"
            "Claude will fetch data as needed and run Canon rules.\n"
            "Expect 60-120 seconds."
        )

        _SYSTEM_PROMPT = f"""You are a Canon Audit specialist for {platform.capitalize()} Ads.
You have access to live {platform.capitalize()} Ads data via tools. Use them to gather evidence,
then produce a structured Canon audit.

Account context:
- Account ID: {account_id}
- Project: {project}
- Account type: {account_type or "unknown"}

{system_hint}

Output format:
- Full Canon Fixlist table (P0 → P1 → P2)
- Then exactly: ===TELEGRAM_REPORT=== ... ===END_TELEGRAM_REPORT===
"""

        def _tool_progress(name: str, inputs: dict) -> None:
            msg = tool_labels.get(name, f"Calling {name}...")
            self.send_message(chat_id, msg)

        def _call():
            lock = self._chat_locks.setdefault(chat_id, threading.Lock())
            if not lock.acquire(blocking=False):
                self.send_message(chat_id, "A request is already running. Please wait.")
                return
            stop_typing = threading.Event()
            try:
                def _typing_loop():
                    while not stop_typing.is_set():
                        self.send_typing(chat_id)
                        stop_typing.wait(4)
                threading.Thread(target=_typing_loop, daemon=True).start()

                text = self.agent.run_agent_loop(
                    system_prompt=_SYSTEM_PROMPT,
                    task=(
                        f"Run a full Canon audit on {platform.capitalize()} Ads account {account_id}. "
                        f"Project: {project}. Account type: {account_type or 'unknown'}. "
                        "Fetch the data you need, then produce a Canon Fixlist (P0→P1→P2) "
                        "and the TELEGRAM_REPORT block."
                    ),
                    tools=tools,
                    tool_executor=tool_executor,
                    on_tool_call=_tool_progress,
                    max_iterations=12,
                )

                tg_block = extract_telegram_report(text)
                if tg_block:
                    tg_msg = render_telegram_report(
                        tg_block,
                        project=project,
                        platform=platform,
                        command="/liveaudit",
                    )
                else:
                    tg_msg = f"<b>Live Audit — {project}</b>\n" + format_for_telegram(text)
                self.send_message(chat_id, tg_msg, html=True)

                full_text = extract_full_fixlist(text)
                try:
                    pdf_bytes = build_report_pdf(
                        output_text=full_text,
                        project=project,
                        platform=platform,
                        mode="live audit",
                        date_range="last 30 days",
                    )
                    proj_slug = project.replace(" ", "_")[:30]
                    filename  = f"{proj_slug}_liveaudit_{datetime.now().strftime('%Y%m%d')}.pdf"
                    self.send_typing(chat_id)
                    self.send_document(chat_id, pdf_bytes, filename, caption="Canon Audit Report")
                except Exception as pdf_exc:
                    logger.warning("Live audit PDF failed: %s", pdf_exc)
                    self.send_message(chat_id, "PDF could not be generated. Full results above.")

            except Exception as exc:
                logger.exception("Live audit failed")
                self.send_message(chat_id, _friendly_error(exc, "/liveaudit"))
            finally:
                stop_typing.set()
                lock.release()

        threading.Thread(target=_call, daemon=True).start()

    def _run_demo_async(self, chat_id: int, arg: str) -> None:
        """Run a pre-loaded demo audit for the current platform — no data paste needed."""
        state = self._state(chat_id)
        platform = state.get("platform", "google")
        self.send_typing(chat_id)
        self.send_message(
            chat_id,
            f"Running /demo audit on a sample {platform.capitalize()} Ads account...\n"
            "This uses pre-loaded realistic account data to showcase the Canon audit system.\n\n"
            "Running full audit — 30–120 seconds."
        )

        def _call():
            lock = self._chat_locks.setdefault(chat_id, threading.Lock())
            if not lock.acquire(blocking=False):
                self.send_message(chat_id, "A request is already running. Please wait.")
                return
            stop_typing = threading.Event()
            try:
                threading.Thread(
                    target=lambda: [self.send_typing(chat_id) or stop_typing.wait(4)
                                    for _ in iter(lambda: stop_typing.is_set(), True)],
                    daemon=True,
                ).start()

                payload = get_demo_payload(platform)
                result  = self.agent.run_agent("ads", payload)
                text     = result.get("result", "No response from agent.")
                tg_block = extract_telegram_report(text)
                if tg_block:
                    tg_msg = render_telegram_report(
                        tg_block,
                        project=payload.get("project", "Demo"),
                        platform=state.get("platform", "google"),
                        command="/demo",
                    )
                else:
                    tg_msg = f"📋 <b>/demo — {payload.get('project','Demo')}</b>\n" + format_for_telegram(text)
                self.send_message(chat_id, tg_msg, html=True)

                full_text = extract_full_fixlist(text)
                try:
                    pdf_bytes = build_report_pdf(
                        output_text=full_text,
                        project=payload.get("project", "Demo"),
                        platform=platform,
                        mode="demo audit",
                        date_range=payload.get("date_range", ""),
                    )
                    proj_slug = (payload.get("project", "demo") or "demo").replace(" ", "_")[:30]
                    filename  = f"{proj_slug}_demo_{datetime.now().strftime('%Y%m%d')}.pdf"
                    self.send_typing(chat_id)
                    self.send_document(chat_id, pdf_bytes, filename, caption="Demo Canon Audit Report")
                except Exception as pdf_exc:
                    logger.warning("Demo PDF failed: %s", pdf_exc)

            except Exception as exc:
                logger.exception("Demo command failed")
                self.send_message(chat_id, f"Demo error: {exc}")
            finally:
                stop_typing.set()
                lock.release()

        threading.Thread(target=_call, daemon=True).start()

    def _run_canon_async(self, chat_id: int, command: str, notes: str) -> None:
        """Run Canon audit command in background thread."""
        state = self._state(chat_id)
        self.send_typing(chat_id)

        # Warn if platform was never explicitly configured (still at default)
        platform_warn = ""
        if not storage.has_explicit_platform(chat_id):
            platform_warn = "\n\nPlatform not set — defaulting to Google Ads. Use /setup platform meta|tiktok to change."

        self.send_message(
            chat_id,
            f"Running {command}...\n"
            f"Platform: {state['platform']} | Account: {state['account_type'] or 'not set'} | "
            f"Project: {state['project'] or 'not set'}\n\n"
            f"This takes 30–90 seconds — results coming up.{platform_warn}"
        )

        def _call():
            lock = self._chat_locks.setdefault(chat_id, threading.Lock())
            if not lock.acquire(blocking=False):
                self.send_message(chat_id, "A request is already running. Please wait for it to finish.")
                return
            stop_typing = threading.Event()
            progress_sent = threading.Event()
            try:
                def _typing_loop():
                    elapsed = 0
                    while not stop_typing.is_set():
                        self.send_typing(chat_id)
                        stop_typing.wait(4)
                        elapsed += 4
                        # Progress update after ~20 seconds
                        if elapsed >= 20 and not progress_sent.is_set():
                            progress_sent.set()
                            self.send_message(chat_id, "Still working — running Canon rules across all checks...")

                threading.Thread(target=_typing_loop, daemon=True).start()

                payload = {
                    "platform": state["platform"],
                    "mode": "audit",
                    "command": command,
                    "project": state["project"],
                    "account_type": state["account_type"],
                    "notes": notes,
                    "goal": notes or "optimize performance",
                }
                result = self.agent.run_agent("ads", payload)
                text = result.get("result", "No response from agent.")

                tg_block = extract_telegram_report(text)
                if tg_block:
                    tg_msg = render_telegram_report(
                        tg_block,
                        project=state["project"] or "project",
                        platform=state["platform"],
                        command=command,
                    )
                else:
                    header = f"<b>{command} — {state['project'] or 'project'}</b>\n"
                    tg_msg = header + format_for_telegram(text)

                self.send_message(chat_id, tg_msg, html=True)

                full_text = extract_full_fixlist(text)
                try:
                    pdf_bytes = build_report_pdf(
                        output_text=full_text,
                        project=state["project"] or "project",
                        platform=state["platform"],
                        mode=command.lstrip("/"),
                        date_range=payload.get("date_range", ""),
                    )
                    date_str  = datetime.now().strftime("%Y%m%d")
                    proj_slug = (state["project"] or "report").replace(" ", "_")[:30]
                    filename  = f"{proj_slug}_{command.lstrip('/')}_{date_str}.pdf"
                    self.send_typing(chat_id)
                    self.send_document(
                        chat_id, pdf_bytes, filename,
                        caption=f"Canon Report — {state['project'] or command}",
                    )
                except Exception as pdf_exc:
                    logger.warning("PDF generation failed: %s", pdf_exc)
                    self.send_message(chat_id, "PDF report could not be generated. Full results are in the message above.")

            except Exception as exc:
                logger.exception("Canon command %s failed", command)
                self.send_message(chat_id, _friendly_error(exc, command))
            finally:
                stop_typing.set()
                lock.release()

        threading.Thread(target=_call, daemon=True).start()

    # ── Skill commands (plan / analyze / copy / forecast / etc.) ─────────────

    def _run_skill_async(self, chat_id: int, command: str, mode: str, notes: str) -> None:
        """Run a non-audit skill mode (plan, analyze, copy, forecast, ...) in background thread."""
        state = self._state(chat_id)
        self.send_typing(chat_id)

        _MODE_LABELS = {
            "plan": "Campaign Plan", "analyze": "Analysis", "copy": "Ad Copy",
            "retargeting": "Retargeting Strategy", "ab_test": "A/B Test Design",
            "budget": "Budget Allocation", "research": "Research", "landing": "Landing Page Audit",
            "forecast": "Forecast",
        }
        label = _MODE_LABELS.get(mode, mode.capitalize())

        platform_warn = ""
        if mode not in ("budget", "forecast") and not storage.has_explicit_platform(chat_id):
            platform_warn = "\nPlatform not set — defaulting to Google Ads. Use /setup platform to change."

        self.send_message(
            chat_id,
            f"Running {label}...\n"
            f"Platform: {state['platform']} | Project: {state['project'] or 'not set'}\n"
            f"This takes 20–60 seconds.{platform_warn}"
        )

        def _call():
            lock = self._chat_locks.setdefault(chat_id, threading.Lock())
            if not lock.acquire(blocking=False):
                self.send_message(chat_id, "A request is already running. Please wait.")
                return
            stop_typing = threading.Event()
            try:
                def _typing_loop():
                    while not stop_typing.is_set():
                        self.send_typing(chat_id)
                        stop_typing.wait(4)

                threading.Thread(target=_typing_loop, daemon=True).start()

                payload = {
                    "platform":     state["platform"],
                    "mode":         mode,
                    "product":      state["project"] or notes or "product",
                    "project":      state["project"],
                    "account_type": state["account_type"],
                    "goal":         "conversions",
                    "context":      notes,
                    "notes":        notes,
                    "budget":       0,
                    "platforms":    [state["platform"]] if state["platform"] else ["google"],
                }
                result = self.agent.run_agent("ads", payload)
                text   = result.get("result", "No response from agent.")

                header   = f"<b>{command} — {label}</b>\n"
                body     = format_for_telegram(text)
                # Keep skill responses to one Telegram message (≤ 3800 chars incl. header)
                max_body = TG_MAX_LEN - len(header) - 80
                if len(body) > max_body:
                    cut  = body.rfind("\n", 0, max_body)
                    body = body[: cut if cut > 0 else max_body]
                    body += "\n\n<i>Output truncated. Ask a more focused question for a shorter result.</i>"
                self.send_message(chat_id, header + body, html=True)

            except Exception as exc:
                logger.exception("Skill command %s (%s) failed", command, mode)
                self.send_message(chat_id, _friendly_error(exc, command))
            finally:
                stop_typing.set()
                lock.release()

        threading.Thread(target=_call, daemon=True).start()

    # ── SEO / Strategy / Creative skill commands ──────────────────────────────

    def _run_other_agent_async(
        self,
        chat_id: int,
        agent_type: str,
        command: str,
        mode: str,
        notes: str,
    ) -> None:
        """Run SEO, Strategy, or Creative skill in a background thread."""
        state = self._state(chat_id)
        self.send_typing(chat_id)

        _LABELS: Dict[str, Dict[str, str]] = {
            "seo": {
                "seo": "SEO Strategy", "aeo": "AEO/GEO Optimization",
                "technical": "Technical SEO Audit", "content": "Content Audit",
                "local": "Local SEO", "schema": "Schema Markup",
                "backlinks": "Backlink Audit", "cluster": "Keyword Cluster",
                "article": "SEO Article", "brief": "Content Brief",
                "meta": "Meta Tags", "rewrite": "Content Rewrite",
            },
            "strategy": {
                "general": "Marketing Strategy", "gtm": "Go-to-Market Plan",
                "positioning": "Brand Positioning", "channel_mix": "Channel Mix",
                "kpi": "KPI Framework",
            },
            "creative": {
                "concept": "Creative Concept", "copy": "Ad Copy",
                "script": "Video Script", "ugc_brief": "UGC Brief",
            },
        }
        label = _LABELS.get(agent_type, {}).get(mode, mode.capitalize())

        self.send_message(
            chat_id,
            f"Running {label}...\n"
            f"Project: {state.get('project') or 'not set'}\n"
            "This takes 20–60 seconds.",
        )

        def _call() -> None:
            lock = self._chat_locks.setdefault(chat_id, threading.Lock())
            if not lock.acquire(blocking=False):
                self.send_message(chat_id, "A request is already running. Please wait.")
                return
            stop_typing = threading.Event()
            try:
                def _typing_loop() -> None:
                    while not stop_typing.is_set():
                        self.send_typing(chat_id)
                        stop_typing.wait(4)

                threading.Thread(target=_typing_loop, daemon=True).start()

                project  = state.get("project", "")
                platform = state.get("platform", "google")

                if agent_type == "seo":
                    _WRITE_MODES = {"article", "brief", "meta", "rewrite"}
                    if mode in _WRITE_MODES:
                        # Writing modes: notes = topic or keywords (no URL needed)
                        kws = [w.strip() for w in notes.split(",") if w.strip()] if notes else []
                        payload: Dict[str, Any] = {
                            "mode":     mode,
                            "topic":    notes,
                            "keywords": kws,
                            "site":     project or "",
                            "industry": "",
                            "context":  notes,
                            "content":  notes,  # rewrite mode: notes = existing content
                        }
                    else:
                        # Audit/analysis modes: first token is site URL
                        words = notes.split(maxsplit=1) if notes else []
                        site  = words[0] if words else (project or "example.com")
                        payload = {
                            "mode":     mode,
                            "site":     site,
                            "industry": "",
                            "keywords": [],
                            "context":  notes,
                        }
                elif agent_type == "strategy":
                    payload = {
                        "mode":     mode,
                        "product":  project or notes or "product",
                        "goal":     notes or "grow revenue",
                        "industry": "",
                        "timeline": "3 months",
                        "context":  notes,
                    }
                else:  # creative
                    payload = {
                        "mode":     mode,
                        "product":  project or notes or "product",
                        "platform": platform,
                        "tone":     "modern, persuasive",
                        "context":  notes,
                    }

                result = self.agent.run_agent(agent_type, payload)
                text   = result.get("result", "No response from agent.")

                header   = f"<b>{command} — {label}</b>\n"
                body     = format_for_telegram(text)
                max_body = TG_MAX_LEN - len(header) - 80
                if len(body) > max_body:
                    cut  = body.rfind("\n", 0, max_body)
                    body = body[: cut if cut > 0 else max_body]
                    body += "\n\n<i>Output truncated. Ask a more focused question for a shorter result.</i>"
                self.send_message(chat_id, header + body, html=True)

            except Exception as exc:
                logger.exception("%s command %s (%s) failed", agent_type, command, mode)
                self.send_message(chat_id, _friendly_error(exc, command))
            finally:
                stop_typing.set()
                lock.release()

        threading.Thread(target=_call, daemon=True).start()

    # ── Regular agent chat ────────────────────────────────────────────────────

    def _run_chat_async(self, chat_id: int, text: str) -> None:
        """Run chat_with_agent in background thread."""
        agent_type = self.get_chat_agent(chat_id)
        if agent_type not in self.available_agents:
            agent_type = DEFAULT_AGENT
            self.set_chat_agent(chat_id, agent_type)

        logger.info("chat_id=%s agent=%s msg=%r", chat_id, agent_type, text[:80])
        self.send_typing(chat_id)

        def _call():
            lock = self._chat_locks.setdefault(chat_id, threading.Lock())
            if not lock.acquire(blocking=False):
                self.send_message(chat_id, "A request is already running. Please wait.")
                return
            stop_typing = threading.Event()
            try:
                def _typing_loop():
                    while not stop_typing.is_set():
                        self.send_typing(chat_id)
                        stop_typing.wait(4)

                threading.Thread(target=_typing_loop, daemon=True).start()

                response = self.agent.chat_with_agent(agent_type, text, chat_id=chat_id)
                result = response.get("result", response)
                self.send_message(
                    chat_id,
                    format_for_telegram(str(result)),
                    html=True,
                )

            except Exception as exc:
                logger.exception("Chat error")
                self.send_message(chat_id, _friendly_error(exc, "chat"))
            finally:
                stop_typing.set()
                lock.release()

        threading.Thread(target=_call, daemon=True).start()

    # ── Bot commands ──────────────────────────────────────────────────────────

    def send_welcome(self, chat_id: int) -> None:
        self.send_message(
            chat_id,
            "AI Performance Marketing Assistant.\n"
            "4 specialist agents: Ads · SEO · Strategy · Creative\n\n"
            "/demo — sample Canon audit, no data needed\n"
            "/liveaudit — live audit from your real ad account\n\n"
            "Quick start:\n"
            "/setup platform google|meta|tiktok\n"
            "/setup project ClientName\n\n"
            "Ads Canon: /audit /weekly /tracking /incident /scale ...\n"
            "Ads skills: /plan /analyze /copy /forecast /landing /budget\n"
            "SEO: /seo /technical /cluster /aeo /backlinks /schema\n"
            "Strategy: /strategy /gtm /positioning /channelmix /kpi\n"
            "Creative: /concept /script /ugc /adcopy\n\n"
            "/skills — full command list with examples\n\n"
            "Or just chat — I'll route to the right agent automatically."
        )

    def send_skills_help(self, chat_id: int) -> None:
        self.send_message(
            chat_id,
            "━━ ADS (Google · Meta · TikTok) ━━\n"
            "/plan — campaign launch strategy\n"
            "  /plan SaaS, $5k/mo, B2B UA\n"
            "/analyze — diagnose metrics\n"
            "  /analyze CTR 3.5%→1.8%, CPA up to $67\n"
            "/copy — RSA/DPA/TikTok ad copy\n"
            "  /copy CRM tool, USP: saves 5h/week\n"
            "/forecast — 3-scenario media plan\n"
            "  /forecast $10k, 3 months, ecom\n"
            "/landing — CRO audit\n"
            "  /landing https://site.com\n"
            "/budget — cross-platform allocation\n"
            "/research — keyword/audience research\n"
            "/retarget — remarketing funnel\n\n"
            "━━ SEO ━━\n"
            "/seo — general SEO strategy\n"
            "  /seo example.com e-commerce\n"
            "/technical — technical audit (CWV, crawl, indexing)\n"
            "  /technical mysite.com\n"
            "/cluster — topical cluster + keyword architecture\n"
            "  /cluster mysite.com CRM software\n"
            "/aeo — AI/GEO optimization for LLM citations\n"
            "/backlinks — backlink audit + link building plan\n"
            "/schema — schema markup audit + JSON-LD\n"
            "/local — local SEO, GBP, NAP, map pack\n\n"
            "━━ STRATEGY ━━\n"
            "/strategy — full marketing plan\n"
            "  /strategy B2B SaaS, $15k/mo, 3 months\n"
            "/gtm — go-to-market launch plan\n"
            "/positioning — brand positioning + messaging\n"
            "/channelmix — channel selection + budget split\n"
            "/kpi — KPI framework + measurement plan\n\n"
            "━━ CREATIVE ━━\n"
            "/concept — 3 creative concepts + visual direction\n"
            "  /concept fitness app, audience: women 25-35\n"
            "/script — video script (hook→problem→solution→CTA)\n"
            "/ugc — UGC creator brief: talking points, shot list\n"
            "/adcopy — ad copy variants for any platform\n\n"
            "All commands use your /setup platform and project."
        )

    def handle_setup(self, chat_id: int, arg: str) -> None:
        """Handle /setup <field> <value>"""
        if not arg:
            self.send_status(chat_id)
            return

        parts = arg.split(maxsplit=1)
        if len(parts) < 2:
            self.send_message(
                chat_id,
                "Usage:\n"
                "/setup platform google|meta|tiktok\n"
                "/setup project YourClientName\n"
                "/setup account ecom|lead-gen|app"
            )
            return

        field, value = parts[0].lower(), parts[1].strip()
        state = self._state(chat_id)

        if field == "platform":
            _aliases = {"facebook": "meta", "instagram": "meta", "google_ads": "google"}
            allowed   = {"google", "meta", "tiktok", "facebook", "instagram"}
            raw = value.lower()
            if raw not in allowed:
                self.send_message(chat_id, f"Supported platforms: google, meta, tiktok")
                return
            normalised = _aliases.get(raw, raw)   # facebook→meta, instagram→meta
            state["platform"] = normalised
            state["platform_set_explicitly"] = True
            storage.save_state(chat_id, state)
            self.send_message(chat_id, f"Platform set: {state['platform']}")

        elif field == "project":
            state["project"] = value
            storage.save_state(chat_id, state)
            self.send_message(chat_id, f"Project set: {state['project']}")

        elif field in ("account", "type"):
            allowed = {"ecom", "lead-gen", "leadgen", "app"}
            if value.lower() not in allowed:
                self.send_message(chat_id, f"Supported account types: {', '.join(sorted(allowed))}")
                return
            state["account_type"] = value.lower()
            storage.save_state(chat_id, state)
            self.send_message(chat_id, f"Account type set: {state['account_type']}")

        else:
            self.send_message(chat_id, "Unknown field. Use: platform / project / account")

    def send_status(self, chat_id: int) -> None:
        state = self._state(chat_id)
        self.send_message(
            chat_id,
            f"Current settings:\n"
            f"  Agent:    {state.get('agent', DEFAULT_AGENT)}\n"
            f"  Platform: {state.get('platform', 'google')}\n"
            f"  Project:  {state.get('project') or '(not set)'}\n"
            f"  Account:  {state.get('account_type') or '(not set)'}"
        )

    def send_cost(self, chat_id: int) -> None:
        rows = storage.get_usage_summary(limit=50)
        if not rows:
            self.send_message(chat_id, "No API usage recorded yet.")
            return

        # Pricing per million tokens (as of 2025)
        PRICES = {
            "claude-opus-4-8":          {"input": 15.0,  "output": 75.0,  "cache_read": 1.5,  "cache_write": 18.75},
            "claude-sonnet-4-6":        {"input": 3.0,   "output": 15.0,  "cache_read": 0.3,  "cache_write": 3.75},
            "claude-haiku-4-5-20251001":{"input": 0.8,   "output": 4.0,   "cache_read": 0.08, "cache_write": 1.0},
        }

        def _cost(row):
            p = PRICES.get(row["model"], {"input": 3.0, "output": 15.0, "cache_read": 0.3, "cache_write": 3.75})
            return (
                row["input_tokens"]  * p["input"]        / 1_000_000 +
                row["output_tokens"] * p["output"]        / 1_000_000 +
                row["cache_read"]    * p["cache_read"]    / 1_000_000 +
                row["cache_write"]   * p["cache_write"]   / 1_000_000
            )

        total = sum(_cost(r) for r in rows)

        # Group by agent+mode
        breakdown: dict = {}
        for r in rows:
            key = f"{r['agent'] or '?'} / {r['mode'] or '?'}"
            if key not in breakdown:
                breakdown[key] = {"cost": 0.0, "calls": 0}
            breakdown[key]["cost"]  += _cost(r)
            breakdown[key]["calls"] += 1

        lines = [f"API cost (last {len(rows)} calls): ~${total:.4f}\n"]
        for key, v in sorted(breakdown.items(), key=lambda x: -x[1]["cost"]):
            lines.append(f"  {key}: ${v['cost']:.4f} ({v['calls']} calls)")

        lines.append(f"\nTop 5 recent calls:")
        for r in rows[:5]:
            c = _cost(r)
            lines.append(
                f"  {r['ts'][:16]} | {r['model'].replace('claude-','')[:16]} | "
                f"{r['agent']}/{r['mode']} | ${c:.4f} "
                f"(in:{r['input_tokens']} out:{r['output_tokens']})"
            )

        self.send_message(chat_id, "\n".join(lines))

    def send_agent_list(self, chat_id: int) -> None:
        self.send_message(chat_id, "Available agents: " + ", ".join(self.available_agents))

    def change_agent(self, chat_id: int, agent_type: str) -> None:
        if not agent_type:
            self.send_message(chat_id, "Specify an agent: /agent ads")
            return
        agent_type = agent_type.strip().lower()
        if agent_type not in self.available_agents:
            self.send_message(chat_id, "Agent not found. Available: " + ", ".join(self.available_agents))
            return
        self.set_chat_agent(chat_id, agent_type)
        self.agent.clear_agent_history(agent_type, chat_id=chat_id)
        self.send_message(chat_id, f"Agent: {agent_type}. History cleared.")

    def _clear_history(self, chat_id: int) -> None:
        agent_type = self.get_chat_agent(chat_id)
        self.agent.clear_agent_history(agent_type, chat_id=chat_id)
        self.send_message(chat_id, f"History cleared for agent: {agent_type}.")

    # ── Polling loop ──────────────────────────────────────────────────────────

    def run(self) -> None:
        offset = None
        while True:
            try:
                updates = self.get_updates(offset)
                if updates:
                    logger.info("Updates received: %d", len(updates))
                for item in updates:
                    offset = item["update_id"] + 1
                    if "message" in item:
                        self.handle_message(item["message"])
            except requests.RequestException as exc:
                logger.error("Telegram API error: %s", exc)
                time.sleep(5)
            except Exception as exc:
                logger.exception("Unhandled error: %s", exc)
                time.sleep(5)


def _ensure_single_instance() -> None:
    """Exit immediately if another bot instance is already running."""
    import ctypes
    import atexit

    pid_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "bot.pid")

    if os.path.exists(pid_file):
        try:
            old_pid = int(open(pid_file).read().strip())
            if old_pid != os.getpid():
                PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
                handle = ctypes.windll.kernel32.OpenProcess(
                    PROCESS_QUERY_LIMITED_INFORMATION, False, old_pid
                )
                if handle:
                    ctypes.windll.kernel32.CloseHandle(handle)
                    logging.getLogger(__name__).error(
                        "Bot already running (PID %d). Exiting.", old_pid
                    )
                    raise SystemExit(0)
        except (ValueError, OSError):
            pass  # stale file — overwrite

    with open(pid_file, "w") as f:
        f.write(str(os.getpid()))

    def _cleanup():
        try:
            if os.path.exists(pid_file):
                os.remove(pid_file)
        except OSError:
            pass

    atexit.register(_cleanup)


if __name__ == "__main__":
    _ensure_single_instance()
    bot = TelegramAgentBot()
    bot.run()
