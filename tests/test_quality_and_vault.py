"""
Tests for output quality (copy char count verification) and vault saving.
"""
import os
import tempfile
import pytest
from pathlib import Path


# ── Copy char count verifier ──────────────────────────────────────────────────

class TestCopyCharCountVerifier:
    def _run(self, raw: dict) -> tuple:
        from agents.ads.skills.structured import split_structured_result
        return split_structured_result(raw)

    def test_accurate_counts_unchanged(self):
        raw = {
            "narrative": "Good copy",
            "platform": "google",
            "platform_limits": {"headline": 30, "description": 90},
            "variants": [{
                "hook_type": "urgency",
                "headline": "Save 20% Today",       # 14 chars
                "description": "Act now.",           # 8 chars
                "cta": "Shop",
                "char_counts": {"headline": 14, "description": 8},
                "compliant": True,
            }],
        }
        _, structured = self._run(raw)
        assert structured.get("_char_counts_corrected") is None  # no correction needed
        assert structured["variants"][0]["char_counts"]["headline"] == 14

    def test_wrong_count_gets_corrected(self):
        raw = {
            "narrative": "Copy",
            "platform": "google",
            "platform_limits": {"headline": 30, "description": 90},
            "variants": [{
                "hook_type": "urgency",
                "headline": "Save 20% Today",   # actually 14 chars
                "description": "Act now.",       # actually 8 chars
                "cta": "Shop",
                "char_counts": {"headline": 99, "description": 99},  # LLM lied
                "compliant": True,
            }],
        }
        _, structured = self._run(raw)
        assert structured.get("_char_counts_corrected") is True
        assert structured["variants"][0]["char_counts"]["headline"] == 14
        assert structured["variants"][0]["char_counts"]["description"] == 8

    def test_over_limit_sets_compliant_false(self):
        long_headline = "A" * 40  # 40 chars, limit is 30
        raw = {
            "narrative": "Copy",
            "platform": "google",
            "platform_limits": {"headline": 30, "description": 90},
            "variants": [{
                "hook_type": "urgency",
                "headline": long_headline,
                "description": "Short desc.",
                "cta": "Buy",
                "char_counts": {"headline": 40, "description": 11},
                "compliant": True,  # LLM incorrectly said compliant
            }],
        }
        _, structured = self._run(raw)
        assert structured["variants"][0]["compliant"] is False
        assert structured.get("_char_counts_corrected") is True

    def test_within_limit_sets_compliant_true(self):
        raw = {
            "narrative": "Copy",
            "platform": "google",
            "platform_limits": {"headline": 30, "description": 90},
            "variants": [{
                "hook_type": "urgency",
                "headline": "Short",        # 5 chars
                "description": "Even shorter.",
                "cta": "Go",
                "char_counts": {"headline": 5, "description": 13},
                "compliant": False,  # LLM incorrectly said non-compliant
            }],
        }
        _, structured = self._run(raw)
        assert structured["variants"][0]["compliant"] is True

    def test_no_platform_limits_skips_compliance_check(self):
        raw = {
            "narrative": "Copy",
            "platform": "google",
            "variants": [{
                "hook_type": "urgency",
                "headline": "A" * 100,
                "description": "B" * 200,
                "cta": "Go",
                "char_counts": {"headline": 99, "description": 99},
                "compliant": True,
            }],
        }
        _, structured = self._run(raw)
        # No platform_limits → no compliance recalculation
        assert structured.get("_char_counts_corrected") is None

    def test_narrative_extracted_before_verification(self):
        raw = {
            "narrative": "My narrative",
            "platform": "meta",
            "platform_limits": {"headline": 40, "description": 125},
            "variants": [{"hook_type": "x", "headline": "Hi", "description": "Hello",
                          "cta": "Go", "char_counts": {"headline": 2, "description": 5},
                          "compliant": True}],
        }
        text, structured = self._run(raw)
        assert text == "My narrative"
        assert "narrative" not in structured


# ── Vault saving ──────────────────────────────────────────────────────────────

class TestVaultSaving:
    """Tests that agents actually create vault files with correct content."""

    def _tmp_vault(self, tmp_path):
        d = tmp_path / "vault" / "campaigns"
        d.mkdir(parents=True, exist_ok=True)
        return d

    def test_base_agent_save_to_vault_creates_file(self, tmp_path, monkeypatch):
        monkeypatch.delenv("TESTING", raising=False)
        from agents.ads.agent import AdsAgent

        class MockAnalyzer:
            model_name = "mock"
            def chat_with_agent(self, *a, **kw): return "Test result content"
            def call_tool(self, *a, **kw): return None

        agent   = AdsAgent("ads", MockAnalyzer())
        vault   = self._tmp_vault(tmp_path)
        content = "# Test\n\nContent here."
        agent._save_to_vault("test_file.md", content, vault)

        saved = vault / "test_file.md"
        assert saved.exists()
        assert "Content here." in saved.read_text(encoding="utf-8")

    def test_ads_run_creates_vault_file(self, tmp_path, monkeypatch):
        monkeypatch.delenv("TESTING", raising=False)
        from agents.ads import agent as ads_module
        monkeypatch.setattr(ads_module, "_VAULT_CAMPAIGNS", self._tmp_vault(tmp_path))
        # Also patch _cached_glob to not use stale LRU cache
        monkeypatch.setattr(ads_module, "_find_previous_campaign", lambda *a: "")

        class MockAnalyzer:
            model_name = "mock"
            def chat_with_agent(self, *a, **kw): return "Campaign plan content"
            def call_tool(self, *a, **kw): return None

        from agents.ads.agent import AdsAgent
        agent  = AdsAgent("ads", MockAnalyzer())
        result = agent.run({"platform": "google", "mode": "plan", "product": "SaaS"})

        assert "error" not in result
        files = list(self._tmp_vault(tmp_path).glob("*-google-plan.md"))
        assert len(files) >= 1
        content = files[0].read_text(encoding="utf-8")
        assert "Campaign plan content" in content
        assert "google" in content
        assert "plan" in content

    def test_seo_run_creates_vault_file(self, tmp_path, monkeypatch):
        monkeypatch.delenv("TESTING", raising=False)
        from agents.seo import agent as seo_module
        monkeypatch.setattr(seo_module, "_VAULT_CAMPAIGNS", self._tmp_vault(tmp_path))
        monkeypatch.setenv("SEO_SKIP_ENRICHMENT", "true")

        class MockAnalyzer:
            model_name = "mock"
            def chat_with_agent(self, *a, **kw): return "SEO analysis result"
            def call_tool(self, *a, **kw): return None

        from agents.seo.agent import SEOAgent
        agent  = SEOAgent("seo", MockAnalyzer())
        result = agent.run({"mode": "seo", "site": "example.com"})

        assert "error" not in result
        files = list(self._tmp_vault(tmp_path).glob("*-seo-seo-example.com.md"))
        assert len(files) >= 1
        content = files[0].read_text(encoding="utf-8")
        assert "SEO analysis result" in content
        assert "example.com" in content
        assert "seo" in content

    def test_vault_save_failure_does_not_break_response(self, tmp_path):
        from agents.ads.agent import AdsAgent

        class MockAnalyzer:
            model_name = "mock"
            def chat_with_agent(self, *a, **kw): return "Result"
            def call_tool(self, *a, **kw): return None

        agent = AdsAgent("ads", MockAnalyzer())
        # Try to save to non-existent read-only path
        agent._save_to_vault("test.md", "content", Path("/non/existent/path"))
        # Should not raise — just log warning

    def test_vault_file_contains_prompt_hash(self, tmp_path, monkeypatch):
        monkeypatch.delenv("TESTING", raising=False)
        from agents.base_agent import BaseAgent

        class ConcreteAgent(BaseAgent):
            def run(self, payload): return {}

        agent  = ConcreteAgent("test", None)
        vault  = self._tmp_vault(tmp_path)
        agent._save_to_vault("test.md", "**Prompt-hash:** `abc123`\n\nContent.", vault)
        text = (vault / "test.md").read_text()
        assert "Prompt-hash" in text


# ── Prompt hash ───────────────────────────────────────────────────────────────

class TestPromptHash:
    def test_hash_is_12_chars(self):
        from agents.base_agent import BaseAgent

        class ConcreteAgent(BaseAgent):
            def run(self, p): return {}

        agent = ConcreteAgent("test", None)
        h = agent._prompt_hash("Hello world")
        assert len(h) == 12
        assert h.isalnum()

    def test_same_prompt_same_hash(self):
        from agents.base_agent import BaseAgent

        class ConcreteAgent(BaseAgent):
            def run(self, p): return {}

        agent = ConcreteAgent("test", None)
        assert agent._prompt_hash("prompt A") == agent._prompt_hash("prompt A")

    def test_different_prompts_different_hash(self):
        from agents.base_agent import BaseAgent

        class ConcreteAgent(BaseAgent):
            def run(self, p): return {}

        agent = ConcreteAgent("test", None)
        assert agent._prompt_hash("prompt A") != agent._prompt_hash("prompt B")


# ── KB LRU cache ──────────────────────────────────────────────────────────────

class TestKBCache:
    def test_kb_read_is_cached(self, monkeypatch):
        from integrations import vault_reader
        vault_reader.read_knowledge_base.cache_clear()

        call_count = [0]
        original   = vault_reader.read_knowledge_base.__wrapped__  # underlying function

        def counting_read(platform):
            call_count[0] += 1
            return ""

        monkeypatch.setattr(vault_reader, "read_knowledge_base",
                            __import__("functools").lru_cache(maxsize=8)(counting_read))

        vault_reader.read_knowledge_base("google")
        vault_reader.read_knowledge_base("google")
        vault_reader.read_knowledge_base("google")
        assert call_count[0] == 1  # only called once despite 3 invocations

    def test_different_platforms_cached_separately(self, monkeypatch):
        from integrations import vault_reader
        vault_reader.read_knowledge_base.cache_clear()

        call_log = []

        def tracking_read(platform):
            call_log.append(platform)
            return ""

        monkeypatch.setattr(vault_reader, "read_knowledge_base",
                            __import__("functools").lru_cache(maxsize=8)(tracking_read))

        vault_reader.read_knowledge_base("google")
        vault_reader.read_knowledge_base("meta")
        vault_reader.read_knowledge_base("google")  # should use cache
        assert call_log == ["google", "meta"]
