# Documentation

Start with the [intent-evaluation guide](intent-evaluation.md). It explains the problem through examples, walks through the results, and shows how to run the comparison yourself.

| What you want to do | Start here |
| --- | --- |
| Try the benchmark without credentials | [Offline example](intent-evaluation.md#run-an-intent-evaluation-without-credentials) |
| Test your agent or another security control | [Agent and guard integrations](intent-evaluation.md#connect-your-agent-or-another-control) |
| Compare with ArmorIQ | [SDK setup and troubleshooting](armoriq-inside.md) |
| Understand the findings | [Results overview and exact counts](benchmark-results.md) |
| See which original benchmark checks accepted extra actions | [AgentDojo and browser examples](authorization-boundaries.md#ports-to-native-benchmarks) |
| Create tasks and permission rules for your application | [Scenario authoring](authoring.md) |
| Measure out-of-scope edits by real coding agents | [Intent drift in AI coding agents](../research/intent-drift/README.md) |
| Understand safe completion, errors and other scores | [Evaluation design](evaluation-design.md) |
| Run, inspect or export results | [Running evaluations](running.md) |
| Install the original benchmark environments | [AgentDojo, ST-WebAgentBench and DoomArena](benchmarks.md) |
| Work with the Python/HTTP interfaces | [Adapter reference](adapters.md) |
| Understand how actions are checked and executed | [Architecture](architecture.md) |

There are two ways to evaluate behavior. **Local scenarios** use simulated tools to test a permission rule in isolation. **Original benchmark environments** run upstream tools and retain their original task and security scores. Both can record whether the user's specific authorization was respected.

Machine-readable evidence is available in the [result index](results.json), [control comparison](defense-layer-results.json), and [seventeen-case authorization study](authorization-boundary-results.json). The reports explain which data belongs to each experiment; their scores are kept separate.

The project is ArmorIQ Agent Intent Gym. Its bundled scenarios are called AgentIntentBench. The Python package is `agent_intent_bench`, and the command is `intentbench`. For development and contribution instructions, see [CONTRIBUTING.md](../CONTRIBUTING.md).
