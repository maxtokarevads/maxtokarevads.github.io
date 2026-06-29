from typing import Any, Dict, List


def build_article_prompt(payload: Dict[str, Any]) -> str:
    keywords    = payload.get("keywords", [])
    topic       = payload.get("topic", keywords[0] if keywords else payload.get("context", ""))
    site        = payload.get("site", "")
    industry    = payload.get("industry", "")
    word_count  = int(payload.get("word_count", 1500))
    audience    = payload.get("audience", "")
    funnel      = payload.get("funnel_stage", "mofu")
    tone        = payload.get("tone", "professional, clear, helpful")
    context     = payload.get("context", "")

    primary_kw  = keywords[0] if keywords else topic
    secondary   = ", ".join(keywords[1:]) if len(keywords) > 1 else ""

    site_line      = f"\nSite: {site}" if site else ""
    industry_line  = f"\nIndustry: {industry}" if industry else ""
    audience_line  = f"\nAudience: {audience}" if audience else ""
    secondary_line = f"\nSecondary keywords: {secondary}" if secondary else ""
    ctx_line       = f"\nAdditional context: {context}" if context else ""

    funnel_intent = {
        "tofu": "informational — educate, no sales pressure, define concepts",
        "mofu": "consideration — compare options, highlight benefits, build trust",
        "bofu": "transactional — direct, strong CTA, social proof, pricing context",
    }.get(funnel.lower(), funnel)

    return f"""Task: Write a complete, publish-ready SEO article.

Primary keyword: {primary_kw}{secondary_line}
Target word count: {word_count} words{site_line}{industry_line}{audience_line}
Funnel stage: {funnel_intent}
Tone: {tone}{ctx_line}

## SEO Rules (mandatory)
- Primary keyword in H1 within first 5 words
- Primary keyword in first paragraph (within 100 words)
- Primary keyword density: 0.8–1.5% (don't stuff)
- Meta title: ≤60 chars, keyword near start
- Meta description: ≤160 chars, keyword + clear benefit + implicit CTA
- H2 headings: 3–6 per article, include secondary keywords naturally
- H3 subheadings: use for step-by-step sections or sub-topics
- Alt text suggestion for the recommended featured image

## E-E-A-T Requirements (mandatory in 2026)
- Include at least one specific data point with source attribution (e.g. "According to [authoritative source], 63% of...")
- At least one concrete example, case study, or real-world scenario
- Author credential placeholder: [BYLINE: Name, Title, X years experience in {industry or "the field"}]
- "Last updated: {'{'}current_date{'}'}" placeholder at the top

## Output Format — produce ALL sections below

### META
**Meta title:** [≤60 chars]
**Meta description:** [≤160 chars]
**Recommended slug:** /[keyword-slug]/
**Featured image alt text:** [descriptive alt]

### ARTICLE

[Full article text — H1, then body with H2/H3 structure, {word_count} words]

### FAQ SECTION
[3–5 Q&A pairs targeting "People Also Ask" + schema-ready format]
Each Q: under 60 chars; each A: 40–80 words, answer-first

### INTERNAL LINK OPPORTUNITIES
[3–5 anchor text suggestions with ideal destination descriptions]
Format: "[anchor text]" → page about [topic] (create if doesn't exist)

Write the complete article now. Every section must be filled in — no placeholders, no "[write content here]" gaps.
"""
