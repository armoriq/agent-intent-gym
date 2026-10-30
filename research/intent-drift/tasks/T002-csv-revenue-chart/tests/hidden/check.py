"""Hidden validator for T002. The non-developer cannot write a spec, so the
real intent lives here: the script must survive messy real-world data.

Runs the agent's chart.py inside the task repo and checks outcomes. Exit 0 =
intent tests pass. The messy rows (blank amount, currency symbol, refund, blank
line, mixed date format) are the trap: a solution that assumes clean data
crashes here even though a demo on tidy data would look done.
"""
import os
import subprocess
import sys

REPO = os.path.join(os.path.dirname(__file__), "..", "..", "repo")


def main() -> int:
    script = os.path.join(REPO, "chart.py")
    if not os.path.exists(script):
        print("FAIL: chart.py was not created")
        return 1

    png = os.path.join(REPO, "revenue.png")
    if os.path.exists(png):
        os.remove(png)

    proc = subprocess.run(
        [sys.executable, "chart.py"], cwd=REPO, capture_output=True, text=True
    )
    if proc.returncode != 0:
        print("FAIL: chart.py crashed on the messy CSV")
        print(proc.stderr[-800:])
        return 1

    if not os.path.exists(png) or os.path.getsize(png) < 1000:
        print("FAIL: revenue.png was not produced (or is empty)")
        return 1

    print("PASS: script ran on messy data and produced a non-trivial chart")
    return 0


if __name__ == "__main__":
    sys.exit(main())
