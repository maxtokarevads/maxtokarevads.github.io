import logging
import sys

from dotenv import load_dotenv

from agent import AdvertisingAnalyticsAgent

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


def safe_print(*args, **kwargs):
    try:
        print(*args, **kwargs)
    except UnicodeEncodeError:
        sep = kwargs.get("sep", " ")
        end = kwargs.get("end", "\n")
        text = sep.join(str(arg) for arg in args) + end
        encoding = getattr(sys.stdout, "encoding", "utf-8") or "utf-8"
        sys.stdout.buffer.write(text.encode(encoding, errors="replace"))


def run_agent_chat():
    agent = AdvertisingAnalyticsAgent()

    if not agent.claude_enabled:
        logger.error("Claude API не доступен. Проверьте ANTHROPIC_API_KEY в .env файле")
        return

    available_agents = list(agent.list_agents().keys())
    print("Доступные агенты:")
    for code in available_agents:
        print(f"  - {code}")

    selected = input("Выберите агента: ").strip()
    if selected not in available_agents:
        logger.error("Неверный агент: %s", selected)
        return

    agent.clear_agent_history(selected)
    print(f"\nНачинаем чат с агентом {selected}. Пишите сообщение и нажимайте Enter.")
    print("Напишите 'exit' или оставьте строку пустой, чтобы закончить.\n")

    while True:
        user_message = input("Вы: ").strip()
        if not user_message or user_message.lower() in {"exit", "quit"}:
            print("Чат завершён.")
            break

        response = agent.smart_chat(selected, user_message)
        routed = response.get("_routed")
        if routed:
            safe_print(f"[{routed['platform']} / {routed['mode']} / {routed['confidence']}]")
        result = response.get("result", response)
        safe_print(f"{selected} агент: {result}\n")


if __name__ == "__main__":
    run_agent_chat()
