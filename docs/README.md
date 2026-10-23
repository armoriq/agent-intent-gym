# Documentation

Start with [running evaluations](running.md). Then choose the guide for your task.

| I want to… | Read |
| --- | --- |
| Run a suite, use the TUI/browser, or inspect a result | [Running evaluations](running.md) |
| Connect my agent or keep its existing decision loop | [Agent adapters and session API](adapters.md) |
| Compare the same agent with and without ArmorIQ | [ArmorIQ setup and troubleshooting](armoriq-inside.md) |
| Run AgentDojo, ST-WebAgentBench, or DoomArena | [Native benchmarks](benchmarks.md) |
| Define my own task, tools, policy, and challenges | [Scenario authoring](authoring.md) |
| Choose evaluation modes and understand the scores | [Evaluation design](evaluation-design.md) |
| Check the latest results, run IDs, and setup differences | [Results ledger](benchmark-results.md) · [summary data](results.json) |
| Understand execution order and implementation boundaries | [Architecture](architecture.md) |

Two tracks share the workbench: **local intent suites** use authored contracts and simulated tools; **native benchmarks** execute upstream environments and retain their graders. The toolkit is ArmorIQ Agent Intent Gym; AgentIntentBench is its reference suite. The import name is `agent_intent_bench`, and the CLI is `intentbench`.

For development checks and contribution conventions, see [CONTRIBUTING.md](../CONTRIBUTING.md).
