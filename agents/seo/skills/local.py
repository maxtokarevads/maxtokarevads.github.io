from typing import Any, Dict, List


def build_local_prompt(payload: Dict[str, Any]) -> str:
    site        = payload.get("site", "client website")
    business    = payload.get("business", payload.get("product", ""))
    location    = payload.get("location", payload.get("market", ""))
    competitors = payload.get("competitors", [])
    context     = payload.get("context", "")

    biz_line  = f"\nBusiness: {business}" if business else ""
    loc_line  = f"\nLocation / Market: {location}" if location else ""
    comp_text = ", ".join(competitors) if competitors else ""
    comp_line = f"\nLocal competitors: {comp_text}" if comp_text else ""
    ctx_line  = f"\nContext: {context}" if context else ""

    return f"""Platform: SEO — Local SEO Audit
Site: {site}{biz_line}{loc_line}{comp_line}{ctx_line}

## Reference Examples

Example A — GBP completeness gap:
Symptom: Not appearing in map pack for "[service] near me" queries
Root cause: GBP profile 60% complete — missing hours, services, photos, description
Fix: Complete all GBP fields, add 10+ photos, get 20+ reviews with responses
Expected: Map pack entry within 60–90 days
Confidence: High

Example B — NAP inconsistency (EDGE CASE):
Symptom: Local rankings fluctuate; citation audit shows conflicting addresses
Root cause: Old address still live on 15+ directory sites from previous location
Fix: Update all citations with Yext or manual outreach; priority: Yelp, YP, BBB, Apple Maps
Confidence: High — NAP inconsistency is confirmed local ranking suppressant

Example C — Review velocity drop:
Symptom: Map pack ranking dropped from #2 to #5 over 3 months
Root cause: Review velocity slowed (2 reviews last 6 months); competitor accelerated (30 reviews)
Fix: Review request automation post-purchase/service; target 2–4 reviews/month minimum
Confidence: Medium (confirm via competitor profile check)

Conduct a complete Local SEO audit:

1. GOOGLE BUSINESS PROFILE (GBP)
   — Profile completeness score (estimate 0–100%):
     ✓ Business name (exact match to signage)
     ✓ Address (precise, matches website)
     ✓ Phone number (local number preferred)
     ✓ Website URL
     ✓ Business hours (including holiday hours)
     ✓ Business category (primary + secondary)
     ✓ Services/products listed
     ✓ Business description (750 chars, keyword-rich)
     ✓ Photos: interior, exterior, team, products (min 10)
     ✓ Q&A section: pre-populate with common questions
   — GBP health: any suspensions, violations, or flags?
   — Posts: active GBP posts? Frequency recommendation?

2. NAP CONSISTENCY
   — Name, Address, Phone consistent across:
     • Website (header/footer/contact page)
     • Google Business Profile
     • Top 10 citation sources (Yelp, YP, BBB, Apple Maps, Bing Places, Facebook, TripAdvisor)
   — Any old addresses or phone numbers live on citation sites?
   — Format consistency: "St" vs "Street", "Suite" vs "Ste"?

3. CITATIONS & DIRECTORIES
   — Tier 1 citations present: Yelp, YP, BBB, Manta, Foursquare, Apple Maps, Bing Places
   — Industry-specific directories: which ones relevant for this business type?
   — Total citation count vs local competitors?
   — Any toxic/spam citations to disavow?

4. REVIEW PROFILE
   — Total reviews: count + rating (Google, Yelp, industry platforms)
   — Review velocity: recent reviews per month? Trending up/down?
   — Response rate: are owner responses present? Speed?
   — Sentiment: common positive/negative themes
   — Review gaps vs competitors: how many reviews do top 3 map pack competitors have?

5. ON-PAGE LOCAL SIGNALS
   — City/region in title tags and H1 on key pages?
   — LocalBusiness schema with correct address, phone, geo coordinates?
   — Embedded Google Map on Contact page?
   — Location-specific landing pages for multiple locations?
   — Content mentions local landmarks, neighborhoods, service areas?

6. MAP PACK RANKING FACTORS
   — Primary category match to search query?
   — Review count and rating vs map pack competitors?
   — Proximity to searcher (uncontrollable) vs prominence (controllable)
   — Domain authority and local backlinks?
   — Engagement signals: clicks, calls, direction requests from GBP?

7. LOCAL LINK BUILDING
   — Backlinks from local news sites, chambers of commerce, local blogs?
   — Sponsor local events → citation + link?
   — Partner businesses with reciprocal local links?

8. MULTI-LOCATION STRATEGY (if applicable)
   — Separate GBP per location?
   — Location-specific landing pages with unique content?
   — Consistent naming convention: [Business] — [City]?

9. ACTION PLAN
   Format: Priority | Action | Timeline | Expected impact
   — Week 1: GBP completeness, NAP fixes
   — Month 1: Citation building, review velocity
   — Quarter 1: Local content, local links

10. CONFIDENCE ASSESSMENT
    - Confidence per finding: High / Medium / Low
    - Access needed for deeper audit: GBP dashboard, review platform analytics
    - Key assumptions made
"""
