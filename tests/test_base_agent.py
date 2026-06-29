"""Tests for BaseAgent — no API calls."""
from agents.base_agent import BaseAgent, MAX_HISTORY_TURNS


class ConcreteAgent(BaseAgent):
    def run(self, payload):
        return {"result": "ok", "agent": self.name}


class MockAnalyzer:
    def chat_with_agent(self, user_message, system_prompt=None, history=None):
        return f"response to: {user_message}"


def test_history_limit_enforced():
    agent = ConcreteAgent("test", MockAnalyzer())
    max_entries = MAX_HISTORY_TURNS * 2

    # Send more messages than the limit
    for i in range(MAX_HISTORY_TURNS + 5):
        agent.chat(f"message {i}")

    assert len(agent.conversation_history) == max_entries


def test_history_keeps_latest_messages():
    agent = ConcreteAgent("test", MockAnalyzer())

    for i in range(MAX_HISTORY_TURNS + 3):
        agent.chat(f"msg {i}")

    # Last message should be the most recent
    last_user = agent.conversation_history[-2]
    assert f"msg {MAX_HISTORY_TURNS + 2}" in last_user["content"]


def test_clear_history():
    agent = ConcreteAgent("test", MockAnalyzer())
    agent.chat("hello")
    assert len(agent.conversation_history) == 2
    agent.clear_history()
    assert len(agent.conversation_history) == 0


def test_chat_without_history():
    agent = ConcreteAgent("test", MockAnalyzer())
    agent.chat("first")
    result = agent.chat("second", use_history=False)
    assert "result" in result


def test_chat_no_analyzer():
    agent = ConcreteAgent("test", None)
    result = agent.chat("hello")
    assert "error" in result


def test_run_returns_agent_name():
    agent = ConcreteAgent("myagent", MockAnalyzer())
    result = agent.run({})
    assert result.get("agent") == "myagent"


def test_get_system_prompt_includes_name():
    agent = ConcreteAgent("seo", MockAnalyzer())
    prompt = agent.get_system_prompt()
    assert "seo" in prompt
