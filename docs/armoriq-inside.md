# Run with ArmorIQ

The experiment runner derives **unguarded**, **armoriq-monitor**, and **armoriq-enforce** conditions from one agent configuration. It keeps task selection, model, prompts, initial planning, attacks, seeds, and budgets fixed within a track. Original native graders are retained.

## 1. Configure credentials and a model

On a fresh checkout, copy [.env.example](../.env.example) to `.env`, then `chmod 600 .env`. Preserve an existing file. Set these values locally:

| Setting | Purpose |
| --- | --- |
| `ARMORIQ_API_KEY`, `ARMORIQ_USER_EMAIL` | Backend authentication and evaluated user |
| `ARMORIQ_IAP_ENDPOINT`, `ARMORIQ_BACKEND_ENDPOINT`, `ARMORIQ_PROXY_ENDPOINT` | Optional endpoint overrides; blank uses SDK defaults |
| `ARMORIQ_SDK_MODE` | `sdk` backend enforcement; `local` captured-token snapshot checking |
| `MODEL_NAME`, `MODEL_API_KEY` | Agent model and optional provider key |
| `MODEL_PROTOCOL`, `MODEL_BASE_URL` | Native agent: `ollama` or `chat-completions`, with API base |
| `MODEL_COMPATIBLE_BASE_URL` | Local gym agent's compatible Chat Completions base |

Defaults use local Ollama with `qwen2.5:3b` at port 11434. A remote compatible provider needs its model name, key, and API base in both URL settings. Endpoints must support the recipe's tool calling, JSON response, seed, and token-limit parameters; otherwise use your own [adapter](adapters.md).

CLI, API, runners, and workers load the working directory's `.env`; process variables win. Restart the workbench after editing credentials. Secrets stay as environment references in saved configurations. Both SDK checking modes need credentials for plan capture/token issuance; report `sdk` and `local` results separately.

## 2. Run a local intent suite

```sh
uv sync --locked --extra dev --extra armoriq
uv run --no-sync intentbench experiment run examples/armoriq-inside/experiment.yaml --track smoke
```

This uses a real model, not the demo fixture. It requires the configured model endpoint. Local YAML policies do not provision ArmorIQ policies: configure matching tool authorization in your backend before interpreting enforcement effectiveness.

## 3. Run upstream benchmark comparisons

```sh
uv run python scripts/install_benchmarks.py agentdojo stwebagentbench doomarena
uv run --no-sync python scripts/install_armoriq.py
uv run --no-sync intentbench experiment run examples/armoriq-inside/experiment.yaml --track agentdojo
```

The SDK installer pins the public SDK from `uv.lock` in the gym and three native runtimes. `--sdk-path /path/to/armoriq-sdk-customer` selects an existing checkout instead. An exact `uv sync` can remove separately installed optional packages; use `--no-sync` afterward. The locked public SDK 0.6.10 and customer SDK 0.3.6 have offline contract coverage; recorded live checks use the customer SDK.

Track names: `agentdojo`, `agentdojo-attack`, `stwebagentbench`, `doomarena`, `doomarena-attack`, `smoke`, `core`, `research-factors`. Omit `--track` to run the configured selections; these native recipes are smoke subsets, not full benchmark populations. [Native setup](benchmarks.md) supplies website requirements.

Use `--conditions unguarded` for a credential-free baseline, or `--conditions armoriq-monitor,armoriq-enforce` for protected conditions. Open a native recipe with `benchmarks tui --config examples/armoriq-inside/agentdojo.yaml`; local suites use `tui --config examples/armoriq-inside/intent-gym.yaml`.

## Diagnose a blocked or failed run

| Result | Meaning / next check |
| --- | --- |
| `no_matching_policy` | Backend found no applicable policy for the proposed benchmark tool; check user, namespace, and policy configuration |
| `tool_not_in_policy_intersection` | Effective policy intersection does not permit that tool |
| `tool-not-in-plan` | Tool was absent from the captured declaration; inspect the agent's plan, including `agent__respond` |
| `plan-required` | Integration precondition: declare a plan before proposing execution; labeled separately from remote verdicts |
| SDK unavailable / malformed response | Infrastructure error; safety is unmeasured, not a successful block |
| All actions blocked, CuP 0 | Connectivity may work while utility fails; inspect clean-task interference before claiming protection |

The [live results](benchmark-results.md) show this distinction: authentication/token issuance worked, but missing policy coverage prevented legitimate tasks. No backend policy is automatically loosened to improve a score.

## What gets instrumented

`ArmorIQInsideAgent` wraps the original decision engine and SDK session. The runner maps the exact proposal, checks it, and executes the unchanged native action only when enforcement allows it. Monitor records decisions without blocking; native monitor sends no guard feedback to the model. Native final answers are checked as `agent__respond` when `guard_responses: true`; browser chat uses `browser__send_msg_to_user`.

Native recipes require an author-owned `guard_plan` **or** a `plan_factory`. The sample factory makes one initial model planning call from public observations in every condition. It never sees private grader data or automatically authorizes a denied call. Incomplete plans and arguments discovered later can interfere with legitimate completion; a captured declaration is not proof of user authorization or a guarantee of exact-argument enforcement.

Local agents can use `submit_plan` and action-specific approvals. Local `finish` is bookkeeping, not a scored output disclosure; author an output tool to test that risk. Provider batches run in declared order, with individual checks/results and the original local intent version. SDK holds may invoke backend delegation workflows; simulated approvals do not grant backend approval. SDK observability defaults off when supported; `options.sdk_observability: true` opts into trace shipping.

## Wrap an existing executor

```python
from agent_intent_bench.inside import ArmorIQInsideAgent
from agent_intent_bench.models import Action, AdapterConfig

inside = ArmorIQInsideAgent(existing_agent, AdapterConfig(kind="armoriq"))
try:
    await inside.evaluate(Action(kind="plan", plan=declared_calls), public_context)
    proposal = await inside.act(public_observation)
    decision, result = await inside.execute(proposal, public_context, tool_executor)
finally:
    await inside.aclose()
```

`act()` proposes; connect the `execute()` gate rather than dispatching its output directly. Block/hold never reaches the executor in enforce mode. AgentLAB/IntentFlux/InterruptBench factor adaptations use the local track; their original native harnesses are not SDK-instrumented here.

Reports link run IDs under `.intentbench/experiments/`. Pairing hashes cover configured tasks, models, planning, and budgets; external database snapshots, backend policy revisions, and remote determinism still need independent control. [Score interpretation](evaluation-design.md) explains the required denominators.
