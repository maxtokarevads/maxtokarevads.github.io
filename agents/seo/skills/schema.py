from typing import Any, Dict, List


def build_schema_prompt(payload: Dict[str, Any]) -> str:
    site        = payload.get("site", "client website")
    url         = payload.get("url", "")
    page_type   = payload.get("page_type", "")
    industry    = payload.get("industry", "")
    existing    = payload.get("existing_schema", [])
    context     = payload.get("context", "")

    url_line      = f"\nURL: {url}" if url else ""
    page_line     = f"\nPage type: {page_type}" if page_type else ""
    ind_line      = f"\nIndustry: {industry}" if industry else ""
    existing_text = ", ".join(existing) if existing else "unknown"
    existing_line = f"\nExisting schema: {existing_text}"
    ctx_line      = f"\nContext: {context}" if context else ""

    return f"""Platform: SEO — Schema Markup Audit & Generation
Site: {site}{url_line}{page_line}{ind_line}{existing_line}{ctx_line}

## Reference Examples

Example A — FAQPage drives AI Overview citation:
Before: No schema on FAQ page → 0 AI Overview appearances
After: FAQPage JSON-LD with 8 Q&As → 3.2× more likely in AI Overviews
Implementation: Each answer = 40–60 words, direct, complete

Example B — Deprecated schema causing rich result loss:
Symptom: HowTo rich results disappeared from SERP
Root cause: HowTo schema removed from Google rich results September 2023
Fix: Remove HowTo schema, replace with ordered list content + How-to heading structure
Note: FAQPage also restricted August 2023 — use only for genuine Q&A sections

Example C — Product schema missing review aggregation:
Symptom: Competitor shows ★★★★☆ 4.2 stars in SERP; our product doesn't
Root cause: Missing AggregateRating nested inside Product schema
Fix: Add AggregateRating with ratingValue, reviewCount pulled from database

Conduct a complete schema markup audit and generate required schemas:

1. SCHEMA AUDIT — What exists and is it valid?
   For each detected schema type:
   — Type and format (JSON-LD preferred / Microdata / RDFa)
   — Required properties: all present?
   — Recommended properties: any missing that add value?
   — Deprecated types: HowTo (Sep 2023), FAQPage restrictions (Aug 2023)?
   — Rich result eligibility: does this schema enable a rich result?
   — Validation status: any Google Search Console rich result errors?

2. SCHEMA OPPORTUNITIES — What's missing?

   BY PAGE TYPE:
   — Homepage: Organization, WebSite (with SearchAction), BreadcrumbList
   — Blog post/Article: Article (with author Person, datePublished, dateModified)
   — Product page: Product, AggregateRating, Review, Offer
   — Service page: Service, LocalBusiness or Organization
   — FAQ page: FAQPage (only if genuine Q&A content)
   — Recipe/HowTo: Recipe (HowTo removed from rich results 2023)
   — Event page: Event with startDate, location, organizer
   — Person page: Person with sameAs (LinkedIn, Wikidata)

   FOR AI SEARCH (GEO/AEO):
   — Article with dateModified: AI uses this for freshness signal
   — Organization with sameAs (Wikidata QID): entity disambiguation
   — FAQPage: highest citability for AI Overviews
   — BreadcrumbList: helps AI understand site structure
   — DefinedTerm: for glossary pages (establishes entity authority)

3. GENERATE MISSING SCHEMAS

   For each missing/broken schema, provide complete JSON-LD ready to copy-paste:

   Article template:
   {{
     "@context": "https://schema.org",
     "@type": "Article",
     "headline": "[PAGE TITLE]",
     "author": {{"@type": "Person", "name": "[AUTHOR]", "jobTitle": "[TITLE]"}},
     "datePublished": "[YYYY-MM-DD]",
     "dateModified": "[YYYY-MM-DD]",
     "publisher": {{"@type": "Organization", "name": "[BRAND]"}}
   }}

   Organization template with Wikidata:
   {{
     "@context": "https://schema.org",
     "@type": "Organization",
     "name": "[BRAND]",
     "url": "[URL]",
     "sameAs": ["https://www.wikidata.org/wiki/[QID]", "[LINKEDIN]", "[TWITTER]"]
   }}

4. IMPLEMENTATION INSTRUCTIONS
   — Where to place: <head> section (JSON-LD, not inline Microdata)
   — CMS-specific: WordPress (Yoast/RankMath), Shopify (theme.liquid), custom (template)
   — Testing: Google Rich Results Test, Schema.org Validator
   — Monitoring: GSC → Enhancements → track rich result impressions

5. SCHEMA STACK IMPACT
   — Single schema: baseline
   — 3–4 complementary schemas: 2× AI citation rate
   — Recommended stack for this page: [list specific types]

6. CONFIDENCE ASSESSMENT
   - Confidence per finding: High / Medium / Low
   - Cannot assess without: page HTML access, GSC rich result report
   - Key assumptions made
"""
