from typing import Any, Dict
from .rules import SEO_CANON_RULES, P0_RULES, P1_RULES, P2_RULES


def _format_rules(rules: list) -> str:
    lines = []
    for r in rules:
        lines.append(
            f"  [{r['id']}] {r['area']}: {r['rule']}\n"
            f"    Why: {r['why']}\n"
            f"    Verify: {r['verify']}"
        )
    return "\n\n".join(lines)


def build_seo_audit_prompt(payload: Dict[str, Any]) -> str:
    site         = payload.get("site", payload.get("url", "client website"))
    industry     = payload.get("industry", "")
    account_type = payload.get("account_type", "")
    date_range   = payload.get("date_range", "last 30 days")
    notes        = payload.get("notes", "")
    command      = payload.get("command", "/audit")

    ind_line   = f"\nIndustry: {industry}" if industry else ""
    type_line  = f"\nSite type: {account_type}" if account_type else ""
    notes_line = f"\nNotes from client: {notes}" if notes else ""

    p0_block = _format_rules(P0_RULES)
    p1_block = _format_rules(P1_RULES)
    p2_block = _format_rules(P2_RULES)

    total = len(SEO_CANON_RULES)
    p0_count = len(P0_RULES)
    p1_count = len(P1_RULES)
    p2_count = len(P2_RULES)

    return f"""Platform: SEO — Canon Audit ({command})
Site: {site}
Period: {date_range}{ind_line}{type_line}{notes_line}

You are executing a Canon SEO Audit — a systematic check of {total} rules across P0/P1/P2 severity tiers.

CRITICAL RULE: If ANY P0 gate fails → halt all optimisation recommendations and fix P0 first.
Never fabricate data. If a rule cannot be assessed without tool access, write: "Cannot assess: [reason]"

═══════════════════════════════════════════
P0 GATES — CRITICAL ({p0_count} rules)
Fix these before anything else. Each blocks meaningful SEO progress.
═══════════════════════════════════════════

{p0_block}

═══════════════════════════════════════════
P1 IMPORTANT — Fix within 1 week ({p1_count} rules)
═══════════════════════════════════════════

{p1_block}

═══════════════════════════════════════════
P2 HYGIENE — Weekly/monthly cycle ({p2_count} rules)
═══════════════════════════════════════════

{p2_block}

═══════════════════════════════════════════
REQUIRED OUTPUT FORMAT
═══════════════════════════════════════════

Return a structured audit report in this exact format:

## P0 STATUS — [PASS / FAIL]
> If any P0 fails: "HALT — resolve P0 issues before proceeding with optimisation"

| Rule ID | Area | Status | Finding | Fix | Verify | Priority |
|---------|------|--------|---------|-----|--------|----------|
[P0 rules here]

## P1 FIXLIST

| Rule ID | Area | Status | Finding | Fix | Est. Impact | Timeline |
|---------|------|--------|---------|-----|-------------|----------|
[P1 rules here]

## P2 HYGIENE LOG

| Rule ID | Area | Status | Finding | Fix |
|---------|------|--------|---------|-----|
[P2 rules here]

## SEO HEALTH SCORE: [X/100]

Weighted calculation:
- Technical (SEC-0001 to SEC-0010): 22% → [X/22]
- On-Page (SEC-0013 to SEC-0015, 0027): 20% → [X/20]
- Content & E-E-A-T (SEC-0017 to SEC-0018, 0021, 0024): 23% → [X/23]
- Schema (SEC-0011 to SEC-0012, 0019, 0028): 10% → [X/10]
- Performance / CWV (SEC-0008 to SEC-0010): 10% → [X/10]
- AI Search Readiness (SEC-0007, 0020, 0021): 10% → [X/10]
- Images (SEC-0023): 5% → [X/5]

Rating: [Poor <40 | Needs Work 40–60 | Good 60–80 | Excellent >80]

## TOP 5 PRIORITY ACTIONS
Ranked by expected organic traffic impact:
1. [Action] — [Expected impact] — [Timeline]
...

## CONFIDENCE ASSESSMENT
- Rules assessed with High confidence: [list IDs]
- Rules assessed with Medium confidence (limited data): [list IDs]
- Rules that CANNOT be assessed without tool access: [list IDs + what tool needed]
- Overall audit completeness: [X]% of rules fully assessed
"""
