# Gen-2 sweep status

Updated: 2026-10-16 12:44:33 IST

Target: 52 tasks, T003–T054. Done means at least one run has `error IS NULL` and `turns IS NOT NULL`.

| Arm | Done | Remaining | Errored tasks remaining | Errored attempts | Unscored attempts | State | Finish or block time (IST) |
|---|---:|---:|---:|---:|---:|---|---|
| g2-opus-5.5 | 52 | 0 | 0 | 14 | 0 | finished | 2026-10-16 11:01:41 IST |
| g2-composer-2.5 | 52 | 0 | 0 | 0 | 0 | finished | 2026-10-16 10:11:49 IST |
| g2-kimi-k3 | 52 | 0 | 0 | 11 | 1 | finished | 2026-10-16 10:58:37 IST |
| g2-glm-5.2 | 52 | 0 | 0 | 12 | 0 | finished | 2026-10-16 10:58:09 IST |
| g2-gpt-5.6-sol | 52 | 0 | 0 | 12 | 0 | finished | 2026-10-16 11:03:30 IST |
| g2-codex-5.3 | 52 | 0 | 0 | 13 | 0 | finished; sandbox validation run 671 | 2026-10-16 12:44:23 IST |
| g2-grok-4.7 | 52 | 0 | 0 | 1 | 0 | finished | 2026-10-16 10:24:26 IST |
| g2-gemini-3.8 | 35 | 17 | 2 | 2 | 20 | blocked | 2026-10-16 12:35:31 IST |

## Diagnosis

The 2026-09-29 empty trajectories contain only Cursor init and user events. Every configured gen-2 model ID is present in `cursor-agent models`. A real GLM retry on T025 on 2026-10-16 completed with tool calls and passed both test sets (run 480, 64 s). The older empty sessions were a Cursor-side transient or usage condition; their saved transcripts do not identify which. The harness correctly marked the short transcripts as errors. A separate Kimi T054 attempt (run 621) produced a long malformed tool-call reply with no tool events; the harness left its error NULL. `_degenerate_session` now flags any tool-free transcript. Run 621 remains unchanged, and a real retry succeeded. The earlier Opus cap did not recur. Gemini resumed after its September reset but hit a new explicit cap on run 670.

## Arm details

- g2-opus-5.5: All 52 tasks covered. Log: `/tmp/intentbench_sweep/g2-opus-5.5.log`.
- g2-composer-2.5: All 52 tasks covered. Log: `/tmp/intentbench_sweep/g2-composer-2.5.log`.
- g2-kimi-k3: All 52 tasks covered. Log: `/tmp/intentbench_sweep/g2-kimi-k3.log`.
- g2-glm-5.2: All 52 tasks covered. Log: `/tmp/intentbench_sweep/g2-glm-5.2.log`.
- g2-gpt-5.6-sol: All 52 tasks covered. Log: `/tmp/intentbench_sweep/g2-gpt-5.6-sol.log`.
- g2-codex-5.3: All 52 tasks covered. Log: `/tmp/intentbench_sweep/g2-codex-5.3.log`.
- g2-grok-4.7: All 52 tasks covered. Log: `/tmp/intentbench_sweep/g2-grok-4.7.log`.
- g2-gemini-3.8: The isolated sweep stopped at 35/52 when Cursor returned `ActionRequiredError` on run 670. Log: `/tmp/intentbench_sweep/g2-gemini-3.8-isolated.log`.

## Isolation boundary

The prior sweep stopped before the in-flight Gemini T023 run committed a database row. The highest pre-isolation run ID was 652. The temp-workdir change starts at run ID **653**, the first scored run with an `ISOLATED` marker. Codex T003 run 653 started with Cursor cwd `/private/tmp/ib-jv1jec31`, archived the work under `runs/`, and scored metric=1, intent=1, turns=14. The archived `work/` and `trajectory.jsonl` paths are unchanged. Earlier rows and run directories remain untouched. Run 303 is a confirmed pre-change oracle read.

**The temp-workdir marker does not prove blind access.** Isolated Gemini run 670 read `/tmp/intentbench_sweep.py`, found the canonical benchmark path, then used tools on `tasks/T039-bisect-loose-prompt/meta.yaml` and `tests/hidden/test_bisect_hidden.py`. The trajectory scan found no canonical-path or hidden-test references in isolated runs 653–669, but that absence is not a filesystem access guarantee. Treat run 670 as contaminated. The SQL coverage table counts rows by the requested success rule and does not establish experimental blindness for any arm.

At 2026-10-16 12:42 IST, the harness gained a macOS `sandbox-exec` rule denying Cursor read and write access to the entire canonical benchmark tree. This is in addition to the temp workspace. It fails closed if `sandbox-exec` is unavailable. The first scored run under this OS rule is **run ID 671**, marked `SANDBOXED` as well as `ISOLATED`; this is the stronger isolation threshold. Existing runs 653–670 retain only their original `ISOLATED` marker. No existing rows or run directories were changed.

The OS rule denied direct, symlink, and `/System/Volumes/Data` reads of the benchmark, and denied a write probe. Standalone Cursor diagnostics showed that both its ReadFile and Shell tools received permission errors when asked to read the canonical README. A real sandboxed Codex T004 run 671 then began with cwd `/private/tmp/ib-xf7ftqqw`, made 12 tool turns, archived `work/`, removed the temp directory, and scored metric=1 and intent=1 with no error. Its trajectory contains no canonical path or hidden-test references. Future Cursor runs will use this rule.

Gemini T023 timed out after 600 seconds as isolated run 654 and remains missing. Before the cap, 15 isolated Gemini tasks succeeded. Their median was 190 seconds and 75th percentile was 208 seconds. The remaining work would take roughly 54–59 minutes at those paces if access returns, plus retry time for T023 and T039. There is no completion ETA while the cap is active.

## Gemini isolated sweep

Blocked at 2026-10-16 12:35:31 IST. Cursor capped T039, run 670, with `ActionRequiredError`. The controller stopped this arm immediately.

No runs remain active. The cap has no known reset time.

Log: `/tmp/intentbench_sweep/g2-gemini-3.8-isolated.log`. Each task runs serially. The T023 timeout remains recorded as run 654.

## Final summary

399 of 416 arm-task cells have at least one successful run. All 17 missing cells are Gemini. Its cap blocked further runs at 2026-10-16 12:35:31 IST. Existing rows and run directories were left untouched. Run 670 exposed hidden benchmark files despite its temp-workdir marker, so that marker must not be used as proof of blindness. Run 671 is the first scored run with the OS read/write boundary.

Missing Gemini tasks: T023, T039–T054. T023 has a 600-second timeout in run 654. T039 hit the cap in run 670. T040–T054 have not received an isolated attempt.

Use this query in `sqlite3 db/results.db` to reproduce the coverage table:

```sql
WITH target AS (
  SELECT id, slug FROM task
  WHERE CAST(substr(slug, 2, 3) AS INTEGER) BETWEEN 3 AND 54
), pair AS (
  SELECT m.name AS arm, t.slug,
         MAX(CASE WHEN r.error IS NULL AND r.turns IS NOT NULL THEN 1 ELSE 0 END) AS done,
         MAX(CASE WHEN r.error IS NOT NULL THEN 1 ELSE 0 END) AS ever_errored,
         SUM(CASE WHEN r.error IS NOT NULL THEN 1 ELSE 0 END) AS errored_attempts,
         SUM(CASE WHEN r.id IS NOT NULL AND r.error IS NULL AND r.turns IS NULL
                  THEN 1 ELSE 0 END) AS unscored_attempts
  FROM model m CROSS JOIN target t
  LEFT JOIN run r ON r.model_id = m.id AND r.task_id = t.id
  WHERE m.name LIKE 'g2-%'
  GROUP BY m.name, t.slug
)
SELECT arm, SUM(done) AS done, SUM(1-done) AS remaining,
       SUM(CASE WHEN done = 0 THEN ever_errored ELSE 0 END) AS errored_tasks_remaining,
       SUM(errored_attempts) AS errored_attempts,
       SUM(unscored_attempts) AS unscored_attempts
FROM pair GROUP BY arm ORDER BY arm;
```
