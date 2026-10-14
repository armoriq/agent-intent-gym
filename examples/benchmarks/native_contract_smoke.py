"""Offline compatibility check with actual installed AgentDojo. Not model benchmark results."""

from agent_intent_bench.benchmarks.environments import AgentDojoEnvironment
from agent_intent_bench.benchmarks.models import BenchmarkConfig


def main():
    from agentdojo.task_suite.load_suites import get_suite

    for suite in ("workspace", "banking", "travel", "slack"):
        attack_id = next(iter(get_suite("v1.2.2", suite).injection_tasks))
        config = BenchmarkConfig(
            benchmark="agentdojo",
            task_ids=["user_task_0"],
            agent={"kind": "python", "factory": "examples.benchmarks.native_agent:create_agent"},
            options={
                "suite": suite,
                "benchmark_version": "v1.2.2",
                "injection_task_id": attack_id,
            },
        )
        env = AgentDojoEnvironment(config, "user_task_0", 42)
        observation, _ = env.reset()
        assert "injection_task_id" not in observation and "ground_truth" not in observation
        # Only the compatibility checker accesses ground truth. The agent channel never does.
        for call in env.task.ground_truth(env.before):
            _, _, _, _, info = env.step(
                {"kind": "tool", "tool": call.function, "args": call.model_dump()["args"]}
            )
            assert info["tool_error"] is None, info
        env.step({"kind": "finish", "args": {"output": env.task.GROUND_TRUTH_OUTPUT}})
        scores = env.grade()
        output = [{"type": "text", "content": env.output}]
        assert scores["utility"] == env.suite._check_user_task_utility(
            env.task, output, env.before, env.environment, env.traces
        )
        assert scores["attack_success"] == env.suite._check_injection_task_security(
            env.attack, output, env.before, env.environment, env.traces
        )
        assert scores["utility"] is True, scores
        env.close()
        print(f"{suite}: native tools and upstream utility/attack predicates agree")
    # A successful attacker goal must retain upstream True semantics (not invert 'security').
    config.options.update(suite="banking", injection_task_id="injection_task_0")
    env = AgentDojoEnvironment(config, "user_task_0", 42)
    env.reset()
    for call in env.attack.ground_truth(env.before):
        env.step({"kind": "tool", "tool": call.function, "args": call.model_dump()["args"]})
    env.step({"kind": "finish", "args": {"output": env.attack.GROUND_TRUTH_OUTPUT}})
    assert env.grade()["attack_success"] is True
    print(
        "Native attack-success polarity verified. This is a contract check, not agent evaluation."
    )
    env.close()
    config.options["attack_factory"] = "examples.benchmarks.agentdojo_attack:create_attack"
    env = AgentDojoEnvironment(config, "user_task_0", 42)
    env.reset()
    assert env.applied_injections
    assert env.reproducibility()["injections"] == env.applied_injections
    env.close()
    print("Native fixed-template attack generation and injection mapping verified")


if __name__ == "__main__":
    main()
