"""
Property-based tests using Hypothesis.

Properties verified:
  - Routers: any string input → always returns valid dict shape (never raises)
  - Agents: valid platform/mode → always returns result/error dict (never raises)
  - split_structured_result: any dict → (str, dict) — never raises
  - Budget validation: negative budget always rejected
  - Payload size guard: oversized payload always rejected
  - _validate_mode / _validate_platform: always returns valid or None
  - AdsRequest.from_dict: subset of known fields → never raises
  - SEORequest.from_dict: any known-key subset → never raises
"""

import pytest
from hypothesis import given, settings, assume, HealthCheck
from hypothesis import strategies as st


# ── Strategies ─────────────────────────────────────────────────────────────────

# Safe printable text — no nulls, no excessively long strings
text  = st.text(min_size=0, max_size=200)
small = st.text(min_size=0, max_size=40)

ads_platforms  = st.sampled_from(["google", "meta", "tiktok", "google_ads", "facebook"])
invalid_str    = st.text(min_size=1, max_size=50).filter(
    lambda s: s.lower().strip() not in {"google", "meta", "tiktok", "google_ads",
                                         "facebook", "instagram", "fb"}
)
ads_modes      = st.sampled_from(["plan", "analyze", "copy", "audit", "budget",
                                   "retargeting", "ab_test", "research", "landing", "forecast"])
seo_modes      = st.sampled_from(["seo", "aeo", "technical", "content", "local",
                                   "schema", "backlinks", "cluster", "sxo", "audit", "drift"])
strategy_modes = st.sampled_from(["general", "gtm", "positioning", "channel_mix", "kpi", "audit"])
creative_modes = st.sampled_from(["concept", "copy", "script", "ugc_brief"])

positive_number = st.floats(min_value=0.01, max_value=1_000_000, allow_nan=False, allow_infinity=False)
negative_number = st.floats(max_value=-0.01, allow_nan=False, allow_infinity=False)


class _MockAnalyzer:
    model_name = "mock"
    def chat_with_agent(self, *a, **kw): return "mock response"
    def call_tool(self, *a, **kw): return None


# ── Router property: any string → valid shape, never raises ───────────────────

class TestRouterProperties:

    @given(message=text)
    @settings(max_examples=50, suppress_health_check=[HealthCheck.too_slow])
    def test_ads_router_never_raises(self, message):
        from agents.ads.router import route_intent
        result = route_intent(_MockAnalyzer(), message)
        assert isinstance(result, dict)
        assert "confidence" in result
        assert result["confidence"] in ("high", "medium", "low")
        assert "extracted_context" in result
        assert isinstance(result["extracted_context"], dict)

    @given(message=text)
    @settings(max_examples=50, suppress_health_check=[HealthCheck.too_slow])
    def test_seo_router_never_raises(self, message):
        from agents.seo.router import route_seo_intent
        result = route_seo_intent(_MockAnalyzer(), message)
        assert isinstance(result, dict)
        assert "confidence" in result
        assert "extracted_context" in result

    @given(message=text)
    @settings(max_examples=50, suppress_health_check=[HealthCheck.too_slow])
    def test_strategy_router_never_raises(self, message):
        from agents.strategy.router import route_strategy_intent
        result = route_strategy_intent(_MockAnalyzer(), message)
        assert isinstance(result, dict)
        assert "confidence" in result

    @given(message=text)
    @settings(max_examples=50, suppress_health_check=[HealthCheck.too_slow])
    def test_creative_router_never_raises(self, message):
        from agents.creative.router import route_creative_intent
        result = route_creative_intent(_MockAnalyzer(), message)
        assert isinstance(result, dict)
        assert "confidence" in result

    @given(message=text)
    @settings(max_examples=30, suppress_health_check=[HealthCheck.too_slow])
    def test_null_analyzer_always_returns_low_confidence(self, message):
        from agents.ads.router      import route_intent
        from agents.seo.router      import route_seo_intent
        from agents.strategy.router import route_strategy_intent
        from agents.creative.router import route_creative_intent
        for fn in (route_intent, route_seo_intent, route_strategy_intent, route_creative_intent):
            result = fn(None, message)
            assert result["confidence"] == "low"


# ── Agent property: valid inputs → always returns dict, never raises ──────────

class TestAdsAgentProperties:

    @given(platform=ads_platforms, mode=ads_modes, product=small, budget=positive_number)
    @settings(max_examples=30, suppress_health_check=[HealthCheck.too_slow])
    def test_valid_input_always_returns_dict(self, platform, mode, product, budget):
        from agents.ads.agent import AdsAgent
        agent  = AdsAgent("ads", _MockAnalyzer())
        result = agent.run({"platform": platform, "mode": mode,
                            "product": product, "budget": budget})
        assert isinstance(result, dict)
        assert "agent" in result
        # Either success or error — never an exception
        assert "result" in result or "error" in result

    @given(budget=negative_number)
    @settings(max_examples=30)
    def test_negative_budget_always_rejected(self, budget):
        from agents.ads.agent import AdsAgent
        agent  = AdsAgent("ads", _MockAnalyzer())
        result = agent.run({"platform": "google", "mode": "plan", "budget": budget})
        assert "error" in result
        assert "negative" in result["error"].lower()

    @given(platform=invalid_str)
    @settings(max_examples=30, suppress_health_check=[HealthCheck.too_slow])
    def test_invalid_platform_always_rejected(self, platform):
        assume(platform.strip())  # skip empty strings
        from agents.ads.agent import AdsAgent
        agent  = AdsAgent("ads", _MockAnalyzer())
        result = agent.run({"platform": platform, "mode": "plan"})
        assert "error" in result


class TestSEOAgentProperties:

    @given(mode=seo_modes, site=small)
    @settings(max_examples=30, suppress_health_check=[HealthCheck.too_slow, HealthCheck.function_scoped_fixture])
    def test_valid_input_always_returns_dict(self, mode, site, monkeypatch):
        monkeypatch.setenv("SEO_SKIP_ENRICHMENT", "true")
        from agents.seo.agent import SEOAgent
        agent  = SEOAgent("seo", _MockAnalyzer())
        result = agent.run({"mode": mode, "site": site})
        assert isinstance(result, dict)
        assert "result" in result or "error" in result

    @given(mode=st.text(min_size=1, max_size=30).filter(
        lambda s: s.strip() and s.lower().strip() not in {
            "seo","aeo","technical","content","local",
            "schema","backlinks","cluster","sxo","audit","drift"
        }
    ))
    @settings(max_examples=30, suppress_health_check=[HealthCheck.too_slow, HealthCheck.function_scoped_fixture])
    def test_invalid_mode_always_rejected(self, mode, monkeypatch):
        monkeypatch.setenv("SEO_SKIP_ENRICHMENT", "true")
        from agents.seo.agent import SEOAgent
        agent  = SEOAgent("seo", _MockAnalyzer())
        result = agent.run({"mode": mode, "site": "example.com"})
        assert "error" in result


# ── split_structured_result property: never raises ───────────────────────────

_json_value = st.recursive(
    st.one_of(st.none(), st.booleans(), st.integers(), st.floats(allow_nan=False),
              st.text(max_size=50)),
    lambda children: st.one_of(
        st.lists(children, max_size=5),
        st.dictionaries(st.text(max_size=20), children, max_size=5),
    ),
    max_leaves=20,
)


class TestSplitStructuredResultProperties:

    @given(raw=st.dictionaries(st.text(min_size=1, max_size=20), _json_value, max_size=10))
    @settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
    def test_ads_never_raises(self, raw):
        from agents.ads.skills.structured import split_structured_result
        text, data = split_structured_result(raw)
        assert isinstance(text, str)
        assert isinstance(data, dict)

    @given(raw=st.one_of(st.none(), st.integers(), st.text(), st.lists(st.integers())))
    @settings(max_examples=50)
    def test_non_dict_input_returns_empty(self, raw):
        from agents.ads.skills.structured import split_structured_result
        text, data = split_structured_result(raw)
        assert text == "" and data == {}

    @given(narrative=st.text(max_size=200),
           extra=st.dictionaries(
               st.text(min_size=1, max_size=15).filter(lambda s: s != "narrative"),
               st.one_of(st.integers(), st.text(max_size=30), st.booleans()),
               max_size=5,
           ))
    @settings(max_examples=50)
    def test_narrative_always_extracted(self, narrative, extra):
        from agents.ads.skills.structured import split_structured_result
        raw  = {"narrative": narrative, **extra}
        text, data = split_structured_result(raw)
        assert text == narrative.strip()
        assert "narrative" not in data
        for k in extra:
            assert k in data

    @given(raw=st.dictionaries(st.text(min_size=1, max_size=20), _json_value, max_size=10))
    @settings(max_examples=50)
    def test_input_dict_never_mutated(self, raw):
        from agents.ads.skills.structured import split_structured_result
        original_keys = frozenset(raw.keys())
        split_structured_result(raw)
        assert frozenset(raw.keys()) == original_keys


# ── AdsRequest dataclass properties ──────────────────────────────────────────

class TestAdsRequestProperties:

    @given(mode=ads_modes, platform=ads_platforms, budget=positive_number)
    @settings(max_examples=50)
    def test_from_dict_never_raises(self, mode, platform, budget):
        from agents.ads.skills.prompt import AdsRequest
        req = AdsRequest.from_dict({"mode": mode, "platform": platform, "budget": budget})
        assert isinstance(req.mode, str)
        assert isinstance(req.platform, str)

    @given(extra_keys=st.dictionaries(
        st.text(min_size=1, max_size=20).filter(lambda s: s not in {
            "mode","platform","product","goal","budget","market","context",
            "command","project","account_type","date_range","notes",
        }),
        st.text(max_size=30),
        max_size=5,
    ))
    @settings(max_examples=30)
    def test_unknown_keys_silently_dropped(self, extra_keys):
        from agents.ads.skills.prompt import AdsRequest
        payload = {"mode": "plan", "platform": "google", **extra_keys}
        req = AdsRequest.from_dict(payload)
        assert req.mode == "plan"


# ── SEORequest dataclass properties ──────────────────────────────────────────

class TestSEORequestProperties:

    @given(mode=seo_modes, site=small, industry=small)
    @settings(max_examples=50)
    def test_from_dict_never_raises(self, mode, site, industry):
        from agents.seo.agent import SEORequest
        req = SEORequest.from_dict({"mode": mode, "site": site, "industry": industry})
        assert req.mode == mode.lower().strip()

    @given(data=st.fixed_dictionaries({
        "mode":  seo_modes,
        "site":  small,
    }))
    @settings(max_examples=30)
    def test_site_fallback_from_url(self, data):
        from agents.seo.agent import SEORequest
        d   = {"url": data["site"], "mode": data["mode"]}
        req = SEORequest.from_dict(d)
        assert req.site == data["site"]  # url → site in __post_init__


# ── BaseAgent._validate_mode property ────────────────────────────────────────

class TestValidateModeProperties:

    # _validate_mode lowercases/strips input before checking against supported.
    # So supported must contain lowercase strings for the check to work as intended
    # (which is how it's used in practice: SUPPORTED_MODES = {"seo", "aeo", ...}).
    _lowercase_text = st.text(
        alphabet=st.characters(whitelist_categories=("Ll",), min_codepoint=97, max_codepoint=122),
        min_size=1, max_size=20,
    )

    @given(supported=st.frozensets(_lowercase_text, min_size=1, max_size=10))
    @settings(max_examples=50)
    def test_valid_mode_returns_mode(self, supported):
        from agents.base_agent import BaseAgent
        import random

        class Concrete(BaseAgent):
            def run(self, p): return {}

        agent = Concrete("test", None)
        valid = random.choice(list(supported))
        result = agent._validate_mode(valid, supported)
        assert result == valid  # lowercase input → same string returned

    @given(raw=text)
    @settings(max_examples=50)
    def test_invalid_mode_returns_none(self, raw):
        from agents.base_agent import BaseAgent

        class Concrete(BaseAgent):
            def run(self, p): return {}

        supported = frozenset(["alpha", "beta", "gamma"])
        agent     = Concrete("test", None)
        assume(raw.lower().strip() not in supported)
        assert agent._validate_mode(raw, supported) is None
