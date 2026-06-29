"""
SEO Canon Rules — definitive checklist mirroring the Ads Canon pattern.
Each rule: ID | Severity | Area | Rule | Why it matters | Verify how
"""

SEO_CANON_RULES = [
    # ── P0 CRITICAL — fix before any optimisation ────────────────────────────
    {
        "id": "SEC-0001", "severity": "P0", "area": "Crawlability",
        "rule": "Googlebot not blocked in robots.txt",
        "why": "If Googlebot is disallowed, nothing ranks. All other SEO work is wasted.",
        "verify": "fetch robots.txt, check for 'Disallow: /' under User-agent: Googlebot or *",
    },
    {
        "id": "SEC-0002", "severity": "P0", "area": "Indexability",
        "rule": "Homepage and key landing pages are indexable (no noindex meta or header)",
        "why": "noindex on key pages removes them from search entirely.",
        "verify": "check <meta name='robots'> and X-Robots-Tag HTTP header on homepage + top pages",
    },
    {
        "id": "SEC-0003", "severity": "P0", "area": "Technical",
        "rule": "HTTPS enabled and HSTS configured (max-age ≥ 31536000)",
        "why": "HTTP sites get Chrome security warnings; HTTPS is a confirmed ranking signal.",
        "verify": "check SSL cert validity, HSTS header in response headers",
    },
    {
        "id": "SEC-0004", "severity": "P0", "area": "Tracking",
        "rule": "Google Search Console verified and receiving data",
        "why": "Without GSC, you cannot diagnose indexing issues, penalties, or CTR problems.",
        "verify": "GSC → Coverage → check for errors and total indexed pages",
    },
    {
        "id": "SEC-0005", "severity": "P0", "area": "Tracking",
        "rule": "GA4 or analytics platform installed and tracking conversions",
        "why": "Cannot measure SEO ROI or organic conversion rate without analytics.",
        "verify": "check GTM/GA4 tag on site, confirm goal tracking in analytics",
    },
    {
        "id": "SEC-0006", "severity": "P0", "area": "Penalties",
        "rule": "No manual actions in Google Search Console",
        "why": "Manual action = Google penalty; site visibility drastically reduced.",
        "verify": "GSC → Security & Manual Actions → Manual Actions",
    },
    {
        "id": "SEC-0007", "severity": "P0", "area": "AI Search",
        "rule": "AI crawlers not blocked: GPTBot, ClaudeBot, PerplexityBot in robots.txt",
        "why": "Blocking AI crawlers prevents citations in ChatGPT, Claude, Perplexity — 2026 critical.",
        "verify": "fetch robots.txt, check User-agent: GPTBot / ClaudeBot / PerplexityBot entries",
    },
    {
        "id": "SEC-0008", "severity": "P0", "area": "Core Web Vitals",
        "rule": "INP (Interaction to Next Paint) < 200ms on mobile — PRIMARY signal 2026",
        "why": "INP elevated to primary ranking signal in March 2026. >500ms = likely ranking suppression.",
        "verify": "GSC → Core Web Vitals → Mobile; PageSpeed Insights field data",
    },

    # ── P1 IMPORTANT — fix within 1 week ────────────────────────────────────
    {
        "id": "SEC-0009", "severity": "P1", "area": "Core Web Vitals",
        "rule": "LCP (Largest Contentful Paint) < 2.0s on mobile",
        "why": "Primary performance ranking signal. >4s = likely penalty.",
        "verify": "PageSpeed Insights → Field Data → LCP",
    },
    {
        "id": "SEC-0010", "severity": "P1", "area": "Core Web Vitals",
        "rule": "CLS (Cumulative Layout Shift) < 0.1",
        "why": "Measures visual stability. >0.25 = poor UX signal to Google.",
        "verify": "PageSpeed Insights → Field Data → CLS",
    },
    {
        "id": "SEC-0011", "severity": "P1", "area": "Structured Data",
        "rule": "Article schema with dateModified on all blog posts",
        "why": "AI systems use dateModified for freshness signals. Missing = treated as stale.",
        "verify": "Rich Results Test on blog post URL; check for dateModified field",
    },
    {
        "id": "SEC-0012", "severity": "P1", "area": "Structured Data",
        "rule": "Organization schema with sameAs (Wikidata QID) on homepage",
        "why": "Wikidata sameAs disambiguates entity for Google Knowledge Graph and AI citation.",
        "verify": "check homepage JSON-LD for Organization type + sameAs array with wikidata.org URL",
    },
    {
        "id": "SEC-0013", "severity": "P1", "area": "On-Page",
        "rule": "Each page has unique, non-truncated title tag (≤60 chars)",
        "why": "Duplicate or truncated titles hurt CTR and send weak relevance signals.",
        "verify": "Screaming Frog or GSC → Search Results → filter by page type",
    },
    {
        "id": "SEC-0014", "severity": "P1", "area": "On-Page",
        "rule": "One H1 per page, matching primary keyword intent",
        "why": "Multiple H1s confuse crawlers about page topic; missing H1 = weak relevance signal.",
        "verify": "crawl check H1 count per URL",
    },
    {
        "id": "SEC-0015", "severity": "P1", "area": "Content",
        "rule": "No keyword cannibalization: two+ pages targeting same query",
        "why": "Splits authority; neither page reaches full potential. Google has to pick one.",
        "verify": "GSC → Search Results → filter by query → check how many pages appear",
    },
    {
        "id": "SEC-0016", "severity": "P1", "area": "Crawlability",
        "rule": "XML sitemap present, submitted to GSC, and auto-updated on publish",
        "why": "Without sitemap, Google may miss new pages for weeks.",
        "verify": "check /sitemap.xml existence; GSC → Sitemaps → check submission status",
    },
    {
        "id": "SEC-0017", "severity": "P1", "area": "E-E-A-T",
        "rule": "Named author with credentials visible on all blog/article content",
        "why": "Experience is #1 weighted E-E-A-T signal since March 2026. Anonymous content scores lower.",
        "verify": "check byline + author bio link on article pages",
    },
    {
        "id": "SEC-0018", "severity": "P1", "area": "Content",
        "rule": "Blog posts ≥1,500 words; product/service pages ≥500 words",
        "why": "Thin content is flagged by Helpful Content System. Below threshold = ranking suppression.",
        "verify": "crawl + word count analysis on key pages",
    },
    {
        "id": "SEC-0019", "severity": "P1", "area": "Structured Data",
        "rule": "No deprecated schema types: HowTo (removed Sep 2023), FAQPage (restricted Aug 2023)",
        "why": "Deprecated types no longer generate rich results; wastes implementation effort.",
        "verify": "Rich Results Test → check for HowTo rich result warnings",
    },
    {
        "id": "SEC-0020", "severity": "P1", "area": "AI Search",
        "rule": "llms.txt file present and correctly configured",
        "why": "Guides AI crawlers for citation accuracy. Sites with llms.txt get better AI attribution.",
        "verify": "fetch /llms.txt; check for GPTBot, ClaudeBot, PerplexityBot entries",
    },
    {
        "id": "SEC-0021", "severity": "P1", "area": "Content",
        "rule": "Answer-first format: 40–60 word direct answer at top of each H2 section",
        "why": "83% of AI citations come from content with direct answer-first format.",
        "verify": "read first paragraph under each H2 — does it start with the answer?",
    },
    {
        "id": "SEC-0022", "severity": "P1", "area": "Internal Linking",
        "rule": "Key conversion pages within 3 clicks from homepage",
        "why": "Deeper pages get less crawl budget and PageRank distribution.",
        "verify": "crawl depth report — flag pages at depth >3",
    },
    {
        "id": "SEC-0023", "severity": "P1", "area": "Images",
        "rule": "All images have descriptive alt text; WebP/AVIF format used",
        "why": "Alt text = accessibility + image search signal. WebP = 30% smaller = better LCP.",
        "verify": "crawl for missing alt text; check image format in page source",
    },

    # ── P2 HYGIENE — weekly/monthly cycle ───────────────────────────────────
    {
        "id": "SEC-0024", "severity": "P2", "area": "Content",
        "rule": "Content updated within 12 months for key pages (freshness signal for AI)",
        "why": "83% of AI citations come from content <12 months old. Stale = invisible to AI.",
        "verify": "check dateModified in schema + visible 'last updated' date on page",
    },
    {
        "id": "SEC-0025", "severity": "P2", "area": "Security",
        "rule": "Security headers present: CSP, X-Frame-Options, Referrer-Policy",
        "why": "Not a direct ranking factor but signals trustworthiness; affects E-E-A-T scoring.",
        "verify": "check response headers via securityheaders.com or curl -I",
    },
    {
        "id": "SEC-0026", "severity": "P2", "area": "Technical",
        "rule": "IndexNow protocol implemented (instant URL submission to Bing/Yandex)",
        "why": "Faster indexing on non-Google engines; increasingly relevant as AI search grows.",
        "verify": "check for IndexNow key at /indexnow.txt or in robots.txt",
    },
    {
        "id": "SEC-0027", "severity": "P2", "area": "On-Page",
        "rule": "Meta descriptions ≤160 chars on all key pages (unique per page)",
        "why": "Duplicate meta descriptions reduce CTR; truncation wastes the CTA.",
        "verify": "crawl for duplicate/missing/truncated meta descriptions",
    },
    {
        "id": "SEC-0028", "severity": "P2", "area": "Structured Data",
        "rule": "FAQPage schema on pages with genuine Q&A content",
        "why": "FAQPage gives 3.2× higher AI Overview probability. Only use on genuine Q&A.",
        "verify": "Rich Results Test; confirm schema matches visible Q&A content",
    },
    {
        "id": "SEC-0029", "severity": "P2", "area": "Backlinks",
        "rule": "Anchor text profile: <5% exact-match, 40-60% branded/URL",
        "why": "Over-optimized anchor text (>15% exact-match) triggers Penguin-era filters.",
        "verify": "Ahrefs/Semrush → Anchors report",
    },
    {
        "id": "SEC-0030", "severity": "P2", "area": "Mobile",
        "rule": "No intrusive interstitials on mobile (pop-ups blocking content)",
        "why": "Google applies mobile interstitial penalty since 2017. Confirmed ongoing.",
        "verify": "mobile preview check; look for immediate pop-ups on page load",
    },
]

P0_RULES = [r for r in SEO_CANON_RULES if r["severity"] == "P0"]
P1_RULES = [r for r in SEO_CANON_RULES if r["severity"] == "P1"]
P2_RULES = [r for r in SEO_CANON_RULES if r["severity"] == "P2"]
