# Author responses to review round 1

Snapshot now frozen: paper2/data/results_snapshot.db (655 runs, max id 655, 2026-10-16 11:43 IST). Build: `paper2/build.sh`.

1. Hidden tests readable (critical). Escape audit added (analysis/out/escape_runs.csv, run_evidence.csv); 21 escaped valid runs excluded from the primary analysis (NoEsc). "Never sees" wording removed (abstract, intro, method). Limitation "Agents were not sandboxed" added. Harness changed for runs >= 653 to use a temp dir outside the tree (ISOLATED marker); those runs are only Gemini/Codex and mostly after the snapshot.
2. Test edits (critical). Broader "any out-of-scope edit" measure added (planted, other non-target functions, test edits, new files); Table 3 reports planted, any-OOS, and test edits by rung; abstract/intro/results/conclusion now say vague prompts produced no planted edits but some other out-of-scope edits, mostly test files. related.tex "do not touch the tests" removed.
3. Stale PDF. Fixed via frozen snapshot; single build script.
4. "Exactly one arm" now "among arms with complete loose-rung coverage"; Gemini 3.8 flagged as incomplete/escaped in table caption.
5. Tool calls now unique call ids, Cursor-only pooled contrast; Claude Code separate.
6. Exposure now measured from file reads in trajectories (observed_exposure.csv): vague runs opened non-target rabbit-hole files in most runs, zero planted edits among them.
7. Verification text now: 17 base repositories pass; variants byte-identical.
8. Test-command confound disclosed in method and limitations with macro counts.
9. Codex id difference stated; non-significance no longer read as stability.
10. Now \NConfigsDistinct (13) distinct configurations; \NArms explained as arm-generation pairs in setup.
11. Invalid-run rule stated exactly in setup and appendix caption.
12. Calibration numbers kept but labeled as a dated design-time description from private history, not reproducible; vague median words reported from the actual prompts (macro).
13. "intent-pass" renamed hidden-pass in method/results; "harmed" sentence rewritten.
14. Goodhart "predicts exactly" removed; negative side effects named as the closer analogy.
15. Duplicate label fixed (tab:armlist vs tab:arms).
16. Coverage table replaced by a compact 7-column table; appendix float placement fixed.
17. Wilson intervals labeled descriptive with the dependence caveat.
18. "same system prompt" claim removed; limited to same client and flags.
19. Flagged sentences rewritten (results opener, discussion parallelism, practical advice, method filler).
20. "a line or two" changed to "a small edit to that function".

Literature: added weinberger2026promptinduced (prior evidence for the cleanup effect), ji2026coding (UnderSpecBench, counter-result on vagueness in DevOps), gloaguen2026coding (FixedBench); closest-prior-work paragraph and intro now credit them. Six citation precision fixes from the literature thread applied.
