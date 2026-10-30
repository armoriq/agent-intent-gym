#!/bin/bash
# Reap orphaned cursor-agent worker-server node procs (ppid=1) left behind by
# finished runs during the sweep. ppid=1 means the parent run already exited, so
# these can never belong to an active run. Stops when the sweep writes DONE.
while [ ! -f /tmp/sweep_gen2/DONE ]; do
  ps -eo pid,ppid,command | \
    awk '$2==1 && /\.local\/share\/cursor-agent\/versions/ && /worker-server/ {print $1}' | \
    while read -r p; do kill "$p" 2>/dev/null; done
  sleep 45
done
echo "reaper exiting at $(date)" >> /tmp/sweep_gen2/reaper.log
