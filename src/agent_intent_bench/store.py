from __future__ import annotations

import json
import re
import sqlite3
from pathlib import Path
from typing import Any

import yaml

from .expressions import canonical_hash
from .models import EpisodeResult, Event, RunResult, Suite


class Store:
    """Portable JSON/YAML/JSONL artifacts plus a small local SQLite index."""

    def __init__(self, root: str | Path = ".intentbench"):
        self.root = Path(root).resolve()
        self.root.mkdir(parents=True, exist_ok=True)
        self.db = self.root / "index.sqlite3"
        with self.connect() as connection:
            connection.execute(
                "CREATE TABLE IF NOT EXISTS runs (id TEXT PRIMARY KEY, started_at TEXT, suite TEXT, agent TEXT, guard TEXT, mode TEXT, status TEXT, cup REAL, effects REAL, episodes INTEGER)"
            )

    def connect(self):
        return sqlite3.connect(self.db, timeout=30)

    def path(self, run_id: str) -> Path:
        if not re.fullmatch(r"[a-zA-Z0-9_-]+", run_id):
            raise ValueError("Invalid run ID")
        return self.root / "runs" / run_id

    def begin(
        self, run_id: str, started_at: str, suite: Suite, config: dict, manifest: dict
    ) -> None:
        path = self.path(run_id)
        path.mkdir(parents=True, exist_ok=False)
        (path / "suite.yaml").write_text(
            yaml.safe_dump(suite.model_dump(mode="json"), sort_keys=False), encoding="utf-8"
        )
        (path / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
        (path / "config.yaml").write_text(yaml.safe_dump(config, sort_keys=False), encoding="utf-8")
        with self.connect() as connection:
            connection.execute(
                "INSERT INTO runs VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    run_id,
                    started_at,
                    suite.id,
                    config["agent"]["kind"],
                    config["guard"]["kind"],
                    config["mode"],
                    "running",
                    None,
                    None,
                    0,
                ),
            )

    def save(self, result: RunResult) -> Path:
        path = self.path(result.id)
        temporary = path / "results.tmp"
        temporary.write_text(result.model_dump_json(indent=2), encoding="utf-8")
        temporary.replace(path / "results.json")
        with (path / "events.jsonl").open("w", encoding="utf-8") as file:
            for episode in result.episodes:
                for event in episode.events:
                    file.write(
                        json.dumps(
                            {
                                "episode_id": episode.id,
                                "scenario_id": episode.scenario_id,
                                "event": event.model_dump(mode="json"),
                            },
                            ensure_ascii=False,
                        )
                        + "\n"
                    )
        metrics = result.metrics
        status = (
            "cancelled"
            if metrics.get("cancelled")
            else "error"
            if metrics.get("errors")
            else "complete"
        )
        with self.connect() as connection:
            connection.execute(
                "UPDATE runs SET status=?, cup=?, effects=?, episodes=? WHERE id=?",
                (
                    status,
                    metrics.get("completion_under_policy"),
                    metrics.get("unauthorized_effect_rate"),
                    len(result.episodes),
                    result.id,
                ),
            )
        return path

    def get(self, run_id: str) -> RunResult:
        return RunResult.model_validate_json(
            (self.path(run_id) / "results.json").read_text(encoding="utf-8")
        )

    def save_episode(self, run_id: str, episode: EpisodeResult) -> None:
        folder = self.path(run_id) / "episodes"
        folder.mkdir(exist_ok=True)
        target = folder / f"{episode.id}.json"
        temporary = target.with_suffix(".tmp")
        temporary.write_text(episode.model_dump_json(indent=2), encoding="utf-8")
        temporary.replace(target)

    def list(self, limit: int = 100) -> list[dict[str, Any]]:
        with self.connect() as connection:
            connection.row_factory = sqlite3.Row
            return [
                dict(row)
                for row in connection.execute(
                    "SELECT * FROM runs ORDER BY started_at DESC LIMIT ?", (limit,)
                )
            ]


def verify_events(events: list[Event]) -> bool:
    previous = ""
    for seq, event in enumerate(events):
        if event.seq != seq or event.prev_hash != previous:
            return False
        if event.hash != canonical_hash(event.model_dump(exclude={"hash"})):
            if event.hash != canonical_hash(event.model_dump(exclude={"hash"}, exclude_unset=True)):
                return False
        previous = event.hash
    return True
