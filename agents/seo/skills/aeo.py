"""
AEO — Answer Engine Optimization.
Optimising content for AI assistants: Google AI Overviews, Perplexity,
ChatGPT Search, Claude, Bing Copilot, and other LLM-powered search engines.
"""
from typing import Any, Dict, List


def build_aeo_prompt(payload: Dict[str, Any]) -> str:
    site         = payload.get("site", payload.get("website", "client website"))
    query        = payload.get("query", payload.get("goal", "get traffic from AI-powered search"))
    keywords: List[str] = payload.get("keywords", [])
    industry     = payload.get("industry", "")
    product      = payload.get("product", "")
    usp          = payload.get("usp", "")
    audience     = payload.get("audience", {})
    competitors  = payload.get("competitors", [])

    keywords_text    = ", ".join(keywords) if keywords else "not specified"
    industry_text    = f"\nIndustry: {industry}" if industry else ""
    product_text     = f"\nProduct/Brand: {product}" if product else ""
    usp_text         = f"\nUSP: {usp}" if usp else ""
    audience_parts   = [f"{k}: {v}" for k, v in audience.items() if v]
    audience_text    = f"\nAudience: {', '.join(audience_parts)}" if audience_parts else ""
    competitors_text = f"\nCompetitors: {', '.join(competitors)}" if competitors else ""

    return f"""Platform: AEO (Answer Engine Optimization) — Optimisation for AI-powered search
Site: {site}
Task: {query}
Keywords / topics: {keywords_text}{product_text}{industry_text}{usp_text}{audience_text}{competitors_text}

Context: AI assistants (Perplexity, Google AI Overviews, ChatGPT Search, Claude, Bing Copilot)
increasingly answer user questions without requiring a click-through to a website.
The goal is to make these systems cite this site/brand as the authoritative source.

Develop a complete AEO strategy across the following sections:

1. UNDERSTANDING AI SEARCH ENGINES (what you need to know)
   — How each platform works:
     • Google AI Overviews: indexes pages, prefers E-E-A-T, structured data
     • Perplexity: real-time web search + LLM, prefers fresh factual content with sources
     • ChatGPT Search (Bing-powered): relies on Microsoft Index, weights similar to Bing SEO
     • Claude / Anthropic: trained on CommonCrawl + licensed data, knowledge cutoff applies
     • Bing Copilot: Bing Index + GPT-4, schema markup is critical
   — Key difference from classic SEO: AI searches for ANSWERS, not links
   — Query types where AI search dominates:
     informational ("what is..."), comparative ("X vs Y"), instructional ("how to...")

2. ENTITY OPTIMIZATION (most important for LLMs)
   — What an Entity means in LLM context: a clear, unambiguous definition of the brand/product
   — How AI "understands" you exist:
     • Wikipedia / Wikidata: create/update article if brand is large enough
     • Google Knowledge Panel: verify via Google Search Console
     • Consistent NAP (Name, Address, Phone) across the web
     • Mentions in authoritative sources (Forbes, TechCrunch, industry publications)
   — Actions:
     • Create an "About" page with clear facts: founding year, what you do, who for
     • Add founder/author bios with professional background
     • Secure mentions in 3–5 authoritative industry sources

3. CONTENT STRUCTURE FOR AI CITABILITY
   — Principle: AI prefers content it can easily "extract" as a direct answer

   A) FAQ pages optimised for AI:
      — Each question = one paragraph with a direct, complete answer (50–150 words)
      — Frame questions as users ask ChatGPT, not as Google searches
      — Generate 5 conversational question examples that the target audience asks AI assistants
        about this industry/product
      — Structure: H2 = question → first sentence = direct answer → supporting detail

   B) Definition pages / Glossary:
      — Pages defining key industry terms
      — Format: "What is [term]?" — first paragraph gives a clear definition
      — AI frequently cites these pages when explaining concepts

   C) Comparison pages:
      — "[Product] vs [Competitor]": objective comparison with a table
      — AI Overviews often generates comparisons — position to appear in them

   D) How-to / Tutorial content:
      — Step-by-step instructions: H2 = step, <p> = details
      — Numbered lists for sequential processes (LLMs cite lists well)

4. SCHEMA MARKUP FOR AI SEARCH
   Priority schema.org types for this site:

   — FAQPage: most important for AI Overviews
     ```json
     {{"@type": "FAQPage", "mainEntity": [{{"@type": "Question",
       "name": "Question?", "acceptedAnswer": {{"@type": "Answer", "text": "Answer."}}}}]}}
     ```
   — HowTo: for instructions and tutorials
   — Article + author: for blog content (datePublished matters — Perplexity prefers fresh content)
   — Organization: full company data
   — Product + Review + AggregateRating: for e-commerce
   — BreadcrumbList: helps AI understand site structure
   — SpeakableSpecification: for Google Assistant / voice (if relevant)

5. E-E-A-T SIGNALS FOR LLMs
   (Experience, Expertise, Authoritativeness, Trustworthiness)

   — Authors:
     • Every article must have a byline with a real named author
     • Author page: bio, credentials, LinkedIn, publications
     • Schema markup for author: Person with sameAs (LinkedIn, Twitter)

   — Expertise signals:
     • Include specific data, research, and sources
     • Link to authoritative external sources (Statista, PubMed, Google, McKinsey)
     • Show last-updated date on content — visible to LLMs

   — Trustworthiness:
     • HTTPS, clear privacy policy, contact information
     • Reviews and case studies with specific results
     • Uptime and load speed (Perplexity caches fast sites)

6. KEYWORD STRATEGY FOR AI SEARCH
   — Conversational queries: users ask AI full questions
     Instead of: "seo tools 2026"
     Optimise for: "What are the best SEO tools to use in 2026?"

   — Long-tail questions with explicit intent:
     • "How to [process] for [business type]?"
     • "What is better: [option A] or [option B]?"
     • "How much does [service/product] cost?"
     • "Why is [customer problem] happening?"

   — Top 10 conversational queries for this niche (propose specific examples)

7. TECHNICAL REQUIREMENTS
   — Page speed: LCP < 2.5 sec (Perplexity quickly filters out slow sites)
   — Robots.txt: ensure AI crawlers are not blocked:
     • GPTBot (OpenAI), ClaudeBot (Anthropic), PerplexityBot, Bingbot
   — Allow or block AI crawlers (strategic decision):
     • Allow: higher chance of being cited in AI answers
     • Disallow (GPTBot): content will not be used for training
   — XML Sitemap: update on every new publication
   — Canonical tags: eliminate duplication that confuses LLMs

8. MONITORING AI PRESENCE
   — How to check mentions:
     • Manual: ask ChatGPT/Perplexity/Claude about the topic and check citations
     • Tools: Brandwatch, Mention, AIM Monitor (specialised AEO tracker)
     • Google Search Console: AI Overviews appear in the impressions report
   — KPIs for AEO:
     • Number of AI citations across top platforms (manual audit weekly)
     • Traffic from referral sources: perplexity.ai, bing.com/chat
     • Zero-click search rate (rising = AI is answering instead of sending clicks)
     • Brand mentions in LLM responses

9. ACTION PLAN (prioritised)
   Format: Action | Platform | Timeline | Difficulty | Expected impact

   Quick wins (0–30 days):
   — Add FAQPage schema to top 5 pages
   — Check robots.txt for AI bot blocking
   — Add author byline and bio to all articles
   — Verify Google Knowledge Panel exists

   Medium-term (1–3 months):
   — Create/update 10 FAQ pages with conversational queries
   — Launch definition pages for key industry terms
   — Secure 3–5 mentions in authoritative industry publications
   — Implement HowTo schema for tutorial content

   Long-term (3–6 months):
   — Systematic weekly AI citation monitoring
   — Build entity network: Wikipedia + Wikidata + Google Knowledge Graph
   — A/B test: FAQ format vs standard article — which gets cited more by AI
"""
