"""Launch an installed, isolated native runtime while retaining shared run artifacts."""

from __future__ import annotations

import asyncio
import json
import os
import sys
from pathlib import Path

from .models import NativeEpisode


def installed_runtime(benchmark):
    return Path.cwd() / ".benchmarks" / "runtimes" / benchmark


def requires_dispatch(config):
    return (
        config.runtime == "installed"
        and not os.environ.get("INTENTBENCH_RUNTIME_CHILD")
        and Path(sys.prefix).resolve() != installed_runtime(config.benchmark).resolve()
    )


async def run_in_runtime(config, store, progress, stop, run_id):
    runtime = installed_runtime(config.benchmark)
    python = runtime / "bin" / "python"
    if not python.exists():
        raise ValueError(f"Install the {config.benchmark} runtime first: {runtime}")
    jobs = store.root / ".runtime-jobs"
    jobs.mkdir(exist_ok=True)
    config_file, stop_file, log_file = [
        jobs / f"{run_id}.{suffix}" for suffix in ("json", "stop", "log")
    ]
    config_file.write_text(config.model_dump_json())
    env = dict(os.environ)
    env["INTENTBENCH_RUNTIME_CHILD"] = "1"
    paths = [str(Path.cwd())]
    if config.benchmark == "stwebagentbench":
        paths.append(str(Path.cwd() / ".benchmarks/sources/stwebagentbench"))
    if env.get("PYTHONPATH"):
        paths.append(env["PYTHONPATH"])
    env["PYTHONPATH"] = os.pathsep.join(paths)
    # Public environment URLs only. Credentials continue to come from the calling shell.
    env_file = Path.cwd() / ".benchmarks" / "environment-urls.json"
    if env_file.exists():
        for key, value in json.loads(env_file.read_text()).get(config.benchmark, {}).items():
            if key not in {"MINIWOB_URL", "WA_SUITECRM", "SUITECRM", "GITLAB", "SHOPPING_ADMIN"}:
                raise ValueError("Environment URL inventory contains an unsupported variable")
            env.setdefault(key, value)
    seen = set()
    with log_file.open("wb") as log:
        process = await asyncio.create_subprocess_exec(
            str(python),
            "-m",
            "agent_intent_bench.benchmarks.worker",
            str(config_file),
            str(store.root.parent),
            run_id,
            str(stop_file),
            env=env,
            stdout=log,
            stderr=log,
        )
        try:
            while process.returncode is None:
                if stop.is_set():
                    stop_file.touch(exist_ok=True)
                folder = store.path(run_id) / "episodes"
                for path in folder.glob("*.json"):
                    if path.name not in seen:
                        episode = NativeEpisode.model_validate_json(path.read_text())
                        seen.add(path.name)
                        if progress:
                            await asyncio.to_thread(
                                progress, episode, len(seen), len(config.task_ids) * config.repeats
                            )
                try:
                    await asyncio.wait_for(process.wait(), 0.25)
                except TimeoutError:
                    pass
        except asyncio.CancelledError:
            stop_file.touch(exist_ok=True)
            await process.wait()
            raise
    if process.returncode:
        raise RuntimeError(f"Native runtime exited {process.returncode}; inspect {log_file}")
    result = store.get(run_id)
    if progress:
        for episode in result.episodes:
            if f"{episode.id}.json" not in seen:
                seen.add(f"{episode.id}.json")
                await asyncio.to_thread(progress, episode, len(seen), len(result.episodes))
    return result
