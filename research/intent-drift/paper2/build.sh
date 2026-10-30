#!/bin/sh
# Regenerate every number, table, and figure from db/results.db, then build main.pdf.
set -e
cd "$(dirname "$0")"
python3 analysis/analyze.py --db "${DB:-data/results_snapshot.db}"
python3 tools/paper_macros.py
python3 tools/heatmaps.py
python3 tools/exec_drift.py
python3 tools/catalog.py
python3 tools/prompts_appendix.py
python3 tools/fallbacks.py
tectonic --keep-logs main.tex
