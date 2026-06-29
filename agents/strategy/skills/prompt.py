from typing import Any, Dict


SUPPORTED_MODES = [
    "general",      # full marketing strategy (default)
    "gtm",          # go-to-market launch plan
    "positioning",  # brand positioning & messaging architecture
    "channel_mix",  # channel selection & budget allocation
    "kpi",          # KPI framework & measurement plan
    "audit",        # Canon strategy audit with P0/P1/P2 gating
]


# ── Shared helpers ────────────────────────────────────────────────────────────

def _base_context(payload: Dict[str, Any]) -> str:
    goal      = payload.get("goal", payload.get("business", "business growth"))
    product   = payload.get("product", "")
    industry  = payload.get("industry", "")
    usp       = payload.get("usp", "")
    budget    = payload.get("budget", "")
    audience  = payload.get("audience", {})
    timeline  = payload.get("timeline", "3 months")

    audience_parts = [f"{k}: {v}" for k, v in audience.items() if v]
    audience_text  = ", ".join(audience_parts) if audience_parts else ""

    lines = [f"Goal: {goal}", f"Timeline: {timeline}"]
    if product:   lines.append(f"Product: {product}")
    if industry:  lines.append(f"Industry: {industry}")
    if usp:       lines.append(f"USP: {usp}")
    if budget:    lines.append(f"Budget: ${budget}/mo")
    if audience_text: lines.append(f"Audience: {audience_text}")
    return "\n".join(lines)


_INDUSTRY_BENCHMARKS = {
    "saas":    "SaaS: CAC:LTV ≥ 1:3, MRR growth ≥10%/mo, churn <2%/mo, trial-to-paid ≥15%",
    "ecom":    "E-commerce: ROAS ≥ 3x, returning customer rate ≥30%, AOV growth target",
    "leadgen": "Lead Gen: CPL by niche, MQL-to-SQL ≥20%, sales cycle <30 days",
    "app":     "App: CPI, DAU/MAU ≥20%, D1/D7/D30 retention, LTV > CPI × 3",
    "local":   "Local: GBP rank top-3, review velocity ≥4/mo, CAC < 1 month LTV",
    "b2b":     "B2B: pipeline velocity, win rate ≥20%, ACV growth, NRR >100%",
}


def _benchmarks_line(industry: str) -> str:
    b = _INDUSTRY_BENCHMARKS.get(industry.lower().strip(), "")
    return f"\nIndustry benchmarks: {b}" if b else ""


# ── Mode builders ─────────────────────────────────────────────────────────────

_STRATEGY_EXAMPLE = """
## Reference Example (use as quality standard, not a template to copy)

Situation: B2B SaaS HR tool, $8k/mo budget, 3-month timeline, ICP = HR managers at 50-200 person companies.
Strong output example:
- Positioning: "The only HR tool that reduces onboarding time by 40% in the first week" (owned claim, measurable)
- Channel mix: LinkedIn Ads 40% (ICP density), SEO/Content 30% (long-cycle buyers research), Email nurture 20%, G2/review 10%
- Month 1 NSM target: 15 qualified demo requests at CPL ≤$320
- Kill signal: if CPL >$500 after 6 weeks → pause LinkedIn, test Google Search
Edge case to avoid: spreading $8k across 5+ channels — algorithm can't learn, no channel reaches minimum threshold.
"""

_GTM_EXAMPLE = """
## Reference Example (use as quality standard, not a template to copy)

Situation: B2C fitness app launching in Germany, €15k launch budget, no prior audience.
Strong output example:
- GTM motion: marketing-led (no sales team, app-led conversion)
- ICP: women 28-42, urban, gym members, trigger = New Year or post-pregnancy
- First channel: Meta (highest ICP density for this segment at lowest CPM in DE)
- Soft launch weeks 1-2: €2k Meta budget to 2 lookalike seeds, target CPI ≤€3.50
- Hard launch month 2: add TikTok Creator Marketplace (UGC lifts CVR 2.4x for this demo), PR pitch to fitness media
- 30-day kill signal: if D7 retention <20% → pause acquisition, fix onboarding before scaling spend
"""

_POSITIONING_EXAMPLE = """
## Reference Example (use as quality standard, not a template to copy)

Situation: Legal tech startup, contract review software, competing vs DocuSign and Ironclad.
Strong positioning output:
- White space: incumbents focus on signing speed; no one owns "legal risk prevention before signing"
- Positioning: "The contract review tool that catches the risks your lawyers miss" (vs DocuSign = signing, vs Ironclad = workflow)
- Primary claim: "Reduces contract risk exposure by 73% in 48-hour legal review cycles"
- Proof point: ISO 27001 certified + 340 contracts reviewed in pilot, 0 disputes in 18 months
- Could a competitor say this? DocuSign = no (they don't do review). Ironclad = not yet. ✓ Differentiating.
- Messaging anti-pattern to avoid: "Fast, easy, affordable" — every competitor says this, owns nothing.
"""

_CHANNEL_MIX_EXAMPLE = """
## Reference Example (use as quality standard, not a template to copy)

Situation: E-commerce skincare brand, $20k/mo budget, ROAS target 3x, mix review after 6 months.
Strong channel mix output:
- Meta (35%, $7k): primary acquisition — best ROAS at 3.8x, scale winner
- Google Shopping (25%, $5k): high-intent, ROAS 4.2x — under-invested, increase next month
- TikTok (20%, $4k): TOFU — Hook Rate 28%, CAC $42 — feed Meta LAL seeds
- Email/CRM (15%, $3k): retention — 40% of revenue from existing buyers, LTV lifts ROAS calc
- Influencer (5%, $1k): brand social proof, not measured by ROAS
- Where the next $1 goes: Google Shopping (highest marginal ROAS, not saturated)
- Kill threshold: if TikTok CPA >$65 at month-end → reallocate to Google
"""

_KPI_EXAMPLE = """
## Reference Example (use as quality standard, not a template to copy)

Situation: SaaS product, trial-to-paid conversion focus, Q3 OKR cycle.
Strong KPI framework output:
- NSM: Weekly Active Paying Users (WAPU) — predicts NRR and expansion revenue
- OKR: Objective: "Become the default tool for the team by end of Q3"
  KR1: Trial-to-paid rate ≥18% (currently 11%) — source: Stripe
  KR2: D30 retention ≥55% (currently 42%) — source: Mixpanel
  KR3: NPS ≥40 from paid users (currently 28) — source: Delighted
- Leading indicators (weekly): new trial signups, activation rate (feature used in 48h), support ticket volume
- P0 alert: if trial signups drop >25% WoW → check paid acquisition immediately (likely tracking or campaign issue)
- Attribution: first-touch for acquisition, last-touch for conversion — separate models, don't blend
"""


def build_strategy_prompt(payload: Dict[str, Any]) -> str:
    """General full marketing strategy (default mode)."""
    industry  = payload.get("industry", "")
    timeline  = payload.get("timeline", "3 months")
    resources = payload.get("resources", {})
    funnel    = payload.get("funnel_stage", "")

    resources_text = ", ".join(f"{k}: {v}" for k, v in resources.items()) if resources else "not specified"

    stage_hints = {
        "tofu": "TOFU — focus on awareness and reach; goal is brand recognition",
        "mofu": "MOFU — focus on engagement and consideration; goal is evaluation",
        "bofu": "BOFU — focus on conversion; goal is closing the deal",
    }
    stage_line = f"\nFunnel stage: {funnel.upper()} — {stage_hints[funnel.lower()]}" \
                 if funnel.lower() in stage_hints else ""

    return f"""Marketing Strategy
{_base_context(payload)}
Resources: {resources_text}{stage_line}{_benchmarks_line(industry)}
{_STRATEGY_EXAMPLE}

Develop a complete marketing plan across the following sections:

1. POSITIONING AND DIFFERENTIATION
   — Target segment: who exactly, their pains, jobs-to-be-done
   — Core message (value proposition): one sentence
   — Differentiation from competitors: 3 key distinctions
   — Tone of voice: how the brand sounds

2. CHANNEL MIX (with budget allocation)
   For each channel:
   — Channel | Funnel role | % of budget | Expected KPI
   Consider: Paid (Google/Meta/TikTok), SEO/content, email/CRM, partnerships, product-led

3. FUNNEL AND CUSTOMER JOURNEY
   — TOFU: how to drive awareness
   — MOFU: how to nurture and engage
   — BOFU: how to convert
   — Retention: how to keep and reactivate customers
   — Conversion metrics at each stage

4. KPIS AND SUCCESS METRICS
   — North Star Metric: one primary indicator
   — Leading indicators (weekly): what predicts the outcome
   — Lagging indicators (monthly): business result
   — Concrete targets for: {timeline}

5. BUDGET AND RESOURCES
   — Budget allocation by channel (if specified)
   — Hiring / tooling priorities
   — Build vs Buy vs Partner: what is done in-house vs outsourced

6. EXECUTION PLAN
   Format: Month | Action | Owner | KPI | Budget
   — Month 1: quick wins and baseline
   — Month 2–3: scaling winners
   — Next quarter: growth and optimisation

7. RISKS AND MITIGATION
   — Top 3 risks with probability and contingency plan
"""


def build_gtm_prompt(payload: Dict[str, Any]) -> str:
    """Go-to-market launch plan for a new product or market."""
    industry = payload.get("industry", "")
    market   = payload.get("market", payload.get("geo", ""))
    stage    = payload.get("stage", "launch")
    icp      = payload.get("icp", "")

    market_line = f"\nTarget market: {market}" if market else ""
    icp_line    = f"\nICP: {icp}" if icp else ""

    return f"""Go-To-Market Plan
{_base_context(payload)}{market_line}{icp_line}
Launch stage: {stage}{_benchmarks_line(industry)}
{_GTM_EXAMPLE}

Build a complete GTM launch plan:

1. ICP AND BUYER JOURNEY
   — ICP definition: company size, industry, role, pain, budget
   — Champion (feels the pain) vs economic buyer (approves spend)
   — Trigger event: what makes them start looking for a solution
   — Evaluation criteria: how they compare options
   — Decision timeline: how long the buying process takes

2. POSITIONING FOR LAUNCH
   — Category: are we creating a category or entering one?
   — Primary claim: what we want to own in the customer's mind
   — Proof points: 3 facts that make the claim credible
   — Launch message: one sentence a journalist could write about us

3. CHANNEL AND MOTION SELECTION
   — Primary GTM motion: PLG / sales-led / marketing-led / community-led
   — Rationale: why this motion fits the ICP and price point
   — First channel: where is the ICP density highest?
   — Channel sequencing: what channels to add in phases 2 and 3

4. LAUNCH SEQUENCE (90-day plan)
   Week 1–2: foundation (tracking, CRM, landing page, baseline)
   Week 3–4: soft launch (limited audience, collect feedback)
   Month 2: hard launch (full channel activation, PR if relevant)
   Month 3: optimise (kill losers, scale winners, document playbook)

5. ACTIVATION AND RETENTION
   — Onboarding: first 7 days experience to reach "aha moment"
   — Activation metric: what proves the customer sees value
   — Retention lever: what brings them back

6. SUCCESS CRITERIA
   — 30-day: [specific KPI]
   — 60-day: [specific KPI]
   — 90-day: [specific KPI]
   — Kill signal: what would trigger a pivot

7. RISKS
   — Top 3 launch risks with mitigation
   — Competitive response: what will incumbents do?
"""


def build_positioning_prompt(payload: Dict[str, Any]) -> str:
    """Brand positioning, messaging architecture, and differentiation."""
    competitors = payload.get("competitors", "")
    category    = payload.get("category", "")
    differentiator = payload.get("differentiator", "")
    industry    = payload.get("industry", "")

    comp_line   = f"\nMain competitors: {competitors}" if competitors else ""
    cat_line    = f"\nCategory: {category}" if category else ""
    diff_line   = f"\nKey differentiator to explore: {differentiator}" if differentiator else ""

    return f"""Brand Positioning Strategy
{_base_context(payload)}{comp_line}{cat_line}{diff_line}{_benchmarks_line(industry)}
{_POSITIONING_EXAMPLE}

Develop a complete positioning and messaging architecture:

1. MARKET MAP
   — Category definition: what game are we playing?
   — Key players: list 3–5 competitors, their positioning claim, and their weakness
   — White space: what position is unclaimed or under-served?
   — Trend tailwind: what market force makes this the right moment?

2. SEGMENTATION AND ICP
   — Segment the total market into 3–5 distinct customer groups
   — Score each: size × growth rate × our fit × willingness to pay
   — Recommended target segment and why

3. POSITIONING STATEMENT
   "For [target segment] who [pain/need],
   [Product] is the [category] that [primary benefit]
   unlike [alternative] because [proof point]."
   — Draft 3 variants with different differentiation axes
   — Recommended variant with rationale

4. MESSAGING ARCHITECTURE
   — Core claim (one sentence, own it completely)
   — Supporting pillars (3 messages that prove the claim)
   — Proof points per pillar (data, case studies, testimonials)
   — What we never say (messaging anti-patterns to avoid)

5. TONE OF VOICE
   — Brand personality: 3 adjectives
   — Communication style: formal / conversational / provocative
   — What we sound like vs what competitors sound like
   — Example rewrites: 3 before/after message examples

6. DIFFERENTIATION SUSTAINABILITY
   — Which differentiator is hardest for competitors to copy?
   — What would strengthen the moat over time?
   — Risk: could the differentiator become table stakes?
"""


def build_channel_mix_prompt(payload: Dict[str, Any]) -> str:
    """Channel selection, budget allocation, and media mix strategy."""
    budget      = payload.get("budget", "")
    funnel      = payload.get("funnel_stage", "full-funnel")
    industry    = payload.get("industry", "")
    current_channels = payload.get("current_channels", [])
    goal        = payload.get("goal", "growth")

    current_line = (
        f"\nCurrent active channels: {', '.join(current_channels)}"
        if current_channels else ""
    )

    return f"""Channel Mix Strategy
{_base_context(payload)}{current_line}
Funnel coverage: {funnel}{_benchmarks_line(industry)}
{_CHANNEL_MIX_EXAMPLE}

Build a complete channel allocation and media mix strategy:

1. CHANNEL AUDIT (if channels are active)
   — Per channel: current spend | ROAS/CPL | volume | saturation level
   — What's working (scale) vs what's not (cut or fix)
   — Marginal ROAS: where should the next $1 go?

2. RECOMMENDED CHANNEL MIX
   Table: Channel | Funnel stage | Monthly budget | % of total | Primary KPI | Target
   — TOFU channels (awareness): reach and CPM focus
   — MOFU channels (consideration): CTR and engagement focus
   — BOFU channels (conversion): CPA and ROAS focus
   — Retention channels (CRM/email): LTV and churn focus

3. SEQUENCING AND DEPENDENCIES
   — Which channels to activate first and why (ICP density + CPA probability)
   — Dependencies: e.g., retargeting requires TOFU volume first
   — Timeline to activate each new channel

4. MINIMUM VIABLE THRESHOLDS
   — Per channel: min budget to exit learning phase
   — Conversion volume needed for algorithm optimisation
   — When to pause a channel vs give it more time

5. ATTRIBUTION MODEL
   — Recommended model: first-touch / last-touch / data-driven / linear
   — How to measure contribution of TOFU channels to BOFU conversions
   — Cross-channel overlap: where do audiences overlap?

6. SCALING PLAYBOOK
   — Rule: what metrics trigger a budget increase?
   — Rule: what metrics trigger a budget cut?
   — New channel test protocol: how much, how long, what success looks like
"""


def build_kpi_prompt(payload: Dict[str, Any]) -> str:
    """KPI framework, OKR structure, and measurement plan."""
    industry   = payload.get("industry", "")
    timeline   = payload.get("timeline", "quarter")
    goal       = payload.get("goal", "growth")
    stage      = payload.get("company_stage", "growth")

    return f"""KPI Framework & Measurement Plan
{_base_context(payload)}
Company stage: {stage}{_benchmarks_line(industry)}
{_KPI_EXAMPLE}

Build a complete KPI framework:

1. NORTH STAR METRIC (NSM)
   — One metric that best captures the value delivered to customers
   — Why this metric (not another) is the NSM
   — Current baseline and target for {timeline}
   — Lagging indicators that the NSM predicts

2. KPI TREE (inputs → outputs)
   Revenue / NSM
     ├── Acquisition: Impressions → Clicks → Leads → SQLs → Customers
     │     └── Per metric: current, target, owner, review cadence
     ├── Conversion: Lead → MQL → SQL → Close (rates at each stage)
     └── Retention: Churn rate, NRR, LTV, reactivation rate

3. OKR STRUCTURE ({timeline})
   Objective: [ambitious qualitative goal]
   — KR1: [measurable, binary, 70% confidence]
   — KR2: [measurable, binary, 70% confidence]
   — KR3: [measurable, binary, 70% confidence]
   Rule: if all 3 KRs hit 100%, the objective was too easy

4. LEADING VS LAGGING INDICATORS
   — Weekly leading (predict the outcome): [list 5 specific metrics]
   — Monthly lagging (measure the result): [list 5 specific metrics]
   — What to do if leading indicators turn negative

5. REPORTING CADENCE
   — Daily: [what to check — anomaly detection only]
   — Weekly: [team review — leading indicators]
   — Monthly: [leadership review — lagging indicators, trend analysis]
   — Quarterly: [strategy review — NSM vs targets, OKR scoring]

6. ATTRIBUTION AND MEASUREMENT SETUP
   — Recommended attribution model and why
   — Tracking requirements: pixels, UTMs, CRM sync
   — Analytics stack: what tools are needed
   — Data confidence: what can we trust vs what has error margin?

7. ALERT THRESHOLDS
   — P0 (stop everything): [specific metric drops that require immediate action]
   — P1 (investigate today): [notable changes requiring same-day review]
   — P2 (flag in weekly): [trends to monitor]
"""
