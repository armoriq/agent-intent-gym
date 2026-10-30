#!/bin/bash
# Expansion-set sweep: the 10 new domains (30 ladder tasks, T025-T054) across the
# 7 gen-2 arms, k=1. Gemini 3.8 is excluded: its Cursor spend cap resets 30 Sep
# 2026, so it is run separately after the reset. Arms run in parallel; each arm
# walks its tasks serially. Appends new run_index rows, never overwrites.
cd "$(dirname "$0")/.." || exit 1

TASKS="T025-stats-median T026-grade-boundary T027-bisect-insert T028-moving-average \
T029-duration-hms T030-nth-largest T031-config-merge T032-cli-flags \
T033-semver-compare T034-querystring-build \
T035-stats-loose-prompt T036-stats-vague-prompt T037-grade-loose-prompt T038-grade-vague-prompt \
T039-bisect-loose-prompt T040-bisect-vague-prompt T041-moving-loose-prompt T042-moving-vague-prompt \
T043-duration-loose-prompt T044-duration-vague-prompt T045-nth-loose-prompt T046-nth-vague-prompt \
T047-config-loose-prompt T048-config-vague-prompt T049-cli-loose-prompt T050-cli-vague-prompt \
T051-semver-loose-prompt T052-semver-vague-prompt T053-querystring-loose-prompt T054-querystring-vague-prompt"

ARMS="g2-opus-5.5 g2-composer-2.5 g2-kimi-k3 g2-glm-5.2 g2-gpt-5.6-sol g2-codex-5.3 g2-grok-4.7"

LOG=/tmp/sweep_expansion
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
