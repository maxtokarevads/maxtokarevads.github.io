"""
Telegram report formatter for Canon audit outputs.

Two modes:
1. extract_telegram_report() — parses the TELEGRAM_REPORT block from LLM output
2. render_telegram_report()  — renders it as clean Telegram HTML
3. format_for_telegram()     — fallback plain-text cleaner for non-audit modes
"""
import re
from typing import Optional


_SEV_EMOJI  = {"P0": "🔴", "P1": "🟠", "P2": "🟡"}
_GATE_EMOJI = {"✅": "✅", "❌": "❌"}


# ─── Parser ───────────────────────────────────────────────────────────────────

def extract_telegram_report(text: str) -> Optional[str]:
    """Extract the ===TELEGRAM_REPORT=== block from LLM output. Returns None if absent."""
    m = re.search(
        r"===TELEGRAM_REPORT===(.*?)===END_TELEGRAM_REPORT===",
        text, re.DOTALL
    )
    return m.group(1).strip() if m else None


def extract_full_fixlist(text: str) -> str:
    """Return the full audit text without the TELEGRAM_REPORT block (for PDF)."""
    return re.sub(
        r"\n*===TELEGRAM_REPORT===.*?===END_TELEGRAM_REPORT===\n*",
        "", text, flags=re.DOTALL
    ).strip()


# ─── Renderer ─────────────────────────────────────────────────────────────────

def render_telegram_report(report_block: str, project: str = "",
                            platform: str = "", command: str = "/audit") -> str:
    """
    Convert the structured TELEGRAM_REPORT block into clean Telegram HTML.

    Expected block format:
        GATES
        ✅ Tracking: ON
        ❌ Enhanced Conv: Not configured

        METRICS
        Spend: $X | CPA: $X | QS: X/10

        FINDINGS
        P0|GAC-0001|Tracking|Auto-tagging OFF|Enable in Account Settings
        P1|GAC-0007|Bidding|QS avg 3/10|Rewrite ad copy + landing pages

        COUNTS
        P0: 1 | P1: 3 | P2: 2
    """
    lines   = report_block.splitlines()
    section = ""
    gates, metrics_str, findings, counts_str = [], "", [], ""

    for line in lines:
        l = line.strip()
        if not l:
            continue
        if l == "GATES":
            section = "gates"; continue
        if l == "METRICS":
            section = "metrics"; continue
        if l == "FINDINGS":
            section = "findings"; continue
        if l == "COUNTS":
            section = "counts"; continue

        if section == "gates":
            # Normalize text gate markers to emoji (LLM sometimes outputs [OK]/[FAIL])
            g = (l
                 .replace("[OK]", "✅").replace("[PASS]", "✅")
                 .replace("[FAIL]", "❌").replace("[ERROR]", "❌"))
            gates.append(g)
        elif section == "metrics":
            metrics_str = l
        elif section == "findings":
            findings.append(l)
        elif section == "counts":
            counts_str = l

    # ── Build output ──────────────────────────────────────────────────────────
    _PLAT_LABEL = {"google": "Google Ads", "meta": "Meta Ads", "tiktok": "TikTok Ads"}
    plat_label = _PLAT_LABEL.get(platform.lower(), platform.capitalize()) if platform else "Ads"
    cmd_label  = command or ""

    out = []

    # Header — project | platform | command
    header_right = f" {cmd_label}" if cmd_label and cmd_label != "/audit" else ""
    out.append(f"<b>🔍 {project or 'Canon Audit'} — {plat_label}{header_right}</b>")
    if metrics_str:
        out.append(f"<i>{metrics_str.replace('&', '&amp;')}</i>")
    out.append("")

    # Gates
    if gates:
        out.append("<b>── Gates ──</b>")
        for g in gates:
            out.append(g)
        out.append("")

    # Findings — strip wrapping [ ] from LLM format [P0|GAC-...|fix]
    if findings:
        out.append("<b>── Findings ──</b>")
        for f in findings:
            f_clean = f.strip().lstrip("[").rstrip("]")
            parts = [p.strip() for p in f_clean.split("|")]
            if len(parts) >= 5:
                sev, rule_id, where, issue, fix = (
                    parts[0], parts[1], parts[2], parts[3], parts[4]
                )
                emoji = _SEV_EMOJI.get(sev, "▪️")
                out.append(
                    f"\n{emoji} <b>{sev} · {rule_id}</b>  <i>{where}</i>\n"
                    f"   {issue}\n"
                    f"   <b>→</b> {fix}"
                )
            elif f_clean:
                out.append(f"\n▪️ {f_clean}")
        out.append("")

    # Counts summary
    if counts_str:
        p0 = re.search(r"P0:\s*(\d+)", counts_str)
        p1 = re.search(r"P1:\s*(\d+)", counts_str)
        p2 = re.search(r"P2:\s*(\d+)", counts_str)
        n0 = int(p0.group(1)) if p0 else 0
        n1 = int(p1.group(1)) if p1 else 0
        n2 = int(p2.group(1)) if p2 else 0
        summary_parts = []
        if n0: summary_parts.append(f"🔴 {n0} blocker{'s' if n0>1 else ''}")
        if n1: summary_parts.append(f"🟠 {n1} fix{'es' if n1>1 else ''}")
        if n2: summary_parts.append(f"🟡 {n2} improvement{'s' if n2>1 else ''}")
        if summary_parts:
            out.append("<b>── Summary ──</b>")
            out.append("  ".join(summary_parts))
            out.append("")

    out.append("<i>Full report → PDF above ☝️</i>")

    return "\n".join(out)


# ─── Fallback formatter for non-audit modes ───────────────────────────────────

def format_for_telegram(text: str) -> str:
    """
    Light formatter for non-Canon modes (plan, analyze, copy, etc.).
    Converts Markdown headers and bold to Telegram HTML.
    Keeps tables as monospace code blocks.
    """
    lines  = text.replace("\r\n", "\n").split("\n")
    output = []
    i = 0

    while i < len(lines):
        raw = lines[i].rstrip()

        # Pipe table → monospace block
        if raw.strip().startswith("|") and i + 1 < len(lines) and re.match(r"^\|[\s\-:|]+\|", lines[i + 1].strip()):
            table_lines = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                table_lines.append(lines[i].rstrip())
                i += 1
            # Render as code block (always readable in Telegram)
            output.append("<pre>" + "\n".join(table_lines) + "</pre>")
            continue

        # H2
        if raw.startswith("## "):
            output.append(f"\n<b>{_esc(raw[3:].strip())}</b>")
            i += 1; continue
        # H3
        if raw.startswith("### "):
            output.append(f"<b>{_esc(raw[4:].strip())}</b>")
            i += 1; continue

        # Checkboxes
        if re.match(r"^-?\s*\[[ xX]\]", raw):
            checked = "x" in raw[raw.index("[")+1:raw.index("]")].lower()
            rest = raw[raw.index("]")+1:].strip()
            output.append(f"{'✅' if checked else '☐'} {_esc(rest)}")
            i += 1; continue

        # Bullet
        m = re.match(r"^(\s*)[-*•]\s+(.*)", raw)
        if m:
            indent = len(m.group(1)) // 2
            bullet = ("•", "–")[min(indent, 1)]
            rest = _inline(m.group(2))
            output.append(f"{'  '*indent}{bullet} {rest}")
            i += 1; continue

        # HR
        if re.match(r"^[-─=]{3,}$", raw.strip()):
            output.append("─" * 25)
            i += 1; continue

        # Regular line
        output.append(_inline(_esc(raw)))
        i += 1

    result = "\n".join(output)
    result = re.sub(r"\n{3,}", "\n\n", result)
    return result.strip()


def _esc(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _inline(s: str) -> str:
    s = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", s)
    s = re.sub(r"\*(.+?)\*",     r"<i>\1</i>", s)
    s = re.sub(r"`(.+?)`",       r"<code>\1</code>", s)
    return s
