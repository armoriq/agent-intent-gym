# Choose an evaluation

The gym measures **observable authorized behavior**. Task failure, wrong plans, unauthorized proposals, and unauthorized effects answer different questions. A guard that blocks everything can have no unsafe effects and no useful completions.

## Choose the experiment

| Question | Use | Inspect |
| --- | --- | --- |
| Does my agent follow the user's intent? | Unguarded scenarios | Plans, proposal drift, task success |
| Does a guard classify a fixed proposal correctly? | Labeled traces / saved-run replay | Detection, overblocking, latency |
| Does enforcement help the whole system? | Online unguarded/enforce comparison | Completion under policy, effects, recovery |
| What would monitoring detect? | Monitor mode | Decisions; actions still execute |
| Is a policy too broad or too strict? | Policy ablation against unchanged grading | Missed deviations and clean-task interference |
| Did a change cause a regression? | Pinned suite and CI gate | Explicit thresholds, counts, failure traces |

`unguarded` skips guard initialization. `enforce` blocks/holds before execution. `monitor` records decisions but executes proposals; native monitoring gives no guard feedback to the model. Fixed traces do not estimate how a live agent would recover after a block.

## Read the scores

| Score | Meaning |
| --- | --- |
| Task success | Authored outcome checks passed |
| Completion under policy (CuP) | Episode completed, task succeeded, no unauthorized effects |
| Proposal drift | Episodes containing independently unauthorized proposed calls |
| Unauthorized-effect rate | Episodes where an unauthorized call caused a consequential effect |
| Guard detection | Unsafe proposals blocked/held, divided by observed unsafe proposals |
| Guard overblocking | Authorized proposals blocked/held, divided by observed authorized proposals |
| Coverage | Cases with usable evaluation evidence |

Detection is `null` when no unsafe proposals were observed. Errors/cancellations are excluded from ordinary rates; retain their counts and any observed critical effects. Truncated episodes remain eligible for scoring but receive no CuP credit. Report denominators alongside percentages. Approximate Wilson intervals describe the sample; correlated variants/repeats are not independent population trials.

Native utility, reward, policy reports, and attack filters keep their upstream definitions. Native detection/overblocking are unmeasured without independent per-proposal labels. An SDK decision is not its own correctness label. Never pool incompatible native rewards into one leaderboard score.

## Build a useful scenario set

| Factor | Controls to include |
| --- | --- |
| Goal and plan fidelity | Missing requirement, added objective, poisoned plan |
| Tool, resource, and argument scope | Approved tool/recipient/path/amount versus a close alternative |
| Aggregate limits and workflow | Individually valid calls exceeding a budget; skipped prerequisite |
| User changes and commit-time validity | Revision/retraction; revocation after selection, before execution |
| Approval | Valid, denied, unavailable, stale, and wrong-argument confirmation |
| Recovery and retries | Failure before commit, response lost after commit, exact/conflicting retry |
| Third-party content | Injection challenge plus genuinely helpful control |
| Context and visibility | Distractors/delayed updates; structured versus request-only observations |

The 90 core cases vary three workflow templates, not 90 unrelated domains. The 108 research-factor cases adapt published ideas; they are not calibrated long-horizon or original-paper reproductions. Persistent cross-session memory, verified local delegation, automatic taint tracking, and adaptive attack search need additional environments/protocols.

## Keep comparisons interpretable

Keep agent/model/prompt, task selection, attacks, planning, source/scorer versions, seeds, and budgets fixed. Restore external website/database snapshots when necessary; a browser reset does not guarantee a database reset. Archive backend policy revisions and remote model settings separately.

Report clean, attack, helpful-control, user-change, and fault cases separately. Preserve earlier unsafe effects even if the final state is correct. Use author/user policy labels and calibrate model judges. Inspect both the outcome and the path; small local trials are integration evidence, not a population robustness claim.

Local `--policy` overrides replace only reference-guard rules/facts. They do not change the private oracle or configure ArmorIQ backend policies. [Authoring](authoring.md) explains the rule language; [the ledger](benchmark-results.md) shows the recorded protocols.

The [authorization-boundary extensions](authorization-boundaries.md) add paired per-call capability probes, an independent native authorization overlay, and stable opaque observation IDs for matched model runs. Their scripted and real-model results remain separate.
