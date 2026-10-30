#!/bin/bash
# Gen-2 newest-lineup sweep: 8 Cursor arms x 21 ladder tasks, k=1.
# Arms run in parallel; each arm walks its tasks serially. Idempotent-ish:
# re-running appends new run_index rows, it does not overwrite.
cd "$(dirname "$0")/.." || exit 1

TASKS="T004-percentile-nearest-rank T005-percentile-loose-prompt T006-percentile-vague-prompt \
T007-pagination-count T008-pagination-loose-prompt T009-pagination-vague-prompt \
T010-money-nickel-rounding T011-money-loose-prompt T012-money-vague-prompt \
T013-backoff-cap T014-backoff-loose-prompt T015-backoff-vague-prompt \
T016-slug-truncate T017-slug-loose-prompt T018-slug-vague-prompt \
T019-cache-expiry T020-cache-loose-prompt T021-cache-vague-prompt \
T022-histogram-bucket T023-histogram-loose-prompt T024-histogram-vague-prompt"

ARMS="g2-opus-5.5 g2-composer-2.5 g2-kimi-k3 g2-glm-5.2 g2-gpt-5.6-sol g2-codex-5.3 g2-grok-4.7 g2-gemini-3.8"

LOG=/tmp/sweep_gen2
mkdir -p "$LOG"
rm -f "$LOG/DONE"

run_one_arm() {
  arm="$1"
  for t in $TASKS; do
    echo "[$(date +%H:%M:%S)] START $arm $t" >> "$LOG/$arm.log"
    python3 harness/run.py run "$t" "$arm" 1 >> "$LOG/$arm.log" 2>&1
    echo "[$(date +%H:%M:%S)] END   $arm $t" >> "$LOG/$arm.log"
  done
  echo "[$(date +%H:%M:%S)] ARM COMPLETE $arm" >> "$LOG/$arm.log"
}

for a in $ARMS; do
  run_one_arm "$a" &
done
wait
echo "all arms complete at $(date)" > "$LOG/DONE"
