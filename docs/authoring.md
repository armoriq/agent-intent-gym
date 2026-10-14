# Scenario and policy authoring

Start with `uv run intentbench new my-evaluation`. Generated JSON schemas can be used in an editor. A scenario or suite is data; YAML is loaded with `safe_load`, and the expression language never evaluates Python or shell text.

## Required scenario fields

`id`, `name`, `domain`, `description`, `request`, `intent`, `tools`, and nonempty `success` predicates. Version defaults to `1.0.0`; schema version is `1.0`. IDs within a suite and rule/tool IDs within a scenario must be unique.

The user request should state the intended task and constraints in natural language, especially for `request_only` runs. The contract has an objective, monotonically increasing version, facts, rules, and revocation status. An optional `oracle_intent` represents author-owned ground truth when testing a mistaken public capture. It is never an agent or guard input.

## Rule types

| Kind | Fields | Interpretation |
| --- | --- | --- |
| `allow_tools` | `allowed` glob patterns | Tool scope; an empty list permits none |
| `predicate` | `predicate.left`, `op`, `right` | Argument, state, data, or resource constraint |
| `cumulative` | `field`, `limit` | Nonnegative quantities accumulated across executed matching calls; exact idempotent retries contribute zero |
| `sequence` | `requires` tool patterns | Each prerequisite must have executed earlier; this is not a full temporal-logic automaton |
| `approval` | tool scope | One exact call requires user approval bound to its arguments and active intent version |

Every rule has `id`, `description`, optional `tools` applicability patterns, and severity (`low`, `medium`, `high`, `critical`). Rules are conjunctive. Revocation and explicit stale versions are always checked. Organization/user precedence is represented by the author-resolved effective contract; this release does not automatically resolve competing policy documents or prove asserted identities.

Example:

```yaml
- id: beneficiary
  kind: predicate
  description: Preserve the approved beneficiary
  tools: [payments__commit]
  severity: critical
  predicate:
    left: {ref: args.beneficiary}
    op: eq
    right: {ref: intent.facts.target}
```

## Expressions

- `{"ref": "args.amount"}` looks up arguments; `state.*`, `intent.facts.*`, and `history.*` are also available where appropriate.
- `{"len": {"ref": "state.outputs"}}` computes a collection/string length.
- Dictionaries/lists otherwise resolve recursively. This allows structured results and effects to refer to arguments or state.
- Operators: `eq`, `ne`, `lt`, `lte`, `gt`, `gte`, `in`, `not_in`, `contains`, `not_contains`, `starts_with`, `within_path`, `matches`, `subset`, `exists`, `truthy`.
- `eq` distinguishes booleans from numbers. Numeric range rules reject booleans/non-finite values. Missing values resolve to null; tool schemas should make important arguments required.
- Use `within_path` for POSIX resource scope rather than a raw prefix. It normalizes `..` and checks segment boundaries. It does not resolve real filesystem symlinks. Regexes and the declarative specifications are trusted author inputs.

## Simulated tools

Each tool has a JSON Schema `parameters` object and an optional response, preconditions, and effects. Available effects are `set`, `append`, `increment`, and `delete`. Paths are arrays, allowing a dynamic key without interpreting dots or slashes:

```yaml
effects:
  - op: set
    path: [files, {ref: args.path}]
    value: {ref: args.content}
```

`side_effect: true` (default) marks execution as consequential, including a sensitive disclosure even with no state mutation. Use `false` only for non-consequential fixture reads/staging. These choices affect effect scoring; proposal conformance is still scored for every tool call.

Set `idempotency_field` to a required string argument for a tool with retry-safe semantics. Repeated exact arguments under that key deduplicate. Different arguments conflict. Leave it unset to model a service without idempotency.

Use integer minor units for money/budget quantities. The generic JSON world uses ordinary numeric arithmetic; it is not a financial accounting engine. Non-finite inputs and overflowed state are rejected before commitment.

`initial_state` is private environment state. `public_state_keys` explicitly selects top-level state keys visible to the agent and guard; otherwise the state is accessed through tools. Include state facts needed for the policy guard, or accept that a guard lacking those facts can overblock. Outcome checks run against private state and the active oracle intent.

## Disturbances and approval

Disturbances declare `step` (zero-based proposal index), `phase`, `kind`, `source`, and `payload`:

| Kind | Payload |
| --- | --- |
| `inject` | `tool` plus untrusted content returned by that tool |
| `intent_update` | New `facts`, `objective`, `rules`, and/or `revoked`; only source `user` or `organization` |
| `state_change` | `effects` applied by the environment |
| `fault` | `tool`, optional `after_commit`, optional `message`; a one-shot simulated failure |
| `message` | Public message text with explicit provenance |

`before_observation` changes what the agent sees. `before_action` applies after selection and before enforcement/execution, for stale-action tests. Updates increment the active public and oracle versions and invalidate approvals. They are scheduled author-owned events; injected text cannot update the contract.

`ask_user` includes `args.action: {tool, args}`. The fixture user follows the declared contract, not instructions inside a tool response. `approval_behavior` can be `approve_valid`, `deny`, or `unavailable`. Production-human interaction is not implemented; use explicit user events or an external adapter for more realistic approval workflows.

## Guard-policy experiments

`--policy policy.yaml` takes an Intent-shaped document. Its rules replace the reference guard's policy, and its facts overlay public facts. The active version/revocation still follows the scenario. The private oracle and success checks remain unchanged. It is therefore possible for a permissive policy to allow an independently scored deviation.

Native ArmorIQ policies are backend-owned. The gym rejects local policy overrides for native/HTTP/Python guards to prevent giving misleading results about a policy that was never actually installed.
