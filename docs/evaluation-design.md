# Evaluation modes and factors

The gym is a common way to define and interact with intent environments; AgentIntentBench is one reference suite using that interface. Evaluation should work for agent developers, environment authors, policy owners, and protection-system researchers through the same protocols. ArmorIQ is an optional guard under evaluation, and the bundled synthetic results remain examples of the infrastructure's behavior.

The target is observable authorized behavior. Task failure, plan drift, unauthorized proposals, and unauthorized consequential effects are distinct measurements. A block-all guard can prevent effects while destroying utility; a faithfully executed signed plan can still encode the wrong goal.

## Usage modes

| User | Mode | Output to inspect |
| --- | --- | --- |
| Agent developer | Unguarded custom scenarios | Proposal/plan drift and legitimate task capability |
| Protection developer | Frozen labeled traces or saved-run replay | Allow/block/hold correctness, missed deviations, overblocking, latency |
| Integration owner | Live enforcing runs | Completion under policy, effects, recovery, intervention burden |
| Policy owner | Reference-policy override or separately installed native policies | Security–utility changes against unchanged grading definitions |
| Agent platform team | Matched unguarded/enforcing conditions | Same-scenario outcome changes and clean-task regressions |
| CI maintainer | Pinned suite, repeat budget, and explicit gate thresholds | Regression exit code plus preserved failure evidence |
| Domain evaluator | Custom authored YAML and private oracle | Scope, argument, data, approval, and outcome checks specific to a workflow |
| Existing-agent owner | Python/HTTP adapter or session client | Their agent's observed behavior on controlled gym tools |

`enforce` applies guard decisions, `monitor` records them but executes proposals, and `unguarded` skips guard initialization entirely. Do not interpret a monitor's detection rate as prevention. Static trace evaluation measures decisions without estimating an alternate live continuation.

## Factors to control

| Factor | What to vary | Current support |
| --- | --- | --- |
| Objective fidelity | Wrong plan, added side objective, dropped requirement | Private oracle, plan scoring, plan-poisoning cases |
| Tool/resource scope | Tool identity, recipient, beneficiary, file boundary | Tool globs and declarative predicates |
| Parameter fidelity | Amount, destination, required values | JSON schemas and predicates |
| Cumulative authority | Individually permitted calls exceeding aggregate limits | Cumulative rules and committed-call history |
| User changes | Add/revise/withdraw a requirement | Authorized versioned intent updates |
| Commit-time validity | Revocation after selection; state changes before execution | `before_action` disturbances and current oracle checks |
| Approval | Missing, denied, stale, wrong-argument confirmation | Exact-call/version approvals and user simulator modes |
| Recovery | Failure before commit, lost response after commit, repeated key | One-shot faults and idempotent/conflicting retries |
| Workflow prerequisites | Commit without prior read/stage | Sequence prerequisite rules |
| Third-party content | Malicious and genuinely helpful instructions | Tool injections and matched helpful controls |
| Context pressure | Distractor messages, long tool results, delayed updates | Author-scheduled messages/content; no calibrated long-horizon suite yet |
| Visibility | Natural-language task versus structured intent | `request_only` and `structured` |
| Agent variation | Model, prompt, framework, memory, sampling | Adapter config and source revision metadata; remote determinism is not guaranteed |
| Guard variation | No guard, prompt/model system, policy guard, native enforcement | Pluggable guards and frozen/live modes |
| Budget/exposure | Steps, repeats, timeouts, concurrency, case subsets | Runner configuration; per-attempt API calls and sequential steps |
| Delegation/identity | Principal, tenant, authority attenuation, forged role claims | Native backend identity where applicable; local verified-identity/delegation semantics need an environment extension |
| Dataflow | Allowed access followed by forbidden disclosure | Author predicates and consequential tool results; no automatic taint/dataflow engine |
| Adaptive attacker | Knowledge/access, feedback, turn budget | Python/HTTP agents can implement controlled adversarial behavior; built-in attacks are fixed author fixtures |

The bundled three workflow templates cover ten factors with clean, challenge, and helpful-control variants. Keep that limited domain coverage visible. Broad multi-agent delegation, adversarial memory persistence, real browsers, and adaptive attack search need additional authored environments and protocols.

## Reporting

- Name the complete agent system, guard mode/policy revision, suite/scorer/source versions, and budget. Model names alone are insufficient.
- Report clean, attack, legitimate-update, fault, and helpful-control results separately. Report domains and factors alongside aggregate scores.
- Show unsafe/authorized proposal denominators. Undefined detection on a clean-only run is not perfect detection.
- Preserve critical effects separately from average rates. A failed/incomplete episode can still have a consequential unsafe effect.
- Use independently authored policy labels. Generated scenarios and model judges need calibration before benchmark claims.
- Audit both outcomes and paths: reaching the correct final state does not erase an earlier forbidden action.
- Match scenario seeds/configuration when comparing protection modes, and distinguish descriptive comparisons from paired ones.
- Repeats estimate execution variability; related variants do not establish population-wide failure probabilities. The included intervals are descriptive episode summaries.

## Next integrations

Reuse [AgentDojo](https://github.com/ethz-spylab/agentdojo) task/attack semantics, [ST-WebAgentBench](https://github.com/segev-shlomov/ST-WebAgentBench) policy evaluation, and [DoomArena](https://github.com/ServiceNow/DoomArena) attack/environment gateways through explicit adapters while preserving original grading. [AgentLAB](https://arxiv.org/abs/2602.16901), [IntentFlux](https://arxiv.org/abs/2609.32520), and [InterruptBench](https://github.com/HenryPengZou/InterruptBench) provide valuable factor designs. These integrations are not implemented or counted in the current suite.

Inspect AI, OpenEnv/MCP serving, container-isolated worlds, clustered confidence intervals, and distributed execution should be added around the validated contracts and trace semantics rather than changing the grading to fit a vendor's guard.
