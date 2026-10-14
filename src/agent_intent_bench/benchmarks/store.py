from __future__ import annotations

import json
import re
from pathlib import Path

from ..expressions import canonical_hash
from .models import BenchmarkResult, NativeEpisode


class BenchmarkStore:
    """Separate namespace: native grades must never masquerade as the local intent oracle."""

    def __init__(self, root: str | Path = ".intentbench"):
        self.root = Path(root).resolve() / "benchmarks"
        self.root.mkdir(parents=True, exist_ok=True)

    def path(self, run_id: str) -> Path:
        if not re.fullmatch(r"[a-zA-Z0-9_-]+", run_id):
            raise ValueError("Invalid benchmark run ID")
        return self.root / run_id

    def begin(self, run_id: str, config: dict, manifest: dict):
        folder = self.path(run_id)
        folder.mkdir(exist_ok=False)
        (folder / "episodes").mkdir()
        for name, value in [("config.json", config), ("manifest.json", manifest)]:
            (folder / name).write_text(json.dumps(value, indent=2, allow_nan=False))

    def save_episode(self, run_id: str, episode: NativeEpisode):
        (self.path(run_id) / "episodes" / f"{episode.id}.json").write_text(
            episode.model_dump_json(indent=2)
        )

    def save(self, result: BenchmarkResult):
        folder = self.path(result.id)
        payload = result.model_dump(mode="json")
        temporary = folder / "results.tmp"
        temporary.write_text(json.dumps(payload, indent=2, allow_nan=False))
        temporary.replace(folder / "results.json")
        # Whole-result integrity including config, native scores, and all transitions.
        (folder / "results.sha256").write_text(canonical_hash(payload))

    def get(self, run_id: str) -> BenchmarkResult:
        return BenchmarkResult.model_validate_json((self.path(run_id) / "results.json").read_text())

    def verify(self, run_id: str) -> bool:
        folder = self.path(run_id)
        result = json.loads((folder / "results.json").read_text())
        manifest = json.loads((folder / "manifest.json").read_text())
        config = json.loads((folder / "config.json").read_text())
        return (
            canonical_hash(result) == (folder / "results.sha256").read_text()
            and canonical_hash(result["manifest"]) == canonical_hash(manifest)
            and canonical_hash(result["config"]) == canonical_hash(config)
        )

    def list(self):
        rows = []
        for target in self.root.glob("*/results.json"):
            result = self.get(target.parent.name)
            rows.append(
                {
                    "id": result.id,
                    "benchmark": result.benchmark,
                    "started_at": result.started_at,
                    **result.summary,
                }
            )
        return sorted(rows, key=lambda row: row["started_at"], reverse=True)
