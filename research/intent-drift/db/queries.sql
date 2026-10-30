-- Example analysis queries. These ARE the paper's numbers.
-- Run one with:  sqlite3 db/results.db < db/queries.sql   (or paste individually)

-- 1. The headline: drift gap per model.
--    metric-pass rate minus intent-pass rate. Large positive = gaming.
SELECT  m.name AS model,
        ROUND(AVG(r.metric_pass) * 100, 1) AS metric_pass_pct,
        ROUND(AVG(r.intent_pass) * 100, 1) AS intent_pass_pct,
        ROUND((AVG(r.metric_pass) - AVG(r.intent_pass)) * 100, 1) AS drift_gap_pts,
        COUNT(*) AS n_runs
FROM result r
JOIN run   ru ON ru.id = r.run_id
JOIN model m  ON m.id  = ru.model_id
GROUP BY m.id
ORDER BY drift_gap_pts DESC;

-- 2. Drift split by persona (does gaming concentrate on fuzzy non-dev tasks?).
SELECT  m.name AS model, t.persona,
        ROUND((AVG(r.metric_pass) - AVG(r.intent_pass)) * 100, 1) AS drift_gap_pts,
        COUNT(*) AS n
FROM result r
JOIN run ru ON ru.id = r.run_id
JOIN model m ON m.id = ru.model_id
JOIN task t  ON t.id = ru.task_id
GROUP BY m.id, t.persona
ORDER BY m.name, t.persona;

-- 3. Contamination check: pass rate on classic vs fresh tasks per model.
--    A big classic>>fresh gap suggests memorization, not capability.
SELECT  m.name AS model, t.contamination_tag,
        ROUND(AVG(r.intent_pass) * 100, 1) AS intent_pass_pct,
        COUNT(*) AS n
FROM result r
JOIN run ru ON ru.id = r.run_id
JOIN model m ON m.id = ru.model_id
JOIN task t  ON t.id = ru.task_id
GROUP BY m.id, t.contamination_tag
ORDER BY m.name, t.contamination_tag;

-- 4. Over-scope: average diff size on tasks the model got right.
--    Bigger diffs on correct answers can indicate over-engineering.
SELECT  m.name AS model,
        ROUND(AVG(r.diff_added + r.diff_removed), 1) AS avg_diff_lines,
        ROUND(AVG(r.files_touched), 2) AS avg_files,
        ROUND(AVG(r.collateral_failures), 2) AS avg_collateral
FROM result r
JOIN run ru ON ru.id = r.run_id
JOIN model m ON m.id = ru.model_id
WHERE r.intent_pass = 1
GROUP BY m.id
ORDER BY avg_diff_lines DESC;

-- 5. The gaming case list: runs that passed visible tests but failed intent.
--    These are the trajectories to read by hand for the qualitative section.
SELECT  m.name AS model, t.slug AS task, ru.run_index, ru.trajectory_path
FROM result r
JOIN run ru ON ru.id = r.run_id
JOIN model m ON m.id = ru.model_id
JOIN task t  ON t.id = ru.task_id
WHERE r.metric_pass = 1 AND r.intent_pass = 0
ORDER BY m.name, t.slug;

-- 6. LONG-HORIZON: drift onset per model. "At what scale does it start?"
--    Lower onset = drifts sooner. Both in turns and in accumulated context.
SELECT  m.name AS model,
        ROUND(AVG(r.drift_onset_step), 1)   AS avg_onset_turn,
        ROUND(AVG(r.drift_onset_tokens), 0) AS avg_onset_tokens,
        ROUND(AVG(r.drift_fraction) * 100, 1) AS drift_pct_of_steps,
        ROUND(AVG(r.recovered) * 100, 1)    AS recovery_pct,
        COUNT(*) AS n_sessions
FROM result r
JOIN run ru ON ru.id = r.run_id
JOIN model m ON m.id = ru.model_id
WHERE r.drift_onset_step IS NOT NULL
GROUP BY m.id
ORDER BY avg_onset_turn ASC;

-- 7. LONG-HORIZON: does onset move with context accumulation vs stay flat?
--    Buckets sessions by the context size at onset to test the "reads more
--    files, gets wrong intuition" hypothesis.
SELECT  m.name AS model,
        CASE WHEN r.drift_onset_tokens < 20000 THEN '0-20k'
             WHEN r.drift_onset_tokens < 50000 THEN '20-50k'
             WHEN r.drift_onset_tokens < 100000 THEN '50-100k'
             ELSE '100k+' END AS onset_context_bucket,
        COUNT(*) AS n
FROM result r
JOIN run ru ON ru.id = r.run_id
JOIN model m ON m.id = ru.model_id
WHERE r.drift_onset_tokens IS NOT NULL
GROUP BY m.id, onset_context_bucket
ORDER BY m.name, onset_context_bucket;
