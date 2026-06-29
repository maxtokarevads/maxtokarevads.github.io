"""Tests for vault_reader — filesystem reads, no API calls."""
from integrations.vault_reader import (
    read_knowledge_base,
    read_agent_kb,
    read_vault_file,
    validate_kb_files,
    kb_context_block,
    agent_kb_context_block,
)


def test_read_knowledge_base_unknown_platform():
    result = read_knowledge_base("nonexistent_platform_xyz")
    assert result == ""


def test_read_agent_kb_unknown_agent():
    result = read_agent_kb("nonexistent_agent_xyz")
    assert result == ""


def test_read_vault_file_nonexistent():
    result = read_vault_file("nonexistent/path/file.md")
    assert result == ""


def test_kb_context_block_unknown_returns_none():
    result = kb_context_block("nonexistent_platform_xyz")
    assert result is None


def test_agent_kb_context_block_unknown_returns_none():
    result = agent_kb_context_block("nonexistent_agent_xyz")
    assert result is None


def test_validate_kb_files_returns_dict():
    result = validate_kb_files()
    assert isinstance(result, dict)


def test_validate_kb_files_covers_all_platforms():
    result = validate_kb_files()
    for platform in ["google", "meta", "tiktok"]:
        assert platform in result, f"'{platform}' missing from validate_kb_files result"


def test_validate_kb_files_covers_all_agents():
    result = validate_kb_files()
    for agent in ["seo", "strategy", "creative"]:
        assert agent in result, f"'{agent}' missing from validate_kb_files result"


def test_validate_kb_files_values_are_bool():
    result = validate_kb_files()
    for key, val in result.items():
        assert isinstance(val, bool), f"validate_kb_files['{key}'] should be bool, got {type(val)}"
