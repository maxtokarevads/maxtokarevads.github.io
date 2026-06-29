from typing import Any, Dict, List


def build_meta_prompt(payload: Dict[str, Any]) -> str:
    pages    = payload.get("pages", [])
    site     = payload.get("site", "")
    industry = payload.get("industry", "")
    keywords = payload.get("keywords", [])
    context  = payload.get("context", "")
    topic    = payload.get("topic", context)

    site_line     = f"\nSite: {site}" if site else ""
    industry_line = f"\nIndustry: {industry}" if industry else ""

    # Build pages block — either from structured list or from free-form topic/keywords
    if pages:
        pages_block = "\n".join(
            f"- URL: {p.get('url', '—')} | Topic: {p.get('topic', '—')} | Keyword: {p.get('keyword', '—')}"
            for p in pages
        )
    elif keywords:
        pages_block = "\n".join(f"- Keyword: {kw}" for kw in keywords)
        if topic:
            pages_block = f"- Topic: {topic}\n" + pages_block
    else:
        pages_block = f"- Topic: {topic or 'not specified'}"

    return f"""Task: Write optimized meta titles and meta descriptions.
{site_line}{industry_line}

Pages / topics to optimise:
{pages_block}

## Rules — apply to EVERY entry

**Meta title:**
- 50–60 characters (hard limit — Google truncates at ~60)
- Primary keyword within first 30 characters
- Brand name at the end: "… | {site or 'Brand'}" if space allows
- Use power words where natural: Best, Guide, Complete, Free, [Year]
- No clickbait — must accurately reflect the page
- No ALL CAPS, no excessive punctuation

**Meta description:**
- 140–160 characters (hard limit)
- Include primary keyword naturally (not forced)
- Clear benefit statement: what the reader gains
- Implicit CTA: "Learn how", "Discover", "Find out", "Get the guide"
- Unique per page — never duplicate across pages

## Output Format (one block per page)

---
**Page:** [URL or topic]
**Primary keyword:** [keyword]
**Meta title** (XX chars): [exact title]
**Meta description** (XXX chars): [exact description]
**Variation A title** (XX chars): [alternative if A/B testing makes sense]
---

After all pages, add:

## QUICK AUDIT CHECKLIST
For each entry flag: ✅ pass / ⚠️ borderline / ❌ fail
- Title length ≤60 chars
- Keyword in first 30 chars of title
- Description 140–160 chars
- Keyword in description
- Unique (no two entries are near-identical)
- No duplicate intent across titles
"""
