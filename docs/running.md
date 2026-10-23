# Running evaluations

This guide covers local intent suites. For upstream websites and graders, use [native benchmarks](benchmarks.md); for live SDK enforcement, use [ArmorIQ setup](armoriq-inside.md).

## Start without credentials

```sh
git clone https://github.com/armoriq/agent-intent-gym.git
cd agent-intent-gym
uv sync --locked --extra dev
uv run intentbench matrix --suite smoke --agent gullible --guard reference
```

This compares a scripted agent with and without the local reference guard. It tests the infrastructure, not a model or ArmorIQ backend.

If you cloned the repository before its transfer to the ArmorIQ organization, update your existing checkout's remote:

```sh
git remote set-url origin https://github.com/armoriq/agent-intent-gym.git
```

| Suite | Cases | Purpose |
| --- | ---: | --- |
| `smoke` | 9 | Injection challenges and matched clean/helpful controls |
| `core` | 90 | Email, payments, coding × ten factors × three variants |
| `email`, `payments`, `coding` | 30 each | One domain from `core` |
| `research-factors` | 108 | Authored AgentLAB, IntentFlux, and InterruptBench adaptations |
| A YAML path | Your cases | A custom scenario or suite |

`smoke` and the domain suites are subsets of `core`. Research adaptations are not official upstream scores.

## Use the interfaces

```sh
uv run intentbench tui --suite smoke
uv run intentbench serve
# Browser: http://127.0.0.1:8765
```

Select the suite, agent, guard, mode, seed, and budget; inspect results and traces after a run. YAML `--config` supplies advanced settings. The browser's Benchmark ecosystem view and `intentbench benchmarks tui` handle native runs.

## Common CLI tasks

| Task | Command after `uv run intentbench` |
| --- | --- |
| List suites / inspect a suite | `suites` / `suites core` |
| Validate definitions | `validate core` |
| Run one case | `run --suite smoke --scenario payments.injection.clean` |
| Bring an agent configuration | `run --suite smoke --config examples/python-agent.yaml` |
| Compare unguarded and enforced conditions | `matrix --suite smoke --config run.yaml` |
| List / inspect results | `history` / `show RUN_ID` |
| Inspect one trajectory | `show RUN_ID --episode email.injection.attack` |
| Compare saved runs | `compare BASELINE_RUN GUARDED_RUN` |
| Evaluate a guard on saved proposals | `replay RUN_ID --guard reference` |
| Score independently labeled proposals | `score-traces examples/labeled-traces.yaml` |
| Export / check integrity | `export RUN_ID --output episodes.csv --format csv` / `verify RUN_ID` |
| Apply a CI threshold | `gate RUN_ID --min-cup 0.9 --max-effects 0` |

Use `--help` on any command for all flags. Select cases with `--scenario` or `--tag`; control repeats, seed, steps, timeouts, and concurrency in the run YAML. [Evaluation design](evaluation-design.md) explains which comparisons are meaningful.

## Where results go

| Location | Contents |
| --- | --- |
| `.intentbench/runs/RUN_ID/` | Local suite/config snapshots, manifest, episodes, `results.json`, `events.jsonl` |
| `.intentbench/benchmarks/RUN_ID/` | Native setup/provenance, original grades, decisions, transitions |
| `.intentbench/experiments/ID/results.json` | Matched-run summary linking individual run IDs |

Partial episode checkpoints survive later failures. Local traces use hash chains; native result/config/manifest files use retained hashes. These detect edits against the retained record, not cryptographic authorship.

Credentials come from environment variables or ignored `.env` files. Task data, arguments, and outputs do appear in local artifacts. The workbench binds to loopback; binding elsewhere requires `INTENTBENCH_API_TOKEN`. Python factories are trusted code, and the workbench is a local single-user service.
