from __future__ import annotations

from functools import lru_cache
from importlib.resources import files
from pathlib import Path

import yaml

from .models import Intent, RunConfig, Scenario, Suite


def read_yaml(path: str | Path):
    with Path(path).open(encoding="utf-8") as file:
        return yaml.safe_load(file)


@lru_cache(maxsize=1)
def _core_suite() -> Suite:
    return Suite.model_validate(
        yaml.safe_load(files("agent_intent_bench").joinpath("data/suites/core.yaml").read_text())
    )


def load_suite(name_or_path: str = "core") -> Suite:
    path = Path(name_or_path)
    if path.exists():
        data = read_yaml(path)
    elif name_or_path == "research-factors":
        return Suite.model_validate(
            yaml.safe_load(
                files("agent_intent_bench")
                .joinpath("data/suites/research-factors.yaml")
                .read_text()
            )
        )
    else:
        if name_or_path not in {"core", "smoke", "email", "payments", "coding"}:
            raise ValueError(
                f"Unknown suite: {name_or_path}. Use core, smoke, email, payments, coding, or a YAML path."
            )
        data = _core_suite().model_dump()
    if "scenarios" not in data:
        scenario = Scenario.model_validate(data)
        return Suite(
            id=scenario.id,
            version=scenario.version,
            description=scenario.description,
            scenarios=[scenario],
        )
    suite = Suite.model_validate(data)
    if not path.exists() and name_or_path != "core":
        if name_or_path == "smoke":
            selected = [s for s in suite.scenarios if s.family == "injection"]
        else:
            selected = [s for s in suite.scenarios if s.domain == name_or_path]
        suite = suite.model_copy(update={"id": name_or_path, "scenarios": selected})
    return suite


def load_config(path: str | Path | None) -> RunConfig:
    return RunConfig.model_validate(read_yaml(path)) if path else RunConfig()


def load_policy(path: str | Path) -> Intent:
    return Intent.model_validate(read_yaml(path))


def validate_suite(suite: Suite) -> None:
    from .expressions import canonical_hash
    from .world import DeclarativeWorld

    canonical_hash(suite.model_dump())  # Reject non-finite numbers and non-JSON YAML values.

    for scenario in suite.scenarios:
        DeclarativeWorld(scenario)
