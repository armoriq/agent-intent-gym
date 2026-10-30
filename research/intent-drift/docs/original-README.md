# Intent Drift Benchmark

A benchmark and study of whether AI coding agents follow developer intent or
optimize the visible metric (Goodhart's Law, measured).

The full rationale and method are in `docs/research-design.md`. This README is
the map.

## Idea in one paragraph

Every task ships with **visible tests** the agent can see and run, plus
**hidden tests and a rubric** it never sees. `drift gap = visible-pass rate -
hidden/intent-pass rate`. A model that scores high on visible and low on hidden
is gaming the measure. All numbers come from SQL queries over a results
database, not hand-tallied.

## Layout

```
docs/
  research-design.md     the paper's thinking (advisor-facing)
  open-questions.md      decisions for the advisor discussion
  task-authoring.md      how to write real, non-synthetic tasks
db/
  schema.sql             queryable results store (SQLite)
  queries.sql            the analysis queries that produce the paper's numbers
  results.db             created by `harness/run.py init-db`
harness/
  run.py                 runner + scorer (agent invocation is a Phase 3 stub)
tasks/
  T001-invoice-late-fee  developer task, hard oracle, verified drift probe
  T002-csv-revenue-chart non-developer task, fuzzy intent, rubric-heavy
```

## Quick start

```bash
python3 -m pip install --user pytest matplotlib   # matplotlib for T002 solutions
python3 harness/run.py init-db
python3 harness/run.py list-tasks
# score any candidate solution directory against a task's oracles:
python3 harness/run.py score T001-invoice-late-fee <path-to-candidate-repo>
```

## Status (prototype v0.1)

- Working: DB schema, scoring (visible vs hidden), two verified seed tasks,
  analysis queries.
- Stubbed: per-agent CLI invocation (needs the model-access decision) and the
  rubric judge + diff metrics (Phase 4).

See `docs/open-questions.md` for what to settle next.
