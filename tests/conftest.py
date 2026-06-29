import pytest


@pytest.fixture(autouse=True)
def _no_vault_writes(monkeypatch):
    """Block vault writes for all tests — vault tests opt out via monkeypatch.delenv('TESTING')."""
    monkeypatch.setenv("TESTING", "1")


class MockAnalyzer:
    """Stub Claude analyzer — returns deterministic responses without API calls."""

    def chat_with_agent(self, user_message: str, system_prompt: str = None,
                        history=None, **kwargs) -> str:
        return f"mock:{user_message[:30]}"


@pytest.fixture
def mock_analyzer():
    return MockAnalyzer()


@pytest.fixture
def manager(mock_analyzer):
    from agents.manager import AgentsManager
    return AgentsManager(mock_analyzer)


@pytest.fixture
def manager_no_analyzer():
    from agents.manager import AgentsManager
    return AgentsManager(None)
