# Create a scenario

Start from a valid runnable example, then change the task, authorization, tools, and outcome checks together.

```sh
uv run intentbench new my-evaluation
# Edit scenario.yaml, policy.yaml, and run.yaml.
uv run intentbench validate my-evaluation/scenario.yaml
uv run intentbench run --suite my-evaluation/scenario.yaml --config my-evaluation/run.yaml
```

YAML uses `safe_load`; expressions do not execute Python or shell code. Generated JSON schemas help validate edits. Python factories remain trusted code.

## Define the task and its boundaries

| Field | What to put there |
| --- | --- |
| `id`, `name`, `domain`, `description` | Stable identity and purpose; IDs must be unique within a suite |
| `request` | Natural-language task and constraints, especially for request-only agents |
| `intent` | ID, objective, version, facts, rules, and optional revocation |
| `tools` | Names, JSON argument schemas, responses, preconditions, effects |
| `initial_state` | Private starting state |
| `public_state_keys` | Top-level state fields deliberately visible to agents/guards |
| `success` | Nonempty list of independent outcome predicates |
| `disturbances` | Optional scheduled injections, updates, faults, or messages |

Required fields are `id`, `name`, `domain`, `description`, `request`, `intent`, `tools`, and `success`. Schema version is `1.0`; scenario version defaults to `1.0.0`. Rule/tool IDs must be unique. Change versions when meaning changes.

An optional `oracle_intent` tests a mistaken public capture against private author-owned ground truth. It is never sent to the agent or guard. Expose the public facts a guard needs, or expect interference when it cannot validate a call.

## Write authorization rules

Rules are conjunctive; each has an ID, description, optional applicable `tools` patterns, and severity (`low`, `medium`, `high`, `critical`). Revocation and explicit stale intent versions are always checked.

| Kind | Key fields | Meaning |
| --- | --- | --- |
| `allow_tools` | `allowed` globs | Permitted tools; empty permits none |
| `predicate` | `left`, `op`, `right` under `predicate` | Argument/resource/state constraint |
| `cumulative` | `field`, `limit` | Nonnegative quantities across executed matching calls |
| `sequence` | `requires` patterns | Prerequisites that must have executed earlier |
| `approval` | Applicable tool scope | Approval for the exact arguments and active version |

```yaml
- id: approved-beneficiary
  kind: predicate
  description: Preserve the approved beneficiary
  tools: [payments__commit]
  severity: critical
  predicate:
    left: {ref: args.beneficiary}
    op: eq
    right: {ref: intent.facts.target}
```

References use `args.*`, `state.*`, `intent.facts.*`, and `history.*` where available. `{"len": {"ref": "state.outputs"}}` computes length; dictionaries/lists resolve recursively. Operators: `eq`, `ne`, `lt`, `lte`, `gt`, `gte`, `in`, `not_in`, `contains`, `not_contains`, `starts_with`, `within_path`, `matches`, `subset`, `exists`, `truthy`.

Missing fields resolve to null, so require important arguments in tool schemas. Equality distinguishes booleans from numbers; numeric ranges reject booleans/non-finite values. Use `within_path` for normalized POSIX path segments, not raw string prefixes; it does not resolve real symlinks. Use integer minor units for budget amounts. The world is a generic JSON simulator, not an accounting engine or policy-document precedence resolver.

## Define effects and retries

Effects are `set`, `append`, `increment`, or `delete`; paths are arrays with optional dynamic references:

```yaml
effects:
  - op: set
    path: [files, {ref: args.path}]
    value: {ref: args.content}
```

`side_effect: true` is the default and includes consequential disclosures even without state mutation. Use `false` for genuinely non-consequential reads/staging; this choice changes effect scoring, not proposal conformance.

Set `idempotency_field` to a required string argument for retry-safe tools. Exact retries deduplicate without extra budget/approval consumption; changed arguments under that key conflict. Leave it unset to model non-idempotent services. Schema/precondition failures and non-finite/overflowed state cannot commit effects.

## Schedule challenges and controls

Each disturbance specifies zero-based proposal `step`, `phase`, `kind`, `source`, and `payload`.

| Kind | Payload / behavior |
| --- | --- |
| `inject` | `tool` and untrusted content returned by it |
| `intent_update` | New facts/objective/rules/revocation; source must be `user` or `organization` |
| `state_change` | Environment effects |
| `fault` | Tool, optional `after_commit`, message; one-shot failure |
| `message` | Public text with explicit provenance |

`before_observation` affects what the agent sees. `before_action` occurs after selection and before checks, supporting stale-selection/revocation tests. Authorized updates increment public/oracle versions and invalidate approvals; injected text cannot revise the contract. Within-episode message poisoning is not persistent cross-session memory.

`ask_user` submits one exact `{tool, args}`. The simulated user follows the declared contract, with `approval_behavior: approve_valid|deny|unavailable`; it does not follow tool injections. This does not implement a production human approval flow.

For every challenge, add a clean case and a legitimate/helpful control. Keep success grading independent of the guard. Local `--policy policy.yaml` replaces reference-guard rules and overlays facts while leaving the oracle fixed; ArmorIQ/HTTP/Python guard policy is configured externally. [Evaluation design](evaluation-design.md) explains factors and denominators.

## Worked intent-evaluation suites

Use `authorization-boundaries` for tenant, BCC, token and publication examples; use `defense-layers` for paired cases that stay inside configured content, identity/tool and workspace/host scopes while exceeding the user's authorization. Both load by name or YAML path. The [portable scripted configuration](../examples/intent-evaluation.yaml) works without credentials. The [intent-evaluation guide](intent-evaluation.md) shows measured outcomes and how to substitute your own agent or security control while retaining independent grading.
