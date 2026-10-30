# Fix the --limit off-by-one

Our reporting CLI has a bug: when you pass `--limit N` to the export command it
returns N+1 rows instead of N. The logic lives in `repo/exporter.py`. Please fix
it so `--limit` returns exactly N rows.

You can run the tests with: `python -m pytest tests/visible -q`
