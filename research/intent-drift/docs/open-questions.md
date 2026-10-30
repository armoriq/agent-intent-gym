# Open questions for the advisor discussion

Decisions that shape the build. My current lean is noted; none are locked.

## 1. Agent access and automation
Cursor is GUI-only and cannot be scripted. Codex is rate-limited on the current
plan. Do we accept a mixed harness (CLI arms automated, Cursor as a hand-run
subset), or narrow the study to CLI-drivable agents only?
Lean: mixed harness, Cursor clearly labeled as low-n manual.

## 2. Framing scope
We compare bundles (model + its harness), not raw models, because we lack API
parity. Is bundle-level drift an acceptable claim for the target venue, or do we
need at least one arm where we hold the harness fixed and swap the model?
Lean: bundle-level for v1; add one held-harness arm if a venue needs it.

## 3. Task sourcing mix
Three tags: fresh (authored here), post_cutoff (real, after cutoffs), classic
(likely trained on, kept as contamination probes). What target ratio? More fresh
is stronger but slower to author.
Lean: 60% fresh, 25% post_cutoff, 15% classic.

## 4. Rubric judging
Fuzzy non-dev criteria need a judge. Human-only (slow, trustworthy) vs
LLM-judge (fast, biased) vs both with human audit on disagreements?
Lean: LLM-judge with human audit on all disagreements and on every
metric_pass=1/intent_pass=0 case.

## 5. Scale and statistics
How many tasks and how many runs per pair for v1? Non-determinism needs k>=3.
Lean: 15 tasks x 5 arms x 3 runs for the calibrated prototype; grow to
60-100 tasks for the publishable version.

## 6. Cost ceiling
Complete budget was offered, but runs multiply fast (tasks x arms x k x retries).
Set a per-phase cap and log cost per arm so rate-limited arms are not undercounted.
Lean: set a phase cap at the next meeting once task count is fixed.
