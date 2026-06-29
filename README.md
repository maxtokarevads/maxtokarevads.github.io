# AI Marketing Agent System

Multi-agent marketing platform powered by Claude. Handles ad campaigns, SEO, strategy, creative — with full human-in-the-loop approval flow.

## Quick Start

```bash
pip install -r requirements.txt
cp .env.example .env   # add ANTHROPIC_API_KEY
python run_agent_chat.py
```

## Architecture

```
agent.py                   # AdvertisingAnalyticsAgent — campaigns, metrics, actions
claude_http_analyzer.py    # Anthropic Messages API client (httpx, model fallback)
agents/
  base_agent.py            # BaseAgent ABC — chat(), history, system_prompt
  manager.py               # AgentsManager — run_many() parallel, orchestrate()
  ads/                     # AdsAgent — 6 modes × 3 platforms (see below)
  seo/                     # SEOAgent
  strategy/                # StrategyAgent
  creative/                # CreativeAgent
run_agent_chat.py          # CLI chat interface
run_agent_chat_gui.py      # Tkinter GUI
run_agent_telegram.py      # Telegram long-polling bot
demo.py                    # Interactive demo menu
tests/                     # 51 unit tests (no API calls)
```

## Agents

| Agent | Key payload fields |
|-------|--------------------|
| `ads` | platform, mode, product, budget, goal, usp, funnel_stage, audience |
| `seo` | site, keywords, query |
| `strategy` | goal, timeline, resources |
| `creative` | product, tone, format |

### AdsAgent modes

| mode | Description |
|------|-------------|
| `plan` | Campaign launch strategy (default) |
| `analyze` | Diagnose metrics — CTR, ROAS, QS, Frequency, Hook Rate |
| `copy` | Generate ad copy respecting platform character limits |
| `retargeting` | TOFU→MOFU→BOFU remarketing strategy |
| `ab_test` | A/B test design per platform tools |
| `budget` | Cross-platform budget allocation |

### Supported platforms

`google` · `meta` (aliases: `facebook`, `instagram`, `fb`) · `tiktok`

## Usage

```python
from agent import AdvertisingAnalyticsAgent

a = AdvertisingAnalyticsAgent()

# Run a single agent
result = a.run_agent("ads", {
    "platform": "meta",
    "mode": "copy",
    "product": "SaaS CRM",
    "usp": "Deploy in 5 minutes",
    "funnel_stage": "tofu",
    "tone": "conversational",
})

# Analyze campaign metrics
result = a.run_agent("ads", {
    "platform": "tiktok",
    "mode": "analyze",
    "metrics": {"hook_rate": 12, "video_completion_rate": 8, "cpa": 55},
})

# Orchestrate all agents + synthesize
result = a.run_md_coordinator(
    task="Launch SaaS product",
    context={"product": "CRM", "platform": "google", "budget": 5000},
    agent_list=["seo", "ads", "strategy", "creative"],
)

# Campaign management with human approval
campaign = a.create_campaign({"name": "Q3 Growth", "platform": "google", "budget": 3000})
action = a.propose_action(campaign.id, "launch_campaign", "launch")
a.approve_action(action.id, approve=True)
a.execute_action(action.id)
```

## Interfaces

```bash
python run_agent_chat.py       # terminal chat, choose agent
python run_agent_chat_gui.py   # Tkinter window
python run_agent_telegram.py   # Telegram bot (set TELEGRAM_BOT_TOKEN in .env)
python demo.py                 # interactive demo menu
```

## Configuration

```env
ANTHROPIC_API_KEY=sk-ant-...
ANTHROPIC_MODEL=claude-haiku-4-5-20251001   # or claude-sonnet-4-6
ANTHROPIC_MAX_TOKENS=2048
TELEGRAM_BOT_TOKEN=...
TELEGRAM_DEFAULT_AGENT=ads
```

## Tests

```bash
pytest tests/ -q   # 51 tests, no API calls required
```

## Adding an agent

1. Create `agents/myagent/` with `agent.py`, `skills/prompt.py`, `__init__.py`
2. Inherit `BaseAgent`, implement `run()` and `get_system_prompt()`
3. Register in `AgentsManager.__init__()` via `register_agent()`
4. Add tests to `tests/`
