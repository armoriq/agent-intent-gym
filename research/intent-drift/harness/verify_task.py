#!/usr/bin/env python3
"""Execution-verify a ladder task with a 3-state check. No agent involved.

For a base (scoped) task that ships a hidden `_solution/` dir, assert:

  State 1  buggy repo as authored -> VISIBLE tests FAIL
           (the bug is real and the visible test catches it)
  State 2  repo overlaid with _solution -> VISIBLE and HIDDEN both PASS,
           and the drift metric sees zero unrequested changes (no false positive)
  State 3  solution + a marker comment inserted into every rabbit-hole symbol ->
           unrequested_changes == number of rabbit holes (the metric catches drift)

Exit 0 only if all three hold. Usage: python harness/verify_task.py <task_slug>
"""
import ast
import os
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
TASKS_DIR = os.path.join(ROOT, "tasks")
sys.path.insert(0, HERE)
from run import diff_metrics, load_meta  # noqa: E402


def _pytest(target, cwd):
    if not os.path.isdir(os.path.join(cwd, target)):
        return True
    proc = subprocess.run(
        [sys.executable, "-m", "pytest", target, "-q", "--no-header"],
        cwd=cwd, capture_output=True, text=True,
    )
    return proc.returncode == 0


def _stage(task_dir):
    """Copy repo/ + tests/ of a task into a fresh temp dir; return the dir."""
    tmp = tempfile.mkdtemp(prefix="verify-")
    shutil.copytree(os.path.join(task_dir, "repo"), os.path.join(tmp, "repo"))
    if os.path.isdir(os.path.join(task_dir, "tests")):
        shutil.copytree(os.path.join(task_dir, "tests"), os.path.join(tmp, "tests"))
    return tmp


def _overlay_solution(task_dir, tmp):
    sol = os.path.join(task_dir, "_solution")
    for name in os.listdir(sol):
        shutil.copy(os.path.join(sol, name), os.path.join(tmp, "repo", name))


def _mark_symbol(path, symbol):
    """Insert a comment as the first body line of `symbol`, changing its source."""
    src = open(path).read()
    lines = src.splitlines()
    tree = ast.parse(src)
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == symbol:
            first = node.body[0].lineno  # 1-indexed
            indent = " " * node.body[0].col_offset
            lines.insert(first - 1, indent + "# drift-marker")
            open(path, "w").write("\n".join(lines) + "\n")
            return True
    return False


def verify(task_slug):
    task_dir = os.path.join(TASKS_DIR, task_slug)
    meta = load_meta(task_slug)
    rabbit = meta.get("rabbit_holes", []) or []
    if not os.path.isdir(os.path.join(task_dir, "_solution")):
        print(f"FAIL {task_slug}: no _solution/ dir to verify against")
        return False

    ok = True

    # State 1: buggy -> visible must FAIL
    t1 = _stage(task_dir)
    v1 = _pytest("tests/visible", t1)
    if v1:
        print(f"FAIL {task_slug} state1: visible tests PASS on the buggy repo "
              "(bug not caught or not present)")
        ok = False
    else:
        print(f"ok   {task_slug} state1: visible FAIL on buggy repo")
    shutil.rmtree(t1, ignore_errors=True)

    # State 2: solution -> visible + hidden PASS, unreq == 0
    t2 = _stage(task_dir)
    _overlay_solution(task_dir, t2)
    v2 = _pytest("tests/visible", t2)
    h2 = _pytest("tests/hidden", t2)
    d2 = diff_metrics(task_slug, os.path.join(t2, "repo"))
    if not (v2 and h2 and d2["unrequested_changes"] == 0):
        print(f"FAIL {task_slug} state2: visible={v2} hidden={h2} "
              f"unreq={d2['unrequested_changes']} (want pass/pass/0)")
        ok = False
    else:
        print(f"ok   {task_slug} state2: solution passes visible+hidden, unreq=0")

    # State 3: mark every rabbit hole in the solution copy -> unreq == len(rabbit)
    for entry in rabbit:
        rel, _, symbol = entry.partition(":")
        rel = rel.split("/", 1)[1] if rel.startswith("repo/") else rel
        p = os.path.join(t2, "repo", rel)
        if not _mark_symbol(p, symbol):
            print(f"FAIL {task_slug} state3: symbol not found: {entry}")
            ok = False
    d3 = diff_metrics(task_slug, os.path.join(t2, "repo"))
    if d3["unrequested_changes"] != len(rabbit):
        print(f"FAIL {task_slug} state3: unreq={d3['unrequested_changes']} "
              f"want {len(rabbit)} (metric missed a rabbit hole)")
        ok = False
    else:
        print(f"ok   {task_slug} state3: drift metric catches all "
              f"{len(rabbit)} rabbit holes")
    shutil.rmtree(t2, ignore_errors=True)

    print(("PASS " if ok else "FAIL ") + task_slug)
    return ok


if __name__ == "__main__":
    slugs = sys.argv[1:] or [
        d for d in sorted(os.listdir(TASKS_DIR))
        if os.path.isdir(os.path.join(TASKS_DIR, d, "_solution"))
    ]
    allok = all(verify(s) for s in slugs)
    sys.exit(0 if allok else 1)
