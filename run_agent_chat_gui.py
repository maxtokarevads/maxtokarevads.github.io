import logging
import os
import threading
import tkinter as tk
from tkinter import scrolledtext, messagebox

from dotenv import load_dotenv

from agent import AdvertisingAnalyticsAgent

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


class ChatWindow:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Agent Chat")
        self.root.geometry("700x550")

        self.agent = AdvertisingAnalyticsAgent()
        if not self.agent.claude_enabled:
            messagebox.showerror("Ошибка", "Claude API не доступен. Проверьте ANTHROPIC_API_KEY в .env файле")
            root.destroy()
            return

        self.available_agents = list(self.agent.list_agents().keys())
        self.selected_agent = tk.StringVar(value=self.available_agents[0] if self.available_agents else "")

        self._build_ui()

    def _build_ui(self) -> None:
        top_frame = tk.Frame(self.root)
        top_frame.pack(fill=tk.X, padx=10, pady=10)

        tk.Label(top_frame, text="Выберите агента:").pack(side=tk.LEFT)
        tk.OptionMenu(top_frame, self.selected_agent, *self.available_agents).pack(side=tk.LEFT, padx=10)
        tk.Button(top_frame, text="Очистить историю", command=self.clear_history).pack(side=tk.RIGHT)

        self.chat_display = scrolledtext.ScrolledText(self.root, wrap=tk.WORD, state=tk.NORMAL)
        self.chat_display.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))
        self.chat_display.configure(state=tk.DISABLED)

        bottom_frame = tk.Frame(self.root)
        bottom_frame.pack(fill=tk.X, padx=10, pady=10)

        self.user_input = tk.Entry(bottom_frame)
        self.user_input.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        self.user_input.bind("<Return>", self.on_send)

        self.send_btn = tk.Button(bottom_frame, text="Отправить", command=self.on_send)
        self.send_btn.pack(side=tk.RIGHT)

        self._append_message("Система", "Выберите агента и задайте вопрос. Напишите «exit» для выхода.")

    def _append_message(self, sender: str, message: str) -> None:
        self.chat_display.configure(state=tk.NORMAL)
        try:
            self.chat_display.insert(tk.END, f"{sender}: {message}\n\n")
        except UnicodeEncodeError:
            self.chat_display.insert(
                tk.END,
                f"{sender}: {message.encode('utf-8', errors='replace').decode('utf-8', errors='replace')}\n\n",
            )
        self.chat_display.configure(state=tk.DISABLED)
        self.chat_display.see(tk.END)

    def _set_input_enabled(self, enabled: bool) -> None:
        state = tk.NORMAL if enabled else tk.DISABLED
        self.user_input.configure(state=state)
        self.send_btn.configure(state=state)

    def clear_history(self) -> None:
        agent_type = self.selected_agent.get()
        if agent_type:
            self.agent.clear_agent_history(agent_type)
            self.chat_display.configure(state=tk.NORMAL)
            self.chat_display.delete("1.0", tk.END)
            self.chat_display.configure(state=tk.DISABLED)
            self._append_message("Система", f"История чата агента {agent_type} очищена.")

    def on_send(self, event=None) -> None:
        user_message = self.user_input.get().strip()
        if not user_message:
            return

        agent_type = self.selected_agent.get()
        if user_message.lower() in {"exit", "quit"}:
            self.root.quit()
            return

        self._append_message("Вы", user_message)
        self.user_input.delete(0, tk.END)
        self._set_input_enabled(False)

        def _call() -> None:
            try:
                response = self.agent.smart_chat(agent_type, user_message)
                result = response.get("result", response)
                routed = response.get("_routed")
                if routed:
                    badge = f"[{routed['platform']} / {routed['mode']} / {routed['confidence']}]\n"
                    result = badge + str(result)
            except Exception as exc:
                logger.exception("Ошибка агента %s", agent_type)
                result = f"Ошибка: {exc}"
            self.root.after(0, lambda: self._append_message(f"{agent_type} агент", str(result)))
            self.root.after(0, lambda: self._set_input_enabled(True))

        threading.Thread(target=_call, daemon=True).start()


def main() -> None:
    root = tk.Tk()
    ChatWindow(root)
    root.mainloop()


if __name__ == "__main__":
    main()
