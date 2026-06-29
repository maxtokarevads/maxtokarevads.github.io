from typing import Any, Dict, List


def build_technical_prompt(payload: Dict[str, Any]) -> str:
    site     = payload.get("site", payload.get("url", "client website"))
    industry = payload.get("industry", "")
    issues   = payload.get("issues", [])
    context  = payload.get("context", "")

    industry_line = f"\nIndustry type: {industry}" if industry else ""
    issues_text   = "\n".join(f"- {i}" for i in issues) if issues else ""
    issues_block  = f"\nKnown issues:\n{issues_text}" if issues_text else ""
    context_block = f"\nContext: {context}" if context else ""

    return f"""Platform: SEO — Technical Audit
Site: {site}{industry_line}{issues_block}{context_block}

## Reference Examples

Example A — JavaScript rendering failure:
Symptom: Pages rank well in GSC but content not indexed
Root cause: Content rendered client-side; Googlebot sees blank page
Fix: Implement SSR or pre-rendering; verify with "Inspect URL" in GSC
Priority: CRITICAL

Example B — Core Web Vitals INP failure (2026 primary signal):
Symptom: INP >500ms, mobile rankings drop after March 2026 update
Root cause: Heavy JS event listeners blocking interaction response
Fix: Defer non-critical JS, use `scheduler.yield()`, reduce main thread blocking
Priority: HIGH

Example C — Security headers missing:
Symptom: Security scan shows missing CSP, X-Frame-Options
Root cause: No server-side headers configured
Fix: Add CSP, X-Frame-Options: SAMEORIGIN, Referrer-Policy: strict-origin-when-cross-origin
Note: Not a direct ranking factor but signals trustworthiness to E-E-A-T

Conduct a complete technical SEO audit across all 9 categories:

1. CRAWLABILITY
   — robots.txt: any important pages disallowed? AI crawlers (GPTBot, ClaudeBot, PerplexityBot) blocked?
   — Crawl budget: are low-value pages (search, filters, parameters) consuming crawl budget?
   — Internal link depth: key pages within 3 clicks from homepage?
   — llms.txt: present? Guides AI crawlers for citation accuracy.

2. INDEXABILITY
   — Noindex tags: any important pages accidentally noindexed?
   — Canonical tags: self-referencing canonicals on all pages? No conflicting signals?
   — Pagination: rel="next/prev" or noindex on paginated pages?
   — Duplicate content: parameter-based duplicates causing index bloat?

3. SECURITY HEADERS
   — CSP (Content-Security-Policy): configured?
   — X-Frame-Options: SAMEORIGIN or DENY?
   — Referrer-Policy: strict-origin-when-cross-origin?
   — HTTPS: HSTS configured with max-age ≥1 year?

4. URL STRUCTURE
   — Clean, keyword-rich URLs without parameters?
   — Consistent URL format (trailing slash or not)?
   — URL length ≤100 characters?
   — No session IDs or tracking parameters in indexed URLs?

5. MOBILE OPTIMIZATION
   — Responsive design or separate mobile site?
   — Viewport meta tag present?
   — Tap targets ≥48×48px?
   — No intrusive interstitials on mobile?

6. CORE WEB VITALS (2026 primary ranking signals)
   — LCP (Largest Contentful Paint): target <2.0s
   — INP (Interaction to Next Paint): target <200ms ← ELEVATED TO PRIMARY SIGNAL 2026
   — CLS (Cumulative Layout Shift): target <0.1
   — Field data (Chrome UX Report) vs lab data (Lighthouse): which is failing?

7. STRUCTURED DATA
   — Schema types present: which ones? Valid JSON-LD?
   — Missing opportunities: FAQPage, HowTo, Product, LocalBusiness, Article?
   — Deprecated types: HowTo (removed Sep 2023), FAQPage restricted (Aug 2023)?
   — AggregateRating: implemented for reviews?

8. JAVASCRIPT RENDERING
   — Is critical content visible without JS?
   — SSR or CSR? What does Googlebot see?
   — Lazy-loaded images: do they use loading="lazy" with visible-above-fold fallback?
   — Any resources blocked to Googlebot in robots.txt?

9. INDEXNOW
   — IndexNow protocol implemented? (instant URL submission to Bing/Yandex on publish)
   — XML sitemap: auto-updated on new content? Submitted to GSC?
   — sitemap.xml: <50,000 URLs per file? Split if larger?

For each category, output:
- Status: ✅ Pass / ⚠️ Warning / ❌ Critical
- Severity: Critical (blocks indexing) | High (fix within 1 week) | Medium (1 month) | Low (backlog)
- Issue found
- Specific fix with implementation detail
- Verification method

10. SEO HEALTH SCORE
    Calculate weighted score (0–100):
    Technical: 22% | On-Page signals observed: 20% | Performance: 10% | Schema: 10%
    Report: X/100 — [Poor <40 | Needs Work 40–60 | Good 60–80 | Excellent >80]

11. CONFIDENCE ASSESSMENT
    - Confidence: High (full crawl data) / Medium (limited data) / Low (assumptions only)
    - What additional data would sharpen this audit (GSC access, crawl report, etc.)
    - Key assumptions made
"""
