# Agent API Reference

Each agent exposes a `run(payload: dict) -> dict` method. This document lists required and optional fields per agent and mode, and the guaranteed output shape.

---

## Common output fields

Every `run()` call returns a dict that always contains:

| Field | Type | Description |
|---|---|---|
| `result` | `str` | Human-readable agent output |
| `agent` | `str` | Agent name (`ads`, `seo`, `strategy`, `creative`) |
| `mode` | `str` | Mode that was executed |
| `error` | `str` | Present only on failure — never alongside `result` |

Optional output fields:

| Field | Type | When present |
|---|---|---|
| `structured` | `dict` | When `call_tool()` succeeded — typed JSON payload |
| `structured_fallback` | `bool` | `True` when `call_tool()` failed and plain chat was used |
| `platform` | `str` | Ads agent only |
| `model_used` | `str` | Ads agent only |
| `_routed` | `dict` | Added by `smart_chat()` — contains `{platform, mode, confidence}` |

---

## AdsAgent

**Class:** `agents.ads.agent.AdsAgent`  
**Platforms:** `google` · `meta` · `tiktok`

### Common fields (all modes)

| Field | Type | Required | Default | Notes |
|---|---|---|---|---|
| `platform` | `str` | Yes* | — | `google`, `meta`, `tiktok`. Also accepts aliases: `facebook`→`meta`, `google_ads`→`google`. *Not required for `budget` and `forecast` modes. |
| `mode` | `str` | No | `plan` | See modes below |
| `product` | `str` | No | `""` | Product or service description |
| `goal` | `str` | No | `"conversions"` | Campaign goal |
| `budget` | `float` | No | `0.0` | Must be ≥ 0 |
| `market` | `str` | No | `""` | Geographic market |
| `context` | `str` | No | `""` | Additional context injected into prompt |
| `funnel_stage` | `str` | No | `"mofu"` | `tofu` · `mofu` · `bofu` |

### Modes

#### `plan` — Campaign launch strategy
Additional fields:
| Field | Type | Notes |
|---|---|---|
| `campaign_type` | `str` | e.g. `"Search"`, `"PMax"`, `"Advantage+"` |
| `seed_keywords` | `str` | Comma-separated seed keywords (Google) |
| `competitors` | `str` | Competitor names for research context |

Structured output (`structured` key):
```json
{
  "campaigns": [{"name", "type", "objective", "budget_usd", "targeting", "bid_strategy", "ad_formats"}],
  "launch_timeline": [{"week", "action", "owner"}],
  "success_criteria": {"target_cpa", "target_roas", "review_at_days", "kpis"}
}
```

#### `analyze` — Diagnose existing campaign metrics
Additional fields:
| Field | Type | Notes |
|---|---|---|
| `metrics` | `dict` | e.g. `{"ctr": 2.5, "roas": 3.1, "cpa": 45.0, "quality_score": 6}` |
| `inputs` | `dict` | Canon `INPUT_CODE → value` pairs for structured analysis |

Structured output:
```json
{
  "findings": [{"metric", "current_value", "benchmark", "severity", "issue", "action", "confidence"}],
  "missing_data": ["INPUT_CODE"],
  "overall_health": "critical|poor|fair|good|excellent"
}
```

#### `copy` — Generate ad copy
Additional fields:
| Field | Type | Notes |
|---|---|---|
| `usp` | `str` | Unique selling proposition |
| `audience` | `dict` | `{"age": "25-34", "interests": ["..."], "location": "US"}` |

Structured output:
```json
{
  "platform": "google|meta|tiktok",
  "variants": [{"hook_type", "headline", "description", "cta", "char_counts", "compliant"}],
  "platform_limits": {"headline": int, "description": int}
}
```

#### `retargeting` — Remarketing funnel strategy
Additional fields: `audience`, `funnel_stage`

Structured output:
```json
{
  "segments": [{"name", "funnel_stage", "signal", "window_days", "message", "cta", "exclusions"}],
  "pixel_events": ["ViewContent", "AddToCart"],
  "budget_split": {"tofu_pct": 20, "mofu_pct": 30, "bofu_pct": 50}
}
```

#### `ab_test` — A/B test design
Additional fields:
| Field | Type | Notes |
|---|---|---|
| `what_to_test` | `str` | Variable to test (e.g. `"headline"`, `"bid_strategy"`) |
| `current_performance` | `dict` | Baseline metrics |

Structured output:
```json
{
  "hypothesis": "str",
  "variable_tested": "str",
  "variants": [{"label", "description", "change"}],
  "sample_size_per_variant": int,
  "duration_days": int,
  "success_metric": "str",
  "native_tool": "str"
}
```

#### `budget` — Cross-platform budget allocation
Platform-agnostic. Fields: `budget` (total), `platforms` (list of platforms).

Structured output:
```json
{
  "allocation": [{"platform", "amount_usd", "percentage", "primary_goal", "rationale", "min_threshold_met"}],
  "total_budget": float,
  "break_even_roas": float|null,
  "marginal_roas_note": "str"
}
```

#### `audit` — Canon audit (platform-specific runbook)
Additional fields:
| Field | Type | Notes |
|---|---|---|
| `command` | `str` | Canon command: `/audit`, `/weekly`, `/tracking`, `/creative`, etc. |
| `project` | `str` | Client/project name |
| `account_type` | `str` | `ecom` · `lead-gen` · `app` |
| `date_range` | `str` | e.g. `"last 30 days"` |
| `notes` | `str` | Additional account context |

Output: Canon Fixlist table (Rule ID · Severity · Issue · Fix · Verify · Rollback) + `TELEGRAM_REPORT` block.

#### `landing` — Landing page CRO audit
Additional fields: `url` (page URL to audit)

Structured output:
```json
{
  "fixlist": [{"priority", "layer", "issue", "fix", "expected_lift"}],
  "ab_test_shortlist": [{"element", "hypothesis", "sample_size_est"}],
  "overall_score": int,
  "p0_count": int, "p1_count": int, "p2_count": int
}
```

#### `research` — Keyword / audience / creative research
Structured output:
```json
{
  "keywords": [{"keyword", "match_type", "intent", "cluster", "priority"}],
  "negative_keywords": ["str"],
  "audience_segments": [{"name", "type", "description", "priority"}],
  "creative_insights": ["str"]
}
```

#### `forecast` — Media plan + scenario projections
Additional fields: `months` (int, default 3), `budget`

Structured output:
```json
{
  "assumptions": {"cpm", "ctr", "cvr", "avg_order"},
  "scenarios": {
    "conservative": {"impressions", "clicks", "conversions", "spend_usd", "cpa", "roas"},
    "base": {...},
    "optimistic": {...}
  },
  "break_even_cpa": float|null,
  "biggest_cpa_lever": "str",
  "learning_phase_days": int,
  "risk_factors": [{"risk", "mitigation"}]
}
```

---

## SEOAgent

**Class:** `agents.seo.agent.SEOAgent`

### Common fields (all modes)

| Field | Type | Required | Notes |
|---|---|---|---|
| `site` | `str` | Recommended | Domain or URL: `example.com` or `https://example.com/` |
| `mode` | `str` | No | See modes below. Default: `seo` |
| `industry` | `str` | No | `saas`, `ecom`, `local`, `publisher`, `agency`, `b2b` |
| `keywords` | `list[str]` | No | Target keywords |
| `query` | `str` | No | Specific question or topic to research |

### Modes

| Mode | Description | Enrichment |
|---|---|---|
| `seo` | General SEO strategy with confidence assessment | GSC |
| `aeo` | AI/Answer Engine Optimization, GEO | — |
| `technical` | 9-category technical audit + health score | URL Inspection, PageSpeed, GSC |
| `content` | E-E-A-T content quality assessment | URL Inspection |
| `local` | GBP, NAP, citations, map pack | — |
| `schema` | Schema markup audit + JSON-LD generation | URL Inspection |
| `backlinks` | Backlink audit + link building strategy | — |
| `cluster` | Topical cluster + keyword architecture | GSC |
| `sxo` | SERP-backward search experience optimization | URL Inspection |
| `audit` | Canon SEO audit (30 rules, P0/P1/P2 + health score) | URL Inspection, PageSpeed, GSC |
| `drift` | Drift monitoring vs SQLite baseline | GSC |

Drift mode additional fields:
| Field | Type | Notes |
|---|---|---|
| `metrics` | `dict[str, float]` | Current numeric metrics: `{"clicks": 1200, "impressions": 45000, "ctr": 2.7, "avg_position": 8.3}` |

Enrichment requires env vars: `PAGESPEED_API_KEY`, `GSC_CREDENTIALS_FILE`. Missing keys produce informative blocks in the output rather than silent failures.

Structured output (for `audit`, `technical`, `content`, `backlinks`, `cluster`, `schema` modes):
```json
{
  "fixlist": [{"rule_id", "area", "status", "finding", "fix", "priority"}],
  "health_score": int,
  "halt": bool
}
```

---

## StrategyAgent

**Class:** `agents.strategy.agent.StrategyAgent`

### Common fields

| Field | Type | Required | Notes |
|---|---|---|---|
| `mode` | `str` | No | Default: `general` |
| `product` | `str` | Recommended | Product/service description |
| `goal` | `str` | No | e.g. `"10k MRR in 90 days"` |
| `industry` | `str` | No | Industry context |
| `timeline` | `str` | No | e.g. `"3 months"` |
| `budget` | `str\|float` | No | Available budget |
| `resources` | `dict` | No | Team/tool availability |
| `competitors` | `str` | No | Known competitors |
| `audience` | `dict` | No | ICP description |
| `usp` | `str` | No | Unique selling proposition |

### Modes

| Mode | Description |
|---|---|
| `general` | Full marketing plan (default) |
| `gtm` | Go-to-market plan: ICP → channels → 90-day milestones |
| `positioning` | STP/JTBD, differentiation, messaging |
| `channel_mix` | Budget allocation across channels (marginal ROAS logic) |
| `kpi` | KPI trees, OKRs, attribution models |
| `audit` | Canon strategy audit — P0 gates: ICP, North Star Metric, kill signal, budget |

Audit mode structured output:
```json
{
  "gates": [{"gate_id", "name", "status", "finding", "fix"}],
  "health_score": int,
  "halt": bool,
  "north_star_metric": "str"
}
```

---

## CreativeAgent

**Class:** `agents.creative.agent.CreativeAgent`

### Common fields

| Field | Type | Required | Notes |
|---|---|---|---|
| `mode` | `str` | No | Default: `concept` |
| `product` | `str` | Recommended | Product/service |
| `platform` | `str` | No | `google`, `meta`, `tiktok`, `youtube`, `instagram` |
| `tone` | `str` | No | e.g. `"modern, persuasive"` |
| `funnel_stage` | `str` | No | `tofu` · `mofu` · `bofu` |
| `usp` | `str` | No | Key differentiator |
| `audience` | `dict` | No | Target persona |

### Modes

| Mode | Description | Structured output |
|---|---|---|
| `concept` | 3 creative concepts with emotional hooks + visual direction | No |
| `copy` | Platform-compliant ad copy: headlines, descriptions, CTAs | Yes |
| `script` | Video script: hook → body → CTA (TikTok/Reels/YouTube) | Yes |
| `ugc_brief` | UGC creator brief: talking points, shot list, dos/don'ts | Yes |

Copy mode additional fields:
| Field | Type | Notes |
|---|---|---|
| `format` | `str` | e.g. `"headline, description, CTA"` |

Script mode additional fields:
| Field | Type | Notes |
|---|---|---|
| `duration` | `int` | Video duration in seconds (default: 30) |

Structured output (copy, script, ugc_brief):
```json
{
  "variants": [{"hook_type", "headline", "body", "cta", "char_counts", "compliant"}],
  "platform_limits": {"headline": int, "description": int}
}
```

---

## AgentsManager — Orchestration

**Class:** `agents.manager.AgentsManager`

### `orchestrate(task, context, agent_list=None) -> dict`

| Arg | Type | Notes |
|---|---|---|
| `task` | `str` | Plain-language task description |
| `context` | `dict` | Shared context injected into all agents. Keys: `product`, `industry`, `goal`, `budget`, `timeline`, `platform`, `site`, `audience`, `usp`, `funnel_stage`, `competitors` |
| `agent_list` | `list[str]` | Optional explicit list: `["strategy", "ads"]`. If omitted, a Sonnet classifier selects agents automatically. |

Output:
```json
{
  "result": "str — CMO synthesis",
  "subagent_outputs": {"strategy": {...}, "ads": {...}},
  "selected_agents": ["strategy", "ads"],
  "execution_order": [["strategy"], ["ads", "seo"]],
  "classification": {"agents": [...], "rationale": "str", "skip_agents": {}, "mode_hints": {}},
  "skipped_agents": {"creative": "reason"},
  "failed_agents": {"seo": "error message"}
}
```

### `run(agent_type, payload) -> dict`

Direct single-agent call. Returns the agent's `run()` output.

### `smart_chat(agent_type, message, chat_id, extra_payload) -> dict`

Routes a free-form message through the agent's intent classifier before calling `run()` or `chat()`.

---

## Error responses

All errors follow the same shape:
```json
{"error": "Human-readable message", "agent": "agent_name"}
```

Common errors:

| Error message pattern | Cause |
|---|---|
| `"No analyzer configured"` | Agent initialized without a backend |
| `"Unknown platform: '...'"` | `platform` not in `[google, meta, tiktok]` |
| `"Unknown mode: '...'"` | `mode` not in supported list |
| `"Budget cannot be negative"` | `budget < 0` |
| `"Payload too large"` | `len(str(payload)) > 80,000` |
| `"No response from model"` | API returned empty response |

---

## Environment variables

| Variable | Required | Default | Description |
|---|---|---|---|
| `ANTHROPIC_API_KEY` | Yes | — | Anthropic API key |
| `ANTHROPIC_MODEL` | No | `claude-sonnet-4-6` | Default model |
| `ANTHROPIC_MAX_TOKENS` | No | `8192` | Max output tokens |
| `ANALYZER_BACKEND` | No | `api` | `api` or `claude_code` |
| `MODEL_ROUTING` | No | `false` | `true` → uses Opus for audit modes |
| `AUDIT_MODEL` | No | `claude-opus-4-8` | Model for audit when routing enabled |
| `DB_PATH` | No | `bot_state.db` | SQLite database path |
| `PAGESPEED_API_KEY` | No | — | Google PageSpeed Insights API key |
| `GSC_CREDENTIALS_FILE` | No | — | Path to GSC OAuth credentials JSON |
| `SEO_SKIP_ENRICHMENT` | No | `false` | `true` disables live SEO enrichment (tests) |
| `TELEGRAM_BOT_TOKEN` | For bot | — | Telegram bot token |
| `ALLOWED_CHAT_IDS` | Recommended | open | Comma-separated allowed Telegram chat IDs |
| `RATE_LIMIT_MAX` | No | `10` | Max requests per window per chat |
| `RATE_LIMIT_WINDOW` | No | `60` | Rate limit window in seconds |
