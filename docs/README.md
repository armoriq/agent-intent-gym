# Documentation

Start with [why intent evaluation needs explicit contracts, and how to run it](intent-evaluation.md). Then choose the guide for your task.

| I want to… | Read |
| --- | --- |
| Understand benchmark gaps and compare security layers | [Intent evaluation, control-layer results and external adapters](intent-evaluation.md) |
| Run a suite, use the TUI/browser, or inspect a result | [Running evaluations](running.md) |
| Connect my agent or keep its existing decision loop | [Agent adapters and session API](adapters.md) |
| Compare the same agent with and without ArmorIQ | [ArmorIQ setup and troubleshooting](armoriq-inside.md) |
| Run AgentDojo, ST-WebAgentBench, or DoomArena | [Native benchmarks](benchmarks.md) |
| Define my own task, tools, policy, and challenges | [Scenario authoring](authoring.md) |
| Choose evaluation modes and understand the scores | [Evaluation design](evaluation-design.md) |
| Compare ArmorIQ results, run IDs, and setup differences | [Results ledger](benchmark-results.md) · [consolidated result index](results.json) |
| Understand benchmark gaps and ArmorIQ enforcement evidence | [Gap analysis and native ports](authorization-boundaries.md#benchmark-gaps-and-armoriq-evidence) · [detailed result data](authorization-boundary-results.json) |
| Understand execution order and implementation boundaries | [Architecture](architecture.md) |

Two tracks share the workbench: **local intent suites** use authored contracts and simulated tools; **native benchmarks** execute upstream environments and retain their graders. The toolkit is ArmorIQ Agent Intent Gym; AgentIntentBench is its reference suite. The import name is `agent_intent_bench`, and the CLI is `intentbench`.

For development checks and contribution conventions, see [CONTRIBUTING.md](../CONTRIBUTING.md).
