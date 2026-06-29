from typing import Any, Dict, List


def build_rewrite_prompt(payload: Dict[str, Any]) -> str:
    content    = payload.get("content", "")
    keywords   = payload.get("keywords", [])
    site       = payload.get("site", "")
    industry   = payload.get("industry", "")
    focus      = payload.get("focus", "")       # e.g. "eeat", "keywords", "readability", "aeo"
    word_count = payload.get("word_count", "")
    context    = payload.get("context", "")

    primary_kw = keywords[0] if keywords else ""
    secondary  = ", ".join(keywords[1:]) if len(keywords) > 1 else ""

    site_line      = f"\nSite: {site}" if site else ""
    industry_line  = f"\nIndustry: {industry}" if industry else ""
    kw_line        = f"\nPrimary keyword to target: {primary_kw}" if primary_kw else ""
    secondary_line = f"\nSecondary keywords: {secondary}" if secondary else ""
    wc_line        = f"\nTarget word count: {word_count}" if word_count else ""
    ctx_line       = f"\nContext / rewrite goals: {context}" if context else ""

    focus_instructions = {
        "eeat":        "Focus on strengthening Experience, Expertise, Authoritativeness, Trustworthiness signals.",
        "keywords":    "Focus on improving keyword placement and density without stuffing.",
        "readability": "Focus on clarity: shorter sentences, active voice, clearer headings.",
        "aeo":         "Focus on making content AI-citation-ready: answer-first format, FAQs, specific data.",
        "full":        "Full rewrite: improve E-E-A-T, keywords, structure, readability, and AEO simultaneously.",
    }.get(focus.lower() if focus else "", "Full rewrite: improve E-E-A-T, keywords, structure, and readability.")

    content_block = f"\n\n## EXISTING CONTENT TO REWRITE\n\n{content}" if content else "\n\n[No content provided — create from scratch using the keyword and context above]"

    return f"""Task: Rewrite and improve existing SEO content.
{site_line}{industry_line}{kw_line}{secondary_line}{wc_line}{ctx_line}

Rewrite focus: {focus_instructions}
{content_block}

## Rewrite Rules

**DO NOT change:**
- Core factual claims (unless factually wrong — flag those)
- The main topic or angle
- Brand/product names
- Existing links (list them at the end as "Links preserved")

**IMPROVE:**
1. **Title / H1** — ensure primary keyword is within first 5 words
2. **Opening paragraph** — hook + primary keyword in first 100 words
3. **H2/H3 structure** — add missing subheadings, rename vague ones, add keywords naturally
4. **E-E-A-T gaps** — add specific data points, examples, author attribution where missing
5. **Thin sections** — expand any section under 100 words that deserves more depth
6. **Keyword density** — 0.8–1.5% for primary keyword (not stuffed)
7. **AEO readiness** — each H2 section should open with a 40–60 word direct answer
8. **CTA** — ensure a clear next action at the end

## Output Format

### REWRITE ASSESSMENT
| Dimension | Before (1–10) | After (1–10) | Key changes |
|-----------|--------------|--------------|-------------|
| E-E-A-T   | | | |
| Keyword   | | | |
| Structure | | | |
| AEO-ready | | | |
| Readability | | | |

### REWRITTEN CONTENT

[Full rewritten article — complete, not just the changed sections]

### CHANGE LOG
List every significant change made:
- [Section / element]: [what changed and why]

### LINKS PRESERVED
[list all hyperlinks from the original — confirm they should stay]

### WHAT STILL NEEDS HUMAN INPUT
[flag anything the AI cannot improve without real data: original photos, author bio, specific case studies]
"""
