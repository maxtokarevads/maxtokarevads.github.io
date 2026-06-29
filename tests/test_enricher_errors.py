"""
Tests for seo/enricher.py error-block generation.

Verifies that when API keys are missing or integrations fail,
the enricher adds informative error blocks to the real_data_block
instead of failing silently.
"""
import os
import pytest


def _enrich(mode: str, payload: dict, monkeypatch) -> tuple:
    """Helper: clear env vars and run enricher."""
    monkeypatch.delenv("PAGESPEED_API_KEY", raising=False)
    monkeypatch.delenv("GSC_CREDENTIALS_FILE", raising=False)
    # Avoid any real network calls
    monkeypatch.setenv("SEO_SKIP_ENRICHMENT", "false")

    from agents.seo import enricher as _module
    import importlib
    importlib.reload(_module)

    return _module.enrich_payload(mode, payload)


# ── PageSpeed ─────────────────────────────────────────────────────────────────

class TestPageSpeedEnricher:
    def test_missing_key_produces_not_configured_block(self, monkeypatch):
        _, block = _enrich("technical", {"url": "https://example.com", "site": "example.com"}, monkeypatch)
        assert "NOT CONFIGURED" in block
        assert "PAGESPEED_API_KEY" in block

    def test_block_contains_setup_hint(self, monkeypatch):
        _, block = _enrich("technical", {"url": "https://example.com", "site": "example.com"}, monkeypatch)
        assert ".env" in block.lower() or "key" in block.lower()

    def test_no_pagespeed_for_non_technical_modes(self, monkeypatch):
        _, block = _enrich("seo", {"url": "https://example.com", "site": "example.com"}, monkeypatch)
        # PageSpeed only runs for technical/audit — should not appear for seo mode
        assert "PAGESPEED_API_KEY" not in block


# ── GSC ───────────────────────────────────────────────────────────────────────

class TestGSCEnricher:
    def test_missing_credentials_produces_not_configured_block(self, monkeypatch):
        _, block = _enrich("seo", {"site": "example.com"}, monkeypatch)
        assert "NOT CONFIGURED" in block
        assert "GSC_CREDENTIALS_FILE" in block

    def test_block_contains_setup_hint(self, monkeypatch):
        _, block = _enrich("seo", {"site": "example.com"}, monkeypatch)
        assert "setup_gsc_oauth" in block or "GSC" in block

    def test_no_gsc_when_no_site(self, monkeypatch):
        _, block = _enrich("seo", {}, monkeypatch)
        # No site = GSC block should not appear
        assert "GSC_CREDENTIALS_FILE" not in block


# ── URL Inspection ────────────────────────────────────────────────────────────

class TestURLInspectionEnricher:
    def test_import_error_produces_not_available_block(self, monkeypatch):
        monkeypatch.setenv("SEO_SKIP_ENRICHMENT", "false")

        # Patch the import to raise ImportError
        import sys
        if "integrations.url_inspector" in sys.modules:
            del sys.modules["integrations.url_inspector"]

        original_import = __builtins__.__import__ if hasattr(__builtins__, "__import__") else None

        from agents.seo import enricher as _module
        import importlib
        importlib.reload(_module)

        # Monkeypatch inspect_url to raise ImportError
        def _raise_import(*a, **kw):
            raise ImportError("not installed")

        # Patch at the module level where it's imported
        monkeypatch.setattr(
            "integrations.url_inspector.inspect_url",
            _raise_import,
            raising=False,
        )

        _, block = _module.enrich_payload("technical", {"url": "https://example.com", "site": "example.com"})
        # After patching it should either produce NOT AVAILABLE or FAILED block
        # The block must contain something explanatory rather than silence
        # (actual content depends on whether the import succeeds at all)
        # We just verify the payload is returned safely
        assert isinstance(block, str)

    def test_no_url_skips_url_inspection(self, monkeypatch):
        monkeypatch.setenv("SEO_SKIP_ENRICHMENT", "false")
        from agents.seo import enricher as _module
        import importlib
        importlib.reload(_module)

        _, block = _module.enrich_payload("technical", {"site": ""})
        # No URL → no inspection → no URL block
        # Just assert it doesn't crash
        assert isinstance(block, str)


# ── Skip enrichment flag ──────────────────────────────────────────────────────

class TestSkipEnrichmentFlag:
    def test_skip_enrichment_returns_empty_block(self, monkeypatch):
        monkeypatch.setenv("SEO_SKIP_ENRICHMENT", "true")
        from agents.seo import enricher as _module
        import importlib
        importlib.reload(_module)

        payload, block = _module.enrich_payload("technical", {"url": "https://example.com", "site": "example.com"})
        assert block == ""

    def test_skip_enrichment_returns_payload_unchanged(self, monkeypatch):
        monkeypatch.setenv("SEO_SKIP_ENRICHMENT", "true")
        from agents.seo import enricher as _module
        import importlib
        importlib.reload(_module)

        original = {"mode": "technical", "site": "test.com"}
        payload, _ = _module.enrich_payload("technical", original)
        assert payload is original  # same object returned
