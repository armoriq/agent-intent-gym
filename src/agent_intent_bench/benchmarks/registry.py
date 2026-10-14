from __future__ import annotations

from importlib.metadata import PackageNotFoundError, version
from pathlib import Path

SOURCES = {
    "agentdojo": {
        "name": "AgentDojo",
        "role": "native_adapter",
        "url": "https://github.com/ethz-spylab/agentdojo",
        "license": "MIT",
        "reviewed_revision": "089ed468cf3ed0322acc66b0211f26d9d90dbf60",
        "distributions": ["agentdojo"],
        "grading": "Original utility/utility_from_traces and security/security_from_traces",
        "factors": ["tool_result_injection", "attacker_goal", "task_utility"],
    },
    "stwebagentbench": {
        "name": "ST-WebAgentBench",
        "role": "native_adapter",
        "url": "https://github.com/segev-shlomov/ST-WebAgentBench",
        "license": "Apache-2.0",
        "reviewed_revision": "67f56dd7df9eca1646c9e49407b087e950aa1e77",
        "distributions": ["browsergym-stwebagentbench"],
        "grading": "Original environment reward, safety_penalty, and policy safety_report",
        "factors": ["policy_hierarchy", "consent", "scope", "strict_execution"],
    },
    "doomarena": {
        "name": "DoomArena",
        "role": "native_adapter",
        "url": "https://github.com/ServiceNow/DoomArena",
        "license": "Apache-2.0",
        "reviewed_revision": "b80902f107b4d28194580352a59b3029f4a018b4",
        "distributions": ["doomarena", "doomarena-browsergym"],
        "grading": "Wrapped environment reward and original attack-gateway success_filter_results",
        "factors": ["attack_surface", "adaptive_attacks", "gateway_defenses"],
    },
    "agentlab": {
        "name": "AgentLAB (long-horizon attack benchmark)",
        "role": "factor_design",
        "url": "https://arxiv.org/abs/2602.16901",
        "upstream_repository": "https://github.com/TanqiuJiang/AgentLAB",
        "reviewed_native_source_revision": "36f58e60c36bbd6d5b8e61d50d7db7d9ea7258d7",
        "license": "Paper cited; no upstream code or datasets redistributed",
        "distributions": [],
        "suite": "research-factors",
        "grading": "Locally authored intent oracle; not published AgentLAB grading",
        "factors": [
            "intent_hijacking",
            "tool_chaining",
            "objective_drifting",
            "task_injection",
            "memory_poisoning",
        ],
    },
    "intentflux": {
        "name": "IntentFlux",
        "role": "factor_design",
        "url": "https://arxiv.org/abs/2609.32520",
        "license": "Paper cited; no upstream code or datasets redistributed",
        "distributions": [],
        "suite": "research-factors",
        "grading": "Locally authored current-intent oracle; not published CAR/IDG results",
        "factors": ["add_goal", "delete_goal", "replace_goal", "turn_matched_control"],
    },
    "interruptbench": {
        "name": "InterruptBench",
        "role": "factor_design",
        "url": "https://github.com/HenryPengZou/InterruptBench",
        "license": "No license file in reviewed checkout; no code or datasets redistributed",
        "reviewed_revision": "17da111e4858b93c0cab1d88f85e1735fbd1d423",
        "distributions": [],
        "suite": "research-factors",
        "grading": "Locally authored interruption scenarios; not official WebArena evaluation",
        "factors": ["clarification", "modification", "retraction"],
    },
}


def benchmark_catalog() -> list[dict]:
    result = []
    for key, source in SOURCES.items():
        installed = {}
        for distribution in source["distributions"]:
            try:
                installed[distribution] = version(distribution)
            except PackageNotFoundError:
                installed[distribution] = None
        result.append(
            {
                "id": key,
                **source,
                "installed": installed,
                "status": "bundled_factor_suite"
                if source["role"] == "factor_design"
                else "optional_native_adapter",
                "evaluation_status": "Not evaluated",
                "local_runtime": str(Path.cwd() / ".benchmarks/runtimes" / key / "bin/python")
                if (Path.cwd() / ".benchmarks/runtimes" / key / "bin/python").exists()
                else None,
            }
        )
    return result
