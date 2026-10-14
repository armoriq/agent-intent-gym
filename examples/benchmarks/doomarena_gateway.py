"""Construct the actual upstream gateway; attack configs remain owned by DoomArena."""

from agent_intent_bench.benchmarks.common import load_symbol


def create_gateway(task_id, seed, options):
    import browsergym.webarena  # noqa: F401 -- register upstream environment IDs
    import gymnasium
    from browsergym.core.action.highlevel import HighLevelActionSet
    from doomarena.browsergym.attack_gateway import BrowserGymAttackGateway

    attacks = load_symbol(options["attack_config_factory"])(task_id=task_id, seed=seed)
    actions = HighLevelActionSet(subsets=["bid", "chat", "nav"], multiaction=False)
    env = gymnasium.make(
        task_id, headless=options.get("headless", True), action_mapping=actions.to_python_code
    )
    try:
        return BrowserGymAttackGateway(
            env,
            attacks,
            task_name=task_id,
            abort_on_detection=options.get("abort_on_detection", False),
            abort_on_successful_attack=options.get("abort_on_successful_attack", True),
        )
    except Exception:
        env.close()
        raise
