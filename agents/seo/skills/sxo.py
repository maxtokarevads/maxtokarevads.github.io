from typing import Any, Dict, List


def build_sxo_prompt(payload: Dict[str, Any]) -> str:
    site        = payload.get("site", "client website")
    keyword     = payload.get("keyword", payload.get("query", ""))
    url         = payload.get("url", "")
    industry    = payload.get("industry", "")
    competitors = payload.get("competitors", [])
    context     = payload.get("context", "")

    kw_line    = f"\nTarget keyword: {keyword}" if keyword else ""
    url_line   = f"\nPage URL: {url}" if url else ""
    ind_line   = f"\nIndustry: {industry}" if industry else ""
    comp_text  = ", ".join(competitors) if competitors else ""
    comp_line  = f"\nCompetitors: {comp_text}" if comp_text else ""
    ctx_line   = f"\nContext: {context}" if context else ""

    return f"""Platform: SEO — SXO (Search Experience Optimization)
Site: {site}{kw_line}{url_line}{ind_line}{comp_line}{ctx_line}

SXO = SERP-backward analysis. Start from what Google shows, not what you want to rank for.
The goal: match content to the exact experience users expect when they search this keyword.

## Methodology: 5 Personas × SERP Analysis

Analyze the SERP for the target keyword through 5 user lenses:

PERSONA 1 — THE BUYER
- Intent: ready to purchase or request a quote
- What they expect from a result: pricing, comparison, CTA, trust signals
- SERP signals for this persona: do results show pricing, "buy", "shop", "get a quote"?
- Your content score for this persona: [1–10]

PERSONA 2 — THE RESEARCHER
- Intent: learning, comparing options, not yet ready to buy
- What they expect: comprehensive guide, pros/cons, expert analysis
- SERP signals: do results show "guide", "what is", "how to", "vs", "review"?
- Your content score: [1–10]

PERSONA 3 — THE COMPARISON SHOPPER
- Intent: deciding between 2–3 specific options
- What they expect: side-by-side comparison table, differentiators, ROI data
- SERP signals: comparison tables, "X vs Y" content, listicles
- Your content score: [1–10]

PERSONA 4 — THE LOCAL USER
- Intent: finding a local provider or physical location
- What they expect: proximity, hours, address, phone number
- SERP signals: map pack visible, local results, "near me" implicit
- Your content score: [1–10]

PERSONA 5 — THE MOBILE USER
- Intent: quick answer on the go, likely voice-adjacent
- What they expect: fast load, immediate answer above fold, click-to-call
- SERP signals: featured snippet, short answers, structured content
- Your content score: [1–10]

═══════════════════════════════════════════
FULL SXO ANALYSIS
═══════════════════════════════════════════

1. SERP LANDSCAPE ANALYSIS
   — What content types dominate top 10? (guides, product pages, listicles, local, videos)
   — What is the dominant intent signal? (informational / commercial / transactional / local)
   — Are there featured snippets, AI Overviews, People Also Ask boxes?
   — What SERP features appear? Map pack, knowledge panel, shopping, image carousel?
   — Median content length in top 10? (estimate)
   — What topics/sections appear in ALL top 10 results? (must-have content)
   — What topics appear in only some results? (differentiation opportunity)

2. DOMINANT PERSONA MATCH
   — Which of the 5 personas does the SERP primarily serve?
   — What is the #1 experience users expect?
   — Does your current content serve this persona? Gap analysis?

3. CONTENT EXPERIENCE AUDIT
   — Above the fold: does the page immediately confirm you're in the right place?
   — Answer speed: how many words before the user gets their answer?
   — Visual hierarchy: is content scannable (headings, bullets, tables)?
   — Trust signals visible: reviews, author bio, last updated, data sources?
   — CTA placement: appropriate to persona intent and funnel stage?
   — Mobile experience: critical content visible without scrolling?
   — Page speed: does it load fast enough not to bounce? (LCP target <2.0s)

4. SERP-BACKWARD CONTENT BRIEF
   Based on SERP analysis, this page MUST include:
   — Required sections (appear in 80%+ of top 10):
   — Recommended sections (appear in 40–80% of top 10):
   — Differentiator sections (appear in <40% = opportunity to stand out):
   — Content format: [article / comparison / tool / local page / product page]
   — Target length: [word count based on SERP median]
   — Required entities: [key terms/brands/concepts that must be mentioned]

5. AI SEARCH EXPERIENCE (GEO alignment)
   — Does current content match how ChatGPT/Perplexity would answer this query?
   — Is there a direct answer in the first 80 words?
   — Are there FAQ-format Q&As that match common follow-up questions?
   — Is the content citable (specific data, named sources, original insight)?

6. PRIORITISED IMPROVEMENTS
   Format: Improvement | Persona served | Expected CTR/ranking impact | Effort | Priority
   — Quick wins (change above-fold, add trust signals)
   — Medium-term (restructure content per SERP format)
   — Long-term (new content sections, format change)

7. CONFIDENCE ASSESSMENT
   - Confidence: High (have SERP data) / Medium (assumptions from keyword only) / Low
   - What would sharpen this: actual SERP screenshot, GSC CTR data for this keyword
   - Key assumptions made
"""
