# Run native benchmarks

Native adapters keep upstream tasks, attacks, execution, and graders. The separate `research-factors` suite contains authored adaptations scored by the local intent oracle.

| Source | Integration | Output / scope |
| --- | --- | --- |
| [AgentDojo](https://github.com/ethz-spylab/agentdojo) | Native suite and functions runtime | Original utility and attack success |
| [ST-WebAgentBench](https://github.com/segev-shlomov/ST-WebAgentBench) | Native BrowserGym environment | Reward, safety penalties, every policy report |
| [DoomArena](https://github.com/ServiceNow/DoomArena) | Native attack gateway factory | Underlying reward and original success filters |
| [AgentLAB](https://arxiv.org/abs/2602.16901) | Five authored factors; separate original-entrypoint smoke | 45 local cases; native smoke judge is uncalibrated |
| [IntentFlux](https://arxiv.org/abs/2609.32520) | Four authored factors | 36 local cases; no installable native release located |
| [InterruptBench](https://github.com/HenryPengZou/InterruptBench) | Three authored factors; native inputs/grader checked | 27 local cases; original WebArena services still needed |

The AgentLAB long-horizon paper is distinct from ServiceNow's `agentlab` package used by DoomArena. [Results](benchmark-results.md) and [licenses](../THIRD_PARTY_NOTICES.md) record the evidence and attribution.

## Why supplement native grades with intent evaluation

Native task, configured attacker-goal and environment-policy checks answer specific questions. They do not by themselves certify every operation against an arbitrary user's authorization. Our selected AgentDojo probes expose collateral actions, reads that leave state unchanged and extra BCCs that utility alone accepts. DoomArena correctly detects both egress routes and exposes a limitation in our guard's click context. We keep these native results intact and add independently authored authorization labels.

Use the [intent-evaluation guide](intent-evaluation.md) for the evidence, reusable local scenarios, content/identity/workspace baseline comparisons, and adapters for other agents and guards. ST's native policies remain part of its grading; no new intent probes have been evaluated on ST.

## Install and choose a recipe

```sh
uv run python scripts/install_benchmarks.py agentdojo stwebagentbench doomarena
uv run intentbench benchmarks list
uv run intentbench benchmarks run examples/benchmarks/local-qwen-agentdojo.yaml
```

Omit installer names to install all available profiles. Checkouts live under `.benchmarks/sources`, isolated Python runtimes under `.benchmarks/runtimes`; manifests/freezes record actual installation state. Existing different revisions are retained rather than overwritten. Native configuration `runtime: installed` dispatches CLI/TUI/browser jobs into these runtimes while sharing result history.

| Recipe in `examples/benchmarks/` | Requires |
| --- | --- |
| `local-qwen-agentdojo.yaml` | Ollama with `qwen2.5:3b`; no browser services |
| `local-qwen-stwebagentbench.yaml` | Same model plus original ST websites/SuiteCRM |
| `local-qwen-doomarena.yaml` | Same model plus original MiniWoB pages/browser runtime |
| `agentdojo.yaml`, `stwebagentbench.yaml`, `doomarena.yaml` | Your native-action HTTP agent, default port 9001 |

The installer does **not** start websites or obtain credentials. Follow each upstream repository's environment setup. `.benchmarks/environment-urls.json` can provide public service URLs (`MINIWOB_URL`, `WA_SUITECRM`, `SUITECRM`, `GITLAB`, `SHOPPING_ADMIN`); credentials stay in the environment. Browser/service version deviations are listed in [the ledger](benchmark-results.md).

```sh
uv run intentbench benchmarks tui --config examples/benchmarks/local-qwen-agentdojo.yaml
uv run intentbench benchmarks history
uv run intentbench benchmarks show RUN_ID
uv run intentbench benchmarks verify RUN_ID
```

The browser workbench's Benchmark ecosystem view edits native JSON configurations and displays original grades. [ArmorIQ setup](armoriq-inside.md) adds matched protection conditions.

## Configure each adapter

| Adapter | Configuration and grading contract |
| --- | --- |
| AgentDojo | Explicit `task_ids`; `options.suite` and `benchmark_version` default to workspace/v1.2.2. `injection_task_id` plus `injections` or `attack_factory` selects attacks. The factory returns native `BaseAttack`; original candidate loading is preserved. Trace-based utility/security grading takes precedence when available. **`attack_success: true` means the attacker succeeded.** |
| ST-WebAgentBench | Numeric IDs map to `browsergym/STWebAgentBenchEnv.ID`. `options.env_kwargs` reaches the native environment; policies stay in public observations. Derived completion uses final reward == 1 and no violated native report, and is unknown if reports are absent. Raw grades are retained. |
| DoomArena | `environment_factory` must return an actual native `AttackGateway` with Gymnasium-shaped reset and five-value step. Configure original attacks/filters through the supplied factory; original abort and success-filter behavior stays intact. Other gateway protocols need their own bridge. |

Ground-truth actions, hidden attacker goals, and grader data stay outside the agent channel. Artifacts freeze native setup and AgentDojo injections. Adaptive attacks need a factory with a real target pipeline; the adapter does not invent that pipeline or substitute an unrelated environment.

## Agent and guard protocol

A native Python factory is called as `create_agent(config=AdapterConfig, seed=int)`. It returns synchronous or asynchronous `act(envelope)` and optional `aclose()`. This differs from the local factory signature in [adapters.md](adapters.md).

```python
envelope = {
    "benchmark": "agentdojo", "task_id": "user_task_0", "seed": 42,
    "step": 0, "observation": native_public_observation, "guard_feedback": None,
}
```

AgentDojo actions are `{kind: tool, tool: native_name, args: ...}` or `{kind: finish, args: {output: answer}}`. Browser actions are native strings such as `click('42')`. An HTTP native agent receives `POST /act` with `{"observation": envelope}` and returns `{"action": native_action}`. NumPy data is encoded with dtype/shape/data; bytes use base64 over HTTP. Python agents keep native types.

Guarded native runs require an author-owned `contract` and guard. Browser guards also require `action_mapper: module:callable` producing a validated gym Action. ArmorIQ needs a declared `guard_plan` or public-observation `plan_factory`; choose `instrumentation: inside` for the SDK wrapper and `guard_responses: true` to check AgentDojo output. [Plan limitations](armoriq-inside.md#what-gets-instrumented) explain interference and scope.

Enforcement blocks before execution without a replacement noop, which would advance the attack schedule. Native monitor is passive. Reset/step/grade/close share one native thread outside asyncio; episodes are serial within a run. Async calls have budgets; blocking native work stops at cooperative boundaries.

For external state restoration, set `state_reset_factory: module:callable`. The synchronous callable receives keyword arguments `task_id`, `seed`, and a private copy of `options`, and must restore the task's intended snapshot before returning `{"snapshot_id": "stable snapshot identifier or digest", "method": "restoration method"}`. It runs on the native thread before environment construction, authentication, or model calls, for each task/repeat in every condition. Failures or malformed receipts stop that episode with an error and no native actions. Callback source hashes and receipts are archived; native experiment summaries include the receipt, derived grades, and actual native step counts. The agent and grader do not receive the receipt.

Supply a reset implementation appropriate to your deployment and compare receipts across conditions. A receipt is an assertion by that implementation, not independent proof of equivalent external state. The ArmorIQ-inside SuiteCRM recipe now binds `examples.benchmarks.stweb_snapshot:restore` for task 47. Capture the dedicated database first with `.venv/bin/python -m examples.benchmarks.stweb_snapshot`. Restoration verifies a logical database hash before task construction; this does not restore general application files. Other deployments and tasks need an appropriate restore implementation. Report any incomplete external-state controls explicitly.

## Factor suite and checks

```sh
uv run intentbench matrix --suite research-factors --agent gullible --guard reference
```

These 108 local cases adapt intent hijacking/chaining/drifting/injection/memory poisoning, evolving goals, and clarification/modification/retraction. They do not reproduce long-horizon optimizers, cross-session memory, interruption replay, or original-paper metrics. Source tags and rebuild code accompany the suite.

Contract checks live in `tests/test_benchmarks.py`, `examples/benchmarks/native_contract_smoke.py`, and `gateway_contract_smoke.py`; InterruptBench's string/current-intent check is `interruptbench_contract_smoke.py`. They validate interfaces, not agent capability. Native manifests keep installed revisions/source hashes separate from catalog review revisions; external database snapshots, model revisions, and backend policies need their own archive.
