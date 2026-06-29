"""
AI Agent for advertising and analytics — entry point and orchestration layer.
"""

import logging
import os
from typing import Any, Dict, List

from dotenv import load_dotenv

load_dotenv()

from agents.manager import AgentsManager

logger = logging.getLogger(__name__)

# ANALYZER_BACKEND = "api"          → HTTP API (requires ANTHROPIC_API_KEY)
# ANALYZER_BACKEND = "claude_code"  → Claude Code CLI (Pro/Max subscription, no API key)
_BACKEND = os.getenv("ANALYZER_BACKEND", "api")

if _BACKEND == "claude_code":
    from claude_code_analyzer import ClaudeCodeAnalyzer as ClaudeAnalyzer
    logger.info("Backend: Claude Code CLI")
else:
    from claude_http_analyzer import ClaudeHTTPAnalyzer as ClaudeAnalyzer
    logger.info("Backend: HTTP API")


class AdvertisingAnalyticsAgent:
    """Orchestration layer: initialises the analyzer and delegates to AgentsManager."""

    def __init__(self):
        try:
            self.claude = ClaudeAnalyzer()
            self.claude_enabled = True
            logger.info("Claude API connected")
        except ValueError as e:
            logger.warning("Claude API not available: %s", e)
            self.claude_enabled = False

        self.agents = AgentsManager(self.claude if self.claude_enabled else None)

    def list_agents(self) -> Dict[str, str]:
        return self.agents.list_agent_types()

    def run_agent(self, agent_type: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        return self.agents.run(agent_type, payload)

    def chat_with_agent(self, agent_type: str, message: str,
                        use_history: bool = True, chat_id: int = 0) -> Dict[str, Any]:
        if not self.claude_enabled:
            return {"error": "Claude API not available."}
        return self.agents.chat(agent_type, message, use_history=use_history, chat_id=chat_id)

    def smart_chat(self, agent_type: str, message: str,
                   chat_id: int = 0) -> Dict[str, Any]:
        if not self.claude_enabled:
            return {"error": "Claude API not available."}
        return self.agents.smart_chat(agent_type, message, chat_id=chat_id)

    def clear_agent_history(self, agent_type: str, chat_id: int = None) -> Dict[str, Any]:
        return self.agents.clear_agent_history(agent_type, chat_id=chat_id)

    def run_agents(self, agent_payloads: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        return self.agents.run_many(agent_payloads)

    def run_all_agents(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        return self.agents.run_all(payload)

    def run_agent_loop(
        self,
        system_prompt: str,
        task: str,
        tools: List,
        tool_executor,
        model_override: str = None,
        max_iterations: int = 10,
        on_tool_call=None,
    ) -> str:
        """Run an agentic tool-use loop. Returns the final text response."""
        if not self.claude_enabled:
            return "Claude API not available."
        return self.claude.run_agent_loop(
            system_prompt=system_prompt,
            task=task,
            tools=tools,
            tool_executor=tool_executor,
            model_override=model_override,
            max_iterations=max_iterations,
            on_tool_call=on_tool_call,
        )

    def run_md_coordinator(self, task: str, context: Dict[str, Any], agent_list: List[str]) -> Dict[str, Any]:
        if not self.claude_enabled:
            return {"error": "Claude API not available."}
        return self.agents.orchestrate(task, context, agent_list or None)
