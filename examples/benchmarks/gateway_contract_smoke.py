"""Offline contract checks with installed upstream libraries; no browser sites or models."""

from __future__ import annotations

import argparse
from pathlib import Path
from unittest.mock import create_autospec

from agent_intent_bench.benchmarks.environments import GymnasiumEnvironment


def check_st():
    from playwright.sync_api import CDPSession, Page
    from stwebagentbench.browser_env import StateInfo
    from stwebagentbench.browser_env.custom_env import ActionTrace
    from stwebagentbench.evaluation_harness import CountActionEvaluator

    evaluator = CountActionEvaluator({"eval": {"action_type": "click", "global_count": 1}})
    page = create_autospec(Page, instance=True)
    client = create_autospec(CDPSession, instance=True)

    class Env:
        def reset(self, seed=None):
            self.trajectory = []
            return {"goal": "Native policy check"}, {}

        def step(self, action):
            self.trajectory.append(
                ActionTrace(
                    action={"action_type": "click"}, state=StateInfo(info={}, observation={})
                )
            )
            penalty, report = evaluator(self.trajectory, Path("unused.json"), page, client)
            return (
                {},
                0.375,
                len(self.trajectory) == 2,
                False,
                {"safety_penalty": penalty, "safety_report": [report]},
            )

        def close(self):
            pass

    env = GymnasiumEnvironment(Env(), "stwebagentbench", 42)
    env.reset()
    env.step("click('1')")
    env.step("click('2')")
    scores = env.grade()
    assert scores["reward"] == 0.375
    assert scores["final_info"]["safety_penalty"] == -1.0
    assert scores["safety_report"][0]["violated"] is False
    assert scores["safety_report"][1]["violated"] is True
    print("ST-WebAgentBench: actual native policy evaluator outputs preserved (offline fixture)")


def check_doom():
    from doomarena.core.attack_gateways.attack_gateway import AttackGateway

    class Gateway(AttackGateway):
        def reset(self, seed=None):
            return {"goal": "Native gateway check"}, {
                "task_info": {"success_filter_results": {"native": False}}
            }

        def step(self, action):
            return (
                {},
                0.375,
                True,
                False,
                {"task_info": {"success_filter_results": {"native": True}}},
            )

        def close(self):
            pass

    native = Gateway(None, [])
    env = GymnasiumEnvironment(native, "doomarena", 42)
    env.reset()
    env.step("noop()")
    scores = env.grade()
    assert scores["reward"] == 0.375
    assert scores["success_filter_results_by_step"] == {"native": [False, True]}
    env.close()
    print(
        "DoomArena: actual core AttackGateway contract preserved (offline fixture, no browser attack)"
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("benchmark", choices=["stwebagentbench", "doomarena"])
    args = parser.parse_args()
    (check_st if args.benchmark == "stwebagentbench" else check_doom)()
