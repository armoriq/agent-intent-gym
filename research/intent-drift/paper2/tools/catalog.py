#!/usr/bin/env python3
"""Write sections/appendix_catalog.tex from tasks/*/meta.yaml and suites/registry.yaml."""
import os
import re
import yaml

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
OUT = os.path.join(ROOT, "paper2", "sections", "appendix_catalog.tex")


def esc(s):
    s = s.replace("\\", r"\textbackslash{}")
    for a, b in [("&", r"\&"), ("%", r"\%"), ("_", r"\_"), ("#", r"\#"), ("$", r"\$"),
                 ("{", r"\{"), ("}", r"\}"), ("--", "-{}-"), ('""', "the empty string")]:
        s = s.replace(a, b)
    return s


CODE = re.compile(r"(\w+\(\)|repo/[\w/]+\.py|--key=value|\"key=\")")


def tex(s):
    s = s.replace("->", "\x00")
    out = []
    for i, part in enumerate(CODE.split(s)):
        out.append(r"\texttt{" + esc(part) + "}" if i % 2 else esc(part))
    return "".join(out).replace("\x00", r"$\rightarrow$")


reg = yaml.safe_load(open(os.path.join(ROOT, "suites", "registry.yaml")))
rows = []
for bench in reg["domain_benchmarks"]:
    for domain, members in sorted(bench["members"].items()):
        base = members[0]
        meta = yaml.safe_load(open(os.path.join(ROOT, "tasks", base, "meta.yaml")))
        fix = meta["in_scope"][0].split(", e.g.")[0].rstrip(".")
        rows.append((bench["id"].upper() if bench["id"] == "swe" else bench["id"].capitalize(),
                     domain, ", ".join(m.split("-")[0] for m in members), tex(fix)))

lines = [r"\begin{table*}[t]", r"\centering", r"\footnotesize",
         r"\caption{Task catalog. Each domain is one repository posed at three rungs "
         r"(scoped, loose, vague). The fix column is the in-scope change from the task "
         r"metadata.}", r"\label{tab:catalog}",
         r"\begin{tabular}{@{}llp{0.13\textwidth}p{0.64\textwidth}@{}}", r"\toprule",
         r"Suite & Domain & Tasks & Requested fix \\", r"\midrule"]
for r in rows:
    lines.append(" & ".join(r) + r" \\")
lines += [r"\bottomrule", r"\end{tabular}", r"\end{table*}"]
open(OUT, "w").write("\n".join(lines) + "\n")
print(f"wrote {OUT} ({len(rows)} domains)")
