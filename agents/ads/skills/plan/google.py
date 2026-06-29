from typing import Any, Dict
from ..benchmarks import GOOGLE


def build_google_prompt(payload: Dict[str, Any]) -> str:
    product       = payload.get("product", "product")
    budget        = payload.get("budget", "not specified")
    audience      = payload.get("audience", {})
    goal          = payload.get("goal", "conversions")
    campaign_type = payload.get("campaign_type", "")
    account_type  = payload.get("account_type", "").lower()

    audience_lines = []
    if audience.get("age"):      audience_lines.append(f"age: {audience['age']}")
    if audience.get("location"): audience_lines.append(f"geo: {audience['location']}")
    if audience.get("interest"): audience_lines.append(f"interests: {audience['interest']}")
    audience_text = ", ".join(audience_lines) if audience_lines else "broad audience"

    if campaign_type:
        campaign_hint = f"\nCampaign type: {campaign_type}"
    else:
        campaign_hint = """
Choose the optimal campaign type:
- Search (RSA) — intent-based, keywords, 15 headlines / 4 descriptions
- Performance Max — AI-assembled from Asset Groups, all Google networks
- Shopping — product feed via Google Merchant Center (ecom only)
- Display — banners, remarketing, look-alike
- YouTube / Demand Gen — video, awareness + consideration
- App — installs and in-app events"""

    is_leadgen = any(x in account_type for x in ("lead", "b2b", "saas", "service"))
    is_ecom    = any(x in account_type for x in ("ecom", "shop", "retail", "product"))

    # ── Lead-gen / B2B specific section ──────────────────────────────────────
    leadgen_section = ""
    if is_leadgen:
        leadgen_section = f"""

━━ B2B / LEAD-GEN SPECIFIC ━━

CONVERSION SETUP (critical — do this before any optimisation):
- Primary conversion: form fill OR demo request (whichever occurs ≥30×/month)
- Secondary conversions: pricing page visit, contact page view (for Smart Bidding data if form volume is low)
- Offline conversion import: GCLID capture required in form → weekly CRM export of MQL/SQL → upload to Google Ads
  → Smart Bidding should optimise on QUALIFIED LEADS, not raw form fills (GAC-0036)
- Enhanced Conversions for Leads: hash email/phone with conversion tag for better match rate (GAC-0035)

BIDDING STRATEGY FOR LEAD-GEN:
  <30 qualified leads/month   → Maximize Clicks (CPC cap) while building conversion history
  30-50 qualified leads/month → tCPA on form fill; switch to qualified-lead import when available
  >50 qualified leads/month   → tCPA on qualified lead (MQL/SQL) imported from CRM
  Value-based available       → assign values (form=1, MQL=10, SQL=50) + Maximize Conversion Value

KEYWORD STRATEGY FOR B2B:
- BOFU: [your product] + price/cost/demo/trial/alternative (highest intent, highest CPC — prioritise)
- MOFU: [problem you solve] + software/tool/platform/solution
- TOFU: [industry pain point] + how to / best way to / guide (informational, lower CPC, longer conversion cycle)
- Negative: job/careers/salary, DIY/template, competitor brand (unless conquest)
- B2B decision cycle: 30-90 days typical — budget for multi-touch attribution window

AUDIENCE LAYERS (observation mode first, then bid adjustment):
- Customer Match: upload CRM (prospects, customers, lost deals) → exclude existing customers from acquisition
- In-Market B2B: Business & Industrial, Business Technology, relevant industry segments → +15-25% bid if CPA favourable
- RLSA: all site visitors 90d (+20%), pricing/demo page visitors 30d (+40%), repeat visitors (+50%)
- Exclude: current customers list from all acquisition campaigns

B2B BENCHMARKS (2026, search):
  CPC range:    ${GOOGLE['cpc_search'][0]}–${GOOGLE['cpc_search'][1]} standard / ${GOOGLE['cpc_search_high'][0]}–${GOOGLE['cpc_search_high'][1]} competitive (legal/finance/SaaS)
  CTR target:   ≥{GOOGLE['ctr_search_good']}% for Search
  CVR (lead-gen): {GOOGLE['cvr_leadgen'][0]}–{GOOGLE['cvr_leadgen'][1]}% (form fill on landing page)
  MQL rate:     ≥15% of form fills should become marketing-qualified (from CRM data)
  Quality Score: ≥{GOOGLE['quality_score_good']} — low QS inflates CPC by 20-50%
  Learning phase: ≥{GOOGLE['learning_conv_min']} conversions in {GOOGLE['learning_days']} days to exit learning
"""

    # ── Ecom specific section ─────────────────────────────────────────────────
    ecom_section = ""
    if is_ecom:
        ecom_section = f"""

━━ E-COMMERCE SPECIFIC ━━

CAMPAIGN PRIORITY ORDER:
1. Brand (Search) — protect brand terms, lowest CPC, highest CVR → always on
2. Shopping / PMax — product-intent queries, highest purchase volume
3. Remarketing (Display/Search RLSA) — recovering cart abandoners
4. Non-brand Search — category keywords, harder to compete but scalable

SHOPPING / PERFORMANCE MAX SETUP:
- Google Merchant Center: feed must have <5% disapproval rate (title, price, availability)
- Asset Groups (PMax): separate by product category / margin tier for budget control
- Brand exclusion in PMax: add brand terms as negative keywords to prevent brand cannibalisation
- Audience signals: Customer Match buyers + high-intent site visitors + similar audiences

ECOM BENCHMARKS (2026):
  CVR ecom:     {GOOGLE['cvr_ecom'][0]}–{GOOGLE['cvr_ecom'][1]}%
  ROAS target:  ≥{GOOGLE['roas_ecom_target']}x
  IS target:    ≥{GOOGLE['impression_share_target']}%
"""

    return f"""Platform: Google Ads
Product: {product}
Budget: ${budget}/mo
Goal: {goal}
Audience: {audience_text}
Account type: {account_type or 'not specified'}{campaign_hint}

Task — deliver a concrete campaign launch plan:

1. Campaign type and structure (campaigns → ad groups → ads)

2. Bidding strategy:
   - Conversions: Target CPA / Target ROAS / Maximize Conversions
   - Traffic: Maximize Clicks / Target Impression Share
   - Specify starting values and Smart Bidding data requirements

3. Targeting:
   - Keywords: match types (broad / phrase / exact), negative keyword list
   - Audiences: in-market, affinity, remarketing, customer match, lookalike
   - Demographics and device adjustments

4. Ads:
   - RSA: 15 headlines (≤30 chars each), 4 descriptions (≤90 chars each)
   - Assets: sitelinks, callouts, structured snippets, promotion
   - Pinning recommendations for headline 1 and CTA

5. KPIs and benchmarks:
   - CTR target: Search ≥{GOOGLE['ctr_search_good']}%
   - Quality Score target: ≥{GOOGLE['quality_score_good']}
   - Impression Share target: ≥{GOOGLE['impression_share_target']}%
   - CPA / ROAS: state account-specific targets

6. First 2 weeks — Smart Bidding learning phase:
   - Minimum {GOOGLE['learning_conv_min']} conversions needed to exit learning
   - Do not change bids, budgets, or targeting during learning
   - Monitor conversion tracking first (auto-tagging ON, primary conversion active)
{leadgen_section}{ecom_section}"""
