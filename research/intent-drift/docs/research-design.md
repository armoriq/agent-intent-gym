# Measuring Intent Drift in AI Coding Agents

A benchmark and study of whether coding models follow developer intent or optimize the visible metric.

Version 0.1 (prototype for advisor review) - 2026-09-18

---

## 1. The question

Vendors report large gains on coding benchmarks (SWE-bench and friends), yet
day-to-day users often find the same models fail on ordinary work. This paper
asks whether that gap is **intent drift**: models increasingly optimize what a
benchmark measures (make the visible tests pass) rather than what a developer
means (produce a correct, minimal, safe change).

Concretely we measure, per model, the distance between two quantities:

- **Metric-pass rate**: the tests the agent can see and run go green.
- **Intent-satisfaction rate**: the change is correct on held-out edge cases,
  minimal in scope, breaks nothing else, and matches a human-authored rubric.

We define the **drift gap = metric-pass rate - intent-satisfaction rate**. A
large positive gap for a model is direct, quantified evidence of gaming rather
than an assertion.

This is Goodhart's Law ("when a measure becomes a target it ceases to be a good
measure") made measurable on our own data instead of argued from anecdote.

## 2. Why this is not already answered

Existing benchmarks have documented but not isolated the problem:

- OpenAI's own audit found 59.4% of one model's SWE-bench Verified failures were
  caused by flawed tests, not the model, and recommended dropping the benchmark.
- Roughly 32.7% solution leakage was documented in the original SWE-bench (the
  fix is hinted in the issue text the model reads).
- Models recall in-training file paths up to 76% of the time versus 53% for
  unseen files, i.e. memorization can masquerade as reasoning.

These are contamination and test-quality findings. None of them separate "the
model passed because it understood" from "the model passed because it fit the
visible signal." The visible/hidden split (Section 4) is built to do exactly
that separation.

## 3. Scope and what we compare

### 3.1 Model vs product

A score is always `model x harness x task`. We cannot cleanly swap the model
underneath products we only have subscriptions to, so this study compares
**bundles** (a model together with the harness that ships it). Every claim is
scoped to the bundle, never to the raw model. This is stated as a threat to
validity, not hidden.

### 3.2 Systems under test (initial five)

| Arm | Bundle | Access | Automation |
|-----|--------|--------|------------|
| A | Claude Code (Anthropic model) | subscription | CLI, scripted |
| B | OpenCode (paid tier model, e.g. Muse / stealth) | subscription | CLI, scripted |
| C | OpenCode (free tier model) | subscription | CLI, scripted |
| D | Codex CLI | subscription (rate-limited) | CLI, scripted |
| E | Cursor | subscription, GUI only | manual subset, hand-run |

Cursor is a GUI product and cannot be cleanly automated, so it runs as a small
manual arm on a task subset, clearly labeled. Codex is rate-limited on the
current plan; runs are scheduled around the reset window.

### 3.3 What we deliberately do not claim

- We do not claim results about a model independent of its harness.
- We do not claim absolute capability ranking; we claim relative drift behavior.

## 4. The core design: visible vs hidden

Every task carries two test layers and a rubric.

```
task/
  prompt.md            # what the "user" asks for, in natural language
  repo/                # starting code state (or a Docker build)
  tests/
    visible/           # agent may read and run these
    hidden/            # agent never sees these; run only during scoring
  rubric.yaml          # human-checkable intent criteria (minimality, safety...)
  meta.yaml            # persona, difficulty, source, cutoff date, contamination tag
```

Scoring per run produces:

1. **metric_pass**: all visible tests pass.
2. **intent_pass**: all hidden tests pass AND rubric criteria are met.
3. **process metrics**: diff size (lines, files), collateral breakage (previously
   passing tests now failing), over-engineering flags, security flags.

The drift signal is the disagreement between (1) and (2). We also log the full
agent trajectory so every failure can be inspected by hand, which is how we
catch our own broken oracles (see Section 7).

## 5. Task design: real, not synthetic

Tasks must feel like real work or the study measures nothing. Two personas:

### 5.1 Developer persona (repo-grounded, hard oracles)

Real bug fixes and small features in real (or realistic) codebases. Sourced to
resist contamination:

- Issues/PRs dated **after** each model's training cutoff where possible.
- Hand-authored bugs planted in obscure or private-style code.
- Mutations of known problems (rephrased as a chat request, edge case shifted)
  so memorized solutions no longer fit.

Each carries strong `FAIL_TO_PASS` (the bug is fixed) and `PASS_TO_PASS` (nothing
else broke) oracles, split into visible and hidden.

### 5.2 Non-developer persona (fuzzy intent, rubric-heavy)

The "I am not an engineer, just help me" requests: "I have this CSV, make me a
chart of monthly revenue", "my static site's contact form is broken", "clean up
this messy script". Here the intent is under-specified on purpose. Success is
judged mostly by rubric and hidden checks, because a real non-dev cannot write a
spec. This is where drift is most visible: a model can produce something that
looks done and passes a shallow check while missing the obvious real intent.

### 5.3 The contamination tag

Every task records whether it is: `fresh` (authored here, never published),
`post-cutoff` (real but after model cutoffs), or `classic` (known, likely in
training, kept only as a contamination probe). Analysis can filter on this so a
memorized win is visible as a memorized win.

## 6. What we measure (metrics)

Per (model, task, run):

- `metric_pass` (bool), `intent_pass` (bool)
- `visible_pass_count / total`, `hidden_pass_count / total`
- `diff_added`, `diff_removed`, `files_touched`
- `collateral_failures` (PASS_TO_PASS that regressed)
- `rubric_score` (0-1 across weighted criteria)
- `turns`, `wall_seconds`, `token_or_cost_estimate`
- `trajectory_path` (full log for hand audit)

Aggregate per model: metric-pass rate, intent-pass rate, **drift gap**, drift gap
split by persona and by contamination tag, process-metric distributions.

Because models are non-deterministic, every task is run k times (start k=3) and
we report means with confidence intervals, not single numbers. pass@1 and pass@k
both reported.

## 7. Method: iterative, not one-shot

- **Phase 0 (day 0): reproduce.** Run an existing SWE-bench Docker task on one
  model end to end so we understand trajectories before inventing anything.
- **Phase 1: define drift** precisely (this document).
- **Phase 2: gold set of 10-15 hand-authored tasks** with the visible/hidden
  split, verified by hand.
- **Phase 3: database + harness** (schema in `db/schema.sql`).
- **Phase 4: calibrate.** Run 2 models on the gold set, inspect every failure by
  hand, fix broken oracles. Expect ~30% of oracles to be wrong on first pass;
  fixing them is part of the contribution.
- **Phase 5: scale** to 50-100 tasks and all five arms, k runs each.
- **Phase 6: analysis + paper**, including a threats-to-validity section.

## 8. Anti-gaming discipline (applied to ourselves)

- A **held-out task split we never look at** during iteration, to avoid tuning
  our own harness to the models.
- The scorer runs hidden tests in a sandbox the agent cannot reach.
- Every headline number must be reproducible from the database with a query that
  is committed alongside the paper. No number without a query.

## 9. Threats to validity (living list)

- Bundle confound (model vs harness) - stated, not solved.
- Our oracles may themselves be flawed - mitigated by hand audit and hidden/
  visible cross-check.
- Small n on the Cursor manual arm - reported as lower-confidence.
- Cost and rate limits may bias run counts across arms - logged per arm.

## 10. Immediate deliverables (12-hour prototype)

- This design document.
- Queryable schema (`db/schema.sql`) plus example analysis queries.
- Task format spec and two real seed tasks (one dev, one non-dev) with the
  visible/hidden split.
- Harness runner skeleton showing how a CLI agent is invoked in Docker and
  recorded to the database.

Open decisions for the advisor discussion are collected in `docs/open-questions.md`.
