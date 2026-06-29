from typing import Any, Dict, List


def build_seo_prompt(payload: Dict[str, Any]) -> str:
    site         = payload.get("site", payload.get("website", "client website"))
    query        = payload.get("query", payload.get("goal", "improve search rankings"))
    keywords: List[str] = payload.get("keywords", [])
    industry     = payload.get("industry", "")
    funnel_stage = payload.get("funnel_stage", "")
    audience     = payload.get("audience", {})
    usp          = payload.get("usp", "")

    keywords_text = ", ".join(keywords) if keywords else "not specified"
    industry_text = f"\nIndustry: {industry}" if industry else ""
    usp_text      = f"\nUSP: {usp}" if usp else ""

    audience_parts = [f"{k}: {v}" for k, v in audience.items() if v]
    audience_text  = ", ".join(audience_parts) if audience_parts else ""
    audience_line  = f"\nTarget audience: {audience_text}" if audience_text else ""

    stage_hints = {
        "tofu": "TOFU — focus on broad informational traffic, brand awareness through content",
        "mofu": "MOFU — transactional and commercial queries, comparison, consideration",
        "bofu": "BOFU — high-intent queries, conversion landing pages, brand + product terms",
    }
    stage_line = f"\nFunnel stage: {funnel_stage.upper()} — {stage_hints[funnel_stage.lower()]}" \
                 if funnel_stage.lower() in stage_hints else ""

    return f"""Platform: SEO
Site: {site}
Task: {query}
Keywords: {keywords_text}{industry_text}{usp_text}{audience_line}{stage_line}

## Reference Examples

Example A — SaaS organic growth (happy path):
Site: project management SaaS, DR 38, 2,400 monthly organic visits
Action: Built pillar page "Project Management Guide" (3,200 words) + 8 spoke articles
Result: 6 months → DR 44, 8,700 monthly visits, #4 for "project management software"
Key: Topical authority cluster + consistent internal linking drove the lift

Example B — Technical SEO blocking growth (edge case):
Symptom: 180 pages in GSC, only 40 indexed; content quality is good
Root cause: JavaScript-rendered content; Googlebot couldn't parse it
Fix: Moved to SSR (Next.js); submitted sitemap after fix
Result: 140 pages indexed within 3 weeks; organic traffic +340% in 60 days
Confidence: High — indexability was the sole bottleneck

Example C — Content cannibalization suppressing rankings (edge case):
Symptom: 4 pages targeting "CRM for small business", all ranking 18–25
Root cause: Split authority across 4 URLs; Google couldn't determine the canonical
Fix: Consolidated into one authoritative page with 301 redirects from other 3
Result: Consolidated page reached #7 within 45 days
Lesson: One strong page beats four mediocre ones every time

Develop a complete SEO strategy across the following sections:

1. TECHNICAL SEO (priority: high / medium / low)
   — Core Web Vitals: LCP, CLS, INP — what to check and target values
   — Crawlability: robots.txt, sitemap.xml, internal linking
   — Indexation: canonical, hreflang (if needed), 404 / 301
   — Structured data (Schema.org): which types are needed for this industry
   — Mobile-first: what to audit

2. KEYWORD RESEARCH
   — Keyword clusters: split by intent (informational / commercial / branded)
   — Priority queries: top 10 with estimated volume and difficulty
   — Negative keywords and exclusions
   — Long-tail opportunities: 3–5 low-competition query examples
   — Search intent per cluster

3. CONTENT STRATEGY
   — Site structure: which pages to create / optimise
   — Content plan: top 5 priority pages/articles with target keywords
   — On-page optimisation: Title (≤60 chars), Meta Description (≤160 chars), H1/H2, alt text
   — Content format for the industry: guides, case studies, comparisons, landing pages
   — Publishing and update cadence

4. LINK PROFILE
   — Current profile analysis (if known)
   — Link acquisition tactics: guest posts, HARO, digital PR, partnerships
   — Internal linking: logic and priorities
   — Target metrics: Domain Rating / DR, number of referring domains

5. MEASUREMENT AND KPIS
   — Tools: Google Search Console, GA4, Ahrefs / Semrush
   — Key metrics: organic traffic, cluster rankings, CTR, organic conversion rate
   — Benchmarks: realistic timeline expectations (SEO takes 3–6 months minimum)
   — Reporting cadence: weekly vs monthly

6. ACTION PLAN (prioritised)
   Format: Action | Priority | Timeline | Expected impact
   — Quick wins (0–30 days): technical fixes, optimise existing pages
   — Medium-term (1–3 months): content + links
   — Long-term (3–6 months): authority building

7. CONFIDENCE ASSESSMENT
   For each major recommendation:
   — Confidence: High (have all data) / Medium (partial data) / Low (assumption)
   — Missing data that would sharpen this strategy (GSC access, crawl report, backlink data)
   — Key assumptions made
"""
