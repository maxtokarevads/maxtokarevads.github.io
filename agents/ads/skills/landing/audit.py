from typing import Any, Dict


def build_landing_audit_prompt(payload: Dict[str, Any]) -> str:
    product   = payload.get("product", "product")
    url       = payload.get("url", "")
    platform  = payload.get("platform", "")
    goal      = payload.get("goal", "purchase")
    traffic   = payload.get("traffic_source", "")
    device    = payload.get("device", "mobile")
    metrics   = payload.get("metrics", {})
    context   = payload.get("context", "")

    url_line      = f"\nLanding URL: {url}" if url else ""
    platform_line = f"\nAd platform: {platform}" if platform else ""
    traffic_line  = f"\nTraffic source: {traffic}" if traffic else ""
    context_line  = f"\nContext: {context}" if context else ""
    metrics_block = ""
    if metrics:
        metrics_block = "\nCurrent metrics:\n" + "\n".join(f"  {k}: {v}" for k, v in metrics.items())

    return f"""## Landing Page CRO Audit
Product: {product}{url_line}{platform_line}
Goal: {goal}
Primary device: {device}{traffic_line}{metrics_block}{context_line}

Run a complete CRO (Conversion Rate Optimisation) audit across all six layers below.
For each failing item output a row in the Fixlist. End with an A/B test shortlist.

---

## Layer 1 — Page Speed & Core Web Vitals

Benchmarks:
- LCP (Largest Contentful Paint): ≤2.5 s good / 2.5–4 s needs improvement / >4 s poor
- FID / INP (Interaction to Next Paint): ≤200 ms good / >500 ms poor
- CLS (Cumulative Layout Shift): ≤0.1 good / >0.25 poor
- Time to First Byte (TTFB): ≤600 ms good
- Total page weight: ≤2 MB mobile / ≤5 MB desktop

What to check:
- Run PageSpeed Insights (Google) + GTmetrix
- Identify heaviest resources: uncompressed images, render-blocking JS, large fonts
- Check server response time and CDN configuration
- Verify lazy-loading on below-fold images

Fixes if failing:
- Convert images to WebP/AVIF, add width/height attributes
- Defer non-critical JS, inline critical CSS
- Enable Gzip / Brotli compression
- Move to CDN-served static assets

---

## Layer 2 — Above-the-Fold (First Screen)

The first screen must answer 3 questions in <5 seconds:
  1. What is this? (product/service clarity)
  2. Why should I care? (primary value proposition)
  3. What do I do next? (CTA)

Checklist:
- [ ] Hero headline: clear, specific, matches ad copy (message match)
- [ ] Sub-headline: expands on benefit, not a repeat of headline
- [ ] Hero image/video: shows product in use or outcome (not generic stock)
- [ ] Primary CTA: visible without scrolling on mobile (375px viewport)
- [ ] CTA button: high contrast, verb-led ("Get My Free Trial" not "Submit")
- [ ] No interstitials or pop-ups blocking content on load
- [ ] Social proof element: number of customers, rating, logo strip
- [ ] Message match: landing page headline ≈ ad headline (score 1–5; target ≥4)

---

## Layer 3 — Mobile UX

Primary device assumption: {device}

Checklist:
- [ ] Tap targets ≥ 48×48 px (iOS/Android standard)
- [ ] Font size ≥ 16px for body text (no pinching required)
- [ ] Horizontal scroll: none
- [ ] Forms: correct input type (tel, email, number) to trigger native keyboard
- [ ] Sticky CTA bar on mobile (appears after scroll past hero)
- [ ] Click-to-call button for phone leads
- [ ] No hover-only interactive elements
- [ ] Checkout flow ≤4 taps from landing to order confirmation (ecom)

---

## Layer 4 — Form Friction (Lead-gen) / Checkout Friction (Ecom)

### For lead-gen forms:
- Field count: ≤4 fields → benchmark CVR 3–5%; each extra field -11% CVR avg
- Required fields rule: collect only what's needed for first step
- Progress indicator: show step X of Y for multi-step forms
- Inline validation: flag errors before submit, not after
- Privacy note: "We never share your data" near email field (+8% trust)
- GDPR/CCPA: checkbox required where applicable

### For ecom checkout:
- Guest checkout option (mandatory — forced registration kills 35% of carts)
- Address autocomplete (Google Places API)
- Saved payment methods / Apple Pay / Google Pay
- Order summary visible at checkout
- Trust badges near pay button: SSL lock, accepted cards, return policy
- Abandoned cart trigger: set up email/SMS within 30 min of abandon

---

## Layer 5 — Trust Signals

Each trust element below adds roughly 5–15% CVR lift when absent:
- [ ] Customer reviews/testimonials (specific, named, with photo or company)
- [ ] Star rating aggregate (e.g., 4.8/5 from 1,240 reviews)
- [ ] Logos: "As seen in" press logos or client logos
- [ ] Security badges: SSL, payment logos, data-safe certification
- [ ] Money-back guarantee / free returns (explicit, near CTA)
- [ ] Company address, phone, live chat (reduces bounce for first-time visitors)
- [ ] Case study or before/after (high-ticket products: ≥$200)
- [ ] UGC photos or video testimonials (ecom: reduces return rate perception)

---

## Layer 6 — Copy Clarity

Evaluate each section against the AIDA framework:
  A — Attention: does the headline stop the scroll?
  I — Interest: does the sub-headline explain WHY this matters?
  D — Desire: do benefits (not features) dominate the copy?
  A — Action: is the CTA specific, low-friction, and repeated?

Common copy problems:
- Feature-led instead of benefit-led ("256GB storage" → "carry every photo you'll ever take")
- Passive voice ("is designed to help") → active ("helps you ship faster")
- Vague superlatives ("best", "leading", "top-quality") — replace with specifics
- Jargon the target customer wouldn't use
- Headline/body mismatch: headline makes a claim that body doesn't support

---

## Fixlist (Canon format)

Output a prioritised table for all issues found:

| Severity | Layer | Issue | Fix | Expected lift | Verify after |
|----------|-------|-------|-----|---------------|--------------|
| P0 = conversion blocker, P1 = significant lift, P2 = incremental improvement |

---

## A/B Test Shortlist

Rank the top 3 highest-impact tests for this landing page:
| Test # | Element | Control | Variant | Hypothesis | KPI | Sample needed |

Sample size guidance:
- Baseline CVR 1%: need ~30,000 sessions/variant for 20% MDE at 95% confidence
- Baseline CVR 2%: need ~15,000 sessions/variant
- Baseline CVR 5%: need ~6,000 sessions/variant
- Use a lower-funnel event (Add to Cart) if purchase volume is too low

---

## Done Criteria
- [ ] All 6 layers evaluated (note "No data" if URL not accessible)
- [ ] Fixlist: P0 items first, each row has Fix + Expected lift
- [ ] A/B test shortlist: 3 tests with sample size estimate
- [ ] Mobile CTA visibility confirmed (375px viewport)
"""
