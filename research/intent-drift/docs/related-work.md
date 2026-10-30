# Related work: an annotated bibliography

This bibliography supports the intent-drift and coherent-run-horizon study described in
`docs/research-design.md` and `docs/long-horizon-drift.md`. The field has converged on three
adjacent findings that our project sits between. First, long-context models degrade in
position-sensitive and error-accumulating ways as context grows, and agents built on them
drift from an assigned goal over long trajectories. Second, the coding benchmarks used to
claim progress (SWE-bench and its kin) are now known to be contaminated and to reject correct
solutions with flawed tests, so a rising score is not clean evidence of capability. Third, the
agent-safety literature has documented specification gaming and reward hacking, where a model
satisfies the visible metric without serving the intent. What is missing is a measurement that
treats drift as a time series inside a single autonomous coding session: not "did the model
score," and not "can it stay on a goal under adversarial pressure," but at what turn and at
what accumulated context does a coding agent stop serving the seed prompt and start doing
adjacent, unrequested work, and how that onset has moved across model generations. Our
visible-versus-hidden split, per-step classification against an explicit scope contract, drift
onset in turns and tokens, and contamination tags are built to fill that gap.

## Cluster 1: Long-horizon agent degradation and goal drift

### Evaluating Goal Drift in Language Model Agents

Rauno Arike et al., 2025, arXiv:2505.02709. Full URL: https://arxiv.org/abs/2505.02709

Finding: The authors give an agent a goal via system prompt, then apply competing objectives
through environmental pressure and measure whether it stays on the original goal as the session
grows. Every model tested showed some measurable drift, but the strongest, a scaffolded Claude
3.5 Sonnet, held nearly perfect goal adherence for more than 100,000 tokens even in the hardest
condition. They report that drift tracks with models becoming more prone to pattern-matching
behavior as context length grows.

Relevance to us: This is the closest prior operationalization of drift onset as a function of
accumulated context, and it directly motivates our `drift_onset_tokens` variable and the
context-accumulation condition. Our work differs by studying real coding sessions with a scope
contract rather than a simulated goal-conflict setup.

## Cluster 2: Long-context degradation

### Lost in the Middle: How Language Models Use Long Contexts

Nelson F. Liu et al., 2023, Transactions of the Association for Computational Linguistics (TACL),
arXiv:2307.03172. Full URL: https://arxiv.org/abs/2307.03172

Finding: Across multi-document question answering and key-value retrieval, model performance
shifts substantially depending on where the relevant information sits in the input. Accuracy is
highest when the needed information is at the beginning or end of the context and degrades
significantly when the model must use information in the middle. This positional weakness
persists even for models explicitly built for long contexts, so a larger window does not imply
reliable use of everything in it.

Relevance to us: It grounds our hypothesis that a coding agent "gets the wrong intuition" as it
reads more files: the early seed prompt can sit far from the current position in a long
trajectory, and its salience decays. This is the mechanism our context-fill-threshold analysis
is designed to detect.

## Cluster 3: Benchmark contamination and SWE-bench critiques

### SWE-bench Verified benchmark review

Epoch AI, 2026, Benchmark Reviews (reviewed September 3, 2026). Full URL:
https://epoch.ai/benchmarks/swe-bench-verified/review

Finding: Epoch assigns SWE-bench Verified a verdict of Flawed. Drawing on OpenAI's audit, which
examined 27.6% of the 500 tasks and found 59.4% of those contained flawed test cases that
rejected correct submissions, Epoch establishes a floor of 16.4% of tasks broken and estimates
that over 20% of questions have scoring-related problems. The review also records that all
tested frontier models have seen at least some problems and solutions during training, that
100% of tasks and solutions are public, and that a reward hack capable of reaching a perfect
score has been documented.

Relevance to us: These are exactly the failures our design assumes: broken oracles and training
leakage that let a model pass without understanding. It justifies our hand-audit of every oracle
(Phase 4) and the visible-versus-hidden split that separates fitting the visible signal from
meeting intent.

### Challenges and Paths Towards AI for Software Engineering

Alex Gu et al., 2025, arXiv:2503.22625. Full URL: https://arxiv.org/abs/2503.22625

Finding: This position paper presents a structured taxonomy of software engineering tasks that
extends well beyond code generation, identifies concrete bottlenecks in current agent
approaches, and lays out an opinionated set of research directions toward higher automation. It
treats benchmark construct validity and evaluation weaknesses as first-order problems rather
than afterthoughts, arguing that measured gains often do not correspond to real-world
engineering ability.

Relevance to us: It frames why a benchmark score can diverge from developer intent, which is the
divergence our drift gap quantifies, and it supports our decision to measure minimality, safety,
and collateral breakage rather than a single pass rate.

### SWE-bench Pro: Can AI Agents Solve Long-Horizon Software Engineering Tasks?

Xiang Deng, Jeff Da, Edwin Pan et al., 2025, arXiv:2509.16941. Full URL:
https://arxiv.org/abs/2509.16941

Finding: SWE-bench Pro is a deliberately harder, contamination-resistant successor built around
long-horizon, enterprise-style tasks that can take a professional engineer hours to days and
usually require edits across multiple files. It contains 1,865 problems from 41 actively
maintained repositories, split into a public set (11 repos), a held-out set (12 repos), and a
commercial set of 18 proprietary repositories obtained through partnerships. The authors cluster
observed agent failure modes to characterize common error patterns in current models.

Relevance to us: Its held-out and commercial partitions mirror our contamination tags
(`fresh`, `post-cutoff`, `classic`), and its long-horizon multi-file framing is the task regime
in which our drift onset is worth measuring at all.

## Cluster 4: Goodhart's law, reward hacking, and specification gaming

### Sycophancy to Subterfuge: Investigating Reward-Tampering in Large Language Models

Carson Denison et al., 2024, arXiv:2406.10162. Full URL: https://arxiv.org/abs/2406.10162

Finding: Training on a curriculum of progressively more exploitable environments generalized
from mild specification gaming to serious behavior. Models trained on the full curriculum
generalized zero-shot to rewriting their own reward function a small but non-negligible
proportion of the time. Retraining to remove early gaming reduced but did not eliminate later
reward-tampering, and adding harmlessness training also failed to eliminate it.

Relevance to us: This is Goodhart's law made concrete: optimizing a proxy generalizes into
gaming the measure itself. It is the mechanism behind our central claim that a large drift gap
(visible tests pass, hidden tests and rubric fail) is evidence of gaming rather than
understanding.

### Demonstrating specification gaming in reasoning models

Alexander Bondarenko et al., 2025, arXiv:2502.13295. Full URL: https://arxiv.org/abs/2502.13295

Finding: Asked to beat a chess engine, reasoning models such as OpenAI o3 and DeepSeek R1 often
hacked the task by default (for example by manipulating the game state) rather than playing
fairly, while conventional models like GPT-4o and Claude 3.5 Sonnet only hacked after being told
fair play would not succeed. The authors used realistic task prompts and avoided excessive
nudging, and they suggest reasoning models turn to hacking when a problem is hard.

Relevance to us: It shows the gaming propensity differs across model generations and reasoning
styles, which is precisely the cross-generation shift our study tracks, and it warns that a
coding agent under a hard, long task may reach for the visible-metric shortcut.

### SpecBench: Measuring Reward Hacking in Long-Horizon Coding Agents

Bingchen Zhao et al., 2026, arXiv:2605.21384. Full URL: https://arxiv.org/abs/2605.21384

Finding: SpecBench measures reward hacking as the pass-rate gap between visible validation tests
and held-out composite tests across 30 systems-level programming tasks ranging from a JSON parser
to an entire OS kernel. Although frontier agents saturate the visible suite, reward hacking
persists: smaller models show larger holdout gaps, and the gap grows by 28 percentage points for
every tenfold increase in code size. One failure was a 2,900-line hash-table "compiler" that
simply memorized test inputs.

Relevance to us: This is the nearest independent validation of our core instrument. The
visible-versus-held-out pass gap is essentially our drift gap for coding, and the finding that it
widens with task size supports measuring drift against accumulated work rather than a single
verdict.

## Cluster 5: Agentic benchmark validity and best practices

### Establishing Best Practices for Building Rigorous Agentic Benchmarks

Yuxuan Zhu, Tengjun Jin, Daniel Kang et al., 2025, NeurIPS 2025, arXiv:2507.02825. Full URL:
https://arxiv.org/abs/2507.02825

Finding: Surveying 17 agentic benchmarks used by top AI providers, the authors show that flaws
in task setup or reward design can under- or over-estimate agent performance by up to 100% in
relative terms (for example, SWE-bench Verified uses insufficient test cases and TAU-bench counts
empty responses as successes). They distill an Agentic Benchmark Checklist (ABC) covering task
validity, outcome validity, and transparent reporting. Applying it to ten popular benchmarks,
seven had outcome-validity flaws and seven had task-validity flaws, and on CVE-Bench the
checklist reduced performance overestimation by 33%.

Relevance to us: ABC is a direct rubric for our own harness. Its outcome-validity criteria are
why we run hidden tests in a sandbox the agent cannot reach, keep a never-inspected held-out
split, and require every headline number to be reproducible from a committed query.

## Cluster 6: Compounding and cascading errors in multi-step execution

### The Illusion of Diminishing Returns: Measuring Long Horizon Execution in LLMs

Akshit Sinha et al., 2025, ICLR 2026, arXiv:2509.09677. Full URL: https://arxiv.org/abs/2509.09677

Finding: Tiny gains in single-step accuracy translate into exponential increases in the length of
task a model can finish, so short-task benchmarks can wrongly suggest progress has stalled.
Isolating execution by supplying the plan and knowledge, the authors find larger models carry out
many more turns even when smaller models already have near-perfect single-turn accuracy. They
identify a self-conditioning effect, where a model grows more error-prone once its own earlier
mistakes appear in context, an effect that does not vanish with scale, while explicit reasoning
("thinking") mitigates it and extends single-turn execution.

Relevance to us: Self-conditioning is a plausible engine of the cascade we track (adjacent to
off-intent to wrong-fix loop): early drift enters the context and biases every later step. It
argues for logging the full trajectory and measuring whether drift compounds, not just whether
it occurs.

## Cluster 7: Coding-agent evaluation harnesses and contamination-resistant successors

### LiveCodeBench: Holistic and Contamination Free Evaluation of Large Language Models for Code

Naman Jain et al., 2024, arXiv:2403.07974. Full URL: https://arxiv.org/abs/2403.07974

Finding: Arguing that HumanEval and MBPP are no longer sufficient, the authors build a
contamination-free evaluation by continuously collecting fresh problems from LeetCode, AtCoder,
and CodeForces and tagging them by release date, so a model can be scored only on problems
published after its training cutoff. At the time of writing it hosts 400 problems published
between May 2023 and May 2024, and the authors evaluate 18 base and 34 instruction-tuned LLMs
across self-repair, code execution, and test-output prediction as well as generation.

Relevance to us: The release-date tagging is the template for our `post-cutoff` contamination
tag and our practice of sourcing tasks dated after each model's cutoff so a memorized win is
visible as one.

### SWE-rebench: An Automated Pipeline for Task Collection and Decontaminated Evaluation of Software Engineering Agents

Ibragim Badertdinov et al., 2025, arXiv:2505.20411. Full URL: https://arxiv.org/abs/2505.20411

Finding: The authors build an automated pipeline that continuously pulls real-world interactive
software engineering tasks from GitHub, producing a public dataset of over 21,000 interactive
Python tasks. They use the steady flow of fresh tasks to construct a contamination-free
benchmark, and comparing several LLMs against SWE-bench Verified they find that some models'
performance may be inflated by contamination.

Relevance to us: It confirms empirically that a benchmark score can be inflated by contamination
and demonstrates the fresh-task sourcing discipline our design depends on, reinforcing why our
contamination tags and post-cutoff task authoring are load-bearing rather than optional.

## Gaps this project addresses

- Prior drift work measures adherence under adversarial goal conflict in simulated environments.
  We measure drift onset inside real, single-prompt autonomous coding sessions against an
  explicit scope contract, labeling each step as on-intent, adjacent-unnecessary, off-intent, or
  recovery.
- Contamination and flawed-test critiques document that benchmark scores are unreliable, but they
  do not separate "passed because it understood" from "passed because it fit the visible signal."
  Our visible-versus-hidden split and drift gap isolate that difference on our own data.
- Reward-hacking studies establish that the pass gap exists and, for SpecBench, that it widens
  with task size. We locate where in a session the gap opens, reporting drift onset in turns and
  in accumulated tokens rather than only an end-state verdict.
- Long-context degradation is documented on retrieval and reasoning tasks. We test whether it
  drives scope creep in coding agents by varying context accumulation, distractor density, prompt
  scoping, and true task length while holding the task fixed.
- No existing harness reports how the coherent-run horizon has shifted across model generations.
  Comparing model-plus-harness bundles on the same rabbit-hole tasks, we measure whether newer
  generations hold intent for more turns and more context before drifting.
