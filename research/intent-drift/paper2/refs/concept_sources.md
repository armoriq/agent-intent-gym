# Which idea came from which paper

No sentence in our paper is copied from another paper; every sentence is our own wording. The ideas below are borrowed or built on, and each is cited where it is used. Papers do not have line numbers, so the location is given as section, table, or figure of the version we read (arXiv version unless noted). Full notes for all 52 references are in notes.md.

| Our concept | Where it comes from | Location in that paper | Where we use it |
|---|---|---|---|
| Passing the metric without doing what was meant (specification gaming) | Krakovna et al. 2020, "Specification gaming: the flip side of AI ingenuity" (DeepMind blog) | Opening paragraph (definition) | Introduction, Related work |
| Out-of-scope edits as side effects the objective ignores | Amodei et al. 2016, "Concrete Problems in AI Safety" | Sec. 3 (Avoiding Negative Side Effects), Sec. 4 (Reward Hacking) | Related work |
| A proxy measure stops tracking the goal under optimization (Goodhart) | Manheim and Garrabrant 2018, "Categorizing Variants of Goodhart's Law" | Sec. 2 (Extremal Goodhart), Sec. 3 (Causal, metric manipulation) | Introduction, Related work |
| Hidden tests catch code that passes the visible tests | Liu et al. 2023, EvalPlus (NeurIPS 2023) | Sec. 3 and Table 3 | Introduction, Related work |
| Visible vs. held-out tests on coding agents | Gabor et al. 2026, EvilGenie | Sec. 2 and Sec. 4.1 | Related work |
| Visible vs. held-out test gap as a measure | Zhao et al. 2026, SpecBench | Sec. 2 (Eq. 1), Table 2 | Related work |
| Visible pass but hidden fail on real bug fixes | Ahmed et al. 2026, "Investigating Test Overfitting on SWE-bench" | Sec. 4.1, Table 1 | Related work |
| Bug-fix tasks graded by tests (fail-to-pass, pass-to-pass) | Jimenez et al. 2024, SWE-bench (ICLR 2024) | Sec. 2.1 and 2.3 | Introduction, Related work |
| Planted traps to measure out-of-scope actions | Qu et al. 2026, "Overeager Coding Agents" (OverEager-Bench) | Sec. 3, Table 1; Sec. 5.2, Table 2 | Related work, Discussion |
| Looser prompts raise test cheating | Zhong et al. 2025, ImpossibleBench | Sec. 5.1, Table 1 | Introduction, Related work |
| Same task with full vs. underspecified wording | Vijayvargiya et al. 2026, Ambig-SWE (ICLR 2026) | Sec. 2.1, 2.3, 3.2 | Related work |
| Cleanup wording causes out-of-scope edits (closest prior result) | Weinberger and Hozez 2026, "Prompt-Induced Waste in Coding Agents" | Sec. 3; Appendix E.1; Table 4 for the clause | Introduction, Related work, Discussion |
| Vague instructions make agents overstep (opposite direction to ours) | Ji et al. 2026, UnderSpecBench | Sec. IV (Def. 1), Sec. V-C, Fig. 6 | Related work, Discussion |
| Action-inviting wording causes unneeded edits | Gloaguen et al. 2026, FixedBench | Sec. 3.1 to 3.3, Table 1 | Related work |
| Real developers see agents overreach scope | Tang et al. 2026, "How Coding Agents Fail Their Users" | Sec. 4.1 | Related work |

## What is ours

The combination is new: the same solvable bug posed three ways (scoped, loose, vague), four planted out-of-scope functions in every repository, and hidden tests, all on one set of tasks. The tasks, prompts, harness, runs, and every number in the paper are our own. The main new findings are that vague wording produced no planted-function edits while loose cleanup wording did, and that 99 of 100 drifted runs still passed every hidden test.
