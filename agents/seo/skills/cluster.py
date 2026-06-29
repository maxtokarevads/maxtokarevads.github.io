from typing import Any, Dict, List


def build_cluster_prompt(payload: Dict[str, Any]) -> str:
    site         = payload.get("site", "client website")
    seed         = payload.get("seed", payload.get("keywords", []))
    industry     = payload.get("industry", "")
    funnel_stage = payload.get("funnel_stage", "")
    competitors  = payload.get("competitors", [])
    context      = payload.get("context", "")

    seed_text  = ", ".join(seed) if isinstance(seed, list) else str(seed)
    comp_text  = ", ".join(competitors) if competitors else ""
    ind_line   = f"\nIndustry: {industry}" if industry else ""
    comp_line  = f"\nCompetitors: {comp_text}" if comp_text else ""
    stage_line = f"\nFunnel stage focus: {funnel_stage.upper()}" if funnel_stage else ""
    ctx_line   = f"\nContext: {context}" if context else ""

    return f"""Platform: SEO — Topical Cluster & Keyword Strategy
Site: {site}
Seed keywords: {seed_text}{ind_line}{comp_line}{stage_line}{ctx_line}

## Reference Examples

Example A — Semantic cluster built around seed "project management":
Pillar: "Project Management Guide" (3,500 words) — targets: "project management", "what is project management"
Spokes:
  - "Project management software comparison" (commercial intent, MOFU)
  - "Agile vs Waterfall: which to choose" (informational, TOFU)
  - "Project management templates free" (informational + lead gen, MOFU)
  - "How to manage remote teams" (informational, TOFU)
  - "Project management certifications" (informational, MOFU)
Internal link structure: all spokes link to pillar; pillar links to all spokes
Result: Topical authority cluster — Google treats site as authority on topic

Example B — SERP-overlap clustering method:
Step 1: Search "project management software" and "best project management tools"
Step 2: Both return same 7 of top 10 results → 70% overlap = SAME cluster
Step 3: One page can rank for both queries (don't create separate pages)
Step 4: If overlap <40% → different intent → separate pages needed

Example C — Cannibalization avoided:
Symptom: 3 pages targeting "CRM software", all ranking 15–20
Fix: Merge into one authoritative pillar; 301 redirect weaker 2 to strongest
Result: Single page now ranks #6, capturing all authority

Build a complete topical cluster strategy:

1. KEYWORD UNIVERSE MAPPING
   From seed keywords, expand to full keyword universe:
   — Head terms (high volume, competitive): primary targets for pillar pages
   — Long-tail variations (lower volume, easier to rank): spoke articles
   — Question-based queries ("how to", "what is", "why does"): FAQ/blog content
   — Comparison queries ("X vs Y", "alternatives to X"): comparison pages
   — Local variants (if applicable): "[service] in [city]"

2. INTENT CLASSIFICATION
   For each keyword group:
   — Informational (TOFU): define, explain, overview
   — Commercial (MOFU): compare, review, best, top
   — Transactional (BOFU): buy, price, discount, order
   — Navigational: brand/product specific

3. CLUSTER ARCHITECTURE

   PILLAR PAGE (one per main topic):
   — Target: head term (1,000–5,000 monthly searches)
   — Length: 3,000+ words
   — Covers: all subtopics at overview level
   — Links out to: all spoke articles

   SPOKE ARTICLES (3–12 per pillar):
   — Target: long-tail, specific subtopics
   — Length: 1,000–2,500 words
   — Covers: deep dive on ONE subtopic
   — Links back to: pillar page + relevant spokes

   Format for each cluster:
   Pillar: [title] — [target keyword] — [estimated volume]
   ├── Spoke 1: [title] — [keyword] — [intent]
   ├── Spoke 2: [title] — [keyword] — [intent]
   └── Spoke 3: [title] — [keyword] — [intent]

4. SERP-OVERLAP ANALYSIS
   For potentially overlapping keywords, assess:
   — Do the same URLs appear in top 10 for both queries? (>60% overlap = same page)
   — What content type dominates: article, product page, comparison, tool?
   — What's the median content length for top 10?
   — What entities/topics do top 10 results cover that you should too?

5. COMPETITIVE GAP
   Topics competitors rank for that you don't:
   — Prioritize: high volume + low difficulty + relevant to your audience
   — Quick wins: topics where DR 30–40 sites rank (you can likely beat them)
   — Long-term: head terms dominated by DR 70+ (build authority first)

6. CONTENT CALENDAR
   Format: Priority | Topic | Target keyword | Intent | Word count | Pillar/Spoke | Month
   — Month 1: pillar pages (most authority)
   — Month 2–3: BOFU spokes (direct revenue impact)
   — Month 4–6: TOFU/MOFU spokes (traffic and lead gen)

7. INTERNAL LINKING PLAN
   — Pillar → Spoke: each spoke linked from pillar with descriptive anchor
   — Spoke → Pillar: each spoke links back to pillar with keyword-rich anchor
   — Spoke → Spoke: relevant cross-links within cluster
   — Category pages: if applicable, link to relevant cluster pages

8. AI SEARCH ALIGNMENT
   Same topical cluster that ranks in Google also increases AI citation probability.
   For each cluster topic, flag:
   — Does it answer common AI search queries? (conversational, "what is", "how to")
   — Is there a FAQ section opportunity?
   — Does it need DefinedTerm schema for key concepts?

9. CONFIDENCE ASSESSMENT
   - Confidence per recommendation: High / Medium / Low
   - Data needed: GSC impressions for existing pages, competitor keyword lists
   - Key assumptions made
"""
