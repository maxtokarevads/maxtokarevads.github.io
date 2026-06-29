"""
URL Inspector — fetches a URL and extracts on-page SEO signals.

No external dependencies beyond httpx (already in requirements).
Uses stdlib html.parser for HTML extraction.
Returns a dict that the SEO enricher injects into the agent payload.
"""
import logging
import re
from html.parser import HTMLParser
from typing import Any, Dict, List, Optional
from urllib.parse import urljoin, urlparse

import httpx

logger = logging.getLogger(__name__)

_TIMEOUT = 15.0
_USER_AGENT = (
    "Mozilla/5.0 (compatible; SEO-Agent/1.0; +https://github.com/claude-agent)"
)


# ── HTML parser ───────────────────────────────────────────────────────────────

class _SEOParser(HTMLParser):
    """Single-pass HTML parser that extracts all SEO-relevant signals."""

    def __init__(self):
        super().__init__()
        self.title: str = ""
        self.h1s: List[str] = []
        self.h2s: List[str] = []
        self.meta: Dict[str, str] = {}      # name/property → content
        self.canonical: str = ""
        self.schema_types: List[str] = []   # @type values found in JSON-LD
        self.hreflang: List[str] = []
        self.img_missing_alt: int = 0
        self.img_total: int = 0
        self.links_internal: int = 0
        self.links_external: int = 0
        self._in_title = False
        self._in_h1 = False
        self._in_h2 = False
        self._in_script = False
        self._current_script_type = ""
        self._script_buf = []
        self._base_domain = ""

    def set_base_domain(self, domain: str) -> None:
        self._base_domain = domain

    def handle_starttag(self, tag: str, attrs: list) -> None:
        attr = dict(attrs)
        t = tag.lower()

        if t == "title":
            self._in_title = True
        elif t in ("h1",):
            self._in_h1 = True
        elif t in ("h2",):
            self._in_h2 = True
        elif t == "meta":
            name = (attr.get("name") or attr.get("property") or "").lower()
            content = attr.get("content", "")
            if name:
                self.meta[name] = content
            # X-Robots-Tag equivalent in meta
            if attr.get("http-equiv", "").lower() == "x-robots-tag":
                self.meta["x-robots-tag"] = content
        elif t == "link":
            rel = attr.get("rel", "").lower()
            if rel == "canonical":
                self.canonical = attr.get("href", "")
            elif rel == "alternate" and attr.get("hreflang"):
                self.hreflang.append(attr.get("hreflang", ""))
        elif t == "img":
            self.img_total += 1
            if not attr.get("alt") and attr.get("alt") != "":
                self.img_missing_alt += 1
        elif t == "a":
            href = attr.get("href", "")
            if href and not href.startswith(("#", "mailto:", "tel:", "javascript:")):
                parsed = urlparse(href)
                if parsed.netloc and parsed.netloc != self._base_domain:
                    self.links_external += 1
                else:
                    self.links_internal += 1
        elif t == "script":
            self._in_script = True
            self._current_script_type = attr.get("type", "")
            self._script_buf = []

    def handle_endtag(self, tag: str) -> None:
        t = tag.lower()
        if t == "title":
            self._in_title = False
        elif t == "h1":
            self._in_h1 = False
        elif t == "h2":
            self._in_h2 = False
        elif t == "script":
            self._in_script = False
            if "application/ld+json" in self._current_script_type:
                raw = "".join(self._script_buf)
                # Extract @type values without full JSON parse (resilient)
                types = re.findall(r'"@type"\s*:\s*"([^"]+)"', raw)
                self.schema_types.extend(types)
            self._script_buf = []

    def handle_data(self, data: str) -> None:
        if self._in_title:
            self.title += data
        elif self._in_h1:
            if self.h1s:
                self.h1s[-1] += data
            else:
                self.h1s.append(data)
        elif self._in_h2:
            if self.h2s:
                self.h2s[-1] += data
            else:
                self.h2s.append(data)
        elif self._in_script:
            self._script_buf.append(data)

    def handle_starttag_h1_fix(self, tag, attrs):
        if tag.lower() == "h1" and not self._in_h1:
            self.h1s.append("")
            self._in_h1 = True


# ── Public API ────────────────────────────────────────────────────────────────

def inspect_url(url: str) -> Dict[str, Any]:
    """
    Fetch a URL and return a dict of on-page SEO signals.
    Returns empty dict with error key if fetch fails.
    """
    if not url.startswith(("http://", "https://")):
        url = "https://" + url

    parsed_base = urlparse(url)
    base_domain = parsed_base.netloc

    try:
        client = httpx.Client(
            timeout=_TIMEOUT,
            follow_redirects=True,
            headers={"User-Agent": _USER_AGENT},
        )
        resp = client.get(url)
        final_url    = str(resp.url)
        status_code  = resp.status_code
        headers      = dict(resp.headers)
        content_type = headers.get("content-type", "")

        result: Dict[str, Any] = {
            "url":           url,
            "final_url":     final_url,
            "status_code":   status_code,
            "redirected":    final_url != url,
            "content_type":  content_type,
            "response_time_ms": int(resp.elapsed.total_seconds() * 1000),
        }

        # HTTP-level security headers
        result["security_headers"] = {
            "strict-transport-security": headers.get("strict-transport-security", "MISSING"),
            "content-security-policy":   headers.get("content-security-policy",   "MISSING"),
            "x-frame-options":           headers.get("x-frame-options",           "MISSING"),
            "referrer-policy":           headers.get("referrer-policy",           "MISSING"),
            "x-content-type-options":    headers.get("x-content-type-options",    "MISSING"),
        }

        if "text/html" not in content_type:
            result["error"] = f"Not HTML ({content_type})"
            return result

        html = resp.text
        result["html_size_kb"] = round(len(html.encode()) / 1024, 1)

        # Parse HTML
        parser = _SEOParser()
        parser.set_base_domain(base_domain)
        # Pre-create H1 slot on start tag
        original_handle = parser.handle_starttag

        def patched_handle_starttag(tag, attrs):
            if tag.lower() == "h1":
                parser.h1s.append("")
            elif tag.lower() == "h2":
                parser.h2s.append("")
            original_handle(tag, attrs)

        parser.handle_starttag = patched_handle_starttag
        parser.feed(html)

        # On-page signals
        title = parser.title.strip()
        result["title"]              = title
        result["title_length"]       = len(title)
        result["title_ok"]           = 10 <= len(title) <= 60
        result["h1_count"]           = len(parser.h1s)
        result["h1_texts"]           = [h.strip() for h in parser.h1s if h.strip()]
        result["h2_count"]           = len(parser.h2s)
        result["meta_description"]   = parser.meta.get("description", "")
        result["meta_robots"]        = parser.meta.get("robots", "index, follow (default)")
        result["meta_og_title"]      = parser.meta.get("og:title", "")
        result["canonical"]          = parser.canonical
        result["schema_types"]       = list(set(parser.schema_types))
        result["hreflang_count"]     = len(parser.hreflang)
        result["hreflang"]           = parser.hreflang
        result["img_total"]          = parser.img_total
        result["img_missing_alt"]    = parser.img_missing_alt
        result["img_alt_coverage"]   = (
            f"{round((1 - parser.img_missing_alt / parser.img_total) * 100)}%"
            if parser.img_total else "N/A"
        )
        result["links_internal"]     = parser.links_internal
        result["links_external"]     = parser.links_external

        # Indexability
        robots_val  = result["meta_robots"].lower()
        xrobots_val = parser.meta.get("x-robots-tag", "").lower()
        result["is_noindex"] = "noindex" in robots_val or "noindex" in xrobots_val
        result["is_nofollow"] = "nofollow" in robots_val

        # Word count estimate (strip tags)
        text_only = re.sub(r"<[^>]+>", " ", html)
        words = [w for w in text_only.split() if len(w) > 1]
        result["word_count"] = len(words)

        # Viewport (mobile)
        result["has_viewport"] = "viewport" in parser.meta

        logger.info("Inspected %s: %d status, %d words, schema=%s",
                    url, status_code, len(words), result["schema_types"])
        return result

    except httpx.TimeoutException:
        return {"url": url, "error": "Timeout after 15s", "status_code": 0}
    except httpx.ConnectError as exc:
        return {"url": url, "error": f"Connection error: {exc}", "status_code": 0}
    except Exception as exc:
        logger.warning("URL inspection failed for %s: %s", url, exc)
        return {"url": url, "error": str(exc), "status_code": 0}


def format_inspection_for_prompt(data: Dict[str, Any]) -> str:
    """Format URL inspection data as a structured block for prompt injection."""
    if data.get("error"):
        return f"URL Inspection: FAILED — {data['error']}"

    lines = [
        f"## Real Data — URL Inspection ({data.get('url', '')})",
        f"Status: {data.get('status_code')} | Response: {data.get('response_time_ms')}ms | "
        f"Size: {data.get('html_size_kb')}KB",
        "",
        "### On-Page Signals",
        f"- Title: \"{data.get('title')}\" ({data.get('title_length')} chars, "
        f"{'✅ OK' if data.get('title_ok') else '❌ too long or short'})",
        f"- H1 count: {data.get('h1_count')} "
        f"({'✅' if data.get('h1_count') == 1 else '❌ should be exactly 1'})",
    ]
    if data.get("h1_texts"):
        lines.append(f"- H1 text: \"{data['h1_texts'][0][:100]}\"")

    lines += [
        f"- Meta description: {len(data.get('meta_description', ''))} chars "
        f"({'✅' if 50 <= len(data.get('meta_description','')) <= 160 else '❌'})",
        f"- Meta robots: {data.get('meta_robots')}",
        f"- Noindex: {'❌ YES — page excluded from Google' if data.get('is_noindex') else '✅ No'}",
        f"- Canonical: {data.get('canonical') or '⚠️ Missing'}",
        f"- Viewport (mobile): {'✅' if data.get('has_viewport') else '❌ Missing'}",
        f"- Word count: {data.get('word_count')} "
        f"({'✅' if data.get('word_count',0) >= 500 else '⚠️ thin content'})",
        f"- Images: {data.get('img_total')} total, {data.get('img_missing_alt')} missing alt "
        f"({data.get('img_alt_coverage')} coverage)",
        "",
        "### Schema Markup",
        f"- Types found: {', '.join(data.get('schema_types', [])) or '⚠️ None detected'}",
        "",
        "### Security Headers",
    ]
    for header, value in data.get("security_headers", {}).items():
        status = "✅" if value != "MISSING" else "❌"
        lines.append(f"- {header}: {status} {value[:60] if value != 'MISSING' else ''}")

    if data.get("hreflang_count"):
        lines.append(f"\n### International SEO\n- hreflang tags: {data['hreflang_count']}")

    return "\n".join(lines)
