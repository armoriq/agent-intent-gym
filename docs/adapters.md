# Agent and guard integrations

The interaction boundary is the intent environment: agents consume its observations and propose actions, while optional guards evaluate those proposals. The same protocols support reference and custom environments. Connect an agent with `GymClient.reset()`/`step()` or adapt its decision function; ArmorIQ-specific configuration is needed only when selecting the native ArmorIQ guard.

## Choose the mode

| Integration | Use when |
| --- | --- |
| Python agent factory | You can wrap an existing agent's decision call |
| HTTP agent | Your agent runs in a separate service/process |
| OpenAI-compatible endpoint | You want the included tool-calling agent loop around a model |
| `GymClient` / session API | Your agent needs to keep its own loop and call gym tools |
| Native ArmorIQ guard | You want actual SDK plan/token and policy checking |
| HTTP/Python guard | You already have a different protection system |
| Independently labeled traces | You want to compare guard decisions on frozen production-derived proposals |

## Python factories

```yaml
agent:
  kind: python
  factory: my_package.bench_adapter:create_agent
  options:
    revision: your-agent-source-revision
```

`create_agent(config: AdapterConfig)` returns an object with:

```python
async def act(self, observation: dict) -> Action: ...
async def aclose(self): ...  # optional
```

Each episode gets a fresh instance. `observation` contains the request, messages with provenance, public state, JSON tool schemas, prior result, and step/session ID. Structured visibility additionally includes the public contract and starter workflow. `request_only` requires a real decision adapter; the bundled fixtures require structured observations.

Actions:

```json
{"kind":"tool","tool":"payments__commit","args":{"beneficiary":"ACME","quantity":100,"request_id":"p1","content":"Payment"},"intent_version":1}
{"kind":"plan","plan":[{"tool":"payments__read_invoice","args":{}}],"intent_version":1}
{"kind":"ask_user","args":{"action":{"tool":"payments__commit","args":{}}},"intent_version":1}
{"kind":"finish"}
```

Missing `intent_version` binds an action to the current version at receipt. Emit the version under which your agent selected the action to test stale planning accurately. A plan contains future tool calls; approval/prerequisite conditions are checked at execution rather than requiring approval merely to describe a plan.

Python guard factories return `async evaluate(action: Action, context: dict) -> Decision`, optionally `aclose()`. Decisions use `action: allow|block|hold`, `reason`, optional `policy_ids`, and optional public evidence. Context includes the public intent, visible state, execution history, approvals, current plan, and tool idempotency fields. No oracle verdict is provided.

Factories execute trusted Python. They are not a security boundary against an agent that reads the process/filesystem; use an external process/container for that threat model.

## HTTP transports

Agent request to configured `/act` endpoint:

```json
{"schema_version":"1.0","observation":{}}
```

Response:

```json
{"action":{"kind":"tool","tool":"my_tool","args":{}}}
```

Guard request to its configured endpoint:

```json
{"schema_version":"1.0","action":{},"context":{}}
```

Guard response:

```json
{"action":"hold","reason":"User confirmation required","policy_ids":["approval"]}
```

Set `api_key_env` to a named environment variable to send a bearer token. Never put credentials in the endpoint or inline options. State must be separated by `episode_id` in multi-episode services. A remote error is an infrastructure failure, not a successful block. See `examples/http_agent_service.py` for an offline transport smoke test.

## Native ArmorIQ

Configure `guard.kind: armoriq`, `api_key_env: ARMORIQ_API_KEY`, and `options.user_email` or `ARMORIQ_USER_EMAIL`. Optional options are `sdk_mode` (`sdk` or `local`), `mcp_name`, `validity_seconds`, `timeout`, `iap_endpoint`, `backend_endpoint`, and `proxy_endpoint`.

The adapter calls SDK `start_plan()` only for a declared plan action, preserving the distinction between a malicious plan and execution drift. It calls `check(tool, args, user_email=...)` before simulated tool execution. It never silently registers a fresh plan for every tool call. Tests use the SDK session interface and a mocked native transport; real backend/token issuance requires your test credentials and native policy setup.

SDK `sdk` mode uses backend checks; `local` mode uses the SDK's token/policy snapshot checks. A reported `enforce-unavailable` becomes an infrastructure error. Backend hold handling may create or consume a delegation request according to the SDK; simulated fixture approvals do not alter backend approval records. Configure this explicitly in a benchmark organization.

To evaluate an existing ArmorIQ agent rather than a fixture, wrap its action-selection function with the Python/HTTP adapter and retain the native guard. If it owns its full tool loop, expose gym tools through the session client instead. Avoid applying the same product guard twice without reporting that configuration.

## Session API

`POST /v1/sessions` with `suite`, `scenario_id`, and `config` returns the initial public observation, session ID, one-time session token, and eventual run ID. Subsequent session calls require `X-Session-Token`; service-level bearer authentication is additionally required if configured.

- `GET /v1/sessions/ID`: current public observation.
- `POST /v1/sessions/ID/step`: an Action object; returns public result, next observation, and `done`.
- `DELETE /v1/sessions/ID`: cancel/finalize a session and preserve its artifacts.

`finish` saves the episode. Session ownership, per-step/episode budgets, and sequential mutation are enforced. Active sessions are capped at 32. Expired sessions can still be deleted. Reviewer APIs (`/api/*`) are separate from this tool protocol and expose saved grading data for the local user.

`examples/external_loop.py` exercises `GymClient`. This is a Gym-style async API, not a claim of Gymnasium `Env` compatibility or a full MCP server.

## Recorded user traces

Use `intentbench score-traces traces.yaml`. A TraceDataset has ID/version/description and cases with `id`, `action`, public `context`, independent `expected: allow|block|hold`, and optional reason/domain/group. See `examples/labeled-traces.yaml`.

Labels must come from your authoritative policy/user annotation, not the guard being measured. Cases in one `group` share a guard instance in input order; include declared-plan cases when evaluating a stateful native guard. Only public guard-context fields are accepted. Metrics include exact three-way decision accuracy, unsafe-decision detection, and overblocking. No effects execute, and no task/effect scores are fabricated. The unsafe fraction reflects dataset composition, not population agent drift frequency.
