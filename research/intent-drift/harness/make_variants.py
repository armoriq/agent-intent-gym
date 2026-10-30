#!/usr/bin/env python3
"""Mint loose + vague prompt variants from a scoped base task.

The variants reuse the base's repo/, tests/, rubric.yaml, and _solution/ verbatim
(identical bug and bait); only prompt.md and meta.yaml differ. The base meta.yaml
supplies `loose_prompt:` and `vague_prompt:` strings.

Usage: python harness/make_variants.py <base_slug> <loose_slug> <vague_slug>
"""
import os
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
TASKS_DIR = os.path.join(os.path.dirname(HERE), "tasks")
sys.path.insert(0, HERE)
from run import load_meta  # noqa: E402

META_TMPL = """slug: {slug}
persona: developer
difficulty: {difficulty}
language: python
contamination_tag: fresh
source: authored for this study
visible_tests: {visible_tests}
hidden_tests: {hidden_tests}

# Prompt-realism ladder variant of {base}. Identical repo, tests, rubric, and bait;
# only prompt.md changes. Compare arm-for-arm against the base to isolate prompt style.
prompt_variant: {variant}
paired_with: {base}
variant_group: {group}

in_scope:
{in_scope}
out_of_scope:
{out_of_scope}

rabbit_holes:
{rabbit_holes}

drift_probe: >
  Same repo and bait as {base} with a {variant} prompt. Behavior is guarded by the
  hidden PASS_TO_PASS tests and the unrequested_changes metric. The arm-for-arm gap
  against {base} isolates the effect of {variant} prompting.
"""


def _yaml_list(items):
    return "\n".join("  - " + str(i) for i in items)


def make_one(base_slug, out_slug, variant, prompt_text):
    base = os.path.join(TASKS_DIR, base_slug)
    out = os.path.join(TASKS_DIR, out_slug)
    if os.path.exists(out):
        shutil.rmtree(out)
    os.makedirs(out)
    for sub in ("repo", "tests", "_solution"):
        src = os.path.join(base, sub)
        if os.path.isdir(src):
            shutil.copytree(src, os.path.join(out, sub))
    shutil.copy(os.path.join(base, "rubric.yaml"), os.path.join(out, "rubric.yaml"))
    open(os.path.join(out, "prompt.md"), "w").write(prompt_text.strip() + "\n")

    m = load_meta(base_slug)
    meta = META_TMPL.format(
        slug=out_slug,
        difficulty=m.get("difficulty", "medium"),
        visible_tests=m.get("visible_tests", 2),
        hidden_tests=m.get("hidden_tests", 6),
        base=base_slug,
        variant=variant,
        group=m.get("variant_group", base_slug),
        in_scope=_yaml_list(m.get("in_scope", [])),
        out_of_scope=_yaml_list(m.get("out_of_scope", [])),
        rabbit_holes=_yaml_list(m.get("rabbit_holes", [])),
    )
    open(os.path.join(out, "meta.yaml"), "w").write(meta)
    print("wrote", out_slug)


def main():
    base_slug, loose_slug, vague_slug = sys.argv[1], sys.argv[2], sys.argv[3]
    m = load_meta(base_slug)
    make_one(base_slug, loose_slug, "loose", m["loose_prompt"])
    make_one(base_slug, vague_slug, "realistic_vague", m["vague_prompt"])


if __name__ == "__main__":
    main()
