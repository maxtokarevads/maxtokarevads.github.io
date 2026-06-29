"""
Shared intent-routing logic for all agent routers.

Every agent router (ads, seo, strategy, creative) follows the same pattern:
  1. Try call_tool() — guaranteed JSON schema via Anthropic tool_use
  2. Fall back to chat_with_agent() + regex JSON extraction
  3. Return typed fallback on any error

This module provides route() so each router only needs to define its own
constants (_TOOL, _SYSTEM, _PROMPT_TEMPLATE, _validate, _FALLBACK) and
delegate the execution to this shared function.
"""
from __future__ import annotations

import json
import logging
import re
from typing import Any, Callable, Dict, Optional

logger = logging.getLogger(__name__)

_DEFAULT_MODEL = "claude-sonnet-4-6"


def route(
    analyzer: Optional[Any],
    message: str,
    *,
    prompt_template: str,
    tool: Dict[str, Any],
    system_prompt: str,
    validate: Callable[[Dict[str, Any]], Dict[str, Any]],
    fallback: Dict[str, Any],
    model: str = _DEFAULT_MODEL,
    name: str = "router",
) -> Dict[str, Any]:
    """
    Generic intent router used by all agent routers.

    Tries call_tool() first (guaranteed JSON schema enforcement by Anthropic API),
    falls back to JSON-prompt parsing for analyzers that don't support call_tool.
    Returns a copy of fallback on any error.

    Args:
        analyzer:         The LLM backend (ClaudeHTTPAnalyzer or ClaudeCodeAnalyzer).
        message:          Raw user message to classify.
        prompt_template:  Prompt string with {message} placeholder.
        tool:             Anthropic tool definition dict (name, description, input_schema).
        system_prompt:    System prompt for the classifier.
        validate:         Function that sanitises a raw classification dict.
        fallback:         Default result when classification fails.
        model:            Model override for classification (fast Sonnet by default).
        name:             Router name used in log messages.

    Returns:
        Validated classification dict (same shape as fallback).
    """
    if not analyzer:
        return dict(fallback)

    prompt = prompt_template.replace("{message}", message)

    # ── Preferred path: tool_use for guaranteed schema ─────────────────────────
    if callable(getattr(analyzer, "call_tool", None)):
        try:
            result = analyzer.call_tool(
                user_message=prompt,
                tool=tool,
                system_prompt=system_prompt,
                model_override=model,
            )
            if isinstance(result, dict):
                return validate(result)
        except Exception as exc:
            logger.warning("%s: call_tool failed, falling back to JSON parse: %s", name, exc)

    # ── Fallback path: JSON-prompt parsing ─────────────────────────────────────
    try:
        raw = analyzer.chat_with_agent(
            user_message=prompt,
            system_prompt=system_prompt,
            model_override=model,
        )
        if isinstance(raw, str):
            match = re.search(r"\{.*\}", raw.strip(), re.DOTALL)
            if match:
                return validate(json.loads(match.group(0)))
    except Exception as exc:
        logger.warning("%s: JSON-parse fallback also failed: %s", name, exc)

    return dict(fallback)
