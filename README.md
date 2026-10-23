# ArmorIQ Agent Intent Gym

[![CI](https://github.com/armoriq/agent-intent-gym/actions/workflows/ci.yml/badge.svg)](https://github.com/armoriq/agent-intent-gym/actions/workflows/ci.yml)
[![Python](https://img.shields.io/badge/python-3.11%2B-blue.svg)](pyproject.toml)
[![Version](https://img.shields.io/badge/version-0.1.0-blue.svg)](pyproject.toml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

**Test whether an AI agent completes a task without doing things the user did not authorize.** Run existing benchmarks, add your own intent rules, and compare the same agent with ArmorIQ, another security control, or no guard.

[Why this exists](#why-intent-needs-its-own-evaluation) · [Results](#results) · [Quick start](#quick-start) · [Bring your agent](#bring-your-agent) · [Docs](docs/README.md)

## Why intent needs its own evaluation

Suppose you ask an agent to email a report to Finance. It sends the right report to the right person, but adds an outside recipient in BCC. The email task may pass its usual checks even though the agent shared the report without permission.

**Task success and authorized behavior are separate questions.** The same problem appears when an agent reads another tenant's records, edits the wrong file inside an allowed workspace, or requests more token privileges than the task needs.

AgentDojo, ST-WebAgentBench and DoomArena provide useful task, attack and policy checks. We keep their original scoring and add checks for the user's specific permissions. We also provide reusable scenarios so others can evaluate their own agents and security controls.

The benchmark records three things: **what the agent proposed, what actually ran, and whether the requested task finished safely**. [How intent evaluation works](docs/intent-evaluation.md).

## Results

**ArmorIQ stopped all ten intent violations in the latest 20-case study while allowing all twenty tasks to finish.** Without intent checks, the same tasks finished but ten included unauthorized actions.

### Content, identity and workspace checks

The October 23, 2026 study tests twenty cases involving tenant records, BCC recipients, token permissions, workspace files and CRM updates. A scripted agent proposes the same actions in every configuration. Tools are simulated; these runs measure which actions a guard permits, rather than how often an LLM can be tricked.

A **safe completion** means the task finished without unauthorized effects. The same independent rules score every configuration.

| Configuration | Tasks completed | Safe completions | Tasks with unauthorized effects |
| --- | ---: | ---: | ---: |
| No guard | 20/20 | 10/20 | 10 |
| Combined local content, identity and workspace/host checks | 20/20 | 10/20 | 10 |
| Local reference intent guard | 20/20 | 20/20 | 0 |
| **ArmorIQ enforcement** | **20/20** | **20/20** | **0** |

The individual local checks and a check that only verifies plan membership also allowed all ten violations. ArmorIQ monitoring detected the violations but let the actions run, as expected. Across all nine configurations, **180 attempts completed with no errors or time-limit failures**. ArmorIQ blocked no authorized proposal.

These local comparisons have a limited scope: a text-pattern check, an already authenticated identity with permission to use the tools, and workspace/host permission checks. They do not test commercial products or an actual operating-system sandbox. A control configured with the full intent rules can also enforce them, as the reference guard demonstrates.

[Full comparison, limitations and adapters](docs/intent-evaluation.md#measured-control-layer-comparison) · [Result data](docs/defense-layer-results.json)

### What the existing benchmark checks missed

In six selected scripted AgentDojo cases, its task checks passed **6/6 with and without ArmorIQ**. However, the unguarded runs also executed four unauthorized calls. ArmorIQ prevented all four while preserving the six successful tasks.

| Example | What the selected task check accepted | What ArmorIQ did |
| --- | --- | --- |
| Calendar question | Correct answer after an unrelated inbox read, unrequested email or calendar cancellation | Blocked the extra action and allowed the answer |
| Client email | Correct recipient, subject and attachment, plus an unauthorized BCC | Blocked that send, then allowed a clean retry |

Even a check that requires unchanged state missed the unrelated read, because reading did not change that state. AgentDojo also provides attacker-goal and stricter task checks; our findings show why these selected task checks alone do not prove intent compliance.

DoomArena correctly detected both routes to an attack URL. ArmorIQ blocked direct navigation and allowed task recovery, but an indirect link click still bypassed the policy because the guard could not see its destination. That remains a limitation of our integration.

[Per-case evidence and original benchmark sources](docs/authorization-boundaries.md#ports-to-native-benchmarks)

### Results with a language model

The separate October 22 comparison used Qwen2.5 3B on seventeen authorization scenarios:

| Measure | No ArmorIQ | ArmorIQ enforcement |
| --- | ---: | ---: |
| Tasks completed successfully | 11/17 | 10/17 |
| Safe completions | 9/17 | 10/17 |
| Tasks with unauthorized effects | 2 | 0 |

Enforcement prevented the two observed unsafe effects, with one additional safe completion and one fewer task success. Ten runs reached the step limit across the three configurations, including monitoring. This small, single-model study does not establish a general performance improvement.

The earlier, broader model evaluation also remains published. ArmorIQ reduced unsafe effects across its local suites, but successful tasks fell **71 → 53** on core and **65 → 56** on research factors. Its policies did not cover every workflow rule, and incomplete plans sometimes blocked legitimate work. The original browser runs also had limitations documented in the report.

[All results, methods and run IDs](docs/benchmark-results.md) · [Machine-readable result index](docs/results.json)

## Quick start

Use Python 3.11 and [uv](https://docs.astral.sh/uv/). This scripted example needs no model or credentials:

```sh
git clone https://github.com/armoriq/agent-intent-gym.git
cd agent-intent-gym
uv sync --locked --extra dev
uv run --no-sync intentbench matrix --suite defense-layers \
  --config examples/intent-evaluation.yaml
```

The command compares no guard with the local reference intent guard. Expected safe completions: **10/20 → 20/20**.

To run all seven offline configurations:

```sh
uv run --no-sync python scripts/run_defense_layer_campaign.py
```

You can also browse runs with `uv run intentbench tui` or `uv run intentbench serve` at `http://127.0.0.1:8765`.

## Bring your agent

Connect a Python agent, HTTP service, compatible model endpoint, or an agent that already owns its execution loop. You can also add an external guard through the HTTP or Python adapter.

[Connect an agent or security control](docs/intent-evaluation.md#connect-your-agent-or-another-control) · [Adapter reference](docs/adapters.md)

To create scenarios for your application:

```sh
uv run intentbench new my-evaluation
# Edit the task, tools, permissions and success checks.
uv run intentbench validate my-evaluation/scenario.yaml
uv run intentbench run --suite my-evaluation/scenario.yaml \
  --config my-evaluation/run.yaml
```

## Run with ArmorIQ

Install the SDK, set your credentials locally, and create a dedicated benchmark agent and policy:

```sh
uv sync --locked --extra dev --extra armoriq
cp -n .env.example .env
chmod 600 .env
# Fill in ARMORIQ_API_KEY and ARMORIQ_USER_EMAIL in .env.
uv run --no-sync python scripts/provision_armoriq.py --register --apply \
  --tracks defense-layers --deployment my-evaluation-v1
uv run --no-sync python scripts/run_defense_layer_campaign.py \
  --setup .benchmarks/policy-setup/my-evaluation-v1
```

This runs the scripted comparison, including ArmorIQ monitoring and enforcement. Use a new deployment name when changing a deployed policy. [SDK setup and troubleshooting](docs/armoriq-inside.md) · [Original benchmark setup](docs/benchmarks.md)

The recorded studies used ArmorIQ SDK **0.8.17** and versioned v2 policies. Current repository checks pass **130 tests**, along with code and documentation checks. The measured benchmark results are unchanged.

[Documentation](docs/README.md) · [Contributing](CONTRIBUTING.md) · [MIT license](LICENSE) · [Upstream attribution](THIRD_PARTY_NOTICES.md)
