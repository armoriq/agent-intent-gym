# Benchmark sources and attribution

The gym's native integrations call optional upstream packages. We do not vendor upstream implementations or datasets. Preserve the upstream license notices when redistributing those dependencies or their data.

| Source | License / attribution boundary |
| --- | --- |
| [AgentDojo](https://github.com/ethz-spylab/agentdojo) | MIT; native toolkit, tasks, attacks, and grader APIs |
| [ST-WebAgentBench](https://github.com/segev-shlomov/ST-WebAgentBench) | Apache-2.0; native browser tasks and policy evaluator APIs |
| [DoomArena](https://github.com/ServiceNow/DoomArena) | Apache-2.0; native attack gateways and success-filter APIs |
| [AgentLAB: Benchmarking LLM Agents against Long-Horizon Attacks](https://arxiv.org/abs/2602.16901) | Cited as a factor-design source; no code or dataset redistribution |
| [IntentFlux: When Users Change Their Minds](https://arxiv.org/abs/2609.32520) | Cited as a factor-design source; no code or dataset redistribution |
| [InterruptBench](https://github.com/HenryPengZou/InterruptBench) | Cited as a factor-design source; the reviewed checkout contains no license file, and no code/data is copied |

`research-factors` contains our own synthetic adaptations of cited ideas, with source tags and links in each scenario. Their outputs are local intent-gym results and should not be attributed to the original benchmarks. The runtime catalog records the reviewed source revisions; run manifests distinguish these from installed versions and actual editable-checkout revisions.
