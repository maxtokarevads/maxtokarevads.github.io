"""
Regression test: ensure no Cyrillic/Ukrainian characters appear in any
prompt body built by the ads skill system.

Run: python -m pytest tests/test_no_cyrillic.py -v
"""
import pathlib
import pytest
from agents.ads.skills.prompt import build_ads_prompt, SUPPORTED_MODES, _ROUTER


def _has_cyrillic(text: str) -> bool:
    return any(0x0400 <= ord(c) <= 0x04FF for c in text)


# ── 1. Source-file scan ────────────────────────────────────────────────────────

AGENTS_DIR = pathlib.Path(__file__).parent.parent / "agents"
SKIP_DIRS  = {"__pycache__"}

# Agents pending English translation — add name here to temporarily exclude from test
_PENDING_TRANSLATION: set = set()  # all agents are now translated

def _is_pending(path: pathlib.Path) -> bool:
    """True if the file belongs to an agent pending English translation."""
    parts = path.parts
    for pending in _PENDING_TRANSLATION:
        if pending in parts:
            return True
    return False

@pytest.mark.parametrize("py_file", [
    f for f in AGENTS_DIR.rglob("*.py")
    if not any(part in SKIP_DIRS for part in f.parts)
    and not _is_pending(f)
])
def test_no_cyrillic_in_source(py_file: pathlib.Path):
    src = py_file.read_text(encoding="utf-8")
    cyrillic_lines = [
        f"line {i+1}: {line.rstrip()}"
        for i, line in enumerate(src.splitlines())
        if _has_cyrillic(line)
    ]
    assert not cyrillic_lines, (
        f"{py_file.relative_to(AGENTS_DIR.parent)} has Cyrillic:\n"
        + "\n".join(cyrillic_lines)
    )


# ── 2. Built-prompt scan ──────────────────────────────────────────────────────

_SAMPLE_PAYLOAD = {
    "product": "SaaS CRM",
    "budget":  3000,
    "goal":    "conversions",
    "market":  "US",
    "command": "/audit",
    "project": "ACME",
    "account_type": "ecom",
    "metrics": {"ctr": 2.1, "roas": 3.5},
    "inputs":  {},
    "months":  3,
}

@pytest.mark.parametrize("platform,mode", [
    (platform, mode)
    for platform, modes in _ROUTER.items()
    for mode in modes
])
def test_no_cyrillic_in_built_prompt(platform: str, mode: str):
    payload = {**_SAMPLE_PAYLOAD, "platform": platform, "mode": mode}
    prompt  = build_ads_prompt(payload)
    assert not _has_cyrillic(prompt), (
        f"Cyrillic found in prompt for platform={platform!r} mode={mode!r}.\n"
        f"First 200 chars:\n{prompt[:200]}"
    )


@pytest.mark.parametrize("mode", ["budget", "forecast", "landing"])
def test_no_cyrillic_cross_platform_modes(mode: str):
    payload = {**_SAMPLE_PAYLOAD, "platform": "google", "mode": mode}
    prompt  = build_ads_prompt(payload)
    assert not _has_cyrillic(prompt), (
        f"Cyrillic found in cross-platform mode={mode!r}.\n{prompt[:200]}"
    )
