"""
Google Ads Canon — Audit skill.
Based on Canon Runbook v0.1 and P1 Command Layer.

Canon severity:
  P0 — tracking/policy/feed incident. STOP optimization, fix first.
  P1 — significant KPI impact (ROAS/CPA/CVR drop). High priority.
  P2 — hygiene/optimization. Do when P0/P1 are clear.

Canon gates (must pass before any optimization):
  Tracking gate  — auto-tagging ON, primary conversions live, no 0-conv anomaly
  Feed/Policy gate (ecom) — no MC disapprovals, shipping OK, product status OK
  Incident gate  — no suspicious changes in Change History before a drop
"""
from typing import Any, Dict, List
from .rules import get_rules_for_audit
from .sops import get_sop_steps


_CANON_RULES_FRAMEWORK = """
## Canon Rules Framework (P0 core)

### Severity levels
- P0 — breaks measurement/policy/spend. STOP all optimization → /tracking /incident /feed first.
- P1 — strongly hits KPI but not an emergency. Fix within 24–48h.
- P2 — hygiene/optimization. Address in weekly cycle.

### Where it applies (taxonomy)
Tracking | Attribution | Account hygiene | Search | PMax | Shopping | Feed | Policies

### Channels
Google Ads | GA4 | GTM | Merchant Center | Looker Studio

### KPI impact tags
ROAS | CPA | CVR | CTR | CPC | Spend control | Attribution | Revenue | Lead quality

### Lifecycle checks
Setup | Weekly | Monthly | Quarterly | Incident
"""

_CANON_GATES = """
## Canon P0 Gates (check FIRST, before any optimization)

### Gate 1 — Tracking
- Auto-tagging: must be ENABLED in Google Ads account settings
- Primary conversion action: must have conversions in last 7 days (no 0-conv anomaly)
- No duplicate conversion counting (check ADS__Conversions__Summary__Settings)
- GA4 purchase events firing: verify in GA4__Events__Purchase
- RED FLAG: 0 conversions after a change → trigger /incident immediately

### Gate 2 — Feed / Policy (ecom accounts)
- Merchant Center: no mass disapprovals (check MC__Diagnostics)
- Shipping settings: match live checkout (MC__Shipping__Settings)
- Product status: no sudden drop in approved products
- Account-level policy warnings: check for active violations

### Gate 3 — Incident
- Review ADS__ChangeHistory for changes 24–48h before any performance drop
- If change correlates with drop → /incident before weekly optimization
- Rollback path must be documented before executing any fix

IF ANY GATE FAILS → document in Fixlist with P0 severity, stop optimization, fix gate first.
"""

_CANON_OUTPUT_FORMAT = """
## Canon Output Format

### Part 1 — Fixlist (full, for PDF)
| Rule ID | Severity | Where | Issue | What to do | Verify after | Rollback |
|---------|----------|-------|-------|------------|--------------|---------|

Rules:
- No invented data. Missing input → "Missing input: [INPUT_CODE]"
- Evidence-first: every finding tied to a specific data point
- P0 first, then P1, then P2

### Part 2 — TELEGRAM_REPORT (short summary, required at the end)

After the full Fixlist, output EXACTLY this block (no deviations):

===TELEGRAM_REPORT===
GATES
[✅ or ❌] Tracking: [one-line status]
[✅ or ❌] Enhanced Conv: [one-line status]
[✅ or ❌] Account health: [one-line status]

METRICS
Spend: $X | CPA: $X | CTR: X% | QS: X/10 | IS: X%

FINDINGS
[P0|GAC-XXXX|Where|One-line issue|One-line fix]
[P1|GAC-XXXX|Where|One-line issue|One-line fix]
[P1|GAC-XXXX|Where|One-line issue|One-line fix]
[P2|GAC-XXXX|Where|One-line issue|One-line fix]
(max 6 findings total, most critical first)

COUNTS
P0: N | P1: N | P2: N
===END_TELEGRAM_REPORT===
"""

_CANON_INPUT_STANDARDS = """
## Canon Input Standards

### Input code format: SYSTEM__OBJECT__SCOPE__WINDOW
Examples:
- ADS__SearchTerms__SearchTerm__30d
- MC__Diagnostics__Account__Current
- GA4__KeyEvents__Property__Current
- SHOPIFY__Orders__Order__30d
- LOOKER__ReportLink__Project__Current

### Data quality gate (Step 1 in every SOP):
Before analysis, validate each input:
- Period ok: ≥ 7d (unless incident — then 48h is fine)
- Currency/timezone consistent with project settings
- No empty critical fields (campaign, cost, conversions/conv_value)
- No all-zero metrics (→ tracking issue, trigger P0 gate)
- Granularity matches SOP need (campaign vs search term vs product)
If Must-have input missing → fallback to UI-only checks + mark "Missing input: [INPUT_CODE]" in output.

### ID conventions (Canon):
- Rule ID: GAC-0001 format
- SOP ID: SOP-0001 format
- Command ID: CMD-0001 format
- Output template ID: OT-0001 format
Never reuse or change an ID after publication.

### List separator standard: | (pipe with spaces)
- Correct:  GA4 | Google Ads | GTM
- Correct:  P0 | P1
- Wrong:    GA4, Google Ads  (commas only in Notion CSV exports)
"""

_CANON_INPUT_PACKS = """
## Canon Required Input Packs

### Minimum for /audit (any account):
- LOOKER__ReportLink__Project__Current (or any performance dashboard/export)
- ADS__AutoTagging__Status
- ADS__Conversions__Summary__Settings
- GA4__Events__Purchase (ecom) or GA4__Conversions__Summary (lead-gen)

### Performance Pack (for /weekly /monthly):
- LOOKER__ReportLink__Project__Current
- ADS__Export__Campaigns__Performance
- ADS__Export__AdGroups__Performance
- ADS__Export__PMax__AssetGroups__Performance
- GA4__LandingPages__Report
- SHOPIFY__Orders__Order (ecom)
- MC__Diagnostics (ecom)

### Tracking Pack (for /tracking /incident):
- ADS__Conversions__Summary__Settings
- ADS__AutoTagging__Status
- GA4__Events__Purchase
- GA4__Conversions__Summary
- ADS__ChangeHistory

### Feed Pack (for /feed):
- MC__Diagnostics
- MC__Shipping__Settings
- MC__ProductStatus__Sample
- MC__FeedRules__Transformations

### Search Terms Pack (for /searchterms):
- ADS__Export__SearchTerms (30d rolling)
- ADS__Export__Campaigns__AdGroups__Mapping
"""

_CANON_COMMANDS = """
## Canon Command Reference — Google Ads

| Command | Intent | Primary SOP | Key Output |
|---------|--------|-------------|-----------|
| /audit | Full account audit + fix plan | Account Audit (Full) | Audit + Fixlist (P0→P1→P2) |
| /weekly | Weekly optimization cycle | Weekly Optimization Loop | Weekly Report + Actions log |
| /monthly | Monthly review | Weekly Optimization Loop | Report (30d vs prev 30d) |
| /quarterly | Quarterly report + roadmap | Quarterly Optimization Review | Quarterly Report + Test plan |
| /fixlist | Prioritized task list only | Relevant SOP by context | Fixlist (P0/P1/P2) |
| /tracking | Tracking & conversions check | Tracking QA + Incident Response | Tracking QA Report + Fixlist |
| /incident | Incident response + recovery | Tracking QA + Incident Response | Incident report + Fixlist |
| /feed | Merchant Center / feed triage | Merchant Center Triage | Feed Triage Report + Fixlist |
| /searchterms | Search terms analysis | Search Terms Cleanup | ST Report + Negatives + KW list |
| /pmax | Performance Max control | PMax Control Playbook | PMax checklist + Actions |
| /launch | Campaign launch checklist | Launch Checklist | Launch checklist |
| /semantic | Keyword research from scratch | Semantic Mining from 0 | Keyword clusters + Campaign map |
| /measurement | Measurement & privacy audit | Measurement & Privacy Setup | Consent/EC/CAPI status + Fixlist |
| /b2b | B2B/lead-gen closed-loop setup | B2B & Lead-gen Closed Loop | CRM sync + qualified lead bidding plan |
| /crm | Same as /b2b | B2B & Lead-gen Closed Loop | CRM closed-loop plan |
| /leadgen | Same as /b2b | B2B & Lead-gen Closed Loop | Lead-gen optimisation plan |
"""


def build_google_audit_prompt(payload: Dict[str, Any]) -> str:
    product      = payload.get("product", "product")
    command      = payload.get("command", "/audit")
    date_range   = payload.get("date_range", "last 30 days")
    market       = payload.get("market", "")
    context      = payload.get("context", "")
    inputs       = payload.get("inputs", {})
    metrics      = payload.get("metrics", {})
    notes        = payload.get("notes", "")
    project      = payload.get("project", "")
    account_type = payload.get("account_type", "")  # ecom | lead-gen | app

    # Build inputs block
    inputs_lines: List[str] = []
    for code, value in inputs.items():
        inputs_lines.append(f"  {code}: {value}")
    inputs_block = "\n".join(inputs_lines) if inputs_lines else "  (no inputs provided — list Missing inputs in output)"

    # Build metrics block
    metrics_lines: List[str] = []
    for k, v in metrics.items():
        metrics_lines.append(f"  {k}: {v}")
    metrics_block = "\n".join(metrics_lines) if metrics_lines else "  (no metrics provided)"

    market_line    = f"\nMarket/Currency: {market}" if market else ""
    context_line   = f"\nContext: {context}" if context else ""
    notes_line     = f"\nNotes: {notes}" if notes else ""
    project_line   = f"\nProject: {project}" if project else ""
    acct_line      = f"\nAccount type: {account_type}" if account_type else ""

    is_ecom = "ecom" in account_type.lower() or "shopify" in str(inputs).lower()
    ecom_gates = "\n- Feed/Policy gate (ecom): MC disapprovals, shipping, product status" if is_ecom else ""

    return f"""Platform: Google Ads — Canon Audit
{_CANON_INPUT_STANDARDS}

Command: {command}
Date range: {date_range}{project_line}{market_line}{acct_line}{context_line}

Inputs provided:
{inputs_block}

Metrics:
{metrics_block}{notes_line}

{_CANON_RULES_FRAMEWORK}

{_CANON_GATES}

{_CANON_OUTPUT_FORMAT}

{_CANON_COMMANDS}

---

TASK: Execute {command} per the Canon Runbook.

{get_sop_steps(command)}

## Step 1 — P0 Gates (mandatory first)

Check all gates before any optimisation:
1. Tracking gate: auto-tagging ON, primary conversion action configured, no 0-conversion anomaly{ecom_gates}
2. Incident gate: does Change History correlate with any performance drop?

If any gate is FAIL → stop optimisation, surface P0 in Fixlist, explain what must be fixed first.

{get_rules_for_audit(account_type)}

## Step 2 — Performance Analysis (only if gates passed)

Analyse provided data:
- KPI vs prior period: ROAS / CPA / CVR / CTR / CPC
- Campaigns: which are driving results / causing issues
- PMax (if present): Asset Groups performance, brand vs non-brand split
- Search: Quality Score, Impression Share, Lost IS (budget/rank)
- Anomalies: sharp changes, new trends, unusual patterns

## Step 3 — Fixlist (Canon format)

Output table:
| Rule ID | Severity | Where | Issue | What to do | Verify after | Rollback |

Rules:
- Missing inputs → explicitly write "Missing input: [CODE]", do not invent data
- Every action: concrete steps (no "consider exploring")
- P0 first, then P1, then P2

## Step 4 — Done criteria (Canon standard)

- [ ] P0 Gates checked and documented (pass or fail with explanation)
- [ ] If any P0 gate FAIL — optimisation halted, only P0 fix in Fixlist
- [ ] Every Fixlist row has: Severity | Rule ID | Where | Issue | What to do | Verify | Rollback
- [ ] Missing inputs explicitly stated (no data invented in their place)
- [ ] Evidence-first: every finding tied to a specific input / metric / value
"""
