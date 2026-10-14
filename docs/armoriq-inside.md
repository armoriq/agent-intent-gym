# Run the same agents with and without ArmorIQ

The experiment runner builds three conditions from one configuration: **unguarded**, **armoriq-monitor**, and **armoriq-enforce**. The agent factory, model, system prompts, public observations, initial planning protocol, task IDs, attacks, budgets, repeats, and environment seeds stay the same. Enforcement adds SDK checks before native execution; monitoring records decisions without sending guard feedback to the native agent or blocking its actions.

## Credentials and installation

On a fresh checkout, copy the project root `.env.example` to `.env`, set owner-only permissions (`chmod 600 .env`), and fill in the credentials. Preserve any existing `.env`. The development workspace already has a blank local file; it is ignored and is not shipped in Git or package artifacts. CLI, API, Python runners, and isolated workers load the working directory's `.env`; existing process variables win. Restart a running workbench after changing credentials. Keep credentials as environment references in YAML; their values are not copied into configurations, manifests, or experiment reports.

```dotenv
ARMORIQ_API_KEY=
ARMORIQ_USER_EMAIL=
ARMORIQ_IAP_ENDPOINT=
ARMORIQ_BACKEND_ENDPOINT=
ARMORIQ_PROXY_ENDPOINT=
ARMORIQ_SDK_MODE=sdk
MODEL_PROTOCOL=ollama
MODEL_NAME=qwen2.5:3b
MODEL_BASE_URL=http://127.0.0.1:11434
MODEL_COMPATIBLE_BASE_URL=http://127.0.0.1:11434/v1
MODEL_API_KEY=
```

Blank ArmorIQ endpoint overrides use the installed SDK defaults. Set the endpoints to your test backend when appropriate. `sdk` checks contact that backend; `local` checks a captured token's policy snapshot and must be reported as a different protection condition. Both still need credentials for plan capture/token issuance. Gym YAML policies do not configure ArmorIQ backend policy. Register policies for the tool/action names used by the benchmark, including `browser__*` and `agent__respond` where applicable.

The native agent supports Ollama's HTTP API and a compatible Chat Completions endpoint. For a remote compatible model, set `MODEL_PROTOCOL=chat-completions`, `MODEL_BASE_URL` and `MODEL_COMPATIBLE_BASE_URL` to its API base, and supply `MODEL_NAME` and `MODEL_API_KEY`. Provider capabilities differ; use your own Python/HTTP adapter if the endpoint does not support this recipe's tool calling, JSON responses, seed, or token limit parameters. The local gym agent always uses the compatible endpoint. The baseline and guarded conditions share the same provider protocol within each track; native and local-gym agents have environment-specific observation/prompt protocols.

```sh
uv sync --extra dev
uv run python scripts/install_benchmarks.py
# Existing customer checkout; installs one SDK into gym + all three native runtimes:
uv run --no-sync python scripts/install_armoriq.py --sdk-path ../armoriq-sdk-customer
# Alternatively omit --sdk-path to install the public SDK pinned in uv.lock.
```

This machine uses the existing `armoriq-sdk-dev` **0.3.6** checkout. Runtime package versions and SDK source hashes are recorded. Use `uv run --no-sync` after installation; an exact `uv sync` can remove separately installed optional SDK packages. Re-run the installer after rebuilding native runtimes. The benchmark installer does not start upstream websites; the original [environment setup requirements](benchmarks.md) still apply.

The locked public SDK is **0.6.10** and is also covered by offline CI checks. SDK observability is disabled by default when supported, keeping the default integration to plan capture/token issuance and enforcement. Set guard `options.sdk_observability: true` to enable the SDK's trace shipping on supported versions; session and client resources are closed after evaluation. SDK outages remain infrastructure errors even when a newer SDK returns a fail-closed block decision.

## Run matched experiments

```sh
# All configured native tasks/attacks plus smoke/core/research-factor gym suites:
uv run --no-sync intentbench experiment run examples/armoriq-inside/experiment.yaml

# Begin with one track:
uv run --no-sync intentbench experiment run examples/armoriq-inside/experiment.yaml --track agentdojo

# Credentials can remain blank for this baseline:
uv run --no-sync intentbench experiment run examples/armoriq-inside/experiment.yaml --track agentdojo --conditions unguarded

# Run only enforcement after configuring ArmorIQ:
uv run --no-sync intentbench experiment run examples/armoriq-inside/experiment.yaml --track agentdojo --conditions armoriq-enforce

# Native and local intent-suite interfaces accept the same inside configurations:
uv run --no-sync intentbench benchmarks tui --config examples/armoriq-inside/agentdojo.yaml
uv run --no-sync intentbench tui --config examples/armoriq-inside/intent-gym.yaml
uv run --no-sync intentbench run --suite core --config examples/armoriq-inside/intent-gym.yaml
```

Track names are `agentdojo`, `agentdojo-attack`, `stwebagentbench`, `doomarena`, `doomarena-attack`, `smoke`, `core`, and `research-factors`. The native recipes are deliberately small smoke selections, not complete benchmark populations. Expand `task_ids`, repeat counts, and attack options for a larger campaign. Every selected configuration and required credential name is checked before the experiment starts spending model tokens.

Reports are saved under `.intentbench/experiments/ID/results.json`, linking to the existing native and gym run artifacts. Pairing hashes include model identity, task/environment configuration, planning protocol, and budgets; model settings are resolved without storing API keys. Original native metrics are kept per task. Gym metrics separately report proposal drift, unauthorized effects, completion under policy, guard detection, and overblocking against authored labels. There is no combined score across incompatible native graders. Native guard detection/overblocking remain unmeasured without independent proposal labels. SDK decisions alone are not labels of intent drift.

Matching configuration/seeds does not prove matching external website state. Archive and restore upstream service/database snapshots between conditions when tasks mutate persistent services; a browser reset is not necessarily a database reset. The gym records native setup but cannot attest to an external service snapshot. Local declarative and AgentDojo environments start from fresh per-episode state. Remote model determinism and backend policy revision also need independent control.

For protection value, compare task utility and attack success together. Include authorized clean/control cases to measure interference; vary policy strictness, interruption/revocation, third-party injection, tool scope, cumulative limits, delegation, recovery, and multi-step plans. Choose online runs to study recovery after intervention. Use the existing labeled-trace/replay interface for fixed-proposal guard evaluation; an enforced online trajectory is not a counterfactual score of the unguarded trajectory. Repeat trials and adjudicate ambiguous cases before treating small differences as meaningful.

## Plans and execution boundaries

`ArmorIQInsideAgent` composes the original agent with `ArmorIQGuard`. Native runners invoke its proposal method, check the canonical tool call through the same object's SDK session, and execute the unchanged native action only when enforcement allows it. The SDK never dispatches the benchmark tools. This keeps native environment state transitions and upstream graders in their original implementations. Native final answers are checked as `agent__respond` when `guard_responses: true`; browser chat actions are checked as `browser__send_msg_to_user`.

Native configurations accept either an **author-owned `guard_plan`** or an explicit **`plan_factory`**. The sample factory obtains one model-generated initial plan from public task/tool/browser observations. That planning call runs in every condition, including the unguarded baseline, and is recorded separately. It does not receive grader state, ground-truth actions, or hidden attacker goals. There is no automatic plan expansion following a denied action. Successful capture feedback is not added to the native model prompt. Browser mapping accepts one literal action call, refuses uncheckable code, and preserves the original native action for execution.

Providers that return several tool calls despite the single-call request are processed in their declared order. Each queued call gets a separate execution check and feedback record; local intent versions remain those of the original proposal. The agent does not make a fresh model decision between calls from that batch. Record this sequential execution protocol when comparing with upstream implementations that execute batches concurrently.

Initial-plan quality is part of this experimental protocol. Tools or arguments discovered later, incomplete plans, and unknown final-answer contents can cause interference. A submitted plan is an agent declaration, not proof that the user authorized it; backend policies must constrain it. Inspect captured plans and blocked calls when interpreting utility changes. The SDK owns plan binding and semantic enforcement; the gym does not claim exact-argument cryptographic enforcement merely because a plan was captured. These planned baselines should be compared against their matching planned guarded runs, not silently against earlier no-planning baseline artifacts.

In local gym suites, the same tool-calling agent already has `submit_plan`, action-specific approval, and task tools. The inside wrapper checks those proposals at the existing session execution boundary. Local `finish` remains terminal bookkeeping rather than a scored output effect; output-exfiltration evaluation needs an authored output tool/scenario. Native response checking is a distinct capability.

A tool proposed before any captured plan is blocked as the SDK integration's `plan-required` precondition, allowing the local agent to declare a plan and recover. This is labeled in decision evidence; it is not reported as a remote backend verdict or an infrastructure outage. Plan capture failures and enforcement outages remain errors.

For an existing agent outside this gym, integrate at its executor:

```python
from agent_intent_bench.inside import ArmorIQInsideAgent
from agent_intent_bench.models import Action, AdapterConfig

inside = ArmorIQInsideAgent(existing_agent, AdapterConfig(kind="armoriq"))
try:
    # context contains only public user intent/authorization, never grader labels.
    await inside.evaluate(Action(kind="plan", plan=agent_declared_calls), context)
    proposal = await inside.act(public_observation)
    decision, result = await inside.execute(proposal, context, existing_tool_executor)
finally:
    await inside.aclose()
```

`act()` returns a proposal; external harnesses must connect the `execute()` gate rather than dispatching that proposal themselves. Block/hold never calls the executor in enforce mode. SDK outages, malformed enforcement responses, and inconsistent decisions raise errors, leaving safety unmeasured for that episode. Holds can trigger the SDK's backend delegation workflow; this integration does not fabricate user approval. Exceptions redact configured credential values.

AgentLAB, IntentFlux, and InterruptBench **factor adaptations** run through the local intent gym and can use the inside wrapper. Native SDK instrumentation in this release is implemented for AgentDojo, ST-WebAgentBench, and DoomArena. The earlier AgentLAB prompt-only native smoke, unavailable native IntentFlux release, and blocked InterruptBench WebArena environment are not represented as fully instrumented native runs.
