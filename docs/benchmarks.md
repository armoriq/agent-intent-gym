# Benchmark ecosystem

The gym includes three optional native environment adapters and three sources of attributed factor designs. Native environments retain their own task definitions, attacks, execution, and graders. Factor adaptations are newly authored synthetic gym scenarios, scored by our intent oracle. These are different evaluation tracks and are reported separately.

| Source | Integration | Preserved output / local adaptation |
| --- | --- | --- |
| [AgentDojo](https://github.com/ethz-spylab/agentdojo) | Native `TaskSuite` and `FunctionsRuntime` adapter | Original utility and attack-success predicates, including trace-based grading; native injection vectors and optional `BaseAttack` factory |
| [ST-WebAgentBench](https://github.com/segev-shlomov/ST-WebAgentBench) | Native BrowserGym environment adapter | Unmodified rewards, safety penalties, policy reports, and transition info |
| [DoomArena](https://github.com/ServiceNow/DoomArena) | Factory for a native attack gateway with Gymnasium-shaped reset/step | Underlying reward, gateway info, original success-filter results, and termination behavior |
| [AgentLAB](https://arxiv.org/abs/2602.16901) | Five factor adaptations | Intent hijacking, tool chaining, objective drifting, task injection, within-episode memory poisoning |
| [IntentFlux](https://arxiv.org/abs/2609.32520) | Four factor adaptations | Add an approval requirement, withdraw an operation, replace a target, and benign repeated-message controls |
| [InterruptBench](https://github.com/HenryPengZou/InterruptBench) | Three factor adaptations | Early clarification, later modification, and pre-commit retraction |

The AgentLAB paper is the **long-horizon attack benchmark**, distinct from ServiceNow's `agentlab` experiment package used by DoomArena.

## Run the included factor suite

```sh
uv run intentbench run --suite research-factors --agent careful --guard reference
uv run intentbench matrix --suite research-factors --agent gullible --guard reference
uv run intentbench tui --suite research-factors
```

There are 108 synthetic episodes: 12 factor designs × three workflows × clean/challenge/control. Source and factor tags accompany each scenario. `examples/build_research_factors.py` rebuilds the suite. The browser workbench has a Research factors selector.

These small deterministic fixtures exercise integration and scoring. They do not reproduce the papers' long-horizon tasks, learned/adaptive attack optimizers, persistent cross-session memory, user simulators, interruption replay protocol, or published metrics. Add-goal uses a new approval requirement; delete-goal uses cancellation of the consequential operation. Message controls match scheduled intervention points, not necessarily realized dialogue lengths. They are starting points for factor authoring, not calibrated reproductions of CAR/IDG or official benchmark coverage.

## Run native benchmarks

Install the tested source revisions into separate local environments:

```sh
uv run python scripts/install_benchmarks.py
uv run intentbench benchmarks run examples/benchmarks/local-qwen-agentdojo.yaml
```

The installer clones into `.benchmarks/sources`, creates `.benchmarks/runtimes`, and records package freezes and an installation manifest. Existing checkouts with a different revision are retained and reported rather than overwritten. AgentLAB uses a CPU API-control profile: its original requirements contain an OpenAI/LiteLLM conflict and CUDA-specific dependencies. InterruptBench uses its legacy runtime plus missing import dependencies. ST's old Chromium crashes on this macOS version, so its tested runtime overrides the upstream Playwright pin with 1.64.0; original task/policy graders remain unchanged. These differences are recorded in the [execution report](benchmark-results.md).

Set `runtime: installed` in a native configuration to dispatch CLI, TUI, and browser jobs to the appropriate installed runtime. `.benchmarks/environment-urls.json` supplies configured public service URLs; credentials come from the calling environment. Per-runtime processes keep incompatible BrowserGym versions separate. Artifacts still use the common `.intentbench/benchmarks` history. The local Qwen examples need Ollama running with `qwen2.5:3b` installed; they use real model inference, not fixture actions.

Native dependencies stay optional and separate from the offline gym installation. Prepare the upstream environments following their own setup instructions; select a runtime containing the appropriate packages when launching the CLI or server. Configurations in `examples/benchmarks` point to an HTTP agent on port 9001; supply your own service or Python agent.

```sh
uv run intentbench benchmarks list
uv run intentbench benchmarks inspect agentdojo

# AgentDojo: installed checkout, native tools, and native grading.
uv run --with-editable /path/to/agentdojo intentbench benchmarks run examples/benchmarks/agentdojo.yaml

# Optional native fixed-template attack generation (repository examples on PYTHONPATH).
PYTHONPATH=. uv run --with-editable /path/to/agentdojo intentbench benchmarks run examples/benchmarks/agentdojo-attack.yaml

# Native configurations and result inspection in a TUI.
uv run --with-editable /path/to/agentdojo intentbench benchmarks tui --config examples/benchmarks/agentdojo.yaml

uv run intentbench benchmarks history
uv run intentbench benchmarks show RUN_ID
uv run intentbench benchmarks verify RUN_ID
```

The browser's **Benchmark ecosystem** view lists all six sources, accepts a native JSON configuration, starts/stops runs, and displays native score and transition artifacts. Start the server with the same upstream dependency options used for the CLI; installing a package in another process does not make it available to an already-running server.

### AgentDojo

Options choose the native suite, benchmark version, injection task, and injection mapping. By default the adapter uses `workspace` and `v1.2.2`. Task IDs are explicit. `injections` maps native injection-vector IDs to payload strings. Alternatively, `attack_factory` returns an actual upstream `BaseAttack`; the adapter calls its `attack(user_task, injection_task)` and applies the returned mapping through the original suite loader. The included factory uses the native fixed-template generator and candidate discovery. Adaptive attackers need a factory with a real target pipeline; the gym does not automatically substitute its external agent for that pipeline.

The adapter initializes the task's environment before taking its pre-execution snapshot. On completion it invokes `utility_from_traces` when available and otherwise `utility`, with the same precedence for `security_from_traces` / `security`. **Upstream `security=True` means the attacker succeeded**; we retain that polarity under the explicit name `attack_success`. Ground-truth actions, attack goals, and graders stay out of the agent observation. Generated injections and the native pre-environment are frozen in artifacts.

### ST-WebAgentBench

Install the upstream BrowserGym package and its requirements, expose the repository's top-level `stwebagentbench` package, and start its websites. For the reviewed checkout, a runtime can be launched with:

```sh
PYTHONPATH=/path/to/ST-WebAgentBench uv run \
  --with-editable /path/to/ST-WebAgentBench/browsergym/stwebagentbench \
  --with openai --with nltk --with pandas \
  intentbench benchmarks run examples/benchmarks/stwebagentbench.yaml
```

Numeric task IDs map to `browsergym/STWebAgentBenchEnv.ID`; explicit native IDs also work. `options.env_kwargs` passes native environment arguments, including a custom action mapping when supplied through an environment factory. Policies remain in the upstream observation. Rewards, safety penalties, all policy reports, and final info are archived unchanged.

An explicitly labeled derived view mirrors the upstream example loop: final reward equal to 1.0 and no report marked `violated`. It remains unmeasured when no safety report was supplied. This view does not replace the original reward or reports.

### DoomArena

The supplied factory constructs `BrowserGymAttackGateway` around an upstream browser environment. Install DoomArena's core/browser packages and prepare the underlying websites. Configure `options.attack_config_factory` as your Python factory returning original `AttackConfig` objects. `PYTHONPATH` must include your factory and any repository examples you use. Native attack filters, content generators, success filters, defenses, and abort behavior remain owned by the gateway.

The adapter checks that the factory returns an actual `AttackGateway`. It supports gateways with Gymnasium-shaped `(observation, info)` reset and five-value step results, including the BrowserGym gateway. Other native gateway protocols require an explicit bridge; OSWorld/tau-bench/MCP are not automatically normalized. The gym preserves raw gateway info and a per-step history of `success_filter_results`, without inventing a universal attack-success metric.

## Native agent and guard protocols

A Python factory is called with `config=AdapterConfig` and `seed=int`, returning an agent with synchronous or asynchronous `act(envelope)`. An optional `aclose()` releases agent resources. Each episode gets a fresh agent and environment. Synchronous environment operations share an owning thread without an asyncio event loop, while agent/guard calls have their own asynchronous loop. This supports synchronous Playwright and thread affinity. Episodes are serial within each run in this release.

```python
# The public envelope, not a gym-local scenario observation:
{
    "benchmark": "agentdojo",  # or stwebagentbench / doomarena
    "task_id": "user_task_0",
    "seed": 123,
    "step": 0,
    "observation": {},         # native public observation
    "guard_feedback": None,    # latest guard decision when a guard is configured
}
```

AgentDojo accepts `{"kind": "tool", "tool": "native_name", "args": {...}}` or `{"kind": "finish", "args": {"output": "final answer"}}`. BrowserGym accepts its native action string. Plan declarations and delegated approval protocols need a custom harness; they are not silently converted into tool calls. An HTTP agent receives `POST /act` with `{"observation": envelope}` and returns `{"action": native_action}`. NumPy observations use an explicit dtype/shape/data encoding over HTTP; bytes use base64. Python agents receive their native types.

Optional `guard` uses the same adapters as the local gym, including ArmorIQ. Enforcing or monitoring runs require an explicit author-owned `contract`. Browser actions additionally require `action_mapper: module:callable`, mapping the exact native proposal to a validated gym `Action`. This is where you define the browser-to-policy tool vocabulary; native benchmark policies remain independent. Public guard context contains that contract and executed mapped-call history, without private grader state.

ArmorIQ runs require an explicit author-owned `guard_plan` or `plan_factory` producing a declared plan from public observations. The runner submits it through the SDK's plan-capture interface before checking actions. A plan factory runs identically in unguarded and guarded conditions; there is no automatic authorization of each proposed call. Other guards can optionally use the same plan. Plan decisions are recorded separately from per-action decisions; a denied plan ends enforcement without executing native actions. `instrumentation: inside` composes the agent with its SDK gate, and `guard_responses: true` also checks AgentDojo final answers. See [matched ArmorIQ-inside experiments](armoriq-inside.md) for runnable profiles and plan limitations.

Enforcement blocks/holds before native execution and returns feedback to the agent. It does not execute a replacement noop, which could advance a native attack schedule. Monitor mode records guard decisions and executes the original proposal. Per-action independent guard labels are not available from these integrations, so detection and overblocking remain unmeasured. Native task/attack outcomes can compare guarded and unguarded runs while retaining their definitions.

## Artifacts and validity

Native artifacts live under `.intentbench/benchmarks/RUN_ID/`, separate from local intent-oracle runs. Each run stores configuration, manifest, per-episode checkpoints, native setup, grader/source identities, raw native scores, labeled derived views, decisions, and transitions. The whole result, manifest, and config can be verified against saved hashes. These are integrity checks, not signed attestations.

Manifests record installed distribution versions, adapter/factory source hashes, and source identities of instantiated upstream tasks/graders/gateways. Editable Git checkouts include their actual revision and dirty status. Registry `reviewed_revision` records what informed adapter development; it is **not** a claim that the installed version matches. External service snapshots, model/prompt revisions, attack configuration dependencies, and remote policy revisions remain your responsibility to archive.

Keeping original grading does not make a gym-owned agent loop an official upstream evaluation protocol. Attack budgets, defenses, model prompts, task selection, service reset, retries, and environment caps can affect outcomes. Do not combine native rewards into a cross-benchmark score. Compare runs only when these settings and source revisions match, and retain errors, truncation, and cancellation counts. Blocking native calls and cleanup stop cooperatively at step boundaries; async agent/guard calls have explicit timeouts.

## Verification and attribution

`tests/test_benchmarks.py` checks reward/report preservation, prior violations, guard enforcement, monitor semantics, thread affinity, cancellation, API jobs, artifact tampering, and attribution. `native_contract_smoke.py` exercises actual AgentDojo task tools and grader agreement in all four suites; `gateway_contract_smoke.py` exercises an actual ST policy evaluator and a DoomArena core gateway subclass without websites. These are compatibility checks, not real-agent or browser benchmark scores.

```sh
PYTHONPATH=. uv run --with-editable /path/to/agentdojo python examples/benchmarks/native_contract_smoke.py
PYTHONPATH=/path/to/ST-WebAgentBench uv run \
  --with-editable /path/to/ST-WebAgentBench/browsergym/stwebagentbench \
  --with openai --with nltk --with pandas \
  python examples/benchmarks/gateway_contract_smoke.py stwebagentbench
uv run --with-editable /path/to/DoomArena/doomarena/core \
  python examples/benchmarks/gateway_contract_smoke.py doomarena
```

See [third-party notices](../THIRD_PARTY_NOTICES.md) for sources and license boundaries. No upstream datasets or implementation files are vendored. Optional package licenses remain applicable when those packages are installed.
