# Run with ArmorIQ

The experiment runner derives **unguarded**, **armoriq-monitor**, and **armoriq-enforce** conditions from one agent configuration. It keeps task selection, model, prompts, initial planning, attacks, seeds, and budgets fixed within a track. Original native graders are retained.

## 1. Configure credentials and a model

On a fresh checkout, copy [.env.example](../.env.example) to `.env`, then `chmod 600 .env`. Preserve an existing file. Set these values locally:

| Setting | Purpose |
| --- | --- |
| `ARMORIQ_API_KEY`, `ARMORIQ_USER_EMAIL` | Backend authentication and evaluated user |
| `ARMORIQ_AGENT_ID` | Registered agent ID; must match the CLI configuration's `identity.agent_id` when policies target a specific agent |
| `ARMORIQ_IAP_ENDPOINT`, `ARMORIQ_BACKEND_ENDPOINT`, `ARMORIQ_PROXY_ENDPOINT` | Optional endpoint overrides; blank uses SDK defaults |
| `ARMORIQ_SDK_MODE` | `sdk` backend enforcement; `local` captured-token snapshot checking |
| `MODEL_NAME`, `MODEL_API_KEY` | Agent model and optional provider key |
| `MODEL_PROTOCOL`, `MODEL_BASE_URL` | Native agent: `ollama` or `chat-completions`, with API base |
| `MODEL_COMPATIBLE_BASE_URL` | Local gym agent's compatible Chat Completions base |

Defaults use local Ollama with `qwen2.5:3b` at port 11434. A remote compatible provider needs its model name, key, and API base in both URL settings. Endpoints must support the recipe's tool calling, JSON response, seed, and token-limit parameters; otherwise use your own [adapter](adapters.md).

CLI, API, runners, and workers load the working directory's `.env`; process variables win. Restart the workbench after editing credentials. Secrets stay as environment references in saved configurations. Both SDK checking modes need credentials for plan capture/token issuance; report `sdk` and `local` results separately.

## 2. Run a local intent suite

First complete [agent registration and v2 provisioning](#register-agents-and-provision-v2-policies) below. The commands here assume deployment `evaluation-001` has been prepared. Inventory export requires the AgentDojo runtime; install the native runtimes in step 3 before provisioning a full profile.

```sh
uv sync --locked --extra dev --extra armoriq
uv run --no-sync intentbench experiment run .benchmarks/policy-setup/evaluation-001/experiment.yaml --track smoke
```

This uses a real model, not the demo fixture. It requires the configured model endpoint. Local YAML policies do not provision ArmorIQ policies: configure matching tool authorization in your backend before interpreting enforcement effectiveness.

## 3. Run upstream benchmark comparisons

```sh
uv run python scripts/install_benchmarks.py agentdojo stwebagentbench doomarena
uv run --no-sync python scripts/install_armoriq.py
uv run --no-sync intentbench experiment run .benchmarks/policy-setup/evaluation-001/experiment.yaml --track agentdojo
```

The SDK installer pins the public SDK from `uv.lock` in the gym and three native runtimes. `--sdk-path /path/to/armoriq-sdk-customer` selects an existing checkout instead. An exact `uv sync` can remove separately installed optional packages; use `--no-sync` afterward. The current lock uses public SDK 0.8.17. The installer removes overlapping public/customer distributions before installation.

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

The [results ledger](benchmark-results.md) records the latest provisioned v2 comparison, including utility loss, coverage gaps and error counts. No backend policy is automatically loosened to improve a score.

## Register agents and provision v2 policies

Use `.venv/bin/armoriq` explicitly; a globally installed TypeScript command may shadow the Python CLI. The Python CLI registers the dedicated benchmark agents. Public SDK **0.8.17** supports v2 enforcement and policy identity metadata, but its `policy propose` command still accepts the older org-profile format. It does not provide a v2 `policy apply` command.

The supplied [v2 schema PDF](schemas/ARMOR_POLICY_V2_SCHEMA.pdf) is archived with an extracted text reference and a strict JSON Schema for the benchmark-authoring subset in `docs/schemas/`. The PDF and deployed compiler remain authoritative; the local subset does not implement every vendor feature. Four templates live in `examples/armoriq-inside/policies/`, each targeting only its dedicated `intentbench-v2-*` agent. Their default tool verdict is block. Arguments are not opted into SDK trace shipping.

```sh
.venv/bin/python scripts/export_policy_inventory.py
.venv/bin/python scripts/provision_armoriq.py --register
```

This resolves the organization from the configured API key, validates and materializes templates under `.benchmarks/policy-setup/`, and uses the Python CLI to register the four agents. CLI state and logs stay in that directory. Registration sends empty legacy allow/deny lists: it does not flatten conditional v2 policies into an inaccurate legacy policy.

For v2 compilation and activation, use the API-key-compatible import route supplied for this deployment:

```sh
.venv/bin/python scripts/provision_armoriq.py --register --apply --deployment evaluation-001
```

The helper invokes `curl` against `https://api.armoriq.ai/policies/yaml/import-apikey`, sending the YAML and `status: active`. The API key enters curl on stdin, rather than the process argument list. No dashboard access token is needed. The endpoint compiles the document and returns the active policy with diagnostics. One condition field accepts exactly one operator; the quantity policy uses an ordered negative-quantity block followed by the permitted upper-bound check.

The import route creates policies and rejects duplicate names. Use a unique deployment suffix when changing policy contents. An unchanged deployment can be resumed after checking its recorded source and active platform policy hashes. All targets are dedicated versioned benchmark agents; the helper does not call org-profile sync or exclusive activation.

Tool inventories must be published before policy import. The helper uses the SDK's own tool-registry contract to publish the actual authored/native tool schemas. Unknown-tool diagnostics stop provisioning rather than silently treating an unbound rule as protection. The generated profile at `.benchmarks/policy-setup/evaluation-001/experiment.yaml` resolves canonical platform agent IDs, references the frozen tool catalogs, and carries catalog hashes. Run this prepared profile for comparisons. The source recipes are templates.

Before spending model tokens on a campaign, run live positive and negative checks:

```sh
.venv/bin/python scripts/check_armoriq_policies.py .benchmarks/policy-setup/evaluation-001
.venv/bin/intentbench experiment run .benchmarks/policy-setup/evaluation-001/experiment.yaml
```

The preflight declares plans and uses real SDK checks without executing any native tool. It requires the exact expected policy ID on every allow/block verdict. Deployment `20261022-e2e` passed all 17 such probes. Policy source, compiler responses, inventory registrations, activation hashes, and preflight evidence remain in the ignored setup directory.

The recipes select `agent_id` explicitly and set `require_active_policy: true`. Backend reasons `no_active_policy` and `no_matching_policy` therefore fail the guarded episode as a setup error. Valid backend `allow_log` verdicts are normalized by the SDK, while malformed or inconsistent responses remain infrastructure failures. Guards retain matched policy ID, version, and rule ID when the backend supplies them.

These benchmark tools execute inside the native/local harness and are registered as **agent-owned** tools, even when their names contain `__`. Their recipes select `tool_name_mode: agent`, keeping the entire original name as the checked action: `payments__commit`, `browser__click`, and `agent__respond`. Names and arguments sent to the original executor remain unchanged. Without this explicit mapping, the SDK's default MCP parser interprets these prefixes as remote server identities and the backend falls through to the default block rule. Actual remote MCP adapters can retain the default `tool_name_mode: mcp` behavior.

### Policy coverage

The frozen local policy covers tool scope, original approved recipient/beneficiary/path, and a per-call quantity bound of 100. It does **not** claim to implement aggregate limits, prerequisite sequences, simulated human approvals, or evolving/revoked user intents. These remain scored by the independent local intent oracle and may expose gaps or overblocking. The policy is frozen across conditions and is not generated from private oracle/grader outcomes.

The AgentDojo policy allows public read operations appropriate to the selected workspace calendar-query task and the final response; it is not a policy for all 97 native tasks. Browser policies allow the supported UI primitives and restrict direct `goto` to the relevant local service. A click's destination is absent from the checked arguments, so those rules cannot attest to the safety of indirect navigation. Native graders remain the authority for native outcomes.

For controlled SuiteCRM task 47 comparisons, first capture the dedicated database:

```sh
.venv/bin/python -m examples.benchmarks.stweb_snapshot
```

Its recipe restores that snapshot before each episode and checks the logical dump hash. This is a database-only restore for the selected account-creation task; it does not reproduce arbitrary filesystem state or all upstream services. The snapshot and any account data remain local under `.benchmarks/snapshots/`.

## What gets instrumented

`ArmorIQInsideAgent` wraps the original decision engine and SDK session. The runner maps the exact proposal, checks it, and executes the unchanged native action only when enforcement allows it. Monitor records decisions without blocking; native monitor sends no guard feedback to the model. Native final answers are checked as `agent__respond` when `guard_responses: true`; browser chat uses `browser__send_msg_to_user`.

Native recipes require an author-owned `guard_plan` **or** a `plan_factory`. The sample factory makes one initial model planning call from public observations in every condition, with at most one repair call for invalid syntax, unknown tools, or an omitted AgentDojo final-response declaration. The public planning catalog includes `agent__respond`; the model must declare it with a string output argument. A failed repair is an infrastructure/setup error, not a protection success. This bounded procedure is identical across conditions and never responds to SDK denials. The planner never sees private grader data or automatically authorizes a denied call. Incomplete plans and arguments discovered later can interfere with legitimate completion; a captured declaration is not proof of user authorization or a guarantee of exact-argument enforcement.

The compatible local recipe selects `options.require_initial_plan: true`. Before execution, it requests a model-authored JSON plan from the public observation, permits at most one syntax/unknown-tool repair, and submits that declaration as the first step in every condition. The execution tool catalog then omits plan resubmission, so denials cannot trigger automatic permission expansion. This avoids relying on the model to voluntarily call `submit_plan`. Planning consumes the same step/time budgets and tokens in every condition. Other local agents can still use `submit_plan` themselves.

Local agents can request action-specific approvals. Local `finish` is bookkeeping, not a scored output disclosure; author an output tool to test that risk. Provider batches run in declared order, with individual checks/results and the original local intent version. SDK holds may invoke backend delegation workflows; simulated approvals do not grant backend approval. SDK observability defaults off when supported; `options.sdk_observability: true` opts into trace shipping.

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
