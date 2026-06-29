"""
ClaudeCodeAnalyzer — использует Claude Code CLI вместо API-ключа.
Работает через подписку Pro/Max, не тратит API-токены.
"""
import logging
import os
import subprocess
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

_CLAUDE_PATH = os.getenv(
    "CLAUDE_CLI_PATH",
    r"C:\Users\Max\.vscode\extensions\anthropic.claude-code-2.1.185-win32-x64\resources\native-binary\claude.exe",
)


class ClaudeCodeAnalyzer:
    """Запускает claude CLI в режиме -p (non-interactive) и возвращает ответ."""

    def __init__(self):
        if not os.path.isfile(_CLAUDE_PATH):
            raise FileNotFoundError(
                f"Claude CLI не найден: {_CLAUDE_PATH}\n"
                "Задай переменную CLAUDE_CLI_PATH в .env"
            )
        logger.info("Claude Code analyzer готов: %s", _CLAUDE_PATH)

    def chat_with_agent(
        self,
        user_message: str,
        system_prompt: Optional[str] = None,
        history: Optional[List[Dict[str, Any]]] = None,
        model_override: Optional[str] = None,  # accepted but ignored — CLI uses its own model
    ) -> str:
        # Собираем полный промпт: история + новое сообщение
        parts = []
        if history:
            for msg in history:
                role = msg.get("role", "user").upper()
                content = msg.get("content", "").strip()
                if content:
                    parts.append(f"{role}: {content}")
        parts.append(user_message)
        full_prompt = "\n\n".join(parts)

        cmd = [_CLAUDE_PATH, "-p", full_prompt]
        if system_prompt:
            cmd += ["--system-prompt", system_prompt]

        logger.debug("Running claude CLI, prompt_len=%d", len(full_prompt))

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=180,        # Canon audit может занять до 3 минут
                stdin=subprocess.DEVNULL,
            )
            if result.returncode != 0 and not result.stdout.strip():
                stderr = result.stderr.strip()
                raise RuntimeError(f"Claude CLI вернул ошибку: {stderr}")

            response = result.stdout.strip()
            if not response:
                raise RuntimeError("Claude CLI вернул пустой ответ")

            logger.debug("Claude CLI ответил, len=%d", len(response))
            return response

        except subprocess.TimeoutExpired:
            raise RuntimeError("Claude CLI не ответил за 180 секунд")
