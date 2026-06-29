"""
Strategy Canon Audit — builds the full audit prompt.

Canon severity:
  P0 — planning gate: missing input that invalidates the plan. HALT and request.
  P1 — structural issue: plan will underperform or mislead. Flag, propose fix.
  P2 — optimisation: plan is valid but could be stronger.
"""
from typing import Any, Dict
from .rules import get_strategy_rules_for_audit
from .sops  import get_strategy_sop

_CANON_GATES = """
## Strategy Canon P0 Gates (check FIRST)

### Gate 1 — ICP Gate
  - Is the target customer defined at company size / role / pain / budget level?
  - "Everyone" or "SMBs" without role is not a gate-pass.

### Gate 2 — Measurement Gate
  - North Star Metric defined?
  - Kill signal defined (specific metric + threshold + timeframe)?

### Gate 3 — Resource Gate
  - Total monthly budget quantified?
  - Timeline specific (not "ASAP")?

IF ANY GATE FAILS → output EXACTLY:
"HALT — [SAC-XXXX]: [what is missing]. Please provide [specific information] before I can generate reliable recommendations."
DO NOT generate a plan with missing P0 inputs.
"""

_OUTPUT_FORMAT = """
## Canon Output Format

### Part 1 — P0 Gate Status
For each gate: ✅ PASS or ❌ FAIL (with specific finding).
If any FAIL: HALT here.

### Part 2 — Fixlist (P0 → P1 → P2)
| Rule ID | Severity | Category | Finding | What to do | Verify |
Only include rules that FAIL. Skip passing rules.

### Part 3 — Strategy Plan
Only output after P0 gates pass.
Include explicit references to P1 fixes inline.

### Part 4 — TELEGRAM_REPORT

After the plan, output EXACTLY this block:

===TELEGRAM_REPORT===
GATES
[✅/❌] ICP: [one-line status]
[✅/❌] Measurement: [one-line status]
[✅/❌] Resources: [one-line status]

FINDINGS
[P0|SAC-XXXX|Category|One-line issue|One-line fix]
[P1|SAC-XXXX|Category|One-line issue|One-line fix]
(max 6 findings total)

COUNTS
P0: N | P1: N | P2: N
===END_TELEGRAM_REPORT===
"""

_INPUT_STANDARDS = """
## Input Standards

Field: product — what is being sold / launched
Field: goal — primary business objective
Field: industry — sector (saas, ecom, b2b, app, local, agency)
Field: audience — ICP description (company size, role, pain, budget signal)
Field: budget — monthly budget in USD
Field: timeline — specific period (e.g. "3 months", "Q3 2026")
Field: competitors — top 2-3 competitors with their positioning
Field: usp — current unique selling proposition (can be a hypothesis)
Field: current_channels — channels already active (optional)

If a required field is missing: write "Missing input: [FIELD_NAME]" — never invent data.
"""


def build_strategy_audit_prompt(payload: Dict[str, Any]) -> str:
    product      = payload.get("product", "product")
    command      = payload.get("command", "/audit")
    context      = payload.get("context", "")
    industry     = payload.get("industry", "")
    audience     = payload.get("audience", {})
    budget       = payload.get("budget", "")
    timeline     = payload.get("timeline", "")
    goal         = payload.get("goal", "")
    usp          = payload.get("usp", "")
    competitors  = payload.get("competitors", "")
    notes        = payload.get("notes", "")
    current_ch   = payload.get("current_channels", [])

    audience_text = (
        ", ".join(f"{k}: {v}" for k, v in audience.items() if v)
        if isinstance(audience, dict)
        else str(audience)
    ) or "(not specified)"
    competitors_line = f"\nCompetitors: {competitors}" if competitors else ""
    current_ch_line  = f"\nActive channels: {', '.join(current_ch)}" if current_ch else ""
    context_line     = f"\nContext: {context}" if context else ""
    notes_line       = f"\nNotes: {notes}" if notes else ""

    return f"""Platform: Marketing Strategy — Canon Audit
{_INPUT_STANDARDS}

Command: {command}
Product: {product}
Goal: {goal}
Industry: {industry}
Audience: {audience_text}
Budget: {f"${budget}/mo" if budget else "(not specified)"}
Timeline: {timeline or "(not specified)"}
USP: {usp or "(not specified)"}{competitors_line}{current_ch_line}{context_line}{notes_line}

{_CANON_GATES}

{get_strategy_sop(command)}

{get_strategy_rules_for_audit({**payload, "mode": command.lstrip("/")})}

{_OUTPUT_FORMAT}

---

TASK: Execute {command} per the Strategy Canon Runbook.

Apply the Canon in order:
1. Check all P0 gates — HALT on first failure
2. Scan P1 rules — flag all failures in Fixlist
3. Generate the strategy plan (only after P0 passes)
4. Apply P2 optimisation suggestions
5. End with TELEGRAM_REPORT block

Never invent data. If a field is missing, write "Missing input: [FIELD]".
Evidence-first: every finding tied to a specific input value.
"""
