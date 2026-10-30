#!/usr/bin/env python3
"""Refresh once after the active sweep stops writing committed results."""
import argparse
import hashlib
import json
from pathlib import Path
import sqlite3
import subprocess
import sys
import time

HERE=Path(__file__).resolve().parent
ROOT=HERE.parent.parent


def fingerprint():
    con=sqlite3.connect((ROOT/'db/results.db').as_uri()+'?mode=ro',uri=True)
    con.execute('PRAGMA query_only=ON')
    data=con.execute('''SELECT r.id,r.task_id,r.model_id,r.run_index,r.turns,r.error,
                       s.metric_pass,s.intent_pass,s.unrequested_changes
                       FROM run r LEFT JOIN result s ON s.run_id=r.id ORDER BY r.id''').fetchall()
    con.close()
    return hashlib.sha256(json.dumps(data).encode()).hexdigest()


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--poll-seconds',type=float,default=60)
    parser.add_argument('--settle-seconds',type=float,default=120)
    parser.add_argument('--max-hours',type=float,default=8)
    args=parser.parse_args()
    start=changed=time.monotonic()
    last=fingerprint()
    status=HERE/'out'/'refresh_status.json'
    while True:
        now=time.monotonic()
        current=fingerprint()
        if current!=last:
            changed=now
            last=current
        runners=subprocess.run(['pgrep','-f','harness/run.py run'],capture_output=True,text=True)
        sweep_status=ROOT/'paper2'/'sweep_status.md'
        states=[line.split('|')[7].strip().lower() for line in sweep_status.read_text().splitlines() if line.startswith('| g2-') and len(line.split('|'))>7] if sweep_status.exists() else []
        status_running=any('running' in state for state in states)
        active=runners.returncode==0 or status_running
        quiet=now-changed
        state=dict(state='waiting',active_runners=active,status_reports_running=status_running,quiet_seconds=round(quiet),
                   elapsed_seconds=round(now-start),source_fingerprint=current)
        status.write_text(json.dumps(state,indent=2)+'\n')
        if not active and quiet>=args.settle_seconds:
            subprocess.run([sys.executable,str(HERE/'analyze.py')],check=True)
            state['state']='refreshed after sweep inactivity'
            state['results_snapshot_sha256']=json.loads((HERE/'out'/'results.json').read_text())['metadata']['snapshot_sha256']
            status.write_text(json.dumps(state,indent=2)+'\n')
            print(json.dumps(state),flush=True)
            return
        if now-start>=args.max_hours*3600:
            subprocess.run([sys.executable,str(HERE/'analyze.py')],check=True)
            state['state']='refreshed at timeout; sweep completion unconfirmed'
            status.write_text(json.dumps(state,indent=2)+'\n')
            print(json.dumps(state),flush=True)
            return
        time.sleep(min(args.poll_seconds,60))


if __name__=='__main__':
    main()
