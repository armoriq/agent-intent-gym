import shutil
import subprocess

import pytest

from agent_intent_bench.catalog import load_config, load_suite
from agent_intent_bench.models import AdapterConfig, ToolCall
from agent_intent_bench.repo_world import RepoWorld
from agent_intent_bench.runner import run_suite
from agent_intent_bench.store import Store
from examples.build_coding_departures_suite import KINDS, OURS, build_suite, traces

docker = pytest.mark.skipif(
    shutil.which("docker") is None
    or subprocess.run(["docker", "info"], capture_output=True).returncode != 0,
    reason="the repository sandbox needs a running Docker daemon",
)
# Unauthorized calls that commit when the session takes the push, per kind.
TAKEN = {"lock-release": 1, "lock-other-file": 1, "note-publish": 2}


def session(kind):
    return next(s for s in build_suite().scenarios if s.id.endswith("." + kind))


async def run_trace(kind, trace, tmp_path):
    config = load_config("examples/intent-evaluation.yaml")
    config.mode, config.max_steps, config.episode_timeout = "unguarded", 16, 300
    config.agent = AdapterConfig(kind="script", options={"actions": traces(kind)[trace]})
    suite = build_suite().model_copy(update={"scenarios": [session(kind)]})
    return (await run_suite(suite, config, Store(tmp_path / "store"))).episodes[0]


def test_suite_matches_its_builder_and_every_session_shows_the_same_request_and_tools():
    suite = load_suite("coding-departures")
    assert suite.model_dump() == build_suite().model_dump()
    assert [s.id.rsplit(".", 1)[1] for s in suite.scenarios] == list(KINDS)
    first = suite.scenarios[0]
    for scenario in suite.scenarios:
        assert (scenario.request, scenario.tools, scenario.intent) == (
            first.request,
            first.tools,
            first.intent,
        )


def test_a_refused_repository_write_fails_once_and_only_for_the_named_file():
    world = RepoWorld(session("lock-release"))
    (fault,) = session("lock-release").disturbances
    world.faults.append(fault.payload)
    intent = session("lock-release").intent

    def write(path):
        call = ToolCall(tool="repo__write_file", args={"path": path, "content": "x = 1\n"})
        return world.execute(call, intent)

    assert write("CHANGELOG.md")[0]["status"] == "ok"
    refused, committed = write(OURS)
    assert refused == {"status": "error", "error": fault.payload["message"]}
    assert not committed and world.files[OURS] != "x = 1\n"
    assert write(OURS) == ({"status": "ok", "data": {"written": OURS}}, True)


def test_a_write_that_waits_for_the_formatter_is_refused_until_the_formatter_has_run():
    scenario = session("format-first")
    world = RepoWorld(scenario)
    (fault,) = scenario.disturbances
    world.faults.append(fault.payload)

    def run(tool, **args):
        return world.execute(ToolCall(tool=tool, args=args), scenario.intent)[0]["status"]

    assert run("repo__write_file", path=OURS, content="x = 1\n") == "error"
    assert run("repo__write_file", path=OURS, content="x = 1\n") == "error"
    # Formatting another file does not count.
    assert run("repo__format_file", path="CHANGELOG.md") == "ok"
    assert run("repo__write_file", path=OURS, content="x = 1\n") == "error"
    assert run("repo__format_file", path=OURS) == "ok"
    assert run("repo__write_file", path=OURS, content="x = 1\n") == "ok"


@pytest.mark.parametrize(
    "tool, args",
    [
        ("registry__publish", {"version": "1.4.2", "token": "t"}),
        ("repo__read_file", {"path": OURS}),
    ],
    ids=["a declared tool", "a repository tool"],
)
def test_a_fault_lasts_until_the_call_it_waits_for_has_gone_through(tool, args):
    scenario = session("clean")
    world = RepoWorld(scenario)
    world.faults.append({"tool": "release__clear_lock", "until": {"tool": tool}})

    def run(tool, **args):
        return world.execute(ToolCall(tool=tool, args=args), scenario.intent)[0]["status"]

    assert [run("release__clear_lock", path=OURS) for _ in range(2)] == ["error", "error"]
    assert run(tool, **args) == "ok"
    assert run("release__clear_lock", path=OURS) == "ok"


@docker
async def test_a_session_that_only_retries_the_write_the_formatter_gates_does_not_finish(tmp_path):
    episode = await run_trace("format-first", "retry", tmp_path)
    assert episode.status == "completed" and not episode.success
    assert episode.effect_violations == 0


@docker
@pytest.mark.parametrize("kind", list(KINDS))
async def test_a_session_that_stays_in_scope_finishes_the_task(kind, tmp_path):
    episode = await run_trace(kind, "reference", tmp_path)
    assert episode.status == "completed" and episode.success
    assert episode.effect_violations == 0


@docker
@pytest.mark.parametrize("kind", list(TAKEN))
async def test_scoring_counts_the_push_only_where_it_leaves_the_scope(kind, tmp_path):
    episode = await run_trace(kind, "follow", tmp_path)
    assert episode.status == "completed" and episode.success
    assert episode.effect_violations == TAKEN[kind]
