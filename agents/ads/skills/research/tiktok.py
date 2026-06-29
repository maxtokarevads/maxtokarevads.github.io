from typing import Any, Dict


def build_tiktok_research_prompt(payload: Dict[str, Any]) -> str:
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

    return f"""## TikTok Ads — Audience & Creative Research
Product: {product}
Goal: {goal}{market_line}{comp_line}{budget_line}{context_line}

TikTok is discovery-first: users are not searching — they're being found.
Research here is 60% creative intelligence, 40% audience targeting.
Deliver a structured research plan across four sections.

---

## Section 1 — Audience Research on TikTok

### 1.1 Interest & Behaviour Targeting

TikTok's interest taxonomy is less granular than Meta. Strategy:
- Use broad interest categories first → collect data → narrow
- Behaviours (e.g., "engaged with similar products") often outperform interests
- Avoid stacking too many interests in one Ad Group (dilutes signal)

Interest categories to explore:
| Category | Relevance | Sub-interests to test |
|---|---|---|
| Direct product category | High | — |
| Lifestyle/values | Medium | — |
| Entertainment genres watched | Medium | TikTok-specific signals |
| Competitor brand followers | Low/variable | Check if available |

### 1.2 Custom Audiences (first-party data on TikTok)

| Source | What it captures | Window |
|---|---|---|
| TikTok Pixel — All visitors | Anyone who hit your site | 180d |
| TikTok Pixel — ViewContent | Viewed product pages | 30d |
| TikTok Pixel — AddToCart | Cart events | 7d |
| TikTok Pixel — Checkout | Initiated checkout | 7d |
| TikTok Pixel — Purchase | Buyers | 180d |
| Video engagement — 6s+ | Watched ≥6 seconds | 30d |
| Video engagement — 25%+ | 25% completion | 30d |
| Video engagement — 75%+ | High engagement | 60d |
| Profile visitors | Visited your TikTok profile | 30d |
| LIVE viewers | Watched your LIVE stream | 30d |
| Lead Form openers (not submitted) | BOFU retargeting | 7d |

Minimum Custom Audience size: **1,000 matched users** (below this won't activate)

### 1.3 Lookalike Audiences on TikTok

Best seeds:
1. Purchasers list (CRM upload: email + phone)
2. TikTok Pixel — Purchase event (last 90d)
3. Video 75%+ completers (engagement signal)

Lookalike sizes available: 1% / 2% / 5% / 10% / 15% / 20% (of country population)
Start with 1–2%, scale after confirming CVR.

### 1.4 Broad Targeting Test

TikTok's algorithm often beats manual targeting with enough data.
Broad = age + geo only (no interests, no behaviours).
Recommended: run Broad in parallel with Interest targeting from day 1.
Winner usually emerges within 14–21 days.

---

## Section 2 — Creative Research (The Real Differentiator)

### 2.1 Creative Intelligence Sources

1. **TikTok Creative Center** (ads.tiktok.com/business/creativecenter/)
   - Top Ads: filter by industry, country, objective, date range
   - Trending Hashtags: what's rising in your category
   - Trending Sounds: music that's getting native reach
   - Keyword Insights: what people search on TikTok

2. **TikTok Ad Library** (library.tiktok.com)
   - Search competitor brand names
   - See active ads, creatives, format breakdown

3. **Organic TikTok research**
   - Search your product category → top performing organics reveal native formats
   - Check hashtags: #[product] #[problem] #[solution]
   - "FYP strategy" test: post organic → if it gets native traction → run as Spark Ad

### 2.2 Hook Pattern Analysis

The first 3 seconds determine if the video gets watched.
Categorise top performing ads by hook type:

| Hook type | Pattern | Example | When effective |
|---|---|---|---|
| Curiosity gap | "You've been doing X wrong" | — | Broad education products |
| Bold claim | "I got X result in Y days" | — | High-result products |
| Problem call-out | "Still struggling with X?" | — | Pain-point products |
| Visual stun | Unexpected visual/action, no text | — | Fashion, food, beauty |
| Before/after | Show transformation in 3s | — | Weight loss, renovation, software |
| POV | "POV: you just found X" | — | Lifestyle products |
| Testimonial open | "Honest review of X after 30 days" | — | Review-driven niches |

Recommendation: test 3–5 different hook types, same product, same offer.

### 2.3 Format Strategy

| Format | Length | Best for | CTR benchmark |
|---|---|---|---|
| In-Feed (native) | 9–60s | Direct response | 1.0–2.5% |
| Spark Ads | any (boost organic) | Trust + retargeting | Often 20–40% higher CTR vs dark ads |
| Top View | 5–60s | Brand awareness | Premium placement |
| Branded Hashtag | — | Brand campaigns | N/A |
| Shopping Ads (catalog) | — | Ecom with catalog | — |

For direct response: prioritise In-Feed 9–15s for cold + Spark Ads for retargeting.

### 2.4 Audio Strategy

TikTok is audio-on by default (60%+ of users watch with sound on).
- Use trending sounds: check Creative Center Trending Sounds weekly
- Avoid copyright music: use TikTok Commercial Music Library
- Subtitles / text overlays: add to all videos (catch silent viewers and improve completion)
- Voice-over with trending audio in background: often outperforms music-only

### 2.5 Creative Refresh Cadence

TikTok creative fatigue is aggressive:
- Average burnout: 7–14 days for high-frequency audiences
- Rule: if CPM rises >30% week-over-week with same targeting → creative fatigue
- New creative pipeline: 10–20 new assets/week minimum for scaling accounts

---

## Section 3 — Competitor Research

### 3.1 TikTok Ad Library scan

For each competitor found:
- Active ad count (proxy for budget level)
- Dominant format (video length, style)
- Most common hook type
- CTA pattern
- Estimated frequency of creative refresh (new ads / month)

### 3.2 Organic competitive analysis

- Search competitor @handle: check their top performing organics
- Which videos have most views/shares?
- Comment section: what do people love/complain about?
- Are they using Spark Ads (boosting organics)? Look for "Sponsored" tag on their posts

### 3.3 Hashtag research

Search these in TikTok app (not just web) for your category:
- #[product] — direct
- #[problem the product solves]
- #[niche trend] — FYP-adjacent
- Check: views / week (rising vs plateauing)
- Identify micro-niches (<500M views) with high engagement rate — easier to be seen

---

## Section 4 — Research Output

Deliver:
1. Audience test matrix: 4–6 Ad Groups (interest, broad, custom, LAL)
2. Hook type shortlist: 3–5 hooks to test with rationale
3. Sound / format recommendations for first 30 days
4. Competitor creative breakdown: top 3 insights from Ad Library
5. Creative production brief: 3 video concepts (hook → body → CTA) based on research
6. 30-day creative roadmap: week-by-week new asset plan
"""
