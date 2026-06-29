"""
TikTok Ads Canon Audit prompt builder.
Mirrors the Google Canon (audit.py) and Meta Canon (meta_audit.py) architecture.
"""
from typing import Any, Dict, List

from .tiktok_rules import TIKTOK_CANON_RULES, get_tiktok_rules_for_audit
from .tiktok_sops  import get_tiktok_sop_steps


# ─── Framework constants ─────────────────────────────────────────────────────

_TIKTOK_CANON_FRAMEWORK = """
## TikTok Ads Canon Framework

### Severity levels
- P0: Breaks measurement, delivery, or policy. Stop all optimisation. Fix first.
- P1: Significant KPI impact (CPA/ROAS/volume). Fix within 24-48h.
- P2: Hygiene and incremental improvements. Address in weekly cycle.

### TikTok-specific principles
1. **Algorithm-first**: The TikTok algorithm distributes based on content relevance, not only demographics.
   Hook Rate is the primary creative health signal — check it before CTR.
2. **Creative velocity**: Creative fatigue is 2-3× faster than Meta (~7-14 day shelf life at active spend).
   Pipeline of new assets is not optional, it is table stakes.
3. **Learning phase**: ≥50 optimisation events / 7 days per Ad Group. Do NOT change bid,
   budget, audience, or creative during learning — any significant edit resets the clock.
4. **Over-attribution**: TikTok Ads Manager over-reports conversions by 35-55% (view-through inflation).
   Always cross-validate with GA4 and backend. Adjust ROAS targets accordingly.
5. **Events API (CAPI equivalent)**: Less mature than Meta CAPI but critical for iOS signal recovery.
   Target ≥50% of conversions reported via server. Enable deduplication via event_id.
"""

_TIKTOK_CANON_GATES = """
## P0 Gates — Check Before Any Optimisation

### Gate 1: Pixel & Events API
- TikTok Pixel fires on all conversion pages (PageView everywhere; Purchase/Lead on confirmation only)
- Primary conversion event (Purchase / Lead / CompleteRegistration) active and receiving data
- No duplicate counting: event_id deduplication active between browser pixel and Events API
- Server events ≥ 50% of total conversion events in Events Manager

### Gate 2: Account Health
- Account in Good Standing: no active policy violations, no payment hold
- All active creatives approved (< 20% of spend-weighted impressions on 'Under Review' ads)
- Business Center verification complete; ≥ 2 admin users

### Gate 3: Attribution Sanity
- TikTok reported conversions vs GA4 / backend: ratio 1.0–2.0 (> 2.0 = duplicate counting P0)
- Attribution window set to 7-day click / 1-day view (standard); deviation documented if different

If any gate FAILS → surface as P0 in Fixlist → stop optimisation → fix gate before proceeding.
"""

_TIKTOK_CANON_OUTPUT_FORMAT = """
## Output Format

### Section 1: P0 Gate Summary
For each gate: PASS or FAIL with evidence. If FAIL: one-line cause + Rule ID.

### Section 2: Performance Snapshot (only if all gates PASS)
| Metric | Current | WoW | Benchmark | Status |
|--------|---------|-----|-----------|--------|
| Hook Rate (3s) | — | — | ≥ 30% | — |
| Video Completion | — | — | ≥ 25% (≤15s) | — |
| CTR (Link) | — | — | 1.0–2.5% | — |
| CVR | — | — | 0.5–1.5% | — |
| CPA | — | — | account target | — |
| ROAS (TikTok reported) | — | — | account target | — |
| ROAS (backend adjusted) | — | — | ÷ attribution factor | — |
| CPM | — | — | $3–8 | — |
| Learning Phase Ad Groups | — | — | 0 stuck | — |

### Section 3: Fixlist (Canon format)
| Rule ID | Severity | Where | Issue | What to do | Verify after | Rollback |
|---------|----------|-------|-------|------------|--------------|---------|
Rows: P0 first → P1 → P2. Every issue must have a Rule ID.
If data is missing: "Missing input: [DESCRIPTION]" — do not invent values.

### Section 4: Creative Actions
For each fatigued or low-Hook-Rate creative:
| Ad Name | Hook Rate | CTR | Age (days) | Action | New hook concept |

### Section 5: Done Criteria
- [ ] All 3 P0 Gates checked and documented
- [ ] If any P0 FAIL: optimisation halted; only P0 items in Fixlist
- [ ] Every Fixlist row has: Rule ID | Severity | Where | Issue | Action | Verify | Rollback
- [ ] Missing inputs stated explicitly
- [ ] Over-attribution factor calculated and noted
- [ ] Creative action plan included (Hook Rate audit)
"""

_TIKTOK_CANON_INPUT_STANDARDS = """
## Input Standards

### Required inputs for /audit
- TIKTOK__Events__Purchase (or Lead) — last 7d and 30d event count
- TIKTOK__Events__Source — browser vs server split (%)
- TIKTOK__Campaigns__Performance — spend, impressions, clicks, conversions, CPA, ROAS
- TIKTOK__Creative__Performance — Hook Rate, Completion Rate, CTR per ad; creative age
- GA4__Conversions__TikTok — TikTok-attributed conversions for over-attribution check
- TIKTOK__Account__Health — any active violations or restrictions

### Input code format: PLATFORM__OBJECT__SCOPE__WINDOW
Examples:
- TIKTOK__Events__Purchase__7d
- TIKTOK__Creative__HookRate__14d
- TIKTOK__Audiences__CustomAudiences__Current
- GA4__Sessions__TikTok__30d

If a required input is missing → write "Missing input: [INPUT_CODE]" in Fixlist. Do not invent data.
"""

_TIKTOK_CANON_COMMANDS = """
## TikTok Canon Command Reference

| Command | Intent | Primary SOP | Key Output |
|---------|--------|-------------|-----------|
| /audit | Full account audit | SOP-T001 | Fixlist (P0→P1→P2) + Creative actions |
| /tracking | Pixel + Events API health check | SOP-T002 | Tracking QA Report |
| /weekly | Weekly optimisation cycle | SOP-T003 | Weekly Report + Actions |
| /creative | Creative refresh playbook | SOP-T004 | Creative rotation plan |
| /scale | Scaling playbook | SOP-T005 | Scale strategy |
| /audiences | Audience strategy & refresh | SOP-T006 | Audience map + actions |
| /smartplus | Smart+ Campaign setup | SOP-T007 | Smart+ launch checklist |
| /incident | Sudden drop diagnosis | SOP-T008 | Incident report + Fixlist |
| /launch | New campaign launch checklist | SOP-T009 | Launch checklist |
| /retargeting | Retargeting funnel setup | SOP-T010 | Retargeting strategy |
"""


# ─── Prompt builder ───────────────────────────────────────────────────────────

def build_tiktok_audit_prompt(payload: Dict[str, Any]) -> str:
    product      = payload.get("product", "product")
    command      = payload.get("command", "/audit")
    date_range   = payload.get("date_range", "last 30 days")
    market       = payload.get("market", "")
    context      = payload.get("context", "")
    inputs       = payload.get("inputs", {})
    metrics      = payload.get("metrics", {})
    notes        = payload.get("notes", "")
    project      = payload.get("project", "")
    account_type = payload.get("account_type", "")   # ecom | lead-gen | app

    # Build inputs block
    inputs_lines: List[str] = []
    for code, value in inputs.items():
        inputs_lines.append(f"  {code}: {value}")
    inputs_block = "\n".join(inputs_lines) if inputs_lines else \
        "  (no inputs provided — list all as Missing inputs in output)"

    # Build metrics block
    metrics_lines: List[str] = []
    for k, v in metrics.items():
        metrics_lines.append(f"  {k}: {v}")
    metrics_block = "\n".join(metrics_lines) if metrics_lines else \
        "  (no metrics provided)"

    market_line  = f"\nMarket/Currency: {market}" if market else ""
    context_line = f"\nContext: {context}" if context else ""
    notes_line   = f"\nNotes: {notes}" if notes else ""
    project_line = f"\nProject: {project}" if project else ""
    acct_line    = f"\nAccount type: {account_type}" if account_type else ""

    is_ecom = "ecom" in account_type.lower() or "shopify" in str(inputs).lower()
    catalog_gate = "\n- Catalog gate (ecom): disapproval rate < 5%, feed freshness < 24h" if is_ecom else ""

    return f"""Platform: TikTok Ads — Canon Audit
{_TIKTOK_CANON_INPUT_STANDARDS}

Command: {command}
Date range: {date_range}{project_line}{market_line}{acct_line}{context_line}

Inputs provided:
{inputs_block}

Metrics:
{metrics_block}{notes_line}

{_TIKTOK_CANON_FRAMEWORK}

{_TIKTOK_CANON_GATES}

{_TIKTOK_CANON_OUTPUT_FORMAT}

{_TIKTOK_CANON_COMMANDS}

---

TASK: Execute {command} per the TikTok Canon Runbook.

{get_tiktok_sop_steps(command)}

## Step 1 — P0 Gates (mandatory first)

Check all gates before any optimisation:
1. Pixel & Events API gate: Pixel firing, primary conversion event active, no duplicate counting, server events ≥ 50%
2. Account Health gate: no active violations, all creatives approved, Business Center verified
3. Attribution Sanity gate: TikTok / GA4 ratio 1.0–2.0; attribution window = 7d click / 1d view{catalog_gate}

If any gate FAILS → stop optimisation, surface as P0 in Fixlist, explain what must be fixed first.

{get_tiktok_rules_for_audit(account_type)}

## Step 2 — Performance Analysis (only if all gates passed)

Analyse provided data:
- Creative health: Hook Rate / Completion Rate / CTR per ad; flag any creative with Hook Rate < 20%
- KPI vs prior period: ROAS (reported AND backend-adjusted) / CPA / CVR / CTR / CPM
- Learning Phase: any Ad Groups stuck > 7 days? Why?
- Audience: custom audience sizes, LAL seed quality, exclusions in prospecting
- Bid strategy match: does current bid strategy match conversion volume and maturity?
- Over-attribution: calculate ratio (TikTok reported ÷ GA4/backend); note adjusted backend ROAS

## Step 3 — Fixlist (Canon format)

Output table:
| Rule ID | Severity | Where | Issue | What to do | Verify after | Rollback |
|---------|----------|-------|-------|------------|--------------|---------|

Rules:
- P0 first, then P1, then P2
- Missing inputs → "Missing input: [INPUT_CODE]" — do not invent data
- Every action: concrete steps with TikTok UI path where applicable
- No vague recommendations ("consider reviewing") — specific actions only

## Step 4 — Creative Action Plan

For every active ad: assess Hook Rate vs benchmark (≥ 30%).
Output the Creative Actions table (Section 4 of output format).
Suggest specific new hook concepts (first 3 seconds) for any fatigued or low-Hook-Rate creative.

## Step 5 — Done Criteria

- [ ] All 3 P0 Gates checked and documented (pass or fail with evidence)
- [ ] If any gate FAIL: optimisation halted; only gate fix in Fixlist
- [ ] Every Fixlist row: Rule ID | Severity | Where | Issue | What to do | Verify | Rollback
- [ ] Missing inputs explicitly listed (nothing invented)
- [ ] Over-attribution factor calculated and backend-adjusted ROAS noted
- [ ] Creative Action Plan completed (Hook Rate for each active ad)
"""
