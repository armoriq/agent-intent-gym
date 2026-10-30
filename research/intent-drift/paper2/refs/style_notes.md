# Style notes for the intent-drift benchmark paper

Sources: six papers, read from the arXiv PDF (pdftotext plus rendered pages) and the arXiv HTML
(LaTeXML markup for caption order, rules, italics, bold). Page numbers are PDF pages of the arXiv
version, which can differ from camera-ready. SWE-bench+ (2410.06992) was checked first for the SE
slot but its PDF is a NeurIPS-style "Preprint. Under review." with no SE venue, so CoderEval
(ICSE 2024, ACM sigconf, venue confirmed on arXiv and in the PDF footer) replaces it.

## Recommended conventions for our paper

1. Template: ICLR or NeurIPS style. 4 of 6 papers use one (SWE-bench ICLR; EvalPlus, SWE-agent
   NeurIPS; LiveCodeBench's arXiv copy is NeurIPS-like). Use ACM sigconf only if we target ICSE/FSE.
2. Citations: natbib author-year with `\citet` for subjects and `\citep` for parentheticals.
   ICLR papers and ImpossibleBench use author-year; NeurIPS papers split (EvalPlus and SWE-agent
   use numeric). Author-year works at both venues. Avoid LiveCodeBench's slip of using a
   parenthetical cite as a subject ("(Liu et al., 2023a) identified ...").
3. Abstract: one paragraph, 170 to 220 words. Observed: 171, 173, 191, 211 (ML venues) versus
   283 to 291 (EvalPlus, CoderEval). The shorter ones read better.
4. Abstract shape: problem (1 to 2 sentences), what we build, how it works in one sentence, one
   concrete headline number, one sentence of implication. SWE-bench ("a mere 1.96%") and SWE-agent
   ("12.5% and 87.7%") give one sharp number; LiveCodeBench and ImpossibleBench give none and are
   vaguer for it. Include our number.
5. Define the measured quantity in the abstract the way ImpossibleBench does ("We measure an
   agent's 'cheating rate' as its pass rate on these impossible tasks"). Ours: one sentence that
   says what counts as intent drift and how it is scored.
6. Teaser figure on page 1 or top of page 2 that shows one concrete task: visible tests pass,
   intent is violated. 5 of 6 papers do this (SWE-bench, SWE-agent p1; EvalPlus, LiveCodeBench,
   ImpossibleBench p2). ImpossibleBench's Fig. 1 (task, mutated test, per-model bar) is the
   closest model for us.
7. Contributions: end the intro with 3 bullets, bold lead-in, each naming a section and carrying
   a number. EvalPlus (3, "Study/Approach/Results") and ImpossibleBench (3, with "(Section 4)")
   do this. SWE-bench and SWE-agent use prose ("Our contributions are twofold"); bullets are easier
   for reviewers to scan.
8. Section order: Introduction, Benchmark (construction, task, metric), Experimental Setup,
   Results (split by question), Related Work, Limitations, Conclusion, then Ethics and
   Reproducibility statements before references. Related work goes late in 4 of 6 papers
   (§4 to §6); ImpossibleBench pushes it to Appendix A, CoderEval puts Background at §2. Late
   is the ML norm.
9. Results subsection or paragraph titles state the finding, not the topic. SWE-bench
   ("Difficulty correlates with context length.") and SWE-agent ("Compact, efficient file
   editing is critical to performance.") use bold run-in headings that are full claims.
10. Tables: caption above, booktabs (`\toprule/\midrule/\bottomrule`, no vertical rules), bold
    for best value per column. Main-body tables in SWE-bench, SWE-agent, EvalPlus, CoderEval are
    captioned above. LiveCodeBench and ImpossibleBench put captions below; ACM requires above;
    above is the majority, so use it.
11. Figures: caption below in every paper. Captions are 1 to 3 sentences: what is plotted, then
    the takeaway (SWE-bench, ImpossibleBench median about 20 to 40 words). Skip LiveCodeBench's
    100+ word captions.
12. Color: limited categorical palette, one fixed color per model across all figures, no more
    than about 6 series per panel. SWE-bench (3 bar colors) and SWE-agent (one blue line) are
    calm; LiveCodeBench's Fig. 5 needs a 30-entry marker legend. Keep it legible in grayscale by
    pairing color with marker shape or hatching.
13. Defined terms: italicize on first use, then plain. SWE-bench (*fail-to-pass*, *issues*) and
    SWE-agent (*agent-computer interface*) do this. Use *intent drift* once, italic, with the
    definition in the same sentence. ImpossibleBench uses quotes ("cheating rate"); do not mix
    quotes and italics.
14. Benchmark and split names: one fixed typographic form via a macro. EvalPlus, LiveCodeBench,
    ImpossibleBench set names in small caps (HumanEval+, Impossible-SWEbench). Small caps or plain
    is fine; pick one and use `\newcommand`.
15. Numbers: percentages with one decimal in text, matching table precision (tables in SWE-bench
    and SWE-agent use two decimals, which overstates precision for n of a few hundred). State
    deltas as "percentage points" (SWE-agent: "10.7 percentage points"). Use "x" ratios only
    for size changes (EvalPlus "80x").
16. Uncertainty: report 95% bootstrap CIs or standard error over seeds. Only ImpossibleBench
    shows CIs (90% CI bars); SWE-agent reports run-to-run spread in an appendix table; SWE-bench,
    EvalPlus, LiveCodeBench, CoderEval report point estimates. This is a gap we should not copy.
17. Limitations: its own numbered section in the main body, with bold run-in paragraph titles
    per limitation (LiveCodeBench §7 "Problem Domain."). SWE-bench folds it into Discussion,
    SWE-agent hides it in Appendix E.3, EvalPlus and ImpossibleBench have none. Add Ethics and
    Reproducibility statements (SWE-bench §8 and §9 is the pattern ICLR expects).
18. Length: about 9 to 10 main pages, appendix unlimited. Observed main bodies: SWE-agent 9,
    SWE-bench and EvalPlus and ImpossibleBench about 10; appendices run 1 to 103 pages. Move
    per-repo tables, prompts, and transcripts to the appendix as SWE-bench and SWE-agent do.
19. If we target ICSE/FSE instead: ACM sigconf two-column, numeric citations, CCS Concepts and
    Keywords, results organized as RQ1 to RQ3 with the question as the subsection title, and
    "Threats to Validity" instead of "Limitations" (CoderEval).

## Per-paper notes

### SWE-bench (arXiv 2310.06770, ICLR 2024)
- Template: ICLR 2024, small-caps headings. 52 pp: main pp1 to 10, statements p11, refs pp12 to 15, appendix pp16 to 52 (A to F).
- Abstract: 191 words. Headline: "The best-performing model, Claude 2, is able to solve a mere 1.96% of the issues."
- Sections: 1 Introduction, 2 SWE-bench, 3 SWE-Llama: Fine-tuning CodeLlama for SWE-bench, 4 Experimental Setup, 5 Results, 6 Related Work, 7 Discussion, 8 Ethics Statement, 9 Reproducibility Statement, 10 Acknowledgements.
- Contributions: prose paragraph at end of intro, no bullets.
- Teaser: Fig. 1 on p1, full-color pipeline diagram (issue, codebase, LM, tests).
- Tables: main-body captions above ("Table 5: We compare models ..."), booktabs (thick top and bottom, thin mid), bold best values. Some appendix tables have vertical rules and captions below.
- Figures: captions below, 12 to 47 words. Bar chart uses 3 colors.
- Emphasis: italics for defined terms (*issues*, *pull requests*, *fail-to-pass*); bold run-in headings ("Difficulty differs across repositories.").
- Citations: natbib author-year "(Chen et al., 2021)".
- Numbers: two-decimal percentages ("1.96%", "% Resolved" columns); no CIs.
- Related work: §6, late. Limitations: paragraph "Limitations and future directions." inside §7; separate Ethics and Reproducibility statements; Societal Impact in Appendix E.

### EvalPlus (arXiv 2305.01210, NeurIPS 2023)
- Template: NeurIPS 2023. 15 pp: main pp1 to 10, refs pp11 to 14, appendix p15 only.
- Abstract: 291 words. Headline: "reducing the pass@k by up-to 19.3-28.9%"; also a mis-ranking claim.
- Sections: 1 Introduction, 2 Approach, 3 Evaluation, 4 Related Work, 5 Conclusion & Future Work, 6 Acknowledgements.
- Contributions: bold "Contribution." paragraph, then 3 bullets with bold lead-ins "Study:", "Approach:", "Results:".
- Teaser: Fig. 1 top of p2, wrong ChatGPT code with red/green highlights.
- Tables: captions above; Table 3 has vertical rules and red heat-shaded cells.
- Figures: captions below, short (5 to 29 words).
- Emphasis: italics for research questions ("*Is the code generated by LLMs really correct?*") and stress words; small caps for HUMANEVAL; sans-serif for the tool name.
- Citations: numeric "[11]".
- Numbers: one decimal, ranges, ratios ("80x", "47x"); no CIs.
- Related work: §4, late. Limitations / broader impact: none.

### LiveCodeBench (arXiv 2403.07974 v2, ICLR 2025)
- Template: arXiv v2 is a NeurIPS-like preprint (no venue footer); the ICLR camera-ready was not inspected. 46 pp: main pp1 to 17, refs pp18 to 25 (with "Cited on pg." backrefs), appendix pp26 to 46.
- Abstract: 173 words. No headline number; claims are qualitative ("empirical findings on contamination ...").
- Sections: 1 Introduction, 2 Holistic Evaluation, 3 Benchmark Curation, 4 Experiment Setup, 5 Results, 6 Related Work, 7 Limitations, 8 Conclusion.
- Contributions: no contributions list; numbered design principles and numbered "Empirical Findings", each with a bold lead-in; a "Concurrent Work." paragraph closes the intro.
- Teaser: Fig. 1 on p2, full-color line plots over release months.
- Tables: Table 1 caption below, horizontal rules plus dashed group separators.
- Figures: captions below, often very long (Fig. 1 109 words, Fig. 5 133 words).
- Color: full color, many series; scatter legend with about 30 model markers.
- Emphasis: small caps for model and platform names; italics for stress (*new*, *release date*).
- Citations: author-year, sometimes misused as subject.
- Numbers: Pass@1, relative gains ("96% and 134%", "19.5x"); bootstrapping mentioned once.
- Related work: §6, late. Limitations: §7 with bold run-in paragraphs ("Problem Domain.").

### SWE-agent (arXiv 2405.15793, NeurIPS 2024)
- Template: NeurIPS 2024. 118 pp: main pp1 to 9, refs pp10 to 15, appendix pp16 to 118 (A to E).
- Abstract: 171 words. Headline: "achieving state-of-the-art performance on both with a pass@1 rate of 12.5% and 87.7%, respectively".
- Sections: 1 Introduction, 2 The Agent-Computer Interface, 3 SWE-agent: Designing an ACI for Software Engineering, 4 Experimental Setup, 5 Results, 6 Related Work, 7 Discussion, Acknowledgements.
- Contributions: prose, "Our contributions are twofold. First, ... Second, ...".
- Teaser: Fig. 1 on p1, pastel system diagram.
- Tables: captions above, booktabs, bold best ("12.47", "18.00"); ablation table uses small red subscript deltas.
- Figures: captions below, 6 to 63 words; single-color line plot.
- Emphasis: italic on first use of the coined term (*agent-computer interface*); bold claim-style run-in headings.
- Citations: numeric "[20]".
- Numbers: two decimals in tables, one in prose; "10.7 percentage points"; 6-run spread in appendix Table 10.
- Related work: §6, late. Limitations, Ethics & Broader Impacts, Reproducibility: Appendix E only.

### ImpossibleBench (arXiv 2510.20270, 2025 preprint)
- Template: custom "Preprint. Under review." style. 25 pp: main pp1 to 10, refs pp11 to 12, appendix pp13 to 25.
- Abstract: 211 words. No number; defines the metric ("cheating rate ... where any pass necessarily implies a specification-violating shortcut") and lists 3 uses as (1), (2), (3).
- Sections: 1 Introduction, 2 Benchmark Curation, 3 Experiment Setup, 4 Results: Model Behaviors, 5 Results: Context Engineering, 6 Results: Monitoring, 7 Conclusion, Acknowledgments, LLM Contribution Statement.
- Contributions: 3 bullets, bold lead-in plus section pointer ("Studying Model Behaviors (Section 4):"), each with a number ("GPT-5 cheats in 76% of the tasks").
- Teaser: Fig. 1 top of p2, full color: normal vs impossible test plus per-model bar chart.
- Tables: Table 1 caption below, booktabs, purple highlights in cells.
- Figures: captions below, 11 to 45 words; caption labels printed in red.
- Color: full categorical palette, one color per model, error bars.
- Emphasis: quotes for coined terms ("impossible", "cheating rate"); small caps for variant names; italics for scaffold names (*Minimal*, *Full*).
- Citations: author-year "(Jimenez et al., 2024)".
- Numbers: integer or one-decimal percents ("76%", "2.9%", "92% to 1%"); 90% confidence intervals on plots.
- Related work: Appendix A. Limitations: none; has an "LLM Contribution Statement".

### CoderEval (arXiv 2302.00288, ICSE 2024), SE-venue contrast
- Template: ACM sigconf two-column, CCS Concepts, Keywords, ACM Reference Format block, uppercase headings ("1 INTRODUCTION"). 12 pp including refs, no appendix.
- Abstract: about 283 words, two paragraphs. Headline is qualitative: "substantially higher than that in generating non-standalone functions."
- Sections: 1 Introduction, 2 Background, 3 CoderEval Benchmark, 4 Experimental Setup (4.1 Research Questions), 5 Experimental Results (5.1 RQ1: ..., 5.2 RQ2: ..., 5.3 RQ3: ..., titles are full questions), 6 Related Work, 7 Threats to Validity, 8 Conclusion.
- Contributions: "In summary, we make the following main contributions:" then 3 plain bullets, no bold.
- Teaser: none; first figure (construction pipeline) on p4.
- Tables: captions above in bold (ACM), several with vertical rules; percents to two decimals.
- Figures: captions below; pastel Venn diagrams.
- Emphasis: italics for defined categories (*standalone*, *self-contained*, *class-runnable*); bold "RQ1:" labels.
- Citations: numeric "[7]".
- Numbers: two-decimal percents; mentions standard deviation over 10 runs.
- Related work: Background §2 early plus Related Work §6. Limitations: §7 Threats to Validity.
