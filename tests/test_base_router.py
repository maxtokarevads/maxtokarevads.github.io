"""
Tests for the shared BaseRouter logic (agents/base_router.py).

Verifies: call_tool preferred path, JSON-parse fallback, error isolation,
correct delegation from each agent router.
"""
import pytest
from agents.base_router import route


_TOOL = {
    "name": "test_classify",
    "description": "Test tool",
    "input_schema": {
        "type": "object",
        "properties": {
            "mode": {"type": ["string", "null"]},
            "confidence": {"type": "string"},
        },
        "required": ["mode", "confidence"],
    },
}

_SYSTEM = "You are a test classifier."
_PROMPT = "Classify: {message}"
_FALLBACK = {"mode": None, "confidence": "low"}


def _validate(result):
    return {
        "mode":       result.get("mode"),
        "confidence": result.get("confidence", "low"),
    }


class CallToolAnalyzer:
    """Returns structured result via call_tool."""
    def call_tool(self, user_message, tool, system_prompt=None, **kwargs):
        return {"mode": "plan", "confidence": "high"}

    def chat_with_agent(self, *a, **kw):
        raise AssertionError("chat_with_agent should not be called when call_tool succeeds")


class FallbackAnalyzer:
    """call_tool not available — falls back to JSON text."""
    def chat_with_agent(self, user_message, system_prompt=None, **kwargs):
        return '{"mode": "analyze", "confidence": "medium"}'


class BrokenCallToolAnalyzer:
    """call_tool exists but raises — should fall back gracefully."""
    def call_tool(self, *a, **kw):
        raise RuntimeError("API error")

    def chat_with_agent(self, user_message, system_prompt=None, **kwargs):
        return '{"mode": "copy", "confidence": "high"}'


class BrokenEverythingAnalyzer:
    """Both call_tool and chat_with_agent raise."""
    def call_tool(self, *a, **kw):
        raise RuntimeError("API error")

    def chat_with_agent(self, *a, **kw):
        raise RuntimeError("Network error")


class NoJsonAnalyzer:
    """chat_with_agent returns non-JSON text."""
    def chat_with_agent(self, *a, **kw):
        return "I don't understand"


# ── route() unit tests ─────────────────────────────────────────────────────────

def test_none_analyzer_returns_fallback():
    result = route(None, "hello", prompt_template=_PROMPT, tool=_TOOL,
                   system_prompt=_SYSTEM, validate=_validate, fallback=_FALLBACK)
    assert result == _FALLBACK


def test_call_tool_preferred_path():
    result = route(CallToolAnalyzer(), "plan a campaign",
                   prompt_template=_PROMPT, tool=_TOOL, system_prompt=_SYSTEM,
                   validate=_validate, fallback=_FALLBACK)
    assert result["mode"] == "plan"
    assert result["confidence"] == "high"


def test_fallback_to_json_parse_when_no_call_tool():
    result = route(FallbackAnalyzer(), "analyze my campaign",
                   prompt_template=_PROMPT, tool=_TOOL, system_prompt=_SYSTEM,
                   validate=_validate, fallback=_FALLBACK)
    assert result["mode"] == "analyze"
    assert result["confidence"] == "medium"


def test_broken_call_tool_falls_back_to_chat():
    result = route(BrokenCallToolAnalyzer(), "write copy",
                   prompt_template=_PROMPT, tool=_TOOL, system_prompt=_SYSTEM,
                   validate=_validate, fallback=_FALLBACK)
    assert result["mode"] == "copy"


def test_both_paths_broken_returns_fallback():
    result = route(BrokenEverythingAnalyzer(), "something",
                   prompt_template=_PROMPT, tool=_TOOL, system_prompt=_SYSTEM,
                   validate=_validate, fallback=_FALLBACK)
    assert result == _FALLBACK


def test_no_json_in_response_returns_fallback():
    result = route(NoJsonAnalyzer(), "something",
                   prompt_template=_PROMPT, tool=_TOOL, system_prompt=_SYSTEM,
                   validate=_validate, fallback=_FALLBACK)
    assert result == _FALLBACK


def test_message_substituted_in_prompt():
    seen = []

    class CapturingAnalyzer:
        def chat_with_agent(self, user_message, **kw):
            seen.append(user_message)
            return "{}"

    route(CapturingAnalyzer(), "my message",
          prompt_template="Context: {message}", tool=_TOOL, system_prompt=_SYSTEM,
          validate=_validate, fallback=_FALLBACK)
    assert seen and "my message" in seen[0]


def test_fallback_not_mutated():
    original = {"mode": None, "confidence": "low"}
    fallback_copy = dict(original)
    route(BrokenEverythingAnalyzer(), "x",
          prompt_template=_PROMPT, tool=_TOOL, system_prompt=_SYSTEM,
          validate=_validate, fallback=fallback_copy)
    assert fallback_copy == original


# ── Agent router delegation ────────────────────────────────────────────────────

class MockAnalyzer:
    def chat_with_agent(self, user_message, **kw):
        return '{"platform": "google", "mode": "plan", "confidence": "high", "extracted_context": {}}'

    def call_tool(self, user_message, tool, **kw):
        if tool["name"] == "classify_intent":
            return {"platform": "google", "mode": "plan", "confidence": "high", "extracted_context": {}}
        if tool["name"] == "classify_seo_intent":
            return {"mode": "technical", "confidence": "high", "extracted_context": {}}
        if tool["name"] == "classify_strategy_intent":
            return {"mode": "gtm", "confidence": "high", "extracted_context": {}}
        if tool["name"] == "classify_creative_intent":
            return {"mode": "concept", "confidence": "high", "extracted_context": {}}
        return None


def test_ads_router_delegates():
    from agents.ads.router import route_intent
    result = route_intent(MockAnalyzer(), "plan a Google Ads campaign")
    assert result["platform"] == "google"
    assert result["mode"] == "plan"
    assert result["confidence"] == "high"


def test_seo_router_delegates():
    from agents.seo.router import route_seo_intent
    result = route_seo_intent(MockAnalyzer(), "run a technical audit")
    assert result["mode"] == "technical"
    assert "extracted_context" in result


def test_strategy_router_delegates():
    from agents.strategy.router import route_strategy_intent
    result = route_strategy_intent(MockAnalyzer(), "build a GTM plan")
    assert result["mode"] == "gtm"


def test_creative_router_delegates():
    from agents.creative.router import route_creative_intent
    result = route_creative_intent(MockAnalyzer(), "develop a creative concept")
    assert result["mode"] == "concept"


def test_all_routers_return_fallback_on_none_analyzer():
    from agents.ads.router import route_intent
    from agents.seo.router import route_seo_intent
    from agents.strategy.router import route_strategy_intent
    from agents.creative.router import route_creative_intent

    assert route_intent(None, "x")["confidence"] == "low"
    assert route_seo_intent(None, "x")["confidence"] == "low"
    assert route_strategy_intent(None, "x")["confidence"] == "low"
    assert route_creative_intent(None, "x")["confidence"] == "low"
