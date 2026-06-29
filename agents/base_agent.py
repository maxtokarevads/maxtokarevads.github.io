from __future__ import annotations

import hashlib
import logging
import os
import re
from abc import ABC, abstractmethod
from datetime import date
from pathlib import Path
from typing import Any, ClassVar, Dict, List, Optional, Set, Tuple

logger = logging.getLogger(__name__)


def _slugify(text: str, max_len: int = 40) -> str:
    """Sanitize user input to a safe filesystem/Obsidian slug."""
    text = re.sub(r"https?://", "", text.lower().strip())
    text = re.sub(r"[^\w.\-]", "-", text)
    text = re.sub(r"-{2,}", "-", text)
    return text.strip("-")[:max_len]

MAX_HISTORY_TURNS  = 20
MAX_TRACKED_CHATS  = 1000  # evict oldest chats when _histories grows beyond this

# Shared output contract appended to every user prompt.
# Covers: language, format, no fabrication, char-limit enforcement.
OUTPUT_CONTRACT = """
---
Respond in the same language the user wrote in.
Be direct and concise — this is a chat conversation, not a document.
No headers (##, ###). Use bullet lists only when listing 3+ distinct items.
Give specific, actionable answers. If key context is missing, ask one focused question.
"""


class BaseAgent(ABC):
    """Base class for all agents."""

    # Agents this one should receive context from before running.
    # Override in subclasses: dependencies = ["strategy", "ads"]
    # AgentsManager reads this at registration time to build the dependency graph.
    dependencies: ClassVar[List[str]] = []

    def __init__(self, name: str, analyzer: Any):
        self.name     = name
        self.analyzer = analyzer
        # Per-chat history keyed by chat_id (int).
        # chat_id=0 is the default for callers that don't supply one.
        self._histories: Dict[int, List[Dict[str, Any]]] = {}

    @abstractmethod
    def run(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        raise NotImplementedError

    # ── Input validation helpers ───────────────────────────────────────────────

    def _validate_mode(self, raw_mode: str, supported: Set[str]) -> Optional[str]:
        """Return normalised mode string or None if unsupported."""
        mode = raw_mode.lower().strip() if raw_mode else ""
        return mode if mode in supported else None

    def _validate_platform(
        self,
        raw_platform: str,
        supported: Set[str],
        aliases: Optional[Dict[str, str]] = None,
    ) -> Optional[str]:
        """Return normalised platform string or None if unsupported."""
        p = raw_platform.lower().strip() if raw_platform else ""
        if aliases:
            p = aliases.get(p, p)
        return p if p in supported else None

    # ── Shared vault saving ────────────────────────────────────────────────────

    def _save_to_vault(
        self,
        filename: str,
        content: str,
        vault_dir: Path,
    ) -> None:
        """Write a campaign result to the vault. Shared by all agent subclasses.
        Failures are logged as warnings — never raise, never block the response.
        Skipped when TESTING env var is set to avoid polluting the real vault during tests.
        """
        if os.getenv("TESTING"):
            return
        try:
            vault_dir.mkdir(parents=True, exist_ok=True)
            (vault_dir / filename).write_text(content, encoding="utf-8")
        except Exception as exc:
            logger.warning("Failed to save to vault (%s): %s", filename, exc)

    @staticmethod
    def _prompt_hash(system_prompt: str) -> str:
        """Short SHA-256 prefix of the system prompt — stored in vault for prompt versioning."""
        return hashlib.sha256(system_prompt.encode()).hexdigest()[:12]

    def get_system_prompt(self, mode: Optional[str] = None) -> str:
        return (
            f"You are an experienced marketing specialist ({self.name}). "
            "You give concrete, structured recommendations with specific numbers and timelines."
        )

    def _build_prompt_with_contract(self, prompt: str) -> str:
        return prompt + OUTPUT_CONTRACT

    def chat(
        self,
        message: str,
        use_history: bool = True,
        chat_id: int = 0,
        mode: Optional[str] = None,
    ) -> Dict[str, Any]:
        if not self.analyzer:
            return {"error": "No analyzer configured"}

        history = self._histories.setdefault(chat_id, []) if use_history else None
        assistant_response = self.analyzer.chat_with_agent(
            user_message=self._build_prompt_with_contract(message),
            system_prompt=self.get_system_prompt(mode),
            history=history,
            agent_name=self.name,
            agent_mode=mode or "chat",
        )

        if not assistant_response:
            return {"error": "No response from model — try again or check API status"}

        if use_history:
            hist = self._histories.setdefault(chat_id, [])
            hist.append({"role": "user",      "content": message})
            hist.append({"role": "assistant",  "content": assistant_response})
            max_entries = MAX_HISTORY_TURNS * 2
            if len(hist) > max_entries:
                self._histories[chat_id] = hist[-max_entries:]
            # Evict oldest chats when the dict grows too large (memory guard)
            if len(self._histories) > MAX_TRACKED_CHATS:
                oldest_id = next(iter(self._histories))
                del self._histories[oldest_id]
            # Persist to SQLite (import lazily to avoid circular import)
            try:
                import storage as _storage
                _storage.save_history(chat_id, self._histories[chat_id])
            except Exception as exc:
                logger.warning("History persistence failed for chat %s: %s", chat_id, exc)

        return {"result": assistant_response}

    def clear_history(self, chat_id: Optional[int] = None) -> None:
        """Clear history for a specific chat_id (or all). Removes from disk too."""
        try:
            import storage as _storage
            if chat_id is None:
                # Collect keys BEFORE clearing so disk deletions still run
                all_ids = list(self._histories.keys())
                self._histories.clear()
                for cid in all_ids:
                    _storage.delete_history(cid)
            else:
                self._histories.pop(chat_id, None)
                _storage.delete_history(chat_id)
        except Exception:
            if chat_id is None:
                self._histories.clear()
            else:
                self._histories.pop(chat_id, None)

    @property
    def conversation_history(self) -> List[Dict[str, Any]]:
        """History for the default chat (chat_id=0). Used by tests and CLI."""
        return self._histories.get(0, [])

    async def arun(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Async entry point for agent execution.

        Default implementation wraps sync run() in a thread executor so it
        doesn't block the event loop. Subclasses may override with a fully
        async implementation that calls analyzer.achat_with_agent() directly.
        """
        import asyncio
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.run, payload)

    def restore_histories(self, histories: Dict[int, List[Dict[str, Any]]]) -> None:
        """Load persisted histories into memory. Call once on startup."""
        self._histories.update(histories)

    def _persist_routed_history(self, chat_id: int, message: str, response_text: str) -> None:
        """Append a routed run() exchange to history and sync to SQLite.

        Called by smart_chat() after a successful run() — avoids duplicating
        this 14-line block across every agent subclass.
        """
        if not response_text:
            return
        hist = self._histories.setdefault(chat_id, [])
        hist.append({"role": "user",      "content": message})
        hist.append({"role": "assistant", "content": response_text})
        max_entries = MAX_HISTORY_TURNS * 2
        if len(hist) > max_entries:
            self._histories[chat_id] = hist[-max_entries:]
        try:
            import storage as _storage
            _storage.save_history(chat_id, self._histories[chat_id])
        except Exception as exc:
            logger.warning("History persistence failed for chat %s: %s", chat_id, exc)
