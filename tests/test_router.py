"""Tests for agents.ads.router — no API calls."""
import json
import pytest
from agents.ads.router import route_intent, _FALLBACK, _PLATFORMS, _MODES


# ── Mock analyzers ────────────────────────────────────────────────────────────

class AnalyzerWithCallTool:
    """Simulates ClaudeHTTPAnalyzer with call_tool support."""

    def __init__(self, result: dict):
        self._result = result

    def call_tool(self, user_message, tool, system_prompt=None, model_override=None):
        return self._result

    def chat_with_agent(self, user_message, system_prompt=None, **kwargs):
        return json.dumps(self._result)


class AnalyzerTextOnly:
    """Simulates an analyzer that only supports chat_with_agent (JSON text)."""

    def __init__(self, response: str):
        self._response = response

    def chat_with_agent(self, user_message, system_prompt=None, **kwargs):
        return self._response


class BrokenAnalyzer:
    """Simulates an analyzer that always raises."""

    def call_tool(self, *args, **kwargs):
        raise RuntimeError("API error")

    def chat_with_agent(self, *args, **kwargs):
        raise RuntimeError("API error")


# ── call_tool path ────────────────────────────────────────────────────────────

def test_call_tool_high_confidence():
    analyzer = AnalyzerWithCallTool({
        "platform": "google",
        "mode": "analyze",
        "confidence": "high",
        "extracted_context": {"budget": 5000},
    })
    result = route_intent(analyzer, "improve ROAS in Google Ads")
    assert result["platform"] == "google"
    assert result["mode"] == "analyze"
    assert result["confidence"] == "high"
    assert result["extracted_context"] == {"budget": 5000}


def test_call_tool_low_confidence_generic():
    analyzer = AnalyzerWithCallTool({
        "platform": None,
        "mode": None,
        "confidence": "low",
        "extracted_context": {},
    })
    result = route_intent(analyzer, "Hello, how are you?")
    assert result["platform"] is None
    assert result["mode"] is None
    assert result["confidence"] == "low"


def test_call_tool_invalid_platform_sanitised():
    analyzer = AnalyzerWithCallTool({
        "platform": "snapchat",  # not in _PLATFORMS
        "mode": "analyze",
        "confidence": "high",
        "extracted_context": {},
    })
    result = route_intent(analyzer, "run snap ads")
    assert result["platform"] is None  # sanitised out


def test_call_tool_invalid_mode_sanitised():
    analyzer = AnalyzerWithCallTool({
        "platform": "meta",
        "mode": "magic_mode",  # not in _MODES
        "confidence": "high",
        "extracted_context": {},
    })
    result = route_intent(analyzer, "do magic on Meta")
    assert result["mode"] is None


# ── Fallback text path ────────────────────────────────────────────────────────

def test_text_fallback_parses_json():
    payload = json.dumps({
        "platform": "tiktok",
        "mode": "copy",
        "confidence": "high",
        "extracted_context": {"product": "SaaS"},
    })
    analyzer = AnalyzerTextOnly(payload)
    result = route_intent(analyzer, "write TikTok ad copy for SaaS")
    assert result["platform"] == "tiktok"
    assert result["mode"] == "copy"
    assert result["extracted_context"]["product"] == "SaaS"


def test_text_fallback_handles_markdown_fences():
    payload = "```json\n" + json.dumps({
        "platform": "meta",
        "mode": "plan",
        "confidence": "medium",
        "extracted_context": {},
    }) + "\n```"
    analyzer = AnalyzerTextOnly(payload)
    result = route_intent(analyzer, "plan Meta campaign")
    assert result["platform"] == "meta"
    assert result["mode"] == "plan"


def test_text_fallback_bad_json_returns_fallback():
    analyzer = AnalyzerTextOnly("not json at all")
    result = route_intent(analyzer, "random message")
    assert result == dict(_FALLBACK)


# ── Error / edge cases ────────────────────────────────────────────────────────

def test_none_analyzer_returns_fallback():
    result = route_intent(None, "any message")
    assert result == dict(_FALLBACK)


def test_broken_analyzer_returns_fallback():
    result = route_intent(BrokenAnalyzer(), "improve ROAS")
    assert result == dict(_FALLBACK)


def test_result_always_has_all_keys():
    analyzer = AnalyzerWithCallTool({
        "platform": "google",
        "mode": "audit",
        "confidence": "high",
        "extracted_context": {},
    })
    result = route_intent(analyzer, "audit Google account")
    for key in ("platform", "mode", "confidence", "extracted_context"):
        assert key in result


def test_all_platforms_accepted():
    for platform in _PLATFORMS:
        analyzer = AnalyzerWithCallTool({
            "platform": platform,
            "mode": "plan",
            "confidence": "high",
            "extracted_context": {},
        })
        result = route_intent(analyzer, f"plan {platform} campaign")
        assert result["platform"] == platform


def test_all_modes_accepted():
    for mode in _MODES:
        analyzer = AnalyzerWithCallTool({
            "platform": "google",
            "mode": mode,
            "confidence": "high",
            "extracted_context": {},
        })
        result = route_intent(analyzer, f"do {mode}")
        assert result["mode"] == mode
