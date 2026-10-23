"""Matched conditions across native upstream graders and gym intent scenarios."""

from __future__ import annotations

import asyncio
import json
import uuid
from pathlib import Path
from typing import Literal

import typer
import yaml
from pydantic import Field

from .benchmarks.cli import load_benchmark_config
from .benchmarks.runner import run_benchmark
from .benchmarks.store import BenchmarkStore
from .catalog import load_config, load_suite
from .errors import safe_error
from .expressions import canonical_hash
from .models import Model
from .runner import run_suite
from .session import utc_now
from .settings import model_identity, protection_identity, require_armoriq_credentials
from .store import Store

app = typer.Typer(help="Matched agents with and without ArmorIQ")
CONDITIONS = {"unguarded": "unguarded", "armoriq-monitor": "monitor", "armoriq-enforce": "enforce"}


class Track(Model):
    name: str
    kind: Literal["native", "gym"]
    config: str
    suite: str | None = None


class Experiment(Model):
    tracks: list[Track] = Field(min_length=1)
    conditions: list[Literal["unguarded", "armoriq-monitor", "armoriq-enforce"]] = Field(
        default_factory=lambda: list(CONDITIONS), min_length=1
    )


def matched_config(config, condition):
    if condition not in CONDITIONS:
        raise ValueError("Unknown condition: " + condition)
    if config.guard is None or config.guard.kind != "armoriq":
        raise ValueError("Experiment templates require an ArmorIQ guard")
    data = config.model_dump()
    data.update(mode=CONDITIONS[condition], instrumentation="inside")
    return type(config).model_validate(data)


def pairing_identity(config):
    data = config.model_dump()
    for key in ("guard", "guard_policy", "mode", "instrumentation"):
        data.pop(key, None)
    data["resolved_agent"] = model_identity(config.agent)
    return canonical_hash(data)


async def run_experiment(
    profile: Path, store: Path, selected_track=None, conditions=None, progress=None
):
    specification = Experiment.model_validate(yaml.safe_load(profile.read_text()))
    selected = conditions or specification.conditions
    if len(set(selected)) != len(selected) or set(selected) - CONDITIONS.keys():
        raise ValueError("Conditions must be unique: " + ", ".join(CONDITIONS))
    tracks = [t for t in specification.tracks if not selected_track or t.name == selected_track]
    if not tracks:
        raise ValueError("No matching track")
    prepared = []
    # Preflight all configurations and credentials before spending model tokens.
    for track in tracks:
        config_path = profile.parent / track.config
        config = (
            load_benchmark_config(config_path)
            if track.kind == "native"
            else load_config(config_path)
        )
        variants = [(condition, matched_config(config, condition)) for condition in selected]
        if any(c != "unguarded" for c in selected):
            require_armoriq_credentials(config.guard)
            protection_identity(config.guard)
        suite = load_suite(track.suite or "smoke") if track.kind == "gym" else None
        prepared.append((track, variants, suite))
    experiment_id = uuid.uuid4().hex[:12]
    folder = store / "experiments" / experiment_id
    folder.mkdir(parents=True)
    report = {
        "id": experiment_id,
        "started_at": utc_now(),
        "profile": specification.model_dump(),
        "runs": [],
        "score_semantics": "Native metrics and gym metrics remain separate; no pooled leaderboard score.",
    }
    path = folder / "results.json"
    path.write_text(json.dumps(report, indent=2))
    for track, variants, suite in prepared:
        identity = pairing_identity(variants[0][1])
        for condition, config in variants:
            if pairing_identity(config) != identity:
                raise ValueError("Agent/environment changed across matched conditions")
            if progress:
                progress(f"{track.name} · {condition}")
            if track.kind == "native":
                result = await run_benchmark(config, BenchmarkStore(store))
                scores = [
                    {
                        "task_id": e.task_id,
                        "repeat": e.repeat,
                        "seed": e.seed,
                        "status": e.status,
                        "native_scores": e.native_scores,
                        "derived_scores": e.derived_scores,
                        "native_steps_executed": sum(
                            t.get("native_step_executed", False) for t in e.transitions
                        ),
                        "state_reset": e.state_reset.model_dump() if e.state_reset else None,
                        "guard_decisions": e.guard_decisions,
                        "error": e.error,
                    }
                    for e in result.episodes
                ]
                summary = result.summary
            else:
                result = await run_suite(suite, config, Store(store))
                scores, summary = None, result.metrics
            report["runs"].append(
                {
                    "track": track.name,
                    "kind": track.kind,
                    "condition": condition,
                    "run_id": result.id,
                    "pairing_hash": identity,
                    "model_identity": result.manifest["model_identity"],
                    "protection_identity": result.manifest.get("protection_identity"),
                    "summary": summary,
                    "native_episodes": scores,
                }
            )
            path.write_text(json.dumps(report, indent=2, allow_nan=False))
    return path, report


@app.command("run")
def run(
    profile: Path,
    store: Path = Path(".intentbench"),
    track: str | None = None,
    conditions: str | None = None,
):
    """Run all or one profile track. --conditions is a comma-separated selection."""
    try:
        path, report = asyncio.run(
            run_experiment(
                profile, store, track, conditions.split(",") if conditions else None, typer.echo
            )
        )
        typer.echo("Saved " + str(path))
        for row in report["runs"]:
            typer.echo(f"{row['track']} · {row['condition']} · {row['run_id']}")
        if any(
            row["summary"].get("error", row["summary"].get("errors", 0)) for row in report["runs"]
        ):
            raise typer.Exit(2)
    except (ValueError, FileNotFoundError, ImportError) as error:
        typer.echo(safe_error(error), err=True)
        raise typer.Exit(2) from error
