"""Native InterruptBench grader check; no websites or live-agent evaluation."""

from pathlib import Path

from browser_env.actions import create_stop_action
from evaluation_harness.evaluators import StringEvaluator, _get_scoring_intent


def main():
    source = Path(".benchmarks/sources/interruptbench/Eval")
    config = source / "tests/test_evaluation_harness/configs/string_match.json"
    evaluator = StringEvaluator()
    assert evaluator([create_stop_action("The date is 1985/04/18")], str(config)) == 1.0
    assert evaluator([create_stop_action("The date is 1936/04/18")], str(config)) == 0.0
    assert _get_scoring_intent({"intent": "stale", "true_intent": "current"}) == "current"
    print(
        "InterruptBench native string grader and current-intent checks passed; no web tasks evaluated."
    )


if __name__ == "__main__":
    main()
