# Writing tasks that measure drift (not synthetic filler)

A task is good only if a lazy or over-eager solution can pass the visible signal
while missing the real intent. If the obvious fix passes everything, the task is
a control, not a drift probe. Label it as such.

## The recipe

1. **Start from a real situation.** A real bug report, a real "help me" request,
   a real feature ask. Rewrite it in the requester's own voice in `prompt.md`.
   Non-developer prompts must not contain a spec; that under-specification is
   the point.
2. **Encode the obvious spec in visible tests.** These must FAIL on the starting
   code so the agent has a clear thing to fix. If they already pass, the agent
   sees green and stops.
3. **Encode the fuller intent in hidden tests + rubric.** Target the edge the
   visible tests do not show: the boundary case, the messy input, the thing a
   careless "improvement" would break. This is where the drift gap appears.
4. **Predict the plausible wrong fix** and confirm it passes visible but fails
   hidden. Record it in `meta.yaml: drift_probe`. If you cannot name a wrong fix
   that slips through, the task is not probing drift.
5. **Tag contamination** honestly: fresh / post_cutoff / classic.
6. **Verify all three states by hand**: buggy (visible fails), minimal correct
   (all pass), plausible-wrong (visible passes, hidden fails). T001 is the
   worked example; its three states are verified in the prototype.

## Files per task

```
prompt.md      the request, in the requester's voice
repo/          starting code (fails visible tests)
tests/visible/ oracle the agent may read and run
tests/hidden/  oracle it never sees (pytest, or a check.py validator)
rubric.yaml    intent criteria a test cannot capture (minimality, safety, order)
meta.yaml      persona, difficulty, tags, oracle lists, the drift_probe note
```

## Anti-patterns

- Puzzle problems (LeetCode-style) - memorized and unlike real work.
- Visible tests that already pass - nothing to fix.
- Hidden tests that only re-check the visible behavior - no drift signal.
- Prompts that leak the fix (a "solution leakage" repeat of SWE-bench's flaw).
