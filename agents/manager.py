import asyncio
import logging
import json
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any, Dict, List, Optional, Tuple, cast

from .ads.agent      import AdsAgent
from .seo.agent      import SEOAgent
from .strategy.agent import StrategyAgent
from .creative.agent import CreativeAgent

logger = logging.getLogger(__name__)

# ── Task classification ────────────────────────────────────────────────────────

_CLASSIFIER_MODEL = "claude-sonnet-4-6"

_CLASSIFIER_SYSTEM = (
    "You are an orchestration classifier for a multi-agent marketing AI. "
    "Output ONLY valid JSON — no explanation, no markdown."
)

_CLASSIFIER_PROMPT = """\
A user submitted a marketing task. Determine which specialist agents are needed.

Task: {task}
Context keys available: {context_keys}

Agents:
  strategy  — marketing strategy, GTM, positioning, channel mix, KPIs
  ads       — paid media: Google Ads, Meta, TikTok campaign planning / analysis / copy
  seo       — SEO strategy, technical audit, content clusters, AEO, backlinks
  creative  — ad creative concepts, copy variants, video scripts, UGC briefs

Return JSON:
{{
  "agents": ["strategy", "ads", ...],   // ordered: dependencies first
  "rationale": "one sentence why",
  "skip_agents": {{"agent": "reason"}},  // agents not needed and why
  "mode_hints": {{"agent": "mode"}}      // suggested mode per agent (optional)
}}

Rules:
- creative almost always needs strategy or ads context first (dependency)
- ads analysis without a site = no seo needed
- strategy alone if the question is purely about planning/positioning
- Include ALL relevant agents, not just one. Omit only if clearly irrelevant.

Respond with ONLY the JSON:"""

_SYNTHESIS_SYSTEM = """\
You are a Chief Marketing Officer synthesising outputs from specialist agents.
You think in three layers: strategic (what), operational (how), execution (who does what, when).
Identify synergies, resolve contradictions, set priorities with confidence ratings.
Be specific: numbers, timelines, owners. No vague advice."""

# ── Agent dependency graph (built dynamically at registration time) ────────────
# Populated by AgentsManager.register_agent() from each agent's `dependencies` ClassVar.
# Agents declare their own dependencies — no hardcoded map needed here.
_DEPENDENCIES: Dict[str, List[str]] = {}


class AgentsManager:
    """Manages specialised agents and orchestrates multi-agent tasks."""

    def __init__(self, analyzer: Optional[Any] = None):
        self.analyzer = analyzer
        self.agents: Dict[str, Any] = {}
        self.register_agent("ads",      AdsAgent("ads",           analyzer))
        self.register_agent("seo",      SEOAgent("seo",           analyzer))
        self.register_agent("strategy", StrategyAgent("strategy", analyzer))
        self.register_agent("creative", CreativeAgent("creative", analyzer))

    def register_agent(self, agent_type: str, agent: Any) -> None:
        self.agents[agent_type] = agent
        # Auto-discover dependencies from the agent's ClassVar
        _DEPENDENCIES[agent_type] = list(getattr(agent, "dependencies", []))

    def list_agent_types(self) -> Dict[str, str]:
        return {name: agent.__class__.__name__ for name, agent in self.agents.items()}

    def get_agent(self, agent_type: str) -> Optional[Any]:
        return self.agents.get(agent_type)

    def run(self, agent_type: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        agent = self.get_agent(agent_type)
        if not agent:
            return {"error": f"Agent '{agent_type}' not found"}
        return cast(Dict[str, Any], agent.run(payload))

    def chat(self, agent_type: str, message: str,
             use_history: bool = True, chat_id: int = 0) -> Dict[str, Any]:
        agent = self.get_agent(agent_type)
        if not agent:
            return {"error": f"Agent '{agent_type}' not found"}
        if not hasattr(agent, "chat"):
            return {"error": f"Agent '{agent_type}' does not support chat"}
        return cast(Dict[str, Any], agent.chat(message, use_history=use_history, chat_id=chat_id))

    def smart_chat(
        self,
        agent_type: str,
        message: str,
        chat_id: int = 0,
        extra_payload: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        agent = self.get_agent(agent_type)
        if not agent:
            return {"error": f"Agent '{agent_type}' not found"}
        if hasattr(agent, "smart_chat"):
            return cast(Dict[str, Any], agent.smart_chat(message, chat_id=chat_id, extra_payload=extra_payload))
        if hasattr(agent, "chat"):
            return cast(Dict[str, Any], agent.chat(message, chat_id=chat_id))
        return {"error": f"Agent '{agent_type}' does not support chat"}

    def clear_agent_history(self, agent_type: str,
                            chat_id: Optional[int] = None) -> Dict[str, Any]:
        agent = self.get_agent(agent_type)
        if not agent:
            return {"error": f"Agent '{agent_type}' not found"}
        if not hasattr(agent, "clear_history"):
            return {"error": f"Agent '{agent_type}' does not support history clearing"}
        agent.clear_history(chat_id)
        scope = f"chat {chat_id}" if chat_id is not None else "all chats"
        return {"result": f"History cleared for agent '{agent_type}' ({scope})"}

    # ── Parallel execution ───────────────────────────────────────────────────

    def run_many(self, agent_payloads: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        """Run multiple agents in parallel."""
        if not agent_payloads:
            return {}
        results: Dict[str, Any] = {}
        # Cap at 4 workers: beyond this parallelism the Anthropic API rate-limits anyway
        with ThreadPoolExecutor(max_workers=min(len(agent_payloads), 4)) as executor:
            futures = {
                executor.submit(self.run, agent_type, payload): agent_type
                for agent_type, payload in agent_payloads.items()
            }
            for future in as_completed(futures):
                agent_type = futures[future]
                try:
                    results[agent_type] = future.result()
                except Exception as exc:
                    logger.exception("Agent %s failed", agent_type)
                    results[agent_type] = {"error": str(exc)}
        return results

    def run_all(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Run all registered agents in parallel with the same payload."""
        return self.run_many({agent_type: payload for agent_type in self.agents})

    # ── Smart Orchestration ──────────────────────────────────────────────────

    def classify_task(self, task: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Classify which agents to run and in what order."""
        _fallback = {
            "agents":      list(self.agents.keys()),
            "rationale":   "Classification failed — running all agents",
            "skip_agents": {},
            "mode_hints":  {},
        }
        if not self.analyzer:
            return _fallback

        prompt = _CLASSIFIER_PROMPT.replace("{task}", task).replace(
            "{context_keys}", str(list(context.keys()))
        )
        try:
            raw = self.analyzer.chat_with_agent(
                user_message=prompt,
                system_prompt=_CLASSIFIER_SYSTEM,
                model_override=_CLASSIFIER_MODEL,
            )
            if isinstance(raw, str):
                match = re.search(r"\{.*\}", raw.strip(), re.DOTALL)
                if match:
                    parsed = json.loads(match.group(0))
                    # Validate agent names
                    valid   = set(self.agents.keys())
                    agents  = [a for a in parsed.get("agents", []) if a in valid]
                    if agents:
                        return {
                            "agents":      agents,
                            "rationale":   parsed.get("rationale", ""),
                            "skip_agents": parsed.get("skip_agents", {}),
                            "mode_hints":  parsed.get("mode_hints", {}),
                        }
        except Exception as exc:
            logger.warning("classify_task failed: %s", exc)
        return _fallback

    def _resolve_execution_order(self, agents: List[str]) -> List[List[str]]:
        """Return agents grouped into parallel batches respecting dependencies.

        Returns a list of batches: [[wave1_agents], [wave2_agents], ...]
        Agents in the same batch can run in parallel.
        """
        selected = set(agents)
        remaining = list(agents)
        batches: List[List[str]] = []
        completed: set = set()

        while remaining:
            wave = []
            still_waiting = []
            for agent in remaining:
                deps = _DEPENDENCIES.get(agent, [])
                needed_deps = [d for d in deps if d in selected]
                if all(d in completed for d in needed_deps):
                    wave.append(agent)
                else:
                    still_waiting.append(agent)

            if not wave:
                # Circular dependency or unresolvable — log warning and run all remaining in parallel
                logger.warning(
                    "_resolve_execution_order: circular or unresolvable dependency detected. "
                    "Running all remaining agents in parallel: %s",
                    still_waiting,
                )
                wave = still_waiting
                still_waiting = []

            batches.append(wave)
            completed.update(wave)
            remaining = still_waiting

        return batches

    def _enrich_payload_with_prior_results(
        self,
        agent_type: str,
        payload: Dict[str, Any],
        prior_results: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Inject prior agent outputs as context into dependent agent payloads."""
        enriched = dict(payload)
        deps = _DEPENDENCIES.get(agent_type, [])
        context_snippets = []

        for dep in deps:
            if dep in prior_results and "result" in prior_results[dep]:
                text = prior_results[dep]["result"]
                if text:
                    # Truncate to avoid prompt bloat: first 800 chars of each
                    snippet = text[:800] + ("..." if len(text) > 800 else "")
                    context_snippets.append(f"[{dep.upper()} agent output]:\n{snippet}")

        if context_snippets:
            prior_context = "\n\n".join(context_snippets)
            existing = enriched.get("context", "")
            enriched["context"] = (
                f"{existing}\n\n{prior_context}".strip() if existing else prior_context
            )

        return enriched

    def _build_payload(
        self,
        agent_type: str,
        task: str,
        context: Dict[str, Any],
        mode_hint: Optional[str] = None,
    ) -> Dict[str, Any]:
        shared = {
            "product":      context.get("product", task),
            "industry":     context.get("industry", ""),
            "funnel_stage": context.get("funnel_stage", "mofu"),
            "usp":          context.get("usp", ""),
            "audience":     context.get("audience", {}),
            "goal":         context.get("goal", task),
        }
        if agent_type == "seo":
            return {
                **shared,
                "site":     context.get("site", context.get("url", "example.com")),
                "keywords": context.get("keywords", []),
                "query":    context.get("query", task),
                **({"mode": mode_hint} if mode_hint else {}),
            }
        if agent_type == "ads":
            return {
                **shared,
                "platform": context.get("platform", "google"),
                "budget":   context.get("budget", 1000),
                "mode":     mode_hint or context.get("ads_mode", "plan"),
            }
        if agent_type == "strategy":
            return {
                **shared,
                "timeline":  context.get("timeline", "3 months"),
                "resources": context.get("resources", {}),
                "budget":    context.get("budget", ""),
                "competitors": context.get("competitors", ""),
                **({"mode": mode_hint} if mode_hint else {}),
            }
        if agent_type == "creative":
            return {
                **shared,
                "tone":     context.get("tone", "modern, persuasive"),
                "format":   context.get("format", "headline, description, CTA"),
                "platform": context.get("platform", ""),
                **({"mode": mode_hint} if mode_hint else {}),
            }
        return {"task": task, "context": context}

    def _build_synthesis_prompt(
        self,
        task: str,
        context: Dict[str, Any],
        subagent_results: Dict[str, Any],
        classification: Dict[str, Any],
        skip_agents: Dict[str, str],
    ) -> str:
        agent_sections = "\n\n".join(
            f"=== {name.upper()} AGENT ===\n{data.get('result', data)}"
            for name, data in subagent_results.items()
        )

        skipped_note = ""
        if skip_agents:
            skipped_note = "\nSkipped agents (not relevant): " + ", ".join(
                f"{k} ({v})" for k, v in skip_agents.items()
            )

        industry = context.get("industry", "")
        budget   = context.get("budget", "")
        timeline = context.get("timeline", "3 months")

        context_block = f"Task: {task}"
        if industry: context_block += f"\nIndustry: {industry}"
        if budget:   context_block += f"\nBudget: ${budget}/mo"
        if timeline: context_block += f"\nTimeline: {timeline}"
        if skipped_note: context_block += skipped_note

        n_agents = len(subagent_results)
        conflict_instruction = (
            "\n\nNote: Multiple agents ran. Where they give conflicting advice, "
            "explicitly surface the conflict, explain the trade-off, and recommend one path."
        ) if n_agents > 1 else ""

        return f"""{context_block}{conflict_instruction}

Specialist agent outputs:

{agent_sections}

---

Synthesise into a single executable plan. Structure:

1. STRATEGIC ALIGNMENT (2-3 sentences)
   — Core insight that ties all agent outputs together
   — One strategic bet: the highest-leverage action given the data

2. CHANNEL INTEGRATION
   — How each channel amplifies others (specific synergies)
   — Where agents contradict each other → your resolution with rationale
   — Channels to activate in sequence vs parallel

3. PRIORITISED ACTION PLAN
   | Priority | Action | Owner role | Timeline | Expected impact | Confidence |
   — P0 (this week): unblock tracking, fix critical issues
   — P1 (month 1): launch winners, establish baselines
   — P2 (month 2-3): scale and optimise

4. RESOURCE ALLOCATION
   — Budget split across channels (if budget provided)
   — Build vs buy vs partner for each major capability
   — Where to hire vs outsource

5. 30-60-90 MILESTONES
   — 30 days: [specific measurable outcome]
   — 60 days: [specific measurable outcome]
   — 90 days: [specific measurable outcome]
   — Kill signal: if [metric] is [value] at day [N], pivot to [alternative]

6. CONFIDENCE ASSESSMENT
   — Overall plan confidence: High / Medium / Low
   — Biggest assumption that could invalidate the plan
   — What data collected in month 1 will sharpen the month 2-3 plan
"""

    # ── Shared orchestration helpers ─────────────────────────────────────────

    def _classify_and_plan(
        self,
        task: str,
        context: Dict[str, Any],
        agent_list: Optional[List[str]],
        log_prefix: str,
    ) -> Tuple[Dict[str, Any], List[str], Dict[str, str], Dict[str, str], List[List[str]]]:
        """Classify task + resolve execution batches. Shared by orchestrate() and aorchestrate()."""
        if agent_list:
            classification: Dict[str, Any] = {
                "agents":      [a for a in agent_list if a in self.agents],
                "rationale":   "Explicit agent list provided",
                "skip_agents": {},
                "mode_hints":  {},
            }
        else:
            classification = self.classify_task(task, context)

        selected_agents: List[str] = cast(List[str], classification["agents"])
        mode_hints:      Dict[str, str] = cast(Dict[str, str], classification.get("mode_hints", {}))
        skip_agents:     Dict[str, str] = cast(Dict[str, str], classification.get("skip_agents", {}))

        if selected_agents:
            logger.info(
                "%s: selected=%s rationale=%s",
                log_prefix, selected_agents, classification.get("rationale", ""),
            )

        batches = self._resolve_execution_order(selected_agents)
        return classification, selected_agents, mode_hints, skip_agents, batches

    def _build_wave_payloads(
        self,
        wave: List[str],
        wave_idx: int,
        task: str,
        context: Dict[str, Any],
        mode_hints: Dict[str, str],
        all_results: Dict[str, Any],
    ) -> Dict[str, Dict[str, Any]]:
        """Build payloads for one execution wave, injecting prior-wave context."""
        wave_payloads: Dict[str, Dict[str, Any]] = {}
        for agent_type in wave:
            payload = self._build_payload(agent_type, task, context, mode_hints.get(agent_type))
            if wave_idx > 0:
                payload = self._enrich_payload_with_prior_results(agent_type, payload, all_results)
            wave_payloads[agent_type] = payload
        return wave_payloads

    def _finalize_orchestration(
        self,
        task: str,
        context: Dict[str, Any],
        all_results: Dict[str, Any],
        classification: Dict[str, Any],
        selected_agents: List[str],
        batches: List[List[str]],
        skip_agents: Dict[str, str],
    ) -> Dict[str, Any]:
        """Split successful/failed, run synthesis, assemble final result dict."""
        successful = {k: v for k, v in all_results.items() if "error" not in v}
        failed     = {k: v for k, v in all_results.items() if "error" in v}

        if failed:
            logger.warning(
                "orchestration: %d agent(s) failed: %s",
                len(failed), {k: v["error"] for k, v in failed.items()},
            )

        if not successful:
            return {
                "error":            "All subagents failed — no data to synthesise.",
                "subagent_outputs": all_results,
                "selected_agents":  selected_agents,
                "classification":   classification,
            }

        synthesis_prompt = self._build_synthesis_prompt(
            task, context, successful, classification, skip_agents
        )
        summary = self.analyzer.chat_with_agent(
            synthesis_prompt,
            system_prompt=_SYNTHESIS_SYSTEM,
        )

        result: Dict[str, Any] = {
            "result":           summary,
            "subagent_outputs": all_results,
            "selected_agents":  selected_agents,
            "execution_order":  batches,
            "classification":   classification,
        }
        if skip_agents:
            result["skipped_agents"] = skip_agents
        if failed:
            result["failed_agents"] = {k: v["error"] for k, v in failed.items()}
        return result

    def orchestrate(
        self,
        task: str,
        context: Dict[str, Any],
        agent_list: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Orchestrate agents with smart classification, dependency ordering, and synthesis."""
        if not self.analyzer:
            return {"error": "No analyzer configured"}

        classification, selected_agents, mode_hints, skip_agents, batches = \
            self._classify_and_plan(task, context, agent_list, "orchestrate")

        if not selected_agents:
            return {"error": "No available agents for orchestration", "classification": classification}

        all_results: Dict[str, Any] = {}
        for wave_idx, wave in enumerate(batches):
            wave_results = self.run_many(
                self._build_wave_payloads(wave, wave_idx, task, context, mode_hints, all_results)
            )
            all_results.update(wave_results)

        return self._finalize_orchestration(
            task, context, all_results, classification, selected_agents, batches, skip_agents,
        )

    # ── Async execution ──────────────────────────────────────────────────────
    # Async versions use asyncio.gather() — agents truly interleave HTTP I/O
    # instead of blocking threads. Use these when calling from an async context
    # (e.g. an async web framework or async Telegram library).

    async def arun_many(self, agent_payloads: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        """Run multiple agents concurrently using asyncio.gather().

        Each agent.arun() wraps its sync run() in a thread executor by default,
        but agents that implement truly async arun() get full I/O concurrency.
        """
        async def _run_one(agent_type: str, payload: Dict[str, Any]) -> Tuple[str, Dict[str, Any]]:
            agent = self.get_agent(agent_type)
            if not agent:
                return agent_type, {"error": f"Agent '{agent_type}' not found"}
            try:
                result = await agent.arun(payload)
                return agent_type, result
            except Exception as exc:
                logger.exception("async agent %s failed", agent_type)
                return agent_type, {"error": str(exc)}

        pairs = await asyncio.gather(*[
            _run_one(at, payload) for at, payload in agent_payloads.items()
        ])
        return dict(pairs)

    async def aorchestrate(
        self,
        task: str,
        context: Dict[str, Any],
        agent_list: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Async version of orchestrate() — uses arun_many() for true I/O concurrency."""
        if not self.analyzer:
            return {"error": "No analyzer configured"}

        classification, selected_agents, mode_hints, skip_agents, batches = \
            self._classify_and_plan(task, context, agent_list, "aorchestrate")

        if not selected_agents:
            return {"error": "No available agents for orchestration", "classification": classification}

        all_results: Dict[str, Any] = {}
        for wave_idx, wave in enumerate(batches):
            wave_results = await self.arun_many(
                self._build_wave_payloads(wave, wave_idx, task, context, mode_hints, all_results)
            )
            all_results.update(wave_results)

        return self._finalize_orchestration(
            task, context, all_results, classification, selected_agents, batches, skip_agents,
        )

    def orchestrate_single(
        self,
        task: str,
        context: Dict[str, Any],
    ) -> Tuple[str, Dict[str, Any]]:
        """Classify task, return (best_agent_type, payload) without running anything.

        Useful for routing a single-agent request before committing to orchestration.
        """
        classification = self.classify_task(task, context)
        agents = classification.get("agents", [])
        best   = agents[0] if agents else "strategy"
        mode   = classification.get("mode_hints", {}).get(best)
        payload = self._build_payload(best, task, context, mode)
        return best, payload
