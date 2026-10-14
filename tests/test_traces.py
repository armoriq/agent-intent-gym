from agent_intent_bench.catalog import read_yaml
from agent_intent_bench.models import AdapterConfig, RunConfig, TraceDataset
from agent_intent_bench.store import Store, verify_events
from agent_intent_bench.traces import evaluate_traces


async def test_custom_trace_labels_distinguish_allow_block_and_hold(tmp_path):
    dataset = TraceDataset.model_validate(read_yaml("examples/labeled-traces.yaml"))
    result = await evaluate_traces(dataset, RunConfig(), Store(tmp_path))
    assert result.metrics["exact_decision_accuracy"] == 1
    assert result.metrics["guard_detection_rate"] == 1
    assert result.metrics["guard_overblocking_rate"] == 0
    assert result.metrics["completion_under_policy"] is None
    assert result.metrics["unauthorized_effect_rate"] is None
    assert result.config.agent.kind == "recorded"
    assert all(verify_events(e.events) for e in result.episodes)


async def test_block_all_is_not_perfect_on_trace_decision_labels(tmp_path):
    dataset = TraceDataset.model_validate(read_yaml("examples/labeled-traces.yaml"))
    result = await evaluate_traces(
        dataset, RunConfig(guard=AdapterConfig(kind="deny")), Store(tmp_path)
    )
    assert result.metrics["exact_decision_accuracy"] < 1
    assert result.metrics["guard_overblocking_rate"] == 1
