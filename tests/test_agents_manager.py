from agents.manager import AgentsManager


class DummyAgent:
    dependencies = []

    def __init__(self, name):
        self.name = name

    def run(self, payload):
        return {"result": f"ok:{payload.get('value', 'none')}"}


class SlowDummyAgent:
    """Agent that depends on another agent."""
    dependencies = ["dummy"]

    def __init__(self, name):
        self.name = name

    def run(self, payload):
        return {"result": "slow-ok"}


# ── Basic agent management ────────────────────────────────────────────────────

def test_run_nonexistent_agent():
    mgr = AgentsManager(None)
    res = mgr.run("no-such-agent", {})
    assert isinstance(res, dict)
    assert "error" in res


def test_register_and_run_dummy_agent():
    mgr = AgentsManager(None)
    dummy = DummyAgent("dummy")
    mgr.register_agent("dummy", dummy)
    res = mgr.run("dummy", {"value": 123})
    assert res.get("result") == "ok:123"


def test_list_agent_types_contains_all_four():
    mgr = AgentsManager(None)
    types = mgr.list_agent_types()
    for name in ["ads", "seo", "strategy", "creative"]:
        assert name in types


def test_get_agent_returns_agent():
    mgr = AgentsManager(None)
    agent = mgr.get_agent("ads")
    assert agent is not None
    assert agent.name == "ads"


def test_get_agent_nonexistent_returns_none():
    mgr = AgentsManager(None)
    assert mgr.get_agent("nonexistent") is None


def test_chat_nonexistent_agent_returns_error():
    mgr = AgentsManager(None)
    res = mgr.chat("nonexistent", "hello")
    assert "error" in res


# ── Parallel execution ────────────────────────────────────────────────────────

def test_run_many_returns_all_results():
    mgr = AgentsManager(None)
    a = DummyAgent("a")
    b = DummyAgent("b")
    mgr.register_agent("a", a)
    mgr.register_agent("b", b)
    results = mgr.run_many({"a": {"value": 1}, "b": {"value": 2}})
    assert results["a"]["result"] == "ok:1"
    assert results["b"]["result"] == "ok:2"


def test_run_many_empty_payloads():
    mgr = AgentsManager(None)
    results = mgr.run_many({})
    assert results == {}


# ── Dependency resolution ─────────────────────────────────────────────────────

def test_resolve_execution_order_no_deps():
    mgr = AgentsManager(None)
    mgr.register_agent("dummy", DummyAgent("dummy"))
    batches = mgr._resolve_execution_order(["dummy"])
    assert len(batches) == 1
    assert "dummy" in batches[0]


def test_resolve_execution_order_respects_deps():
    mgr = AgentsManager(None)
    dummy = DummyAgent("dummy")
    slow  = SlowDummyAgent("slow")
    mgr.register_agent("dummy", dummy)
    mgr.register_agent("slow", slow)
    batches = mgr._resolve_execution_order(["dummy", "slow"])
    assert len(batches) == 2
    assert "dummy" in batches[0]
    assert "slow" in batches[1]


def test_resolve_execution_order_strategy_before_ads():
    mgr = AgentsManager(None)
    batches = mgr._resolve_execution_order(["strategy", "ads"])
    flat = [a for wave in batches for a in wave]
    assert flat.index("strategy") < flat.index("ads")


def test_resolve_execution_order_creative_last():
    mgr = AgentsManager(None)
    agents = ["strategy", "ads", "seo", "creative"]
    batches = mgr._resolve_execution_order(agents)
    flat = [a for wave in batches for a in wave]
    # creative depends on strategy AND ads — must come after both
    assert flat.index("creative") > flat.index("strategy")
    assert flat.index("creative") > flat.index("ads")


def test_resolve_execution_order_single_wave_for_independent():
    mgr = AgentsManager(None)
    # strategy and seo are independent — should be in same wave
    batches = mgr._resolve_execution_order(["strategy", "seo"])
    # seo depends on strategy, so NOT independent
    flat = [a for wave in batches for a in wave]
    assert flat.index("strategy") < flat.index("seo")


# ── Orchestration ─────────────────────────────────────────────────────────────

def test_orchestrate_no_analyzer():
    mgr = AgentsManager(None)
    result = mgr.orchestrate("launch a product", {})
    assert "error" in result


def test_classify_task_no_analyzer_returns_fallback():
    mgr = AgentsManager(None)
    result = mgr.classify_task("any task", {})
    assert "agents" in result
    assert isinstance(result["agents"], list)
    # Fallback runs all agents
    assert len(result["agents"]) == len(mgr.agents)


# ── Payload building ──────────────────────────────────────────────────────────

def test_build_payload_ads_has_platform():
    mgr = AgentsManager(None)
    context = {"platform": "meta", "budget": 2000}
    payload = mgr._build_payload("ads", "run ads", context)
    assert "platform" in payload
    assert payload["platform"] == "meta"


def test_build_payload_seo_has_site():
    mgr = AgentsManager(None)
    context = {"site": "example.com"}
    payload = mgr._build_payload("seo", "audit site", context)
    assert "site" in payload


def test_build_payload_strategy_has_timeline():
    mgr = AgentsManager(None)
    payload = mgr._build_payload("strategy", "plan launch", {})
    assert "timeline" in payload


def test_build_payload_creative_has_tone():
    mgr = AgentsManager(None)
    context = {"tone": "bold"}
    payload = mgr._build_payload("creative", "create ad", context)
    assert payload.get("tone") == "bold"
