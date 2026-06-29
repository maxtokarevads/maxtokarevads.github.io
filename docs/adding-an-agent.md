# Adding a New Agent

Step-by-step guide to adding a new specialist agent (e.g. `email`, `analytics`, `pr`).

---

## Overview

Every agent follows this structure:
```
agents/<name>/
├── __init__.py
├── agent.py          ← Main agent class (inherits BaseAgent)
├── router.py         ← Intent classifier (delegates to base_router.route())
└── skills/
    ├── __init__.py
    ├── prompt.py     ← Mode-specific prompt builders
    └── structured.py ← Structured output tool schemas (optional)
```

---

## Step 1 — Create the directory structure

```bash
mkdir agents/email
touch agents/email/__init__.py agents/email/agent.py agents/email/router.py
mkdir agents/email/skills
touch agents/email/skills/__init__.py agents/email/skills/prompt.py
```

---

## Step 2 — Define modes and prompt builders (`skills/prompt.py`)

```python
# agents/email/skills/prompt.py

SUPPORTED_MODES = {"subject", "sequence", "reactivation", "audit"}

def build_subject_prompt(payload: dict) -> str:
    product = payload.get("product", "product")
    goal    = payload.get("goal", "conversions")
    return f"Write 5 subject line variants for: {product}. Goal: {goal}. ..."

def build_sequence_prompt(payload: dict) -> str:
    ...

_BUILDERS = {
    "subject":      build_subject_prompt,
    "sequence":     build_sequence_prompt,
    "reactivation": build_reactivation_prompt,
    "audit":        build_audit_prompt,
}

def build_email_prompt(payload: dict) -> str:
    mode    = payload.get("mode", "subject")
    builder = _BUILDERS.get(mode)
    if not builder:
        return f"ERROR: Unknown mode '{mode}'. Supported: {list(_BUILDERS)}"
    return builder(payload)
```

---

## Step 3 — Create the router (`router.py`)

Copy the pattern from any existing router and replace the constants:

```python
# agents/email/router.py
import logging
from typing import Any, Dict

logger = logging.getLogger(__name__)

_ROUTER_MODEL = "claude-sonnet-4-6"

_MODES = list(SUPPORTED_MODES)

_SYSTEM = (
    "You are an intent classifier for an email marketing AI agent. "
    "Output ONLY a valid JSON object — no explanation, no markdown."
)

_PROMPT_TEMPLATE = """\
Classify this message from an email marketer.

Message: {message}

Return JSON:
- mode: one of ["subject","sequence","reactivation","audit"] or null
- confidence: "high" | "medium" | "low"
- extracted_context: dict with useful fields (product, list_size, goal)

Respond with ONLY the JSON:"""

_TOOL = {
    "name": "classify_email_intent",
    "description": "Classify the user's email marketing request into a mode.",
    "input_schema": {
        "type": "object",
        "properties": {
            "mode":              {"type": ["string", "null"], "enum": _MODES + [None]},
            "confidence":        {"type": "string", "enum": ["high", "medium", "low"]},
            "extracted_context": {"type": "object", "additionalProperties": True},
        },
        "required": ["mode", "confidence", "extracted_context"],
    },
}

_FALLBACK: Dict[str, Any] = {"mode": None, "confidence": "low", "extracted_context": {}}


def _validate(result: Dict[str, Any]) -> Dict[str, Any]:
    mode       = result.get("mode")
    confidence = result.get("confidence", "low")
    extracted  = result.get("extracted_context", {})
    if mode not in _MODES:
        mode = None
    if confidence not in ("high", "medium", "low"):
        confidence = "medium" if mode else "low"
    return {
        "mode":              mode,
        "confidence":        confidence,
        "extracted_context": extracted if isinstance(extracted, dict) else {},
    }


def route_email_intent(analyzer: Any, message: str) -> Dict[str, Any]:
    from agents.base_router import route
    return route(
        analyzer, message,
        prompt_template=_PROMPT_TEMPLATE,
        tool=_TOOL,
        system_prompt=_SYSTEM,
        validate=_validate,
        fallback=_FALLBACK,
        model=_ROUTER_MODEL,
        name="email_router",
    )
```

---

## Step 4 — Create the agent class (`agent.py`)

```python
# agents/email/agent.py
import logging
from pathlib import Path
from typing import Any, Dict, Optional

from ..base_agent import BaseAgent
from .skills.prompt import build_email_prompt, SUPPORTED_MODES
from .router import route_email_intent

logger = logging.getLogger(__name__)

_VAULT_CAMPAIGNS = Path(__file__).parent.parent.parent / "vault" / "campaigns"

_SYSTEM_PROMPTS = {
    "subject":      "You are an email subject line specialist with 10+ years of A/B testing...",
    "sequence":     "You are an email sequence strategist specialising in lifecycle marketing...",
    "reactivation": "You are a win-back campaign specialist...",
    "audit":        "You are an email deliverability and performance auditor...",
}


class EmailAgent(BaseAgent):
    """Email marketing agent.

    Modes: subject, sequence, reactivation, audit
    """

    def get_system_prompt(self, mode: str = None) -> str:
        return _SYSTEM_PROMPTS.get(mode or "subject", _SYSTEM_PROMPTS["subject"])

    def run(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        if not self.analyzer:
            return {"error": "No analyzer configured"}

        # Payload size guard (inherited pattern — all agents do this)
        if len(str(payload)) > 80_000:
            return {"error": "Payload too large.", "agent": self.name}

        raw_mode = str(payload.get("mode", "subject")).lower().strip()
        mode     = self._validate_mode(raw_mode, SUPPORTED_MODES)
        if mode is None:
            return {"error": f"Unknown mode: '{raw_mode}'. Supported: {SUPPORTED_MODES}",
                    "agent": self.name}

        prompt       = build_email_prompt(payload)
        final_prompt = self._build_prompt_with_contract(prompt)

        result_text = self.analyzer.chat_with_agent(
            final_prompt,
            system_prompt=self.get_system_prompt(mode),
            agent_name=self.name,
            agent_mode=mode,
        )

        # Vault save using BaseAgent helper (handles errors, adds prompt-hash)
        filename = f"{__import__('datetime').date.today().isoformat()}-email-{mode}-{payload.get('product','')[:30]}.md"
        content  = f"# Email {mode} — {payload.get('product','—')}\n\n**Prompt-hash:** `{self._prompt_hash(self.get_system_prompt(mode))}`\n\n---\n\n{result_text}"
        self._save_to_vault(filename, content, _VAULT_CAMPAIGNS)

        return {"result": result_text, "agent": self.name, "mode": mode}

    def smart_chat(self, message: str, chat_id: int = 0,
                   extra_payload: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        intent     = route_email_intent(self.analyzer, message)
        mode       = intent["mode"]
        confidence = intent["confidence"]
        extracted  = intent.get("extracted_context", {})

        if confidence in ("high", "medium") and mode:
            payload = {"mode": mode, **extracted}
            if extra_payload:
                payload.update(extra_payload)
            result = self.run(payload)
            result["_routed"] = {"mode": mode, "confidence": confidence}
            self._persist_routed_history(chat_id, message, result.get("result", ""))
            return result

        return self.chat(message, chat_id=chat_id, mode=mode)
```

---

## Step 5 — Register in AgentsManager

Edit `agents/manager.py`:

```python
# Add import at top:
from .email.agent import EmailAgent

# Add registration in __init__:
self.register_agent("email", EmailAgent("email", analyzer))

# Add dependencies (if email needs strategy context first):
_DEPENDENCIES: Dict[str, List[str]] = {
    ...existing...
    "email": ["strategy"],   # email agent benefits from strategy output
}
```

---

## Step 6 — Add Telegram commands (optional)

In `run_agent_telegram.py`:

```python
# Add to SKILL_COMMANDS dict:
SKILL_COMMANDS: Dict[str, str] = {
    ...existing...
    "/email":  "sequence",      # default mode for /email command
    "/subject": "subject",
}
```

---

## Step 7 — Write tests

Create `tests/test_email_agent.py`:

```python
from tests.conftest import MockAnalyzer

def test_email_agent_valid_run():
    from agents.email.agent import EmailAgent
    agent  = EmailAgent("email", MockAnalyzer())
    result = agent.run({"mode": "subject", "product": "SaaS tool"})
    assert "error" not in result
    assert "result" in result
    assert result["agent"] == "email"

def test_email_agent_unknown_mode():
    from agents.email.agent import EmailAgent
    agent  = EmailAgent("email", MockAnalyzer())
    result = agent.run({"mode": "magic"})
    assert "error" in result

def test_email_router_delegates():
    from agents.email.router import route_email_intent

    class MockAnalyzer:
        def call_tool(self, *a, **kw):
            return {"mode": "subject", "confidence": "high", "extracted_context": {}}

    result = route_email_intent(MockAnalyzer(), "write email subjects for my SaaS")
    assert result["mode"] == "subject"
    assert result["confidence"] == "high"
```

---

## Checklist

- [ ] `agents/<name>/agent.py` — inherits `BaseAgent`, implements `run()` and `smart_chat()`
- [ ] `agents/<name>/router.py` — delegates to `agents.base_router.route()`
- [ ] `agents/<name>/skills/prompt.py` — defines `SUPPORTED_MODES` and one builder per mode
- [ ] Registered in `agents/manager.py` — `register_agent()` + `_DEPENDENCIES`
- [ ] Tests in `tests/test_<name>_agent.py`
- [ ] Added to `docs/api.md` — input/output schema

---

## Key rules

1. **`run()` must always return `{"result": ..., "agent": self.name, "mode": ...}` or `{"error": ..., "agent": self.name}`** — never raise.
2. **Input validation first** — check payload size and mode before any LLM call.
3. **Vault saving is best-effort** — use `self._save_to_vault()`, never raise on failure.
4. **Router always delegates to `base_router.route()`** — never copy-paste the routing logic.
5. **System prompts are the agent's personality** — each mode needs a distinct, domain-specific persona.
