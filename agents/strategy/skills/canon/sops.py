"""
Strategy Canon SOPs — Standard Operating Procedures for each strategy audit command.
"""
from typing import Dict

STRATEGY_SOPS: Dict[str, str] = {

    "/audit": """\
## SOP: Strategy Audit (Full)

Step 1 — DATA QUALITY GATE
  Validate each input field: product, goal, industry, audience, budget, timeline.
  If any P0-gated field is missing → HALT. Output exactly: "HALT — [SAC-XXXX]: [missing field]. Request before proceeding."

Step 2 — P0 GATE CHECK
  Check SAC-0001 through SAC-0005 in order.
  First P0 failure → stop all recommendations, surface the failure with fix instructions.
  ALL P0s must pass before generating the plan.

Step 3 — P1 STRUCTURAL SCAN
  Check SAC-0006 through SAC-0015.
  Flag every failure with rule ID, specific finding, and concrete fix.
  P1 failures do NOT halt the plan — they appear as high-priority fixes.

Step 4 — GENERATE PLAN
  Only after P0 + P1 scan: generate the strategy output.
  Each section must explicitly reference findings from Step 3.

Step 5 — P2 OPTIMISATION
  Apply SAC-0016 through SAC-0030 as improvement suggestions.
  Include in a "Optimisations" section at the end.

Step 6 — CONFIDENCE ASSESSMENT
  Rate each major recommendation: High / Medium / Low.
  List what additional data would upgrade Low → High confidence.
  Flag any assumption made due to missing input.
""",

    "/gtm": """\
## SOP: Go-To-Market Audit

Step 1 — ICP GATE (SAC-0001, SAC-0011)
  If ICP is not defined at company/role/pain level → HALT.

Step 2 — LAUNCH READINESS CHECK
  Tracking setup plan: is it included in week 1-2?
  Kill signal defined (SAC-0003)?
  Activation metric defined (SAC-0013)?

Step 3 — CHANNEL MOTION VALIDATION
  Is the GTM motion (PLG / sales-led / marketing-led) appropriate for the price point and ICP?
  Under $500 ACV: PLG or marketing-led preferred.
  Over $5k ACV: sales-led or hybrid.

Step 4 — 90-DAY PLAN QUALITY
  Week 1-2: foundation only (SAC-0015, SAC-0027)
  Month 2: hard launch with clear success criteria
  Month 3: optimise (kill losers, scale winners)

Step 5 — RISK ASSESSMENT
  Top 3 launch risks with specific mitigation.
  Competitive response: what will incumbents do in the first 30 days?
""",

    "/positioning": """\
## SOP: Positioning Audit

Step 1 — COMPETITOR TEST (SAC-0008)
  For each claim: "Could a top competitor say this?"
  If yes → the claim is generic, not positioning.

Step 2 — WHITE SPACE VALIDATION
  Is the claimed position genuinely unclaimed, or just under-marketed?
  Evidence required: competitor messaging audit (Ad Library, G2, SERP).

Step 3 — JTBD ALIGNMENT (SAC-0024)
  Does the positioning address a functional + emotional job?
  Pure feature positioning fails emotional resonance.

Step 4 — PROOF POINT CHECK
  Is each positioning claim backed by a specific, verifiable proof point?
  Vague: "faster than competitors" → Specific: "2.3× faster deployment, proven in 47 enterprise deployments"

Step 5 — MOAT ASSESSMENT
  How long before competitors can copy this differentiator?
  <6 months: weak moat, needs network effect or switching cost on top.
  >18 months: strong moat, double down.
""",

    "/channel_mix": """\
## SOP: Channel Mix Audit

Step 1 — BUDGET VIABILITY (SAC-0004, SAC-0006, SAC-0010)
  For each recommended channel: does allocation meet minimum viable threshold?
  If total budget <$5k/mo: recommend single-channel focus.

Step 2 — SEQUENCING CHECK (SAC-0009)
  Map channel dependencies:
  TOFU must exist before retargeting.
  Brand search must exist before branded PMAX/DSA.
  Email list must reach critical mass before email automation ROI is meaningful.

Step 3 — ATTRIBUTION ALIGNMENT (SAC-0012)
  Is the attribution model appropriate for the channel mix?
  If TOFU channels are recommended: last-touch will undervalue them — note this explicitly.

Step 4 — MARGINAL ROAS STATEMENT (SAC-0017)
  Where does the next $1 go? This must be explicit.

Step 5 — TEST BUDGET ALLOCATION (SAC-0022)
  Is 10-20% reserved for new channel tests?
""",

    "/kpi": """\
## SOP: KPI Framework Audit

Step 1 — NSM VALIDATION (SAC-0002)
  Does the NSM represent value delivered to the customer?
  Bad NSMs: page views, MQLs, signups. Good NSMs: revenue, activated users, completed jobs.

Step 2 — OKR CALIBRATION (SAC-0018)
  Apply 70% confidence rule to each KR.
  If all KRs are expected to be hit: targets are too safe.

Step 3 — LEADING → LAGGING CAUSAL CHAIN (SAC-0028)
  For each leading indicator: confirm causal mechanism to NSM.
  Lag time estimated (e.g. "pipeline velocity leads to revenue by ~45 days").

Step 4 — ALERT THRESHOLDS
  P0 thresholds: metric drops that require same-day action.
  P1 thresholds: require same-week investigation.
  No alert defined → monitoring is not actionable.

Step 5 — DATA SOURCE AUDIT
  Is each metric traceable to a specific tool and owner?
  Untraceable metrics cannot be measured and should be removed.
""",
}


def get_strategy_sop(command: str) -> str:
    """Return SOP steps for a given command. Falls back to /audit if not found."""
    return STRATEGY_SOPS.get(command, STRATEGY_SOPS["/audit"])
