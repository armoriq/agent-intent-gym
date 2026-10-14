# Contributing

The repository is the ArmorIQ Agent Intent Gym toolkit; AgentIntentBench is its reference evaluation suite. Python imports and the distribution retain the `agent_intent_bench` / `agent-intent-bench` names, and the command is `intentbench`.

## Development

Use Python 3.11 and uv. No model or ArmorIQ credentials are needed for the base checks:

```sh
uv sync --locked --extra dev
uv run ruff check src tests examples scripts
uv run ruff format --check src tests examples scripts
uv run pytest -q
uv run intentbench validate core
uv run intentbench validate research-factors
uv run intentbench matrix --suite smoke --agent gullible
uv build
uv run python scripts/check_repository.py
```

Tests that exercise the actual optional ArmorIQ SDK skip when it is absent. See [ArmorIQ-inside setup](docs/armoriq-inside.md) to install it, then run tests with `uv run --no-sync pytest -q`. These tests use offline transports and synthetic credentials; they never require a production account. Native benchmark and browser smoke checks depend on the separate upstream runtime and website setup described in [benchmarks.md](docs/benchmarks.md).

CI checks both the base installation and `uv sync --locked --extra dev --extra armoriq`, using the public SDK locked in `uv.lock`. SDK tests disable trace shipping and mock backend requests.

Keep a local `.env` for credentials. Only `.env.example` belongs in Git, with credential fields blank. Local runtime checkouts, benchmark artifacts, caches, logs, and package builds are ignored. `check_repository.py` examines staged/tracked files and never prints secret values. Run it before a commit; it also runs in CI.

## Evaluation changes

Preserve native graders and original action execution. Do not turn missing reports, cancelled runs, outages, or truncated trials into successful safety results. Keep native outcomes, authored intent-oracle metrics, and derived summaries distinct. Label fixtures and research-factor adaptations explicitly. Include independent labels before reporting guard detection or overblocking on native tasks.

For a new benchmark adapter, provide the public observation/agent protocol, source provenance, original grading contract, setup requirements, action-to-policy mapping, and meaningful executor/grader preservation tests. For an authored scenario, follow [authoring.md](docs/authoring.md), maintain clean and authorized controls, and use versioned contracts. Changes to scenario semantics or scoring should update the corresponding versions and result interpretation.

Explain the concrete behavior change and how it was verified in pull requests. Contributions use the repository's MIT license; preserve notices for third-party code and data.
