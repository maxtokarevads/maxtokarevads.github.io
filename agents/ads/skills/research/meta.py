from typing import Any, Dict


def build_meta_research_prompt(payload: Dict[str, Any]) -> str:
    product    = payload.get("product", "product")
    goal       = payload.get("goal", "conversions")
    market     = payload.get("market", "")
    competitor = payload.get("competitors", "")
    context    = payload.get("context", "")
    budget     = payload.get("budget", 0)

    market_line  = f"\nMarket/language: {market}" if market else ""
    comp_line    = f"\nCompetitors: {competitor}" if competitor else ""
    context_line = f"\nContext: {context}" if context else ""
    budget_line  = f"\nMonthly budget: ${budget}" if budget else ""

    return f"""## Meta Ads — Audience Research & Strategy
Product: {product}
Goal: {goal}{market_line}{comp_line}{budget_line}{context_line}

Deliver a structured audience research and targeting plan across four sections.
Flag any recommendation that requires live Audience Insights data.

---

## Section 1 — Core Audience Architecture

### 1.1 Targeting approach spectrum

| Approach | Description | When to use | Expected CPM |
|----------|-------------|-------------|--------------|
| Detailed (interest) targeting | Specific interests, behaviours, demographics | New account, testing, niche products | Medium |
| Broad targeting | Age + geo only, no interests | Scaled accounts with ≥500 conv/mo data | Low–Medium |
| Advantage+ Audience | Meta's AI expands beyond your suggestion | Accounts with strong pixel data (≥50 conv/wk) | Varies |
| Custom Audiences | Website, video, customer list | Retargeting, Lookalike seeds | Low (high match) |
| Lookalike Audiences | 1–10% expansion from a seed | Prospecting with quality seed | Medium |

Recommended testing order (new account):
1. Broad + strong creative → collect pixel data
2. Once ≥50 weekly events: add Advantage+ Audience test
3. Build Lookalikes from first-party data after ≥500 seed events

### 1.2 Interest targeting — discovery framework

Seed interest categories to explore for this product:
- Direct: interests that exactly describe the product/service category
- Adjacent: interests of the ideal customer (lifestyle, related hobbies)
- Behavioural: purchase behaviour signals (online shoppers, frequent buyers, B2B decision makers)
- Competitor: interest in competitor brands (if available in Meta's taxonomy)
- Publication: magazines, blogs, media outlets the ICP reads

Validation approach:
- Stack interests in a single Ad Set first (Meta's algorithm picks best signals)
- Split winning interests into separate Ad Sets only after ≥200 events to avoid data fragmentation

### 1.3 Audience sizing

| Audience size | Guidance |
|---|---|
| <100K | Too narrow — CPM inflates, frequency spikes fast |
| 100K–1M | Good for niche B2B or hyper-local |
| 1M–10M | Ideal for most consumer products |
| 10M–50M | Good for broad prospecting with strong creative |
| >50M | Use only with Advantage+ or broad; creative quality critical |

---

## Section 2 — Custom Audiences (First-Party Data)

### 2.1 Website Custom Audiences (require Pixel / CAPI)

| Audience | Window | Use for |
|---|---|---|
| All website visitors | 180d | Broad retargeting seed |
| Product/service page viewers | 30d | MOFU retargeting |
| Cart abandoners | 7d | BOFU retargeting |
| Checkout initiators | 7d | Highest-intent BOFU |
| Purchasers | 180d | Exclusion + Lookalike seed |
| Blog/content readers | 90d | MOFU nurture |

### 2.2 Video Engagement Audiences

| Segment | Threshold | Recommended window |
|---|---|---|
| Video ThruPlays | 15s watch | 30d |
| 25% video views | 25% completion | 30d |
| 50% video views | 50% completion | 60d |
| 75% / 95% completers | High engagement | 90d |

Use 75%+ completers as Lookalike seed — highest intent signal from video.

### 2.3 Lead Form Audiences

- People who opened form (didn't submit) → BOFU retargeting with simpler ask
- People who submitted form → exclude from acquisition, add to nurture

### 2.4 Customer List Upload (CRM)

Requirements:
- Email + phone (both hash automatically in Meta upload)
- Minimum 1,000 matched users for reliable activation
- Upload format: CSV with columns: email, phone, first_name, last_name, city, country

Segment recommendations:
- All customers (lifetime) → Lookalike seed
- VIP customers (top 20% LTV) → highest-quality Lookalike seed
- Lapsed customers (no purchase 6+ months) → reactivation campaign
- Recent buyers (30d) → exclude from all acquisition

---

## Section 3 — Lookalike Strategy

### 3.1 Seed quality hierarchy

Best seeds (highest quality Lookalikes):
1. Purchasers / paying customers — best signal
2. High-LTV customers (top 20% by revenue)
3. Cart completers
4. Video 75%+ completers
5. All website visitors (worst quality but largest)

### 3.2 Lookalike size testing

| LAL % | Similarity | Size | When to use |
|---|---|---|---|
| 1% | Most similar | ~1–2M (US) | Best quality, higher CPM |
| 1–3% | High | ~3–6M | Balance of quality and reach |
| 3–5% | Medium | ~6–10M | Scale phase |
| 5–10% | Broad | ~10–20M | Max scale, creative-quality dependent |

Start with 1% LAL. Scale to 3–5% only after 1% shows profitable ROAS.
Do NOT mix LAL% in the same Ad Set — test separately.

### 3.3 Lookalike refresh cadence

- Refresh seed list: every 60–90 days (new purchaser data)
- Lookalike audience rebuilds automatically every 3–7 days
- Add new LAL seed when cumulative purchasers grow by ≥500

---

## Section 4 — Competitor Research on Meta

### 4.1 Meta Ad Library analysis

URL: https://www.facebook.com/ads/library/
Search for competitor brand names and analyse:
- Creative formats: video vs image vs carousel ratio
- Copy angle: offer-led vs benefit-led vs social proof-led
- CTA pattern: most common CTAs
- Frequency of new creatives: how often they refresh
- Active ads vs. total historical: ratio indicates what's working

### 4.2 Competitor audience signals (indirect)

- Competitor brand names as interests (if available in Meta's taxonomy)
- Competitor audience overlap via Audience Insights (deprecated in Meta, use Advantage+ as proxy)
- SpyFu / AdSpy / BigSpy tools for deeper creative analysis

### 4.3 SOV (Share of Voice) estimate

Meta doesn't provide direct competitor impression share.
Proxy method:
1. Set up Advantage+ Audience → observe estimated audience size in delivery
2. Track your frequency vs industry — if your frequency rises fast, competition for your audience is rising
3. Monitor CPM trend: rising CPM with same targeting = more competitors entering auction

---

## Output Format

Deliver:
1. Audience testing matrix: 4–6 Ad Sets to test, each with targeting approach + expected CPM range
2. Custom Audience build list: which segments to create first (priority order)
3. Lookalike seed recommendation: which seed to use + why
4. Competitor ad analysis: 3 key insights from Ad Library for this product category
5. Next 30 days targeting roadmap: week-by-week audience testing plan
"""
