# Connect your agent

Choose the integration that lets your agent keep its decision logic. The local and native tracks have different observation/action formats.

| Integration | Use it when | Example |
| --- | --- | --- |
| Python factory | You can wrap an agent's decision call | [agent_adapter.py](../examples/agent_adapter.py) |
| HTTP adapter | Your agent runs in another process/service | [http_agent_service.py](../examples/http_agent_service.py) |
| Compatible model endpoint | You want the included tool-calling loop | [openai-compatible.yaml](../examples/openai-compatible.yaml) |
| Session client | Your agent already owns the loop | [external_loop.py](../examples/external_loop.py) |
| Native action adapter | Your agent drives an upstream environment | [Native protocol](benchmarks.md#agent-and-guard-protocol) |

## Local Python factory

```yaml
agent:
  kind: python
  factory: my_package.adapter:create_agent
mode: unguarded
intent_visibility: request_only
```

`create_agent(config: AdapterConfig)` returns a fresh object per episode with `async act(observation) -> Action` and optional `async aclose()`.

The observation contains the request, provenance-tagged messages, public state, tool schemas, prior result, and step/session ID. `structured` visibility also exposes the public contract and starter workflow; fixtures require this mode. `request_only` leaves the model to infer its task from public instructions. Neither mode exposes private grading rules or disturbance schedules.

| Action | Shape |
| --- | --- |
| Tool | `{"kind":"tool","tool":"my_tool","args":{}}` |
| Plan | `{"kind":"plan","plan":[{"tool":"my_tool","args":{}}]}` |
| Approval request | `{"kind":"ask_user","args":{"action":{"tool":"my_tool","args":{}}}}` |
| Finish | `{"kind":"finish"}` |

Include `intent_version` when the agent selected an action under a particular contract. Omitting it binds the action to the current version on receipt, so it cannot measure an explicitly stale selection. Declaring a plan does not grant execution-time approval.

## Keep your existing loop

Start `uv run intentbench serve`, then:

```python
from agent_intent_bench.client import GymClient
from agent_intent_bench.models import RunConfig

async def evaluate(agent):
    async with GymClient() as gym:
        obs = await gym.reset("payments.approval.clean",
                              config=RunConfig(mode="unguarded", intent_visibility="request_only"))
        while True:
            step = await gym.step(await agent.act(obs))
            if step["done"]:
                return step["run_id"]
            obs = step["observation"]
```

This is a Gym-style async session API; it does not implement Gymnasium `Env`, spaces, or a scalar reward.

| Endpoint | Purpose |
| --- | --- |
| `POST /v1/sessions` | `suite`, `scenario_id`, `config`; returns observation, ID, token, run ID |
| `GET /v1/sessions/ID` | Current public observation |
| `POST /v1/sessions/ID/step` | Action; returns result, observation, `done`, run ID |
| `DELETE /v1/sessions/ID` | Cancel/finalize and save evidence |

Follow-up requests require `X-Session-Token` and configured service authentication. `GymClient` handles session tokens and cleanup. Sessions enforce sequential steps, timeouts, ownership, and a 32-session limit; expired sessions can still be deleted. Reviewer `/api/*` endpoints expose grading data and are separate from agent sessions.

## HTTP and other guards

A local HTTP agent receives `{"schema_version":"1.0","observation":{...}}` at its configured endpoint and returns `{"action":{...}}`. An HTTP guard receives `schema_version`, `action`, and public `context`; it returns `{"action":"allow|block|hold","reason":"..."}` with optional `policy_ids` and `evidence`. `api_key_env` supplies a bearer token; separate service state by episode ID.

A Python guard factory takes `AdapterConfig` and returns `async evaluate(action, context) -> Decision`, optionally `aclose()`. Context contains public intent/state, executed-call history, approvals, declared plan, and idempotency fields; it contains no oracle verdict. Transport failures are errors, not successful blocks.

For SDK enforcement and an execution wrapper around an existing agent, see [ArmorIQ-inside](armoriq-inside.md). Python plugins share the process and filesystem; use a separate service/container when that is outside your threat model.
