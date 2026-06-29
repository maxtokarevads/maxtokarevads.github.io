"""
Meta Ads Canon — Audit skill.
Based on Meta Ads Canon Runbook (MAC rules) and 10 SOPs.

Canon severity:
  P0 — pixel/CAPI/policy incident. STOP optimization, fix first.
  P1 — significant KPI impact (ROAS/CPA/CVR drop). Fix within 24-48h.
  P2 — hygiene/optimization. Do when P0/P1 are clear.

Canon gates (must pass before any optimization):
  Pixel gate    — pixel firing, primary conversions live, no 0-event anomaly
  CAPI gate     — CAPI active, EMQ ≥6.0, deduplication configured
  Account gate  — Good Standing, no violations, BM verified
"""
from typing import Any, Dict
from .meta_rules import get_meta_rules_for_audit
from .meta_sops import get_meta_sop_steps


_META_CANON_FRAMEWORK = """
## Meta Ads Canon Framework

### Severity levels
- P0 — breaks measurement or violates policy. STOP all optimization → /tracking /incident first.
- P1 — significantly impacts ROAS/CPA/CVR/CVR but not an emergency. Fix within 24-48h.
- P2 — hygiene/optimization. Address in weekly cycle.

### Where it applies
Pixel | CAPI | Attribution | Account | Campaigns | Audiences | Creative | Feed/Catalog | Landing Page

### KPI impact tags
ROAS | CPA | CVR | CTR | CPM | Frequency | Reach | EMQ | Learning Phase

### Lifecycle checks
Setup | Weekly | Monthly | Quarterly | Incident
"""

_META_CANON_GATES = """
## Meta Canon P0 Gates (check FIRST, before any optimization)

### Gate 1 — Pixel Tracking (MAC-0001, MAC-0002)
- Pixel fires on all conversion pages: Purchase/Lead event must show data in last 7d
- Test via Pixel Helper Chrome extension on all key pages
- RED FLAG: 0 Purchase events in Events Manager → trigger /tracking immediately

### Gate 2 — CAPI & Signal Quality (MAC-0003, MAC-0005, MAC-0006)
- CAPI active: Server events must appear in Events Manager (not only Browser)
- Deduplication: event_id passed in both browser and server events
- EMQ ≥ 6.0 for primary conversion event
- RED FLAG: EMQ <6.0 or 0 server events → fix CAPI before optimization

### Gate 3 — Account Health (MAC-0004, MAC-0007)
- Account Quality: no active policy violations, no restrictions, no payment holds
- Business Manager: verified, ≥2 admins, pixel/catalog owned by BM
- RED FLAG: any active violation → /incident before any other work

IF ANY GATE FAILS → document in Fixlist with P0 severity, stop optimization, fix gate first.
"""

_META_CANON_OUTPUT_FORMAT = """
## Meta Canon Output Format

### Part 1 — Fixlist (full, for PDF)
| Rule ID | Severity | Where | Issue | Action | Verify by | Rollback |
|---------|----------|-------|-------|--------|-----------|---------|

Rules:
- No invented data. Missing input → "Missing input: [INPUT_NAME]"
- Evidence-first: every finding tied to a specific data point
- P0 first, then P1, then P2

### Part 2 — TELEGRAM_REPORT (required at the end)

===TELEGRAM_REPORT===
GATES
[✅ or ❌] Pixel + CAPI: [one-line status]
[✅ or ❌] EMQ Score: [one-line status]
[✅ or ❌] Account health: [one-line status]

METRICS
Spend: $X | ROAS: Xx | CPM: $X | CTR: X% | Frequency: X

FINDINGS
[P0|MAC-XXXX|Where|One-line issue|One-line fix]
[P1|MAC-XXXX|Where|One-line issue|One-line fix]
(max 6 findings)

COUNTS
P0: N | P1: N | P2: N
===END_TELEGRAM_REPORT===
"""

_META_INPUT_STANDARDS = """
## Input Standards — what data to provide for accurate audit

### Minimum inputs (for any audit)
- META__Account_Quality — Account Quality dashboard status
- META__Events_Manager — Events list, EMQ scores, last 7d event counts
- META__Campaigns_Overview — All active campaigns: spend, ROAS, CPA, CTR, CPM, Frequency (last 30d)
- META__Ad_Sets_List — Ad sets: audience type, size, learning phase, budget

### Recommended inputs (for deeper audit)
- META__Audiences_List — All custom + lookalike audiences with sizes and last-updated dates
- META__Creative_Performance — Per-ad CTR, Frequency, ROAS, age of creative
- META__Change_History — Changes in last 7-30 days
- META__Catalog_Diagnostics — Product catalog issues (ecom only)

### Input pack shortcuts
Use these codes when referencing missing data:
  [PACK_EVENTS]      → Events Manager full export (last 7d)
  [PACK_CAMPAIGNS]   → Campaign performance report (last 30d)
  [PACK_AUDIENCES]   → Audience list with sizes
  [PACK_CREATIVE]    → Ad-level performance with creative preview
  [PACK_CATALOG]     → Commerce Manager Diagnostics (ecom)
  [PACK_CHANGES]     → Change History last 30d

If a required pack is missing, acknowledge it in output:
"Input missing: [PACK_EVENTS] — tracking gate cannot be fully verified."
"""

_META_CANON_COMMANDS = """
## Meta Canon Commands

| Command | SOP | When to use |
|---------|-----|-------------|
| /audit | SOP-M001 Account Audit (Full) | Full account health check |
| /tracking | SOP-M002 Pixel & CAPI Health Check | Tracking issues, 0-conversion anomaly |
| /weekly | SOP-M003 Weekly Optimization Loop | Weekly performance review |
| /monthly | SOP-M003 | Monthly review (extended) |
| /creative | SOP-M004 Creative Refresh Playbook | Creative fatigue, CTR declining |
| /scale | SOP-M005 Scaling Playbook | Ready to scale |
| /audiences | SOP-M006 Audience Strategy & Refresh | Audience refresh, CPM spike |
| /asc | SOP-M007 Advantage+ Shopping Setup | Launch ASC |
| /incident | SOP-M008 Incident Response | Sudden ROAS/conversion drop |
| /launch | SOP-M009 Campaign Launch Checklist | New campaign setup |
| /retargeting | SOP-M010 Retargeting Funnel Setup | Set up retargeting funnel |
| /measurement | SOP-M011 Measurement & Privacy Setup | Consent/CAPI/EMQ audit |
| /b2b | SOP-M012 B2B & Lead-gen Closed Loop | Lead quality + CRM sync setup |
| /crm | SOP-M012 | Same as /b2b |
| /leadgen | SOP-M012 | Same as /b2b |
"""


def build_meta_audit_prompt(payload: Dict[str, Any]) -> str:
    """Build the full Meta Canon audit prompt from payload."""
    command      = payload.get("command", "/audit")
    project      = payload.get("project", "")
    account_type = payload.get("account_type", "")   # ecom | lead-gen | app
    notes        = payload.get("notes", "")
    goal         = payload.get("goal", "")

    sop_section = get_meta_sop_steps(command)
    rules_section = get_meta_rules_for_audit(account_type)

    context_block = ""
    if project or account_type or notes or goal:
        parts = []
        if project:
            parts.append(f"Project: {project}")
        if account_type:
            parts.append(f"Account type: {account_type}")
        if goal:
            parts.append(f"Goal / context: {goal}")
        if notes:
            parts.append(f"Notes: {notes}")
        context_block = "## Audit Context\n" + "\n".join(parts) + "\n"

    return f"""You are a senior Meta Ads performance specialist executing a Canon audit command: {command}

Platform: Meta Ads (Facebook / Instagram)
{context_block}
{_META_CANON_FRAMEWORK}

{_META_CANON_GATES}

{_META_INPUT_STANDARDS}

## Active SOP for command {command}

{sop_section}

## All Meta Canon Rules (MAC-XXXX)

Use these rules as the evaluation checklist. For each rule that applies:
1. Check if the input data satisfies the rule
2. If data is missing: note "Input missing: [PACK_CODE]" and skip
3. If violation found: add to Fixlist with Rule ID, severity, and concrete action

{rules_section}

{_META_CANON_OUTPUT_FORMAT}

{_META_CANON_COMMANDS}

## Your task

Execute the {command} command following the SOP steps above.
Apply all relevant Canon rules to the provided data.
Output a structured Fixlist sorted P0 → P1 → P2.
Do not fabricate data. If inputs are missing, request them explicitly.
End with: "Next command: /[recommended follow-up command] — [reason]"
"""
