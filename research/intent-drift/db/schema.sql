-- Intent Drift Benchmark: queryable results store (SQLite)
-- Every headline number in the paper must be derivable from a query here.
-- Apply with:  sqlite3 db/results.db < db/schema.sql

PRAGMA foreign_keys = ON;

-- A model+harness bundle under test (Claude Code, OpenCode paid, etc.)
CREATE TABLE IF NOT EXISTS model (
    id            INTEGER PRIMARY KEY,
    name          TEXT NOT NULL UNIQUE,   -- e.g. "opencode-muse"
    vendor        TEXT NOT NULL,          -- e.g. "OpenCode"
    harness       TEXT NOT NULL,          -- e.g. "opencode-cli"
    access        TEXT NOT NULL,          -- "cli" | "gui-manual"
    model_version TEXT,                   -- exact version string if known
    cutoff_date   TEXT,                   -- training cutoff if published (ISO)
    notes         TEXT
);

-- A benchmark task.
CREATE TABLE IF NOT EXISTS task (
    id                INTEGER PRIMARY KEY,
    slug              TEXT NOT NULL UNIQUE, -- e.g. "T001-csv-revenue-chart"
    persona           TEXT NOT NULL,        -- "developer" | "non_developer"
    difficulty        TEXT NOT NULL,        -- "easy" | "medium" | "hard"
    language          TEXT,                 -- primary language / stack
    contamination_tag TEXT NOT NULL,        -- "fresh" | "post_cutoff" | "classic"
    source            TEXT,                 -- where it came from
    visible_tests     INTEGER NOT NULL DEFAULT 0,
    hidden_tests      INTEGER NOT NULL DEFAULT 0,
    created_at        TEXT NOT NULL DEFAULT (datetime('now'))
);

-- One execution of one model on one task (repeat k times per pair).
CREATE TABLE IF NOT EXISTS run (
    id              INTEGER PRIMARY KEY,
    model_id        INTEGER NOT NULL REFERENCES model(id),
    task_id         INTEGER NOT NULL REFERENCES task(id),
    run_index       INTEGER NOT NULL,        -- 0..k-1
    started_at      TEXT NOT NULL DEFAULT (datetime('now')),
    finished_at     TEXT,
    turns           INTEGER,
    wall_seconds    REAL,
    cost_usd        REAL,                    -- estimate if not exact
    trajectory_path TEXT,                    -- full log on disk for hand audit
    error           TEXT,                    -- harness-level failure, if any
    UNIQUE (model_id, task_id, run_index)
);

-- Scoring outcome for a run. Split so drift is directly queryable.
CREATE TABLE IF NOT EXISTS result (
    run_id              INTEGER PRIMARY KEY REFERENCES run(id) ON DELETE CASCADE,
    metric_pass         INTEGER NOT NULL,    -- 0/1: all VISIBLE tests pass
    intent_pass         INTEGER NOT NULL,    -- 0/1: all HIDDEN tests pass AND rubric met
    visible_pass_count  INTEGER NOT NULL DEFAULT 0,
    hidden_pass_count   INTEGER NOT NULL DEFAULT 0,
    rubric_score        REAL,                -- 0..1
    diff_added          INTEGER,
    diff_removed        INTEGER,
    files_touched       INTEGER,
    collateral_failures INTEGER,             -- PASS_TO_PASS that regressed
    over_engineering    INTEGER,             -- 0/1 flag from rubric
    security_flag       INTEGER,             -- 0/1 flag from rubric
    -- long-horizon (session) drift outcomes; NULL for single-shot runs
    drift_onset_step    INTEGER,             -- first non-recovering adjacent/off step
    drift_onset_tokens  INTEGER,             -- accumulated context at onset ("the scale")
    drift_fraction      REAL,                -- share of steps adjacent/off
    cascade             INTEGER,             -- 0/1 drift compounded
    recovered           INTEGER,             -- 0/1 returned to intent before stop
    unrequested_changes INTEGER              -- out-of-scope lines changed at stop
);

-- One step of a long-horizon session (a run with many steps).
CREATE TABLE IF NOT EXISTS step (
    id             INTEGER PRIMARY KEY,
    run_id         INTEGER NOT NULL REFERENCES run(id) ON DELETE CASCADE,
    step_index     INTEGER NOT NULL,      -- 0..n in trajectory order
    context_tokens INTEGER,               -- cumulative context size at this step
    action_type    TEXT,                  -- read | edit | run | plan | other
    files_touched  TEXT,                  -- comma-separated paths
    classification TEXT,                  -- on_intent | adjacent_unnecessary | off_intent | recovery
    judged_by      TEXT,                  -- auto | llm_judge | human
    note           TEXT,
    UNIQUE (run_id, step_index)
);

CREATE INDEX IF NOT EXISTS idx_step_run ON step(run_id, step_index);
CREATE INDEX IF NOT EXISTS idx_step_class ON step(classification);

-- Per-criterion rubric detail, so fuzzy non-dev tasks stay auditable.
CREATE TABLE IF NOT EXISTS rubric_item (
    id         INTEGER PRIMARY KEY,
    run_id     INTEGER NOT NULL REFERENCES run(id) ON DELETE CASCADE,
    criterion  TEXT NOT NULL,   -- e.g. "handles empty CSV"
    weight     REAL NOT NULL DEFAULT 1.0,
    passed     INTEGER NOT NULL,-- 0/1
    judged_by  TEXT NOT NULL,   -- "auto" | "llm_judge" | "human"
    note       TEXT
);

CREATE INDEX IF NOT EXISTS idx_run_model_task ON run(model_id, task_id);
CREATE INDEX IF NOT EXISTS idx_result_passes ON result(metric_pass, intent_pass);
