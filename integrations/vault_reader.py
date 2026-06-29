"""
Reads Markdown files from the local Obsidian vault so the agent can use
them as runtime context without any Notion API calls.
"""
import functools
import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

_VAULT = Path(__file__).parent.parent / "vault"

_PLATFORM_KB: dict[str, str] = {
    "google": "google-ads.md",
    "meta":   "meta-ads.md",
    "tiktok": "tiktok-ads.md",
}

_AGENT_KB: dict[str, str] = {
    "seo":      "seo.md",
    "strategy": "strategy.md",
    "creative": "creative.md",
}

# Modes where injecting the full platform KB adds real value
KB_MODES = {"analyze", "research", "plan", "copy", "budget", "retargeting"}


@functools.lru_cache(maxsize=8)
def read_knowledge_base(platform: str) -> str:
    """Return the knowledge-base markdown for a given platform, or ''.
    Cached in-process — KB files change rarely; restart clears cache.
    """
    filename = _PLATFORM_KB.get(platform.lower().strip(), "")
    if not filename:
        return ""
    kb_path = _VAULT / "knowledge-base" / filename
    if not kb_path.exists():
        logger.warning("KB file not found for platform '%s': %s", platform, kb_path)
        return ""
    return kb_path.read_text(encoding="utf-8")


@functools.lru_cache(maxsize=8)
def read_agent_kb(agent_name: str) -> str:
    """Return the knowledge-base for a non-ads agent (seo, strategy), or ''.
    Cached in-process — KB files change rarely; restart clears cache.
    """
    filename = _AGENT_KB.get(agent_name.lower().strip(), "")
    if not filename:
        return ""
    kb_path = _VAULT / "knowledge-base" / filename
    if not kb_path.exists():
        return ""
    return kb_path.read_text(encoding="utf-8")


def read_vault_file(relative_path: str) -> str:
    """Return the content of any vault file by relative path, or ''."""
    path = _VAULT / relative_path
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8")


def validate_kb_files() -> dict:
    """Check all expected KB files exist. Returns {name: bool}. Logs warnings for missing."""
    status = {}
    for name, filename in {**_PLATFORM_KB, **_AGENT_KB}.items():
        path = _VAULT / "knowledge-base" / filename
        exists = path.exists()
        status[name] = exists
        if not exists:
            logger.warning("KB file missing: %s (expected at %s)", name, path)
    return status


def kb_context_block(platform: str) -> Optional[str]:
    """
    Return the raw knowledge-base text for a platform, or None.
    Passed as cached_context to chat_with_agent() — Anthropic caches it
    as a separate system block so repeated requests pay only read cost (~10%).
    """
    kb = read_knowledge_base(platform)
    return kb if kb else None


def agent_kb_context_block(agent_name: str) -> Optional[str]:
    """Return KB for a non-ads agent (seo, strategy), or None."""
    kb = read_agent_kb(agent_name)
    return kb if kb else None
