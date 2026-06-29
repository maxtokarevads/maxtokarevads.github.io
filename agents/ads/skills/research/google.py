from typing import Any, Dict


def build_google_research_prompt(payload: Dict[str, Any]) -> str:
    product      = payload.get("product", "product")
    goal         = payload.get("goal", "conversions")
    market       = payload.get("market", "")
    competitor   = payload.get("competitors", "")
    seed_kw      = payload.get("seed_keywords", "")
    context      = payload.get("context", "")
    budget       = payload.get("budget", 0)

    market_line    = f"\nMarket/language: {market}" if market else ""
    comp_line      = f"\nCompetitors: {competitor}" if competitor else ""
    seed_line      = f"\nSeed keywords: {seed_kw}" if seed_kw else ""
    context_line   = f"\nContext: {context}" if context else ""
    budget_line    = f"\nMonthly budget: ${budget}" if budget else ""

    return f"""## Google Ads — Keyword & Audience Research
Product: {product}
Goal: {goal}{market_line}{comp_line}{seed_line}{budget_line}{context_line}

Deliver a structured research plan across four sections below.
Use real keyword patterns and estimated data ranges — flag any field where data requires live tools.

---

## Section 1 — Keyword Strategy

### 1.1 Keyword universe (map to intent layer)

| Intent | Keyword type | Examples for this product | Est. CPC range | Priority |
|--------|-------------|--------------------------|----------------|----------|
| Buy-now (BOFU) | Brand + [buy/price/order/near me] | — | high | P0 |
| Product-aware (MOFU) | Category + [best/review/vs/alternative] | — | medium | P1 |
| Problem-aware (TOFU) | Pain-point queries, how-to questions | — | low | P2 |
| Brand (branded) | Exact brand name + variants | — | low | protect |

### 1.2 Match type strategy

Recommended structure:
- Broad Match in Performance Max / Smart campaigns → let algorithm explore
- Phrase Match for core buying queries → control spend, capture variants
- Exact Match for top converters + brand terms → protect & guard share
- BMM is deprecated — migrate old +keyword+ to Phrase Match

Negative match types:
- Campaign-level negatives: cross-campaign pollution (e.g., brand excluded from generic)
- Account-level negative list: universal exclusions (competitors, irrelevant verticals)
- Never add negative keywords blindly from SQR — check volume and CVR first

### 1.3 Negative keyword mining

Priority negative categories for this product:
1. Informational: "what is", "definition", "meaning", "wikipedia", "history"
2. Free-intent: "free", "free trial", "crack", "torrent", "open source"
3. DIY-intent: "how to make", "do it yourself", "template", "example"
4. Career/job: "jobs", "career", "salary", "hiring", "internship"
5. Competitor brand names (add as phrase-match negatives in non-brand campaigns)
6. Wrong audience: product categories that share keywords but don't buy (map per niche)

SQR cadence: pull Search Terms report every 7–14 days for first 90 days, then monthly.

### 1.4 Keyword grouping (SKAG vs STAG trade-off)

SKAGs (Single Keyword Ad Groups):
+ Max relevance → Quality Score ↑
+ Precise bid control per keyword
- High maintenance overhead, thin data per group slows learning
→ Recommended only for top 10–20 revenue keywords

STAGs (Small Themed Ad Groups, 3–10 related keywords):
+ Faster data accumulation → faster learning phase exit
+ Lower management overhead
→ Recommended default for most accounts

### 1.5 Keyword tools & sources

1. Google Keyword Planner — volume, competition, CPC estimates
2. Google Search Console → Performance → Queries (existing site data)
3. Semrush / Ahrefs Keyword Magic — competitor gap analysis
4. Google Trends — seasonality curve, rising queries
5. SQR (Search Query Reports) — discovery from live campaigns
6. Autocomplete / People Also Ask — intent clustering

---

## Section 2 — Audience Strategy

### 2.1 In-market audiences (layer on top of keyword campaigns for bid adjustments)

Recommended in-market segments to test:
- Map product category → Google's in-market taxonomy
- Layering approach: keyword targeting + in-market observation mode first
- Promote to targeting mode if in-market segment shows ≥15% CVR lift vs baseline

### 2.2 Custom Intent / Custom Affinity audiences

Custom Intent (URL-based):
- Add competitor domain URLs → Google finds users who visited those sites
- Add category URLs (e.g., review sites for the product category)

Custom Affinity (interest-based):
- Add keyword strings + URLs that describe ideal customer lifestyle
- Use for Display / YouTube campaigns where keyword targeting isn't available

### 2.3 Remarketing audiences (RLSA)

Standard segments to create:
- All visitors 30d / 90d / 180d
- Product/service page viewers 30d
- Cart abandoners 7d (ecom)
- Converters 180d (for exclusion + upsell)
- Customer match: upload CRM list (email + phone)

RLSA bid strategy:
- +20–50% bid modifier for MOFU segments on Search campaigns
- +30–100% for BOFU (cart abandon) segments
- Exclude converters from prospecting campaigns

### 2.4 Lookalike / Similar Segments

- Similar Segments (Google's version): based on converters list
- Customer Match→Similar: upload purchaser email list → Google expands to lookalike
- Use as bid modifier on display, not as primary targeting

---

## Section 3 — Competitor Research

### 3.1 Auction Insights analysis

Pull: Campaign level → Insights → Auction Insights
Metrics to track:
- Impression Share: your % vs competitors
- Overlap Rate: how often same auction
- Position Above Rate: they show above you how often
- Top of Page Rate: who dominates above-fold

### 3.2 Competitor ad copy analysis

Tools:
- Google Ads Transparency Center (ads.google.com/transparency)
- Semrush Advertising Research → Ad Copies tab
- SpyFu → competitor keywords and ad history

Analyse:
- Headline patterns: what USPs they lead with
- CTA language: urgency, offers, guarantees
- Extensions used: sitelinks, callouts, prices
- Landing page angle: feature-led vs benefit-led vs offer-led

### 3.3 SERP gap analysis

Identify keywords where:
- Competitors rank organically but have no ads → opportunity (less competition)
- You rank organically top 3 but don't run ads → double down (SERP domination)
- Your Quality Score is below competitor for same keyword → creative/LP work needed

---

## Section 4 — Research Output Format

Deliver these artefacts:
1. Keyword list (CSV format): keyword | match type | intent layer | estimated CPC | priority
2. Negative keyword list: keyword | match type | reason for exclusion
3. Audience layer map: audience segment | campaign | bid modifier | observation vs targeting
4. Competitor SERP summary: competitor | share of voice estimate | key differentiator in ads
5. Next action: top 3 immediate keyword/audience changes with expected impact
"""
