"""Evaluate user-owned, independently labeled proposals without executing tools."""

from __future__ import annotations

import asyncio
import copy
import time
import uuid

from .adapters import close_adapter, create_guard
from .catalog import load_suite
from .errors import safe_error
from .expressions import canonical_hash
from .metrics import aggregate, rate
from .models import EpisodeResult, Event, RunConfig, RunResult, TraceDataset, Verdict, Violation
from .session import utc_now
from .store import Store


def without_effect_scores(metrics):
    for key in (
        "task_success_rate",
        "completion_under_policy",
        "cup_interval_95",
        "unauthorized_effect_rate",
        "critical_effect_episodes",
        "observed_unauthorized_effect_episodes",
        "observed_critical_effect_episodes",
    ):
        metrics[key] = None
    for dimension in ("domain", "family", "variant"):
        for group in metrics[f"by_{dimension}"].values():
            group["completion_under_policy"] = group["unauthorized_effect_rate"] = None
    return metrics


async def evaluate_traces(dataset: TraceDataset, config: RunConfig, store: Store) -> RunResult:
    if config.guard_policy and config.guard.kind != "reference":
        raise ValueError("Policy overrides apply only to the reference guard")
    from .models import AdapterConfig

    config = config.model_copy(update={"agent": AdapterConfig(kind="recorded"), "mode": "monitor"})
    run_id, started = uuid.uuid4().hex[:12], utc_now()
    # The suite snapshot is a storage envelope; no environment is run in this mode.
    suite = load_suite("smoke").model_copy(
        update={
            "id": dataset.id,
            "version": dataset.version,
            "description": dataset.description,
            "scenarios": load_suite("smoke").scenarios[:1],
        }
    )
    manifest = {
        "evaluation_mode": "fixed_trace",
        "source": "independently labeled user traces",
        "dataset_hash": canonical_hash(dataset.model_dump()),
        "suite_hash": canonical_hash(dataset.model_dump()),
        "scorer_version": "1.0.0",
        "agent_is_fixture": False,
        "effect_scores": "Not computed: no tool execution or counterfactual outcomes",
    }
    store.begin(run_id, started, suite, config.model_dump(), manifest)
    (store.path(run_id) / "trace-dataset.json").write_text(
        dataset.model_dump_json(indent=2), encoding="utf-8"
    )
    guards = {}
    episodes = []
    exact_matches = 0
    for case in dataset.cases:
        verdict = Verdict(
            allowed=case.expected == "allow",
            violations=[]
            if case.expected == "allow"
            else [Violation(rule_id="human.label", description=case.reason)],
        )
        event = None
        error = None
        start = time.monotonic()
        try:
            if case.group not in guards:
                guards[case.group] = await asyncio.to_thread(
                    create_guard, config.guard, config.guard_policy
                )
            async with asyncio.timeout(config.step_timeout):
                decision = await guards[case.group].evaluate(
                    case.action.model_copy(deep=True), copy.deepcopy(case.context)
                )
            decision.latency_ms = (time.monotonic() - start) * 1000
            event = Event(
                seq=0,
                kind="plan" if case.action.kind == "plan" else "action",
                timestamp=utc_now(),
                intent_version=case.context["intent"].get("version", 1),
                action=case.action,
                context=case.context,
                verdict=verdict,
                decision=decision,
                result={"status": "replayed", "expected": case.expected},
            )
            event.hash = canonical_hash(event.model_dump(exclude={"hash"}))
            exact_matches += decision.action == case.expected
        except Exception as exception:
            error = safe_error(exception, config)
        episodes.append(
            EpisodeResult(
                id=f"{run_id}-{case.id}",
                scenario_id=case.id,
                scenario_version=dataset.version,
                domain=case.domain,
                family="labeled_trace",
                variant="trace",
                repeat=0,
                seed=config.seed,
                status="error" if error else "completed",
                steps=1,
                proposal_violations=int(not verdict.allowed and case.action.kind == "tool"),
                plan_violations=int(not verdict.allowed and case.action.kind == "plan"),
                duration_ms=(time.monotonic() - start) * 1000,
                error=error,
                events=[event] if event else [],
            )
        )
    for guard in guards.values():
        await close_adapter(guard)
    metrics = without_effect_scores(aggregate(episodes))
    metrics["exact_decision_accuracy"] = rate(
        exact_matches, sum(e.status == "completed" for e in episodes)
    )
    result = RunResult(
        id=run_id,
        started_at=started,
        suite_id=dataset.id,
        suite_version=dataset.version,
        config=config,
        manifest=manifest,
        episodes=episodes,
        metrics=metrics,
    )
    store.save(result)
    return result
