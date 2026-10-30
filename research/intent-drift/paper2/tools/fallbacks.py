#!/usr/bin/env python3
"""Write sections/_fallbacks.tex: \\providecommand stubs for macros the text uses but
analysis/out/macros.tex does not define yet, rendered as a visible red marker."""
import glob, os, re
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
defined = set()
for src in ("analysis/out/macros.tex", "sections/_paper_macros.tex"):
    defined |= set(re.findall(r"\\newcommand\{\\([A-Za-z]+)\}", open(os.path.join(ROOT, src)).read()))
used = set()
for f in glob.glob(os.path.join(ROOT, "sections", "*.tex")):
    used |= set(re.findall(r"\\((?:N|Gone|Gtwo|Loose|Cross|Suite|Overall|Exposure|Ladder|Disagreement|Coverage|Sc|Ex|Tc|Q|Dg|Snapshot)[A-Za-z]*)", open(f).read()))
missing = sorted(used - defined)
with open(os.path.join(ROOT, "sections", "_fallbacks.tex"), "w") as fh:
    for m in missing:
        fh.write("\\providecommand{\\%s}{\\textcolor{red}{\\textbf{[%s]}}}\n" % (m, m))
print("missing macros:", " ".join(missing) or "none")
