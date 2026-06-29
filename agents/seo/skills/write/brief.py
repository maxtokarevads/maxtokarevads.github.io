from typing import Any, Dict, List


def build_brief_prompt(payload: Dict[str, Any]) -> str:
    keywords    = payload.get("keywords", [])
    topic       = payload.get("topic", keywords[0] if keywords else payload.get("context", ""))
    site        = payload.get("site", "")
    industry    = payload.get("industry", "")
    word_count  = int(payload.get("word_count", 1500))
    funnel      = payload.get("funnel_stage", "mofu")
    competitors = payload.get("competitors", [])
    audience    = payload.get("audience", "")
    context     = payload.get("context", "")

    primary_kw  = keywords[0] if keywords else topic
    secondary   = keywords[1:] if len(keywords) > 1 else []

    site_line     = f"\nSite: {site}" if site else ""
    industry_line = f"\nIndustry: {industry}" if industry else ""
    audience_line = f"\nTarget audience: {audience}" if audience else ""
    comp_line     = f"\nCompetitors to analyse: {', '.join(competitors)}" if competitors else ""
    ctx_line      = f"\nAdditional context: {context}" if context else ""

    secondary_line = f"\nSecondary / LSI keywords: {', '.join(secondary)}" if secondary else ""

    funnel_label = {
        "tofu": "TOFU — informational, awareness",
        "mofu": "MOFU — consideration, comparison",
        "bofu": "BOFU — transactional, conversion",
    }.get(funnel.lower(), funnel)

    return f"""Task: Create a detailed content brief for a copywriter.

Primary keyword: {primary_kw}{secondary_line}
Target word count: {word_count}{site_line}{industry_line}{audience_line}{comp_line}
Funnel stage: {funnel_label}{ctx_line}

## Output Format

### 1. OVERVIEW
- **Goal:** [one sentence — what this article must achieve]
- **Primary keyword:** {primary_kw}
- **Secondary keywords:** [list 5–8 LSI + semantic variants]
- **Search intent:** [Informational / Commercial / Transactional / Navigational + explanation]
- **Target word count:** {word_count} words (±10%)
- **Funnel stage:** {funnel_label}

### 2. AUDIENCE PROFILE
- Who is reading this and why
- Their level of knowledge (beginner / intermediate / expert)
- The ONE question they need answered
- What they will do after reading (desired next action)

### 3. SERP ANALYSIS
Analyse what the top 10 results do — even if you can't browse, reason from keyword intent:
- Dominant content type (how-to, listicle, comparison, guide, product page)
- Typical H2 structure in top results
- Common angles competitors use
- Gaps: what they miss that this article should cover
- SERP features to target: Featured Snippet / People Also Ask / Image Pack / Video

### 4. MANDATORY STRUCTURE
Provide the exact outline the writer must follow:

**H1:** [exact H1 — must include primary keyword near start]

**[Opening paragraph notes]** — hook + primary keyword in first 100 words + article promise

**H2: [heading]** — [what to cover, word count target for this section]
  H3: [subheading] — [notes]
  H3: [subheading] — [notes]

[Continue for all H2/H3...]

**FAQ Section** — mandatory for PAA capture + schema
  Q1: [question]
  Q2: [question]
  Q3: [question]

**[Closing / CTA]** — [notes on what action to drive]

### 5. E-E-A-T REQUIREMENTS
- **Experience signal:** [specific example, test, or first-hand data the writer must include]
- **Expertise:** [credential or data point that establishes authority]
- **Author byline:** [recommended: name, title, years of experience]
- **Data requirement:** [at least 1 specific stat with source — suggest a real source]
- **Original element:** [screenshot, chart, tool output, or proprietary data to add]

### 6. META TAGS
**Meta title (≤60 chars):** [exact title — keyword near start]
**Meta description (≤160 chars):** [keyword + benefit + implicit CTA]
**URL slug:** /[keyword-slug]/

### 7. INTERNAL LINKS (mandatory)
[3–5 anchor texts + destination page descriptions the writer must include]
Format: anchor → [destination page topic]

### 8. EXTERNAL LINKS
[2–3 authoritative sources to cite — prefer .gov, .edu, peer-reviewed, or known industry authorities]

### 9. DO / DON'T FOR THIS ARTICLE
DO:
- [specific instruction]
- [specific instruction]

DON'T:
- [specific instruction]
- [specific instruction]

### 10. SUCCESS CRITERIA
This brief is complete when the article:
- [ ] Ranks for primary keyword within 90 days
- [ ] Captures a PAA box for at least one H2 question
- [ ] Time on page > 2:30 (engagement signal)
- [ ] Has zero AI-detectable generic filler paragraphs
"""
