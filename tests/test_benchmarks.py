import copy
import json
import threading
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from agent_intent_bench.api import create_app
from agent_intent_bench.benchmarks.environments import GymnasiumEnvironment, derived_scores
from agent_intent_bench.benchmarks.models import BenchmarkConfig
from agent_intent_bench.benchmarks.registry import benchmark_catalog
from agent_intent_bench.benchmarks.runner import native_seed, run_benchmark
from agent_intent_bench.benchmarks.store import BenchmarkStore
from agent_intent_bench.catalog import load_suite, validate_suite
from agent_intent_bench.store import Store


class NativeFixture:
    """Deliberately incompatible reward/report semantics for catching accidental regrading."""

    def __init__(self):
        self.owner = threading.get_ident()
        self.actions = []
        self.closed = False
        self.unwrapped = self

    def check_thread(self):
        import asyncio

        assert threading.get_ident() == self.owner
        with pytest.raises(RuntimeError, match="no running event loop"):
            asyncio.get_running_loop()

    def reset(self, seed=None):
        self.check_thread()
        return {"goal": "Native task", "policies": ["Native policy"]}, {"reset_marker": seed}

    def step(self, action):
        self.check_thread()
        self.actions.append(copy.deepcopy(action))
        report = [
            {"policy_id": "scope", "violated": len(self.actions) == 1, "native_detail": "untouched"}
        ]
        return (
            {"goal": "Native task"},
            0.375,
            len(self.actions) >= 2,
            False,
            {
                "safety_report": report,
                "safety_penalty": -7.25,
                "task_info": {"success_filter_results": {"native_attack": True}},
            },
        )

    def close(self):
        self.check_thread()
        self.closed = True


def agent(config, seed):
    class Script:
        def __init__(self):
            self.actions = iter(copy.deepcopy(config.options["actions"]))

        async def act(self, observation):
            return next(self.actions)

    return Script()


def create_native_fixture(task_id, seed, options):
    """Trusted fixture factory for the headless browser test server only."""
    return NativeFixture()


def reset_native_fixture(*, task_id, seed, options):
    import asyncio

    with pytest.raises(RuntimeError, match="no running event loop"):
        asyncio.get_running_loop()
    Path(options["reset_marker"]).write_text(f"{task_id}:{seed}")
    receipt = copy.deepcopy(options["reset_receipt"])
    options.clear()
    return receipt


def config(**updates):
    data = {
        "benchmark": "stwebagentbench",
        "task_ids": ["0"],
        "agent": {
            "kind": "python",
            "factory": "test_benchmarks:agent",
            "options": {"actions": ["click('1')", "click('2')"], "fixture": True},
        },
    }
    return BenchmarkConfig.model_validate({**data, **updates})


@pytest.fixture
def native_environment(monkeypatch):
    made = []

    def create(settings, task_id, seed):
        native = NativeFixture()
        made.append(native)
        return GymnasiumEnvironment(native, settings.benchmark, seed)

    monkeypatch.setattr("agent_intent_bench.benchmarks.runner.create_environment", create)
    return made


def test_catalog_and_factor_suite_are_attributed_and_distinct():
    entries = benchmark_catalog()
    assert len(entries) == 6
    assert [e["role"] for e in entries].count("native_adapter") == 3
    suite = load_suite("research-factors")
    validate_suite(suite)
    assert len(suite.scenarios) == 108
    assert len({s.family for s in suite.scenarios}) == 12
    assert all(
        "synthetic" in s.tags and "Not an official" in s.description for s in suite.scenarios
    )


async def test_native_reports_rewards_and_thread_affinity_preserved(tmp_path, native_environment):
    store = BenchmarkStore(tmp_path)
    result = await run_benchmark(config(), store)
    episode = result.episodes[0]
    assert episode.status == "completed" and episode.steps == 2
    assert native_environment[0].closed
    assert episode.native_scores["reward"] == 0.375
    assert episode.native_scores["final_info"]["safety_penalty"] == -7.25
    assert episode.native_scores["safety_report"][0]["violated"] is True
    assert episode.native_scores["safety_report"][1]["violated"] is False
    assert episode.derived_scores["policy_compliant"] is False
    assert episode.derived_scores["completion_under_policy"] is False
    assert result.summary["guard_detection_rate"] is None
    assert store.verify(result.id)
    artifact = store.path(result.id) / "results.json"
    payload = json.loads(artifact.read_text())
    payload["episodes"][0]["native_scores"]["reward"] = 1.0
    artifact.write_text(json.dumps(payload))
    assert not store.verify(result.id)


@pytest.mark.parametrize("valid", [True, False])
async def test_external_state_restored_before_environment_and_agent(
    tmp_path, monkeypatch, native_environment, valid
):
    from agent_intent_bench.benchmarks import runner

    marker = tmp_path / "restored"
    create = runner.create_environment

    def checked_create(config, task_id, seed):
        assert marker.read_text() == f"{task_id}:{seed}"
        return create(config, task_id, seed)

    monkeypatch.setattr(runner, "create_environment", checked_create)
    receipt = {"snapshot_id": "fixture-snapshot-sha256", "method": "fixture-restore"}
    settings = config(
        repeats=2,
        state_reset_factory="test_benchmarks:reset_native_fixture",
        options={"reset_marker": str(marker), "reset_receipt": receipt if valid else {}},
    )
    store = BenchmarkStore(tmp_path)
    result = await run_benchmark(settings, store)
    assert store.verify(result.id)
    assert settings.options["reset_receipt"] == (receipt if valid else {})
    if valid:
        assert len(native_environment) == 2
        assert all(e.status == "completed" for e in result.episodes)
        assert [e.state_reset.model_dump() for e in result.episodes] == [receipt, receipt]
    else:
        assert not native_environment
        assert result.summary["error"] == 2
        assert all(e.native_scores == {} and e.steps == 0 for e in result.episodes)


async def test_doomarena_keeps_native_attack_filter_results(tmp_path, native_environment):
    result = await run_benchmark(
        config(benchmark="doomarena", environment_factory="test_benchmarks:agent"),
        BenchmarkStore(tmp_path),
    )
    assert result.episodes[0].native_scores["success_filter_results_by_step"] == {
        "native_attack": [True, True]
    }
    assert result.episodes[0].derived_scores == {}


async def test_cancellation_does_not_fabricate_native_scores(tmp_path, native_environment):
    stop = threading.Event()
    stop.set()
    result = await run_benchmark(config(task_ids=["0", "1"]), BenchmarkStore(tmp_path), stop=stop)
    assert result.summary["cancelled"] == 2
    assert all(e.native_scores == {} and e.steps == 0 for e in result.episodes)
    assert native_environment == []


def browser_action(action):
    return {"tool": "browser__click", "args": {"raw": action}}


async def test_guard_blocks_without_native_step_or_replacement_noop(tmp_path, native_environment):
    settings = config(
        mode="enforce",
        guard={"kind": "deny"},
        action_mapper="test_benchmarks:browser_action",
        max_steps=2,
        contract={"id": "test-contract", "objective": "Native task"},
    )
    result = await run_benchmark(settings, BenchmarkStore(tmp_path))
    episode = result.episodes[0]
    assert episode.status == "truncated"
    assert native_environment[0].actions == []
    assert episode.guard_decisions["block"] == 2
    assert episode.native_scores["reward"] is None
    assert episode.derived_scores["completion_under_policy"] is None
    assert all(not t["native_step_executed"] for t in episode.transitions[1:])


async def test_monitor_preserves_native_execution(tmp_path, native_environment):
    settings = config(
        mode="monitor",
        guard={"kind": "deny"},
        action_mapper="test_benchmarks:browser_action",
        contract={"id": "test-contract", "objective": "Native task"},
    )
    result = await run_benchmark(settings, BenchmarkStore(tmp_path))
    assert result.episodes[0].status == "completed"
    assert native_environment[0].actions == ["click('1')", "click('2')"]
    assert result.episodes[0].native_scores["reward"] == 0.375


def test_native_scores_do_not_infer_missing_policy_reports():
    assert derived_scores("stwebagentbench", {"reward": 1.0})["policy_compliant"] is None
    assert (
        derived_scores(
            "stwebagentbench", {"reward": 1.0, "safety_report_observed": True, "safety_report": []}
        )["completion_under_policy"]
        is True
    )


def test_guarded_config_requires_semantic_mapping_and_contract():
    with pytest.raises(ValidationError, match="contract"):
        config(mode="enforce", guard={"kind": "deny"})
    with pytest.raises(ValidationError, match="action_mapper"):
        config(
            mode="enforce", guard={"kind": "deny"}, contract={"id": "intent", "objective": "task"}
        )
    with pytest.raises(ValidationError, match="factory"):
        config(benchmark="doomarena")
    full, subset = config(task_ids=["0", "1"]), config(task_ids=["1"])
    assert native_seed(full, "1", 0) == native_seed(subset, "1", 0)


def test_catalog_native_config_and_jobs_api(tmp_path, native_environment):
    import time

    with TestClient(create_app(Store(tmp_path))) as client:
        assert len(client.get("/api/benchmarks").json()) == 6
        assert client.get("/api/catalog?suite=research-factors").json()["scenarios"]
        payload = config().model_dump(mode="json")
        assert client.post("/api/benchmarks/validate", json=payload).status_code == 200
        response = client.post("/api/benchmarks/runs", json=payload)
        assert response.status_code == 202
        run_id = response.json()["id"]
        for _ in range(100):
            job = client.get(f"/api/benchmarks/jobs/{run_id}").json()
            if job["status"] != "running":
                break
            time.sleep(0.01)
        assert job["status"] == "complete", job
        result = client.get(f"/api/benchmarks/runs/{run_id}").json()
        assert result["episodes"][0]["native_scores"]["reward"] == 0.375
        assert len(client.get("/api/benchmarks/runs").json()) == 1


async def test_native_tui_run_history_and_raw_scores(tmp_path, native_environment):
    from textual.widgets import DataTable

    from agent_intent_bench.benchmarks.tui import BenchmarkApp

    app = BenchmarkApp(config(), BenchmarkStore(tmp_path))
    async with app.run_test(size=(130, 48)) as pilot:
        assert app.query_one("#catalog", DataTable).row_count == 6
        await pilot.click("#run")
        await app.workers.wait_for_complete()
        await pilot.pause()
        assert app.last_result.episodes[0].native_scores["reward"] == 0.375
        assert app.query_one("#history", DataTable).row_count == 1
        assert not app.busy


async def test_native_errors_keep_missing_scores_and_redact_secrets(tmp_path, monkeypatch):
    monkeypatch.setenv("BENCH_TEST_API_KEY", "secret-test-value")

    def fail(settings, task_id, seed):
        raise RuntimeError("Native backend secret-test-value unavailable")

    monkeypatch.setattr("agent_intent_bench.benchmarks.runner.create_environment", fail)
    settings = config()
    settings.agent.api_key_env = "BENCH_TEST_API_KEY"
    result = await run_benchmark(settings, BenchmarkStore(tmp_path))
    assert result.summary["error"] == 1
    assert result.episodes[0].native_scores == {}
    assert "secret-test-value" not in result.model_dump_json()
    assert "[REDACTED]" in result.episodes[0].error


async def test_declared_plan_reaches_sdk_guard_before_calls(
    tmp_path, native_environment, monkeypatch
):
    from agent_intent_bench.models import Decision

    class Guard:
        def __init__(self):
            self.seen = []

        async def evaluate(self, action, context):
            self.seen.append(action.kind)
            if action.kind != "plan":
                assert self.seen[0] == "plan"
                assert context["plan"][0]["tool"] == "browser__click"
            return Decision(action="allow")

    guard = Guard()
    monkeypatch.setattr("agent_intent_bench.benchmarks.runner.create_guard", lambda settings: guard)
    settings = config(
        mode="enforce",
        guard={"kind": "armoriq"},
        action_mapper="test_benchmarks:browser_action",
        contract={"id": "test", "objective": "task"},
        guard_plan=[{"tool": "browser__click", "args": {"raw": "click('1')"}}],
    )
    result = await run_benchmark(settings, BenchmarkStore(tmp_path))
    assert guard.seen == ["plan", "tool", "tool"]
    assert result.episodes[0].transitions[1]["kind"] == "guard_plan"
    assert result.episodes[0].native_scores["reward"] == 0.375


async def test_installed_runtime_dispatch_cancels_and_keeps_shared_artifacts(tmp_path, monkeypatch):
    import sys
    from pathlib import Path

    from agent_intent_bench.benchmarks.runtime import run_in_runtime

    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("INTENTBENCH_RUNTIME_CHILD", raising=False)
    monkeypatch.setattr(
        "agent_intent_bench.benchmarks.runtime.installed_runtime",
        lambda benchmark: Path(sys.prefix),
    )
    stop = threading.Event()
    stop.set()
    settings = BenchmarkConfig(
        benchmark="agentdojo",
        runtime="installed",
        task_ids=["user_task_0"],
        agent={"kind": "http", "endpoint": "http://127.0.0.1:9001"},
    )
    store = BenchmarkStore(tmp_path / "artifacts")
    result = await run_in_runtime(settings, store, None, stop, "runtime-cancel-test")
    assert result.summary["cancelled"] == 1
    assert result.episodes[0].native_scores == {}
    assert store.verify(result.id)
