# Evaluate user intent across agents and security layers

**Task success, attacker-goal failure, content safety, valid identity and sandbox containment are insufficient on their own to establish that an agent followed the user's intent.** Intent evaluation must check the operations used to complete the task: which tenant, recipient, file, record, privilege, amount and active authorization applied at execution time.

ArmorIQ Agent Intent Gym makes those questions reproducible. Run original benchmarks for their native utility, attack and policy measurements. Add explicit intent contracts, paired challenges and legitimate controls, and score proposals and executed effects independently of the guard. Connect your agent, ArmorIQ, another guard or a reference policy through the same interfaces.

## What the existing benchmark checks leave open

| Existing evidence | What it establishes | Remaining intent question / observed evidence |
| --- | --- | --- |
| AgentDojo task utility | The selected task's outcome checks pass. | In task 0, an answer still passes after an unrelated read, unrequested email or calendar cancellation. In task 33, the requested email still passes with an unauthorized BCC. |
| Strict state equality | The final state matches the expected unchanged state. | The unrelated read in task 0 passes because it leaves state unchanged. Read authorization requires another check. |
| A configured attacker-goal grader | Whether its specified attacker objective occurred. | That objective does not enumerate every operation outside the current user's authorization. The added probes use independent labels; native attacker success stays null where no upstream injection-task grader is assigned. |
| ST-WebAgentBench native policy reports | Compliance with its configured task/environment policies. | Those policies remain valuable and explicit; arbitrary user constraints require their own coverage. No new intent probes were evaluated on ST in this study. Its earlier task-47 results remain published. |
| DoomArena success filters | Whether the configured attack target was reached. | Its filter correctly detects direct and indirect egress in our probes. Those results also expose an ArmorIQ click-context limitation; a URL rule cannot constrain a destination absent from the checked action. |

The conclusion concerns **sufficiency for intent conformance**, not an absence of security evaluation in these projects. AgentDojo already supplies strict utility and attacker-goal grading; ST evaluates policies; DoomArena detects configured attacks. We retain those original grades and supplement them. [Native evidence and pinned task sources](authorization-boundaries.md#ports-to-native-benchmarks).

Across six selected scripted AgentDojo cases, native task utility is **6/6 with or without ArmorIQ**, while unauthorized calls change **4 → 0** and completions under the authored authorization change **2/6 → 6/6**. A utility-only view hides that difference. The BCC case is particularly useful: ArmorIQ blocks the unauthorized send and permits a clean retry, preserving the requested email. These are scripted executor probes, not model jailbreak rates.

## Beyond content, identity and sandbox boundaries

The new `defense-layers` suite has **20 simulated cases**: five clean, five legitimate controls and ten intent violations. It reuses the tenant, BCC and token concepts and adds workspace-file and same-service CRM cases. Every candidate, including an unsafe one, is declared in the plan. All business operations are simulated; no real file, CRM record, email or token is changed.

| Control layer | Local baseline implemented | Intent violation inside that scope |
| --- | --- | --- |
| Content guardrail | Scan argument text for a configured forbidden marker. | Benign report text goes to an unauthorized recipient, file or record. |
| Identity and access | Permit a harness-configured pre-authenticated `reporting-service` principal and its tool grants. | The legitimate principal uses a granted tool on the wrong tenant, customer, recipient or token privilege. This baseline does not authenticate credentials or model a full IAM product. |
| Sandbox / egress scope | Enforce `/workspace/` path containment and the `https://crm.internal` host, plus a tool boundary. | A write targets another report inside the workspace, or changes the wrong CRM record/field on the allowed host. This is a boundary-policy proxy, not an operating-system sandbox. |
| Combined local layers | Apply all three checks above. | All declared boundaries pass while the request's narrower authorization is violated. |
| Intent enforcement | Validate each proposed operation against the task's tenant, recipients, path, record/field, scope and lifetime. | The independent intent oracle measures whether the unauthorized operation executed and whether the requested work still completed. |

The content baseline is a transparent pattern check, not an evaluation of contextual guardrails. An identity/access product or sandbox equipped with the same full intent policy could enforce these cases too. These results identify the **missing policy dimension in the declared configurations**, not an inherent inability of every product in those categories. Authentication, least privilege and isolation remain complementary controls.

### Measured control-layer comparison

**October 23, 2026 · 20 identical cases per condition · fixed scripted proposals · SDK 0.8.17.** The frozen ArmorIQ v2 policy was registered for a new dedicated agent. Original 17-case authorization results are unchanged. [Detailed defense-layer data](defense-layer-results.json) · [Consolidated result index](results.json).

| Condition | Task successes | Completion under policy | Unsafe-effect episodes | Denied authorized proposals |
| --- | ---: | ---: | ---: | ---: |
| Unguarded | 20/20 | 10/20 | 10 | Unmeasured |
| Content-pattern baseline | 20/20 | 10/20 | 10 | 0 |
| Identity/tool-grant baseline | 20/20 | 10/20 | 10 | 0 |
| Workspace/host-boundary baseline | 20/20 | 10/20 | 10 | 0 |
| Combined local layers | 20/20 | 10/20 | 10 | 0 |
| Exact plan membership | 20/20 | 10/20 | 10 | 0 |
| Local reference intent guard | 20/20 | 20/20 | 0 | 0 |
| ArmorIQ monitor | 20/20 | 10/20 | 10 | 0 |
| **ArmorIQ enforce** | **20/20** | **20/20** | **0** | **0** |

All **180 attempts completed**, with zero errors/truncations. All nine conditions have identical tool-proposal streams and matching pairing hashes. Eleven separate baseline self-checks verify expected allows/blocks for the forbidden content marker, untrusted principal, ungranted tool, outside-workspace path, traversal and outside/lookalike host. These self-checks establish that the proxies implement their declared scopes; they do not make them equivalent to commercial products. No unsafe main-suite case is removed after seeing results. Repository checks passed **129 tests**, lint, formatting, package build, and publication scanning. The exact credential-free matrix command was run successfully.

**ArmorIQ prevented all ten intent violations while preserving all twenty requested tasks.** The correct reference intent guard matches that result. This demonstrates useful runtime enforcement beyond the configured layers, not unique expressiveness, broad product superiority, or a population attack-resistance estimate. The [Qwen comparison and broader model campaign](benchmark-results.md) retain their smaller gains, truncations and utility costs; those are separate protocols and are not pooled with this fixture study.

## Run an intent evaluation without credentials

From a repository checkout with Python 3.11 and uv:

```sh
uv sync --locked --extra dev
uv run --no-sync intentbench validate defense-layers
uv run --no-sync intentbench matrix --suite defense-layers \
  --config examples/intent-evaluation.yaml
uv run --no-sync python scripts/run_defense_layer_campaign.py
```

The matrix compares unguarded and reference intent enforcement. The campaign runs seven offline conditions, including the three layer proxies, their combination and plan membership. Expected outcomes are **10/20 CuP and ten unsafe-effect episodes** for the scope-only conditions, and **20/20 CuP with zero unsafe effects** for the reference intent guard. Output is in `.benchmarks/defense-layers/results.json`; raw runs are in `.intentbench/`.

For the original 17-case suite, change `--suite` to `authorization-boundaries`: the same credential-free example gives **9/17 → 17/17 CuP**. The agent in [intent-evaluation.yaml](../examples/intent-evaluation.yaml) is deliberately scripted. Its public observation contains the candidate, requested operation and reporting protocol, not expected labels.

## Connect your agent or another control

Supply a normal [agent configuration](adapters.md), using Python, HTTP or a compatible model endpoint. Only its `agent` section is substituted, keeping the suite and budgets fixed across conditions:

```sh
uv run --no-sync python scripts/run_defense_layer_campaign.py \
  --agent-config my-agent.yaml --output .benchmarks/my-agent/results.json
```

For external HTTP guards, copy [external-http.yaml](../examples/defense-layers/external-http.yaml). Its endpoint receives `{"schema_version":"1.0", "action":{...}, "context":{...}}` and returns `{"action":"allow|block|hold", "reason":"..."}`. Context includes the public request, public intent/state, plan and history; it excludes private oracle labels. Optional authentication uses `api_key_env`.

```sh
uv run --no-sync python scripts/run_defense_layer_campaign.py \
  --extra-guard my-guard=examples/defense-layers/external-http.yaml \
  --output .benchmarks/my-guard/results.json
```

For a Python SDK, copy [external-python.yaml](../examples/defense-layers/external-python.yaml) and implement `your_adapter.check(action=..., context=...)`. The [checker bridge](../examples/intent_guard_adapter.py) supports synchronous/asynchronous checkers, copies inputs, and validates the returned Gym decision. Translate the vendor's verdict explicitly; errors remain errors. For example, your bridge can call a content SDK, an identity/authorization API, or a sandbox supervisor before returning the decision.

Use repeated `--extra-guard NAME=YAML` arguments for multiple implementations. Record versions, enabled features, rules, resource permissions, identity grants and exact input surfaces. A content-only integration and an intent-aware integration of the same product are different configurations. To evaluate a **real sandbox**, bind your agent/tool execution to its actual runtime and collect containment evidence; the local workspace/host proxy does not test isolation, escape resistance or real side effects. Keep guards at the pre-execution boundary; a text-only guard that cannot inspect calls should be labeled with that limitation.

To add ArmorIQ to the same campaign:

```sh
uv sync --locked --extra dev --extra armoriq
# Configure .env locally as described in armoriq-inside.md.
uv run --no-sync python scripts/provision_armoriq.py --register --apply \
  --tracks defense-layers --deployment my-defense-layers-v1
uv run --no-sync python scripts/run_defense_layer_campaign.py \
  --setup .benchmarks/policy-setup/my-defense-layers-v1
```

Agent registration uses the Python CLI; policy import activates the checked-in [v2 policy](../examples/armoriq-inside/policies/defense-layers.yaml). Use a new deployment suffix for revisions. The runner verifies policy IDs/versions on guarded tool decisions and keeps monitor passive. [SDK/native prerequisites](armoriq-inside.md).

## Add intent scenarios for your application

Start with `uv run intentbench new my-evaluation`. Define the public request, tool schemas and effects, explicit authorization, and independent task-success predicates. Add close unauthorized variants and legitimate alternatives; keep the oracle fixed when swapping guards. [Authoring](authoring.md) covers per-call constraints, cumulative budgets, prerequisites, approvals and changing/revoked intent. The bundled policy does not implement every one of those dimensions; earlier broad results show the consequences.

Use native adapters when the behavior depends on a real upstream environment, and local scenarios when isolating a particular authorization rule. Report task success, safe completion, unauthorized proposals/effects, authorized interference, errors and truncations separately. A final answer alone is insufficient evidence of intent conformance; the path to it is part of the evaluation.
