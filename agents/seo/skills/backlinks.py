from typing import Any, Dict, List


def build_backlinks_prompt(payload: Dict[str, Any]) -> str:
    site        = payload.get("site", "client website")
    competitors = payload.get("competitors", [])
    industry    = payload.get("industry", "")
    dr          = payload.get("domain_rating", None)
    ref_domains = payload.get("referring_domains", None)
    context     = payload.get("context", "")

    comp_text  = ", ".join(competitors) if competitors else "not specified"
    ind_line   = f"\nIndustry: {industry}" if industry else ""
    dr_line    = f"\nCurrent Domain Rating: {dr}" if dr is not None else ""
    rd_line    = f"\nCurrent Referring Domains: {ref_domains}" if ref_domains is not None else ""
    ctx_line   = f"\nContext: {context}" if context else ""

    return f"""Platform: SEO — Backlink Audit & Link Building Strategy
Site: {site}
Competitors: {comp_text}{ind_line}{dr_line}{rd_line}{ctx_line}

## Reference Examples

Example A — Toxic backlinks causing penalty:
Symptom: Traffic drop after Google Link Spam Update; spammy anchor text in profile
Root cause: 340 links from PBN and link farm sites; over-optimized anchor text 68% exact match
Fix: Disavow file for 340 domains; diversify anchor text to brand/URL/generic
Timeline to recovery: 2–3 months post-disavow processing
Confidence: High

Example B — Competitor gap opportunity:
Analysis: Competitor ranks #1 for "project management software" with 450 referring domains
Our profile: 180 referring domains, DR 42 vs competitor DR 67
Gap: 270 more referring domains needed; competitor earned links via original research + HARO
Action: Publish quarterly data report; join HARO/Connectively for journalist outreach
Confidence: Medium (link acquisition is probabilistic)

Example C — Anchor text over-optimization (EDGE CASE):
Symptom: Manual action penalty for unnatural links; 72% exact match anchor
Fix: Disavow exact-match links, build branded/URL anchors to dilute; reach out to remove worst offenders
Note: Natural anchor profile = 40–60% branded, 20–30% URL, 10–20% generic, <5% exact match

Conduct a complete backlink audit and build a link strategy:

1. PROFILE OVERVIEW
   — Total backlinks vs referring domains (links per domain ratio)
   — Domain Rating / Domain Authority trend (rising, stable, declining)?
   — Organic traffic correlation with link profile changes?
   — New vs lost links in last 30/90 days?

2. TOXIC LINK AUDIT
   Identify potentially harmful links:
   — Links from PBNs, link farms, adult/gambling/pharma sites
   — Over-optimized anchor text (exact-match >15% = risk)
   — Links from same IP subnets (network footprint)
   — Footer/sitewide links with keyword-rich anchors
   — Purchased links with "dofollow" on non-editorial pages

   Severity assessment:
   — Critical: disavow immediately (penalty risk)
   — Warning: monitor, consider disavow
   — Low risk: keep, no action

3. ANCHOR TEXT DISTRIBUTION
   — Current distribution: branded / URL / generic / exact-match / partial-match
   — Natural profile target: 40–60% branded, 20–30% URL, 10–20% generic, <5% exact-match
   — Over-optimization risk: exact-match >15%?
   — Actions to diversify anchor text profile?

4. COMPETITOR GAP ANALYSIS
   For each competitor provided:
   — Their DR vs ours
   — Their referring domain count vs ours
   — Link sources they have that we don't (gap opportunities)
   — Content types earning their best links (research, tools, guides, news)
   — Common link sources across all competitors = highest priority targets

5. LINK BUILDING STRATEGY

   TIER 1 — Earned (highest authority, hardest to get):
   — Digital PR: original research, data studies, surveys
   — HARO/Connectively: journalist quote requests in your niche
   — Newsjacking: comment on trending industry news

   TIER 2 — Relationship (medium effort, sustainable):
   — Guest posts on niche-relevant DR 40+ sites
   — Expert roundup contributions
   — Partner/vendor reciprocal links (if genuinely relevant)
   — Industry association membership pages

   TIER 3 — Technical (lower authority, consistent):
   — Resource page outreach (link to your useful tool/guide)
   — Broken link building (find broken links on competitor-linked pages)
   — Reclaim unlinked brand mentions (use alerts)

6. PRIORITISED ACTION PLAN
   Format: Tactic | Effort | Expected DR gain | Links/month | Timeline

7. MONITORING
   — Set up: Google Alerts for brand mentions
   — Tools: Ahrefs/Semrush weekly link alerts
   — KPIs: referring domain count, DR trend, new vs lost links monthly

8. CONFIDENCE ASSESSMENT
   - Confidence: High (have backlink data) / Medium (limited data) / Low (estimates only)
   - Tools needed for full audit: Ahrefs, Semrush, or Moz access
   - Key assumptions made
"""
