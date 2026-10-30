#!/usr/bin/env python3
"""Write sections/appendix_prompts.tex: the verbatim prompt.md of every ladder task."""
import os
import textwrap
import yaml

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
OUT = os.path.join(ROOT, "paper2", "sections", "appendix_prompts.tex")
RUNGS = ("Scoped", "Loose", "Vague")


def wrapped(text):
    out = []
    for line in text.rstrip().splitlines():
        out.extend(textwrap.wrap(line, 58, break_on_hyphens=False) or [""])
    return "\n".join(out)


reg = yaml.safe_load(open(os.path.join(ROOT, "suites", "registry.yaml")))
lines = []
for bench in reg["domain_benchmarks"]:
    suite = bench["id"].upper() if bench["id"] == "swe" else bench["id"].capitalize()
    for domain, members in sorted(bench["members"].items()):
        lines.append(r"\subsection*{%s: \emph{%s}}" % (suite, domain))
        for rung, task in zip(RUNGS, members):
            text = open(os.path.join(ROOT, "tasks", task, "prompt.md"), encoding="ascii").read()
            lines.append(r"\noindent\textit{%s} (%s)" % (rung, task.split("-")[0]))
            lines += [r"\begin{Verbatim}[fontsize=\scriptsize,frame=leftline,xleftmargin=0.5em]",
                      wrapped(text), r"\end{Verbatim}", ""]
open(OUT, "w").write("\n".join(lines) + "\n")
print(f"wrote {OUT}")
