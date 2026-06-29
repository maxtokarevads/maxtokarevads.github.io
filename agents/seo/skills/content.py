from typing import Any, Dict, List


def build_content_prompt(payload: Dict[str, Any]) -> str:
    site         = payload.get("site", "client website")
    url          = payload.get("url", "")
    keywords     = payload.get("keywords", [])
    industry     = payload.get("industry", "")
    funnel_stage = payload.get("funnel_stage", "mofu")
    competitors  = payload.get("competitors", [])
    context      = payload.get("context", "")

    kw_text    = ", ".join(keywords) if keywords else "not specified"
    comp_text  = ", ".join(competitors) if competitors else ""
    url_line   = f"\nURL to assess: {url}" if url else ""
    comp_line  = f"\nCompetitors: {comp_text}" if comp_text else ""
    ind_line   = f"\nIndustry: {industry}" if industry else ""
    ctx_line   = f"\nContext: {context}" if context else ""

    stage_hints = {
        "tofu": "TOFU — informational content, brand awareness, broad topics",
        "mofu": "MOFU — comparison, consideration, feature/benefit content",
        "bofu": "BOFU — conversion-focused, high-intent, product/service pages",
    }
    stage_line = f"\nFunnel stage: {stage_hints.get(funnel_stage.lower(), funnel_stage)}"

    return f"""Platform: SEO — Content Quality & E-E-A-T Assessment
Site: {site}{url_line}
Keywords: {kw_text}{ind_line}{comp_line}{stage_line}{ctx_line}

## Reference Examples

Example A — Thin content penalised (EDGE CASE):
Symptom: 200-word product description pages dropping after Helpful Content Update
Root cause: No unique value beyond manufacturer specs; user gets nothing they can't get on Amazon
Fix: Add comparison tables, real-user reviews, buying guide, sizing advice
Target: 800–1,500 words with genuine expertise signals
Confidence: High

Example B — Missing Experience signals post-March 2026 update:
Symptom: Rankings dropped despite "good" content; competitor with author bios outranks
Root cause: Google now weights Experience heavily — AI cannot fake first-hand experience
Fix: Add named author + credentials, original photos/screenshots, first-person outcome data
Confidence: High

Example C — Keyword cannibalization (EDGE CASE):
Symptom: Two pages ranking #8 and #11 for same query; neither reaches top 5
Root cause: Duplicate intent coverage splitting authority
Fix: Merge weaker page into stronger, 301 redirect, consolidate backlinks
Confidence: Medium (confirm with GSC click data)

Conduct a complete E-E-A-T and content quality assessment:

1. EXPERIENCE SIGNALS (highest weighted in 2026)
   — First-person narratives with measurable outcomes?
   — Original photos, screenshots, tested tool outputs?
   — "Tested by" / "Reviewed by" attribution with visible credentials?
   — Named tools, specific timelines, documented failures/successes?

2. EXPERTISE SIGNALS
   — Dedicated author pages at /about/[author]/ with degrees, certs, LinkedIn?
   — Content covers edge cases, not just surface-level overview?
   — Peer-reviewed citations with year and org name?
   — Technical depth appropriate for the audience?

3. AUTHORITATIVENESS SIGNALS
   — Topical coverage: pillar page (3,000+ words) + 8–15 spoke articles?
   — Internal linking hierarchy: do spokes link back to pillar?
   — Backlinks from relevant authoritative domains?
   — Brand mentions in industry publications?

4. TRUSTWORTHINESS SIGNALS
   — HTTPS, privacy policy, ToS, About page, contact info?
   — NAP consistency: Name, Address, Phone consistent across site + GBP + directories?
   — Links on factual claims to primary sources?
   — dateModified Schema markup? Quarterly content refreshes?
   — AggregateRating schema from Google Reviews / Trustpilot?

5. CONTENT QUALITY METRICS
   — Word count: blog posts ≥1,500 words? Product pages ≥500 words?
   — Thin content: pages <300 words without clear justification?
   — Duplicate content: same topic covered on 2+ URLs?
   — Content gaps: topics competitors cover that you don't?
   — Freshness: pages older than 12 months without update?

6. KEYWORD & INTENT ALIGNMENT
   — Does content match primary keyword intent (informational/commercial/transactional)?
   — Title tag ≤60 chars, includes primary keyword near start?
   — Meta description ≤160 chars with keyword + CTA?
   — H1: one per page, matches search intent?
   — H2/H3: structured for skimmability, secondary keywords included?
   — Keyword cannibalization check: any two pages targeting same query?

7. AI SEARCH CITABILITY (GEO signal)
   — Answer-first format: 40–60 word direct answer at top of each H2 section?
   — Specific data with attribution ("32% of marketers...") vs vague claims?
   — FAQ section present? Maps directly to user questions?
   — Last-updated date visible and accurate?
   — Content fresher than 12 months? (83% of AI citations = content <12 months old)

8. CONTENT IMPROVEMENT PLAN
   Format: Issue | Severity | Page | Specific fix | Expected impact
   — Priority 1: Quick wins (add author bio, update date, fix title tag)
   — Priority 2: Content expansion (add sections competitors have)
   — Priority 3: Structural (merge cannibalized pages, rebuild pillar)

9. CONFIDENCE ASSESSMENT
   - Confidence per finding: High / Medium / Low
   - Missing data that would sharpen this assessment
   - Key assumptions made
"""
