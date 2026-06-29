"""
PDF report builder for Canon audit outputs.

Usage:
    from agents.ads.reporting.pdf_builder import build_report_pdf
    pdf_bytes = build_report_pdf(result_text, project="ACME", platform="google", mode="audit")
    # Send pdf_bytes as a Telegram document
"""

import os
import re
from datetime import datetime
from typing import List, Optional, Tuple

from fpdf import FPDF, FPDFException
from fpdf.enums import XPos, YPos


class _PDF(FPDF):
    """FPDF subclass that adds page numbers in the footer."""
    _use_arial: bool = True

    def footer(self) -> None:
        self.set_y(-12)
        _set_font(self, self._use_arial, 8)
        self.set_text_color(*_BRAND_MID)
        self.cell(0, 8, f"Page {self.page_no()}", align="C")

# ─── Colors ──────────────────────────────────────────────────────────────────

_BRAND_DARK  = (15,  23,  42)    # slate-900  — headings
_BRAND_MID   = (71,  85, 105)    # slate-600  — sub-text
_BRAND_LIGHT = (241, 245, 249)   # slate-100  — alternating row bg

_SEV_BG: dict = {
    "P0": (254, 226, 226),   # red-100
    "P1": (255, 237, 213),   # orange-100
    "P2": (254, 249, 195),   # yellow-100
}
_SEV_TEXT: dict = {
    "P0": (185, 28,  28),    # red-700
    "P1": (154, 52,  18),    # orange-800
    "P2": (133, 77,   14),   # yellow-800
}
_WHITE   = (255, 255, 255)
_BORDER  = (203, 213, 225)   # slate-300

# ─── Fonts ───────────────────────────────────────────────────────────────────

_FONT_NAME = "UniFont"
_THIS_DIR  = os.path.dirname(os.path.abspath(__file__))

# Font search order: bundled → Windows → Linux → macOS
_FONT_CANDIDATES = {
    "regular": [
        os.path.join(_THIS_DIR, "fonts", "DejaVuSans.ttf"),
        os.path.join(_THIS_DIR, "fonts", "Arial.ttf"),
        "C:/Windows/Fonts/arial.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
        "/Library/Fonts/Arial.ttf",
        "/System/Library/Fonts/Supplemental/Arial.ttf",
        os.path.expanduser("~/Library/Fonts/Arial.ttf"),
    ],
    "bold": [
        os.path.join(_THIS_DIR, "fonts", "DejaVuSans-Bold.ttf"),
        os.path.join(_THIS_DIR, "fonts", "ArialBold.ttf"),
        "C:/Windows/Fonts/arialbd.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
        "/Library/Fonts/Arial Bold.ttf",
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
    ],
    "italic": [
        os.path.join(_THIS_DIR, "fonts", "DejaVuSans-Oblique.ttf"),
        "C:/Windows/Fonts/ariali.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Oblique.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Italic.ttf",
    ],
}


def _find_font(style: str) -> Optional[str]:
    for path in _FONT_CANDIDATES.get(style, []):
        if path and os.path.exists(path):
            return path
    return None


def _load_fonts(pdf: FPDF) -> bool:
    """Load a Unicode-capable font. Returns True if successful, False → Helvetica fallback."""
    reg  = _find_font("regular")
    bold = _find_font("bold")
    if not reg or not bold:
        return False
    try:
        pdf.add_font(_FONT_NAME,             fname=reg)
        pdf.add_font(_FONT_NAME, style="B",  fname=bold)
        ital = _find_font("italic")
        if ital:
            pdf.add_font(_FONT_NAME, style="I", fname=ital)
        return True
    except Exception:
        return False


# ─── Helpers ─────────────────────────────────────────────────────────────────

def _set_font(pdf: FPDF, use_arial: bool, size: int, style: str = "") -> None:
    name = _FONT_NAME if use_arial else "Helvetica"
    pdf.set_font(name, style=style, size=size)


def _set_color(pdf: FPDF, rgb: tuple, text: bool = True) -> None:
    if text:
        pdf.set_text_color(*rgb)
    else:
        pdf.set_fill_color(*rgb)


def _parse_table(lines: List[str]) -> Tuple[List[str], List[List[str]]]:
    """Return (headers, data_rows) from a list of Markdown table lines."""
    headers: List[str] = []
    rows: List[List[str]] = []
    for line in lines:
        if not line.strip().startswith("|"):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        # Skip separator lines (|---|---|)
        if all(re.fullmatch(r"[-: ]+", c) for c in cells if c):
            continue
        if not headers:
            headers = cells
        else:
            rows.append(cells)
    return headers, rows


def _severity_of_row(row: List[str], headers: List[str]) -> Optional[str]:
    """Detect P0/P1/P2 in row — check Severity column first, then any cell."""
    sev_col = next((i for i, h in enumerate(headers) if "severity" in h.lower()), None)
    if sev_col is not None and sev_col < len(row):
        val = row[sev_col].strip()
        if val in _SEV_BG:
            return val
    for cell in row:
        if cell.strip() in _SEV_BG:
            return cell.strip()
    return None


def _is_fixlist_table(headers: List[str]) -> bool:
    """True when the table is a Canon Fixlist (severity + issue columns present)."""
    low = [h.lower() for h in headers]
    return (
        any("severity" in h for h in low)
        and any("issue" in h for h in low)
        and len(headers) >= 4
    )


def _col_idx(headers: List[str], *names: str) -> Optional[int]:
    """Return index of first header that contains any of the given name fragments."""
    low = [h.lower() for h in headers]
    for name in names:
        for i, h in enumerate(low):
            if name in h:
                return i
    return None


def _render_fixlist_cards(pdf: FPDF, use_arial: bool,
                           headers: List[str], rows: List[List[str]]) -> None:
    """Render Canon Fixlist as human-readable severity cards instead of a cramped table."""
    i_sev      = _col_idx(headers, "severity")
    i_id       = _col_idx(headers, "rule id", "id", "sop id")
    i_where    = _col_idx(headers, "where")
    i_issue    = _col_idx(headers, "issue")
    i_action   = _col_idx(headers, "what to do", "action", "fix")
    i_verify   = _col_idx(headers, "verify")
    i_rollback = _col_idx(headers, "rollback")

    def cell_val(row: List[str], idx: Optional[int]) -> str:
        if idx is None or idx >= len(row):
            return ""
        return row[idx].strip()

    W = 190  # card width

    for row in rows:
        sev      = cell_val(row, i_sev)
        rule_id  = cell_val(row, i_id)
        where    = cell_val(row, i_where)
        issue    = cell_val(row, i_issue)
        action   = cell_val(row, i_action)
        verify   = cell_val(row, i_verify)
        rollback = cell_val(row, i_rollback)

        if not (sev or rule_id or issue):
            continue

        bg   = _SEV_BG.get(sev, _BRAND_LIGHT)
        t_hd = _SEV_TEXT.get(sev, _BRAND_DARK)

        # Page break: ensure at least 28mm left for card
        if pdf.get_y() > pdf.page_break_trigger - 28:
            pdf.add_page()

        x0 = 10

        # ── Header bar ──────────────────────────────────────────────────────
        hdr_parts = [p for p in [sev, rule_id, where] if p]
        hdr_text  = "  •  ".join(hdr_parts)
        _set_font(pdf, use_arial, 10, "B")
        pdf.set_fill_color(*bg)
        pdf.set_draw_color(*_BORDER)
        pdf.set_text_color(*t_hd)
        pdf.set_x(x0)
        pdf.cell(W, 7, hdr_text, border=1, fill=True,
                 new_x=XPos.LMARGIN, new_y=YPos.NEXT)

        # ── Issue ────────────────────────────────────────────────────────────
        if issue:
            _set_font(pdf, use_arial, 10)
            pdf.set_fill_color(252, 252, 252)
            pdf.set_draw_color(*_BORDER)
            pdf.set_text_color(30, 30, 30)
            pdf.set_x(x0)
            pdf.multi_cell(W, 5.5, issue, border="LR", fill=True,
                           new_x=XPos.LMARGIN, new_y=YPos.NEXT)

        # ── Action ───────────────────────────────────────────────────────────
        if action:
            _set_font(pdf, use_arial, 10, "B")
            pdf.set_fill_color(252, 252, 252)
            pdf.set_text_color(*t_hd)
            pdf.set_x(x0)
            pdf.multi_cell(W, 5.5, f"-> {action}", border="LR", fill=True,
                           new_x=XPos.LMARGIN, new_y=YPos.NEXT)

        # ── Verify + Rollback footer ─────────────────────────────────────────
        footer_parts = []
        if verify:   footer_parts.append(f"Verify: {verify}")
        if rollback: footer_parts.append(f"Rollback: {rollback}")
        if footer_parts:
            _set_font(pdf, use_arial, 8)
            pdf.set_fill_color(*_BRAND_LIGHT)
            pdf.set_text_color(*_BRAND_MID)
            pdf.set_x(x0)
            pdf.multi_cell(W, 5, "  |  ".join(footer_parts),
                           border=1, fill=True,
                           new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        else:
            # Close bottom border
            pdf.set_draw_color(*_BORDER)
            pdf.set_x(x0)
            pdf.cell(W, 0, "", border="B", new_x=XPos.LMARGIN, new_y=YPos.NEXT)

        pdf.ln(3)  # breathing room between cards

    pdf.set_text_color(0, 0, 0)


# ─── Section parsers ─────────────────────────────────────────────────────────

def _render_page_header(pdf: FPDF, use_arial: bool,
                        project: str, platform: str,
                        mode: str, date_range: str) -> None:
    """Top band: accent bar + report title + metadata."""
    # Accent bar
    pdf.set_fill_color(15, 23, 42)
    pdf.rect(0, 0, 210, 12, style="F")

    # Report title in bar
    _set_font(pdf, use_arial, 11, "B")
    pdf.set_text_color(255, 255, 255)
    pdf.set_xy(10, 2)
    mode_label = mode.upper().replace("_", " ")
    pdf.cell(0, 8, f"Canon {mode_label} Report", align="L")

    # Date (right side of bar)
    date_str = datetime.now().strftime("%d %b %Y")
    pdf.set_xy(-60, 2)
    _set_font(pdf, use_arial, 9)
    pdf.cell(50, 8, date_str, align="R")

    # Metadata row
    pdf.set_y(16)
    meta_parts = []
    if project:    meta_parts.append(f"Project: {project}")
    if platform:   meta_parts.append(f"Platform: {platform.capitalize()}")
    if date_range: meta_parts.append(f"Period: {date_range}")

    if meta_parts:
        pdf.set_fill_color(*_BRAND_LIGHT)
        pdf.rect(0, 14, 210, 10, style="F")
        _set_font(pdf, use_arial, 9)
        _set_color(pdf, _BRAND_MID)
        pdf.set_xy(10, 15)
        pdf.cell(0, 8, "  |  ".join(meta_parts))

    pdf.set_y(28)
    pdf.set_text_color(0, 0, 0)


def _render_h2(pdf: FPDF, use_arial: bool, text: str) -> None:
    pdf.ln(5)
    pdf.set_fill_color(*_BRAND_DARK)
    pdf.set_text_color(255, 255, 255)
    _set_font(pdf, use_arial, 12, "B")
    pdf.set_x(10)
    pdf.cell(190, 8, text, fill=True, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.ln(2)
    pdf.set_text_color(0, 0, 0)


def _render_h3(pdf: FPDF, use_arial: bool, text: str) -> None:
    pdf.ln(3)
    pdf.set_fill_color(*_BRAND_LIGHT)
    pdf.set_text_color(*_BRAND_DARK)
    _set_font(pdf, use_arial, 10, "B")
    pdf.set_x(10)
    pdf.cell(190, 6, text, fill=True, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.ln(1)
    pdf.set_text_color(0, 0, 0)


def _render_paragraph(pdf: FPDF, use_arial: bool, text: str) -> None:
    _set_font(pdf, use_arial, 10)
    pdf.set_text_color(30, 30, 30)
    pdf.set_x(10)
    pdf.multi_cell(190, 5.5, text, new_x=XPos.LMARGIN, new_y=YPos.NEXT)


def _render_bullet(pdf: FPDF, use_arial: bool, text: str, level: int = 0) -> None:
    indent = 14 + level * 6
    _set_font(pdf, use_arial, 10)
    pdf.set_text_color(30, 30, 30)
    bullet = "•  " if level == 0 else "–  "
    pdf.set_x(indent)
    pdf.multi_cell(190 - indent, 5.5, bullet + text.lstrip("-• ").strip(),
                   new_x=XPos.LMARGIN, new_y=YPos.NEXT)


def _render_table(pdf: FPDF, use_arial: bool, lines: List[str]) -> None:
    headers, rows = _parse_table(lines)
    if not headers:
        return

    # Fixlist tables → card layout (much more readable than 7-column cramped table)
    if _is_fixlist_table(headers):
        _render_fixlist_cards(pdf, use_arial, headers, rows)
        return

    pdf.ln(3)
    page_w = 190  # usable width (10mm margins each side)
    n_cols = len(headers)
    if n_cols == 0:
        return

    # Column width heuristics: Severity gets fixed 16mm, others share rest
    sev_idx = next((i for i, h in enumerate(headers) if "severity" in h.lower()), None)
    id_idx  = next((i for i, h in enumerate(headers)
                    if h.lower() in ("rule id", "id", "sop id")), None)

    col_w = [page_w / n_cols] * n_cols
    if sev_idx is not None:
        col_w[sev_idx] = 16
        remaining = page_w - 16
        others = [i for i in range(n_cols) if i != sev_idx]
        if id_idx is not None and id_idx in others:
            col_w[id_idx] = 20
            others = [i for i in others if i != id_idx]
            remaining -= 20
        per = remaining / max(len(others), 1)
        for i in others:
            col_w[i] = per

    row_h = 6

    def draw_row(cells: List[str], bg: tuple, text_rgb: tuple,
                 bold: bool = False) -> None:
        x0 = 10
        y0 = pdf.get_y()
        # Measure max height (multi-line cells)
        max_lines = 1
        for i, cell in enumerate(cells):
            if i >= n_cols:
                break
            w = col_w[i]
            cell_str = str(cell).strip()[:300]
            # Estimate lines
            chars_per_line = max(int(w / 2.2), 1)
            lines_est = max(1, -(-len(cell_str) // chars_per_line))
            max_lines = max(max_lines, lines_est)
        h = max(row_h, max_lines * 4.5)

        # Page break check
        if y0 + h > pdf.page_break_trigger:
            pdf.add_page()
            y0 = pdf.get_y()

        x = x0
        for i, cell in enumerate(cells):
            if i >= n_cols:
                break
            w = col_w[i]
            cell_str = str(cell).strip()[:300]
            pdf.set_fill_color(*bg)
            pdf.set_draw_color(*_BORDER)
            pdf.rect(x, y0, w, h, style="FD")
            _set_font(pdf, use_arial, 8, "B" if bold else "")
            pdf.set_text_color(*text_rgb)
            pdf.set_xy(x + 1.5, y0 + 1)
            pdf.multi_cell(w - 3, 4, cell_str,
                           new_x=XPos.RIGHT, new_y=YPos.TOP, max_line_height=4)
            x += w

        pdf.set_y(y0 + h)
        pdf.set_text_color(0, 0, 0)

    # Header row
    draw_row(headers, _BRAND_DARK, _WHITE, bold=True)

    # Data rows
    for idx, row in enumerate(rows):
        # Pad or trim to n_cols
        padded = (row + [""] * n_cols)[:n_cols]
        sev = _severity_of_row(padded, headers)
        if sev:
            bg    = _SEV_BG[sev]
            t_rgb = _SEV_TEXT[sev]
        elif idx % 2 == 0:
            bg    = _WHITE
            t_rgb = (30, 30, 30)
        else:
            bg    = _BRAND_LIGHT
            t_rgb = (30, 30, 30)
        draw_row(padded, bg, t_rgb)

    pdf.ln(4)


# ─── Main builder ─────────────────────────────────────────────────────────────

_EMOJI_MAP = {
    "✅": "[OK]",    # ✅
    "❌": "[FAIL]",  # ❌
    "\U0001f534": "[P0]",   # 🔴
    "\U0001f7e0": "[P1]",   # 🟠
    "\U0001f7e1": "[P2]",   # 🟡
    "⚠":  "[!]",    # ⚠️
    "️":  "",       # variation selector (strip)
}

_EMOJI_RE = re.compile(
    "["
    "\U0001F300-\U0001F9FF"  # misc symbols and pictographs
    "☀-➿"          # misc symbols
    "︀-️"          # variation selectors
    "]+",
    re.UNICODE,
)


def _strip_emoji(text: str) -> str:
    """Replace known emoji with text equivalents; strip the rest."""
    for char, replacement in _EMOJI_MAP.items():
        text = text.replace(char, replacement)
    return _EMOJI_RE.sub("", text)


def build_report_pdf(
    output_text: str,
    project:     str = "",
    platform:    str = "",
    mode:        str = "audit",
    date_range:  str = "",
) -> bytes:
    """
    Convert a Canon audit output (Markdown) to a PDF bytes object.

    Parameters
    ----------
    output_text : str   — raw LLM output (Markdown with pipe tables)
    project     : str   — client/project name shown in header
    platform    : str   — google | meta | tiktok
    mode        : str   — audit | landing | weekly | etc.
    date_range  : str   — e.g. "last 30 days"

    Returns
    -------
    bytes  — PDF file content, ready to send as a Telegram document
    """
    output_text = _strip_emoji(output_text)
    pdf = _PDF(orientation="P", unit="mm", format="A4")
    pdf.set_margins(10, 10, 10)
    pdf.set_auto_page_break(auto=True, margin=18)

    use_arial = _load_fonts(pdf)
    pdf._use_arial = use_arial

    pdf.add_page()
    _render_page_header(pdf, use_arial, project, platform, mode, date_range)

    # ── Parse content line by line ────────────────────────────────────────────
    lines = output_text.replace("\r\n", "\n").split("\n")
    i = 0
    while i < len(lines):
        line = lines[i]

        # H2
        if line.startswith("## "):
            _render_h2(pdf, use_arial, line[3:].strip())
            i += 1

        # H3
        elif line.startswith("### "):
            _render_h3(pdf, use_arial, line[4:].strip())
            i += 1

        # Table: first pipe line followed by separator
        elif (line.strip().startswith("|") and
              i + 1 < len(lines) and
              re.match(r"\|[\s\-:|]+\|", lines[i + 1])):
            # Collect all consecutive pipe lines
            table_lines = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                table_lines.append(lines[i])
                i += 1
            _render_table(pdf, use_arial, table_lines)

        # Bullet (- or * or •, possibly indented)
        elif re.match(r"^\s*[-*•]\s+", line):
            level = 1 if line.startswith("  ") else 0
            _render_bullet(pdf, use_arial, line, level)
            i += 1

        # Numbered list
        elif re.match(r"^\s*\d+\.\s+", line):
            _render_bullet(pdf, use_arial, line, level=0)
            i += 1

        # Horizontal rule
        elif re.match(r"^[-─=]{3,}$", line.strip()):
            pdf.ln(2)
            pdf.set_draw_color(*_BORDER)
            pdf.line(10, pdf.get_y(), 200, pdf.get_y())
            pdf.ln(3)
            i += 1

        # Non-empty text
        elif line.strip():
            _render_paragraph(pdf, use_arial, line.strip())
            i += 1

        # Blank line
        else:
            pdf.ln(2)
            i += 1

    return bytes(pdf.output())
