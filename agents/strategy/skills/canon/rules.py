"""
Strategy Canon Rules — 30 rules across 6 categories.

Severity:
  P0 — planning gate failure: missing inputs that invalidate any recommendation.
       STOP and request clarification before outputting a plan.
  P1 — structural issues: recommendation will underperform or mislead.
       Flag prominently, propose fix.
  P2 — optimisation: plan is valid but could be stronger.

Categories: ICP | Market | Budget | Funnel | Measurement | Execution
Rule ID format: SAC-XXXX (Strategy Agent Canon)
"""
from typing import Any, Dict, List

STRATEGY_CANON_RULES: List[Dict[str, Any]] = [

    # ── P0 — Planning Gates ────────────────────────────────────────────────────

    {
        "id": "SAC-0001",
        "severity": "P0",
        "category": "ICP",
        "rule": "ICP must define company size, role, pain, and budget — 'everyone' is not an ICP",
        "how_to_check": "Does the audience field contain at least 3 of: size, industry, role, pain, budget signal?",
        "what_to_do": "Ask: Who feels the pain? Who signs the check? What triggers them to look for a solution?",
        "verify": "ICP can be described in one sentence a salesperson could use to qualify a lead.",
        "objective_fit": "All",
    },
    {
        "id": "SAC-0002",
        "severity": "P0",
        "category": "Measurement",
        "rule": "North Star Metric must be defined before channel or budget recommendations",
        "how_to_check": "Is there a single primary KPI that represents value delivered to the customer?",
        "what_to_do": "Define NSM: Revenue (ecom), MRR (SaaS), SQLs (B2B lead-gen), DAU (app). Cannot be 'traffic'.",
        "verify": "NSM is measurable weekly, owned by one team, and leads lagging revenue.",
        "objective_fit": "All",
    },
    {
        "id": "SAC-0003",
        "severity": "P0",
        "category": "Market",
        "rule": "Kill signal must be defined: the metric that triggers a strategy pivot",
        "how_to_check": "Is there a specific threshold (e.g. 'if CPL >$400 at week 6') that triggers pivot?",
        "what_to_do": "Define: 'If [metric] is [value] after [timeframe], we will [action].' No vague 'reassess'.",
        "verify": "Kill signal is a binary decision — either the threshold is hit or not.",
        "objective_fit": "All",
    },
    {
        "id": "SAC-0004",
        "severity": "P0",
        "category": "Budget",
        "rule": "Total budget must be quantified — 'flexible' or 'TBD' invalidates channel allocation",
        "how_to_check": "Is a numeric monthly budget provided?",
        "what_to_do": "Request budget. If unavailable, output channel ranking by priority only — not allocation %.",
        "verify": "Budget is a specific number, not a range wider than 50% of the midpoint.",
        "objective_fit": "All",
    },
    {
        "id": "SAC-0005",
        "severity": "P0",
        "category": "Execution",
        "rule": "Timeline must be specific — 'soon' or 'ASAP' cannot anchor a 90-day plan",
        "how_to_check": "Is timeline a specific period (e.g. 3 months, Q3 2026)?",
        "what_to_do": "Default to 3 months if unspecified — state assumption explicitly.",
        "verify": "Each action in the plan maps to a specific week or month.",
        "objective_fit": "All",
    },

    # ── P1 — Structural Issues ─────────────────────────────────────────────────

    {
        "id": "SAC-0006",
        "severity": "P1",
        "category": "Budget",
        "rule": "Each channel must meet minimum viable budget to exit algorithm learning phase",
        "how_to_check": "Google Ads: ≥10× target CPA/day. Meta: ≥$50/day per ad set. TikTok: ≥$30/day.",
        "what_to_do": "If total budget is insufficient for multi-channel, recommend single-channel focus first.",
        "verify": "No channel allocation falls below minimum viable threshold.",
        "objective_fit": "All",
    },
    {
        "id": "SAC-0007",
        "severity": "P1",
        "category": "Funnel",
        "rule": "Retention strategy must be included — acquisition without retention burns budget",
        "how_to_check": "Does the plan include post-purchase/post-signup engagement actions?",
        "what_to_do": "Add CRM/email lifecycle, onboarding sequence, reactivation trigger.",
        "verify": "Retention KPI defined (churn rate, NRR, D30 retention, repeat purchase rate).",
        "objective_fit": "All",
    },
    {
        "id": "SAC-0008",
        "severity": "P1",
        "category": "Market",
        "rule": "Positioning must pass the competitor test: could a competitor say the same thing?",
        "how_to_check": "Read the core claim — does it uniquely describe this product vs alternatives?",
        "what_to_do": "Replace generic claims ('fast', 'easy', 'affordable') with owned, specific differentiators.",
        "verify": "Claim references a specific, verifiable advantage that competitors cannot copy immediately.",
        "objective_fit": "All",
    },
    {
        "id": "SAC-0009",
        "severity": "P1",
        "category": "Execution",
        "rule": "Channel sequencing must respect dependencies — retargeting requires TOFU volume first",
        "how_to_check": "Is there a phase 1 / phase 2 ordering? Do BOFU channels assume MOFU audiences exist?",
        "what_to_do": "Define channel activation order. Don't activate retargeting before 1,000+ TOFU touchpoints/week.",
        "verify": "Every channel dependency is made explicit in the plan.",
        "objective_fit": "All",
    },
    {
        "id": "SAC-0010",
        "severity": "P1",
        "category": "Budget",
        "rule": "Multi-channel plans with <$5k/mo total budget must concentrate, not diversify",
        "how_to_check": "Total budget divided by number of recommended channels: is each allocation viable?",
        "what_to_do": "Recommend 1–2 channels max at <$5k/mo. Spreading thin is a common expensive mistake.",
        "verify": "Minimum channel count rule: budget ÷ channels ≥ $2,000/mo per channel.",
        "objective_fit": "All",
    },
    {
        "id": "SAC-0011",
        "severity": "P1",
        "category": "ICP",
        "rule": "B2B plans must distinguish champion (feels pain) from economic buyer (approves budget)",
        "how_to_check": "Are both roles defined? Do they have different messages and channels?",
        "what_to_do": "Map: champion = LinkedIn content + thought leadership. Buyer = case studies + ROI proof.",
        "verify": "Two distinct personas with different content and channel strategies.",
        "objective_fit": "B2B",
    },
    {
        "id": "SAC-0012",
        "severity": "P1",
        "category": "Measurement",
        "rule": "Attribution model must be specified — last-touch inflates BOFU, first-touch inflates TOFU",
        "how_to_check": "Is an attribution model recommended? Is it appropriate for the channel mix?",
        "what_to_do": "Recommend: data-driven (if >1k conv/mo), linear (multi-touch awareness), first-touch (brand building).",
        "verify": "Attribution model is named, not 'default'. Data-driven requires ≥1,000 conversions/month.",
        "objective_fit": "All",
    },
    {
        "id": "SAC-0013",
        "severity": "P1",
        "category": "Funnel",
        "rule": "GTM plan must define the activation metric — proof that the customer sees value",
        "how_to_check": "Is there an 'aha moment' or activation event defined in the plan?",
        "what_to_do": "Define: first action that correlates with long-term retention (e.g. 'create 3 projects', 'invite teammate').",
        "verify": "Activation metric is a behaviour, not a login or signup.",
        "objective_fit": "SaaS | App | GTM",
    },
    {
        "id": "SAC-0014",
        "severity": "P1",
        "category": "Market",
        "rule": "Competitive analysis must identify specific weaknesses of top 3 competitors",
        "how_to_check": "Are competitors named with specific positioning weaknesses (not generic 'they're expensive')?",
        "what_to_do": "Research: G2 reviews, Reddit threads, sales objections. Find real pain in competitor reviews.",
        "verify": "Each competitor weakness is specific enough to build messaging against.",
        "objective_fit": "All",
    },
    {
        "id": "SAC-0015",
        "severity": "P1",
        "category": "Execution",
        "rule": "Weeks 1-2 plan must be all foundation — no paid scale before tracking is validated",
        "how_to_check": "Does the plan launch paid spend in week 1 without tracking verification?",
        "what_to_do": "Week 1-2 = tracking setup, CRM configuration, landing page, baseline. No paid scale yet.",
        "verify": "Tracking validated before first paid $1 is spent.",
        "objective_fit": "All",
    },

    # ── P2 — Optimisation ──────────────────────────────────────────────────────

    {
        "id": "SAC-0016",
        "severity": "P2",
        "category": "ICP",
        "rule": "ICP should be scored by: size × growth × fit × willingness-to-pay",
        "how_to_check": "Is a scoring matrix used to select the primary ICP from multiple segments?",
        "what_to_do": "If multiple segments exist, score each on 4 dimensions and recommend the highest-scoring primary.",
        "verify": "Recommended ICP score is documented with rationale.",
        "objective_fit": "All",
    },
    {
        "id": "SAC-0017",
        "severity": "P2",
        "category": "Budget",
        "rule": "Marginal ROAS analysis: define where the next $1 of incremental budget should go",
        "how_to_check": "Is there a marginal ROAS or marginal CPL statement in the plan?",
        "what_to_do": "Add: 'Given current channel performance, incremental budget goes to [X] because [marginal efficiency].'",
        "verify": "Next-dollar allocation is justified by current channel data or benchmarks.",
        "objective_fit": "All",
    },
    {
        "id": "SAC-0018",
        "severity": "P2",
        "category": "Measurement",
        "rule": "OKRs must be set at 70% confidence — 100% hit rate means targets were too easy",
        "how_to_check": "Are OKR targets ambitious enough that full achievement is unlikely (70% probability)?",
        "what_to_do": "Apply the 70% rule: reduce targets by ~30% vs 'safe' estimates for OKRs.",
        "verify": "At least one KR is a stretch (team estimates <50% probability of hitting it).",
        "objective_fit": "All",
    },
    {
        "id": "SAC-0019",
        "severity": "P2",
        "category": "Funnel",
        "rule": "Product-led growth signal: if there is a self-serve trial/freemium, PLG motion should be evaluated",
        "how_to_check": "Is there a free tier, trial, or demo? Is PLG explicitly evaluated vs sales-led?",
        "what_to_do": "For products with self-serve: evaluate PLG motion alongside or instead of paid acquisition.",
        "verify": "PLG vs sales-led choice is explicit and reasoned.",
        "objective_fit": "SaaS | App",
    },
    {
        "id": "SAC-0020",
        "severity": "P2",
        "category": "Market",
        "rule": "Category creation vs category entry: plan should state which game is being played",
        "how_to_check": "Is the product entering an existing category or trying to define a new one?",
        "what_to_do": "Category creation: educate first, own the name. Category entry: attack the leader's weakness.",
        "verify": "Go-to-market motion matches category strategy.",
        "objective_fit": "All",
    },
    {
        "id": "SAC-0021",
        "severity": "P2",
        "category": "Execution",
        "rule": "Each action in execution plan must have an owner role (not just a task)",
        "how_to_check": "Does every action have an assigned role (e.g. 'media buyer', 'content team', 'founder')?",
        "what_to_do": "Add owner to every action. Ownerless actions don't happen.",
        "verify": "No action row is missing an owner.",
        "objective_fit": "All",
    },
    {
        "id": "SAC-0022",
        "severity": "P2",
        "category": "Budget",
        "rule": "Test budget must be allocated: 10-20% of total budget for new channel experiments",
        "how_to_check": "Is there explicit budget for testing, separate from scaling proven channels?",
        "what_to_do": "Reserve 10-20% as 'test budget' for new channels. Run structured tests, not random experiments.",
        "verify": "Test budget is a named line item with entry/exit criteria.",
        "objective_fit": "All",
    },
    {
        "id": "SAC-0023",
        "severity": "P2",
        "category": "Measurement",
        "rule": "Reporting cadence must be defined: daily anomaly detection vs weekly trend vs monthly strategy",
        "how_to_check": "Is there a differentiated review cadence (daily/weekly/monthly/quarterly)?",
        "what_to_do": "Define: Daily = anomaly detection only. Weekly = leading indicators. Monthly = lagging + decisions.",
        "verify": "Three distinct review rhythms with different audiences and different metrics.",
        "objective_fit": "All",
    },
    {
        "id": "SAC-0024",
        "severity": "P2",
        "category": "ICP",
        "rule": "JTBD (Jobs-to-be-Done) framing: define what job the customer hires the product to do",
        "how_to_check": "Is there a JTBD statement: 'When [situation], I want to [motivation], so I can [outcome]'?",
        "what_to_do": "Map the core JTBD. Functional: the task. Emotional: how they want to feel. Social: how they want to be seen.",
        "verify": "Messaging maps to functional + emotional JTBD, not just product features.",
        "objective_fit": "All",
    },
    {
        "id": "SAC-0025",
        "severity": "P2",
        "category": "Funnel",
        "rule": "Reactivation strategy must be defined for churned or dormant customers",
        "how_to_check": "Is there a win-back or reactivation flow for lapsed customers?",
        "what_to_do": "Add: triggered reactivation email at 30/60/90 days of inactivity. Offer must be different from initial acquisition.",
        "verify": "Reactivation trigger event is defined and measurable.",
        "objective_fit": "All",
    },
    {
        "id": "SAC-0026",
        "severity": "P2",
        "category": "Market",
        "rule": "Trend tailwind: identify one market force that makes this the right moment to launch",
        "how_to_check": "Is there a market timing argument in the plan?",
        "what_to_do": "Name the tailwind: regulation change, platform shift, economic condition, cultural moment.",
        "verify": "Tailwind is external (market-driven), not internal ('we're ready now').",
        "objective_fit": "All",
    },
    {
        "id": "SAC-0027",
        "severity": "P2",
        "category": "Execution",
        "rule": "Quick wins (week 1-2) must be actions executable without dependencies or approvals",
        "how_to_check": "Are week 1-2 actions truly executable immediately by the team as described?",
        "what_to_do": "Quick wins = no design needed, no dev work, no legal review. E.g.: add UTMs, set up GA4, publish landing page.",
        "verify": "Each quick win has zero blocking dependencies.",
        "objective_fit": "All",
    },
    {
        "id": "SAC-0028",
        "severity": "P2",
        "category": "Measurement",
        "rule": "Leading indicators must be confirmed to lead lagging indicators by 2-8 weeks",
        "how_to_check": "Is there evidence or logic that each leading indicator predicts the NSM?",
        "what_to_do": "Map the causal chain: leading metric → intermediate metric → NSM. No proxy metrics without causal link.",
        "verify": "Leading indicators have a known or estimated lag time to NSM impact.",
        "objective_fit": "All",
    },
    {
        "id": "SAC-0029",
        "severity": "P2",
        "category": "Budget",
        "rule": "Build vs buy vs partner decision must be explicit for each major capability",
        "how_to_check": "Does the plan specify what is built in-house vs outsourced vs via partnerships?",
        "what_to_do": "For each major capability (creative, SEO, paid media, CRM): state build/buy/partner rationale.",
        "verify": "No capability left ambiguous about ownership.",
        "objective_fit": "All",
    },
    {
        "id": "SAC-0030",
        "severity": "P2",
        "category": "Funnel",
        "rule": "Content strategy must match SERP intent, not just keywords — format follows intent",
        "how_to_check": "Does the content plan distinguish informational / commercial / transactional intent?",
        "what_to_do": "Audit top 3 SERP results per cluster: what format do they use? Match that format first.",
        "verify": "Each content piece maps to a specific intent type and SERP format.",
        "objective_fit": "All",
    },
]


def get_strategy_rules_for_audit(context: Dict[str, Any]) -> str:
    """Return a formatted Canon Rules checklist for the given strategy context."""
    industry  = str(context.get("industry", "")).lower()
    is_b2b    = any(x in industry for x in ("b2b", "saas", "enterprise", "agency"))
    is_app    = any(x in industry for x in ("app", "mobile", "gaming"))
    is_saas   = "saas" in industry

    def _fits(rule: Dict[str, Any]) -> bool:
        fit    = rule.get("objective_fit", "All")
        tokens = {t.strip() for t in fit.split("|")}
        if "All" in tokens:
            return True
        if is_b2b and any(t in tokens for t in ("B2B", "B2B | SaaS", "B2B")):
            return True
        if is_saas and any(t in tokens for t in ("SaaS", "App")):
            return True
        if is_app and any(t in tokens for t in ("App",)):
            return True
        if "GTM" in tokens and context.get("mode") == "gtm":
            return True
        if "All" not in tokens and not any(
            t in ("B2B", "SaaS", "App", "GTM") for t in tokens
        ):
            return False
        return False

    lines = ["## Strategy Canon Rules — Checklist\n"]
    lines.append("Apply EVERY applicable rule. Mark: ✓ OK | ✗ FAIL | ? Missing data\n")

    for sev in ["P0", "P1", "P2"]:
        sev_rules = [
            r for r in STRATEGY_CANON_RULES
            if r["severity"] == sev and _fits(r)
        ]
        if not sev_rules:
            continue
        lines.append(f"\n### {sev} Rules\n")
        for r in sev_rules:
            lines.append(f"**{r['id']}** [{r['category']}] {r['rule']}")
            lines.append(f"  How to check: {r['how_to_check']}")
            lines.append(f"  What to do: {r['what_to_do']}")
            lines.append(f"  Verify: {r['verify']}")
            lines.append("")

    return "\n".join(lines)
