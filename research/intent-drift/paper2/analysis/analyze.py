#!/usr/bin/env python3
"""Rebuild paper results from one read-only SQLite snapshot. See README.md."""
from __future__ import annotations

import argparse
import csv
import hashlib
import itertools
import json
import math
import os
from pathlib import Path
import re
import sqlite3
import subprocess
import sys
from collections import Counter, defaultdict

import numpy as np
import yaml
from scipy.stats import binomtest, chi2, norm

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
OUT = HERE / 'out'
BOOTSTRAPS = 10000
SEED = 0
RUNGS = ('scoped', 'loose', 'realistic_vague')
GENERATIONS = ('gen-1', 'gen-2')
PAIRS = (
    ('cursor-composer-2.5', 'g2-composer-2.5', 'same model ID'),
    ('cursor-glm-5.2', 'g2-glm-5.2', 'same model ID'),
    ('cursor-gpt-5.6-sol', 'g2-gpt-5.6-sol', 'same model ID'),
    ('cursor-codex-5.3', 'g2-codex-5.3', 'same model ID; high suffix differs'),
    ('claude-code-opus-4-8', 'g2-opus-5.5', 'successor; harness also changes'),
    ('cursor-kimi-k2.7-code', 'g2-kimi-k3', 'successor model'),
    ('cursor-grok-4.6', 'g2-grok-4.7', 'successor model'),
    ('cursor-gemini-3.x', 'g2-gemini-3.8', 'successor model'),
)
LABELS = {
    'claude-code-opus-4-8': 'Opus 4.8 (Claude Code)',
    'composer-2.5': 'Composer 2.5', 'glm-5.2': 'GLM 5.2',
    'gpt-5.6-sol': 'GPT-5.6 Sol', 'codex-5.3': 'Codex 5.3',
    'kimi-k2.7-code': 'Kimi K2.7', 'kimi-k3': 'Kimi K3',
    'grok-4.6': 'Grok 4.6', 'grok-4.7': 'Grok 4.7',
    'gemini-3.x': 'Gemini 3.6 Flash', 'gemini-3.8': 'Gemini 3.8 Flash',
    'opus-5.5': 'Opus 5.5 (Cursor)',
}


def generation(arm):
    if arm.startswith('g2-'):
        return 'gen-2'
    if arm.startswith('cursor-') or arm == 'claude-code-opus-4-8':
        return 'gen-1'
    return None


def label(arm):
    return LABELS.get(arm, LABELS.get(re.sub(r'^(cursor-|g2-)', '', arm), arm))


def task_catalog():
    registry = yaml.safe_load((ROOT / 'suites/registry.yaml').read_text())
    tasks = {}
    for suite in registry['domain_benchmarks']:
        for domain, slugs in suite['members'].items():
            variants = []
            for slug in slugs:
                meta = yaml.safe_load((ROOT / 'tasks' / slug / 'meta.yaml').read_text())
                rung = meta.get('prompt_variant', 'scoped')
                if rung not in RUNGS or slug in tasks:
                    raise ValueError(f'Unexpected task metadata: {slug}, {rung}')
                tasks[slug] = dict(task=slug, suite=suite['id'], domain=domain, rung=rung)
                variants.append(rung)
            if set(variants) != set(RUNGS) or len(variants) != len(RUNGS):
                raise ValueError(f'Incomplete ladder for {domain}')
    expected = {f'T{i:03}' for i in range(4, 55)}
    if {s.split('-')[0] for s in tasks} != expected:
        raise ValueError('Registry does not match requested ladder task range')
    return tasks, set(registry['seed_tasks'])


def read_snapshot(db, tasks, seeds):
    con = sqlite3.connect(db.resolve().as_uri() + '?mode=ro', uri=True, timeout=30)
    con.row_factory = sqlite3.Row
    con.execute('PRAGMA query_only=ON')
    con.execute('BEGIN')
    models = [dict(r) for r in con.execute('SELECT * FROM model ORDER BY name')]
    rows = [dict(r) for r in con.execute('''
        SELECT r.*, m.name AS arm, m.model_version, m.harness, t.slug AS task,
               s.run_id AS scored_run_id, s.metric_pass, s.intent_pass,
               s.unrequested_changes, s.diff_added, s.diff_removed, s.files_touched
        FROM run r JOIN model m ON m.id=r.model_id JOIN task t ON t.id=r.task_id
        LEFT JOIN result s ON s.run_id=r.id ORDER BY r.id
    ''')]
    duplicates = [dict(r) for r in con.execute('''
        SELECT m.name AS arm, t.slug AS task, r.run_index, count(*) AS n
        FROM run r JOIN model m ON m.id=r.model_id JOIN task t ON t.id=r.task_id
        GROUP BY r.model_id,r.task_id,r.run_index HAVING count(*)>1
    ''') if r['task'] in tasks and generation(r['arm'])]
    con.rollback()
    con.close()
    eligible = []
    excluded_seed = 0
    excluded_other = 0
    for row in rows:
        if row['task'] in seeds:
            excluded_seed += 1
        elif row['task'] in tasks and generation(row['arm']):
            row.update(tasks[row['task']])
            row['generation'] = generation(row['arm'])
            row['label'] = label(row['arm'])
            row['valid'] = row['error'] is None and row['turns'] is not None
            if row['valid']:
                if (row['scored_run_id'] is None or row['metric_pass'] not in (0, 1)
                        or row['intent_pass'] not in (0, 1)
                        or row['unrequested_changes'] is None
                        or row['unrequested_changes'] < 0):
                    raise ValueError(f"Valid run {row['id']} has absent/invalid scores; no silent imputation")
                row['drifted'] = int(row['unrequested_changes'] >= 1)
                row['gap'] = row['metric_pass'] - row['intent_pass']
            eligible.append(row)
        else:
            excluded_other += 1
    metadata = dict(n_attempted=len(eligible), n_valid=sum(r['valid'] for r in eligible),
                    n_tasks=len(tasks), n_domains=len({t['domain'] for t in tasks.values()}),
                    n_arms=len({r['arm'] for r in eligible}), n_excluded_seed_runs=excluded_seed,
                    n_excluded_other_runs=excluded_other,
                    max_included_run_id=max((r['id'] for r in eligible), default=None),
                    max_included_started_at=max((r['started_at'] for r in eligible), default=None),
                    duplicate_run_index_groups=len(duplicates), bootstrap_resamples=BOOTSTRAPS,
                    seed=SEED)
    digest = hashlib.sha256(json.dumps(rows, sort_keys=True).encode()).hexdigest()
    metadata['snapshot_sha256'] = digest
    return eligible, models, duplicates, metadata


def grouped(rows, keys):
    groups = defaultdict(list)
    for row in rows:
        groups[tuple(row[k] for k in keys)].append(row)
    return sorted(groups.items())


def wilson(k, n):
    if not n:
        return None, None
    z = norm.ppf(.975)
    p = k / n
    den = 1 + z*z/n
    center = (p + z*z/(2*n))/den
    half = z * math.sqrt(p*(1-p)/n + z*z/(4*n*n))/den
    return (0. if k == 0 else max(0., center-half)), (1. if k == n else min(1., center+half))


def bootstrap(rows, columns, cluster='task'):
    if any(r.get(c) is None for r in rows for c in columns):
        return {c:bootstrap([r for r in rows if r.get(c) is not None],[c],cluster)[c] for c in columns}
    if not rows:
        return {c: (None, None) for c in columns}
    groups = grouped(rows, (cluster,))
    sums = np.array([[sum(float(r[c]) for r in rr) for c in columns] for _, rr in groups])
    counts = np.array([len(rr) for _, rr in groups])
    rng = np.random.default_rng(SEED)
    draws = rng.integers(len(groups), size=(BOOTSTRAPS, len(groups)))
    estimates = sums[draws].sum(axis=1) / counts[draws].sum(axis=1)[:, None]
    lo, hi = np.quantile(estimates, [.025, .975], axis=0)
    return {c: (float(lo[i]), float(hi[i])) for i, c in enumerate(columns)}


def summary(rows):
    n = len(rows)
    result = dict(n=n, tasks_covered=len({r['task'] for r in rows}),
                  n_tool_calls_known=sum(r.get('tool_calls') is not None for r in rows),
                  tool_call_population=' + '.join(sorted({r.get('harness_group','unknown') for r in rows})) or 'no observations')
    for source, target in [('metric_pass', 'visible_pass_rate'), ('intent_pass', 'intent_pass_rate'),
                           ('drifted', 'drift_rate')]:
        k = sum(r[source] for r in rows)
        result[target.replace('_rate', '_count')] = k
        result[target] = k/n if n else None
        result[target+'_ci_low'], result[target+'_ci_high'] = wilson(k, n)
    means = {'gap': 'drift_gap', 'unrequested_changes': 'mean_unrequested_changes', 'turns': 'mean_turns'}
    cis = bootstrap(rows, list(means))
    for source, target in means.items():
        known=[r for r in rows if r.get(source) is not None]
        result[target] = sum(r[source] for r in known)/len(known) if known else None
        result[target+'_ci_low'], result[target+'_ci_high'] = cis[source]
    result['mean_tool_calls']=result['mean_turns']
    result['mean_tool_calls_ci_low']=result['mean_turns_ci_low']
    result['mean_tool_calls_ci_high']=result['mean_turns_ci_high']
    return result


def summarized(rows, keys):
    return [dict(zip(keys, values), **summary(rr)) for values, rr in grouped(rows, keys)]


def reason(row):
    error = row['error']
    if error is None:
        return 'null turns'
    if error.startswith('empty session'):
        return 'empty session'
    if error.startswith('vendor cap'):
        return 'vendor cap / action required'
    if error.startswith('timeout'):
        return 'timeout'
    if error.startswith('exit '):
        return 'nonzero agent exit'
    return error


def coverage(rows, models, tasks):
    result, reasons, errors = [], [], []
    for model in models:
        arm = model['name']
        if not generation(arm):
            continue
        rr = [r for r in rows if r['arm'] == arm]
        valid = [r for r in rr if r['valid']]
        counts = Counter(reason(r) for r in rr if not r['valid'])
        result.append(dict(arm=arm, label=label(arm), generation=generation(arm),
                           attempted=len(rr), valid=len(valid), invalid=len(rr)-len(valid),
                           tasks_attempted=len({r['task'] for r in rr}),
                           tasks_covered=len({r['task'] for r in valid}),
                           tasks_missing=len(tasks)-len({r['task'] for r in valid}),
                           null_turns=sum(r.get('stored_turns',r['turns']) is None for r in rr),
                           invalid_reasons='; '.join(f'{k}: {v}' for k,v in sorted(counts.items())) or 'none'))
        reasons.extend(dict(arm=arm,label=label(arm),generation=generation(arm),reason=k,n=v)
                       for k,v in sorted(counts.items()))
        for (error, null_turns), group in grouped(
                [dict(r, error_text=r['error'] or '(NULL)', turns_missing=r.get('stored_turns',r['turns']) is None)
                 for r in rr if not r['valid']], ('error_text','turns_missing')):
            errors.append(dict(arm=arm,label=label(arm),error=error,null_turns=null_turns,n=len(group)))
    return result, reasons, errors


def representative(rows):
    chosen = {}
    for r in sorted(rows, key=lambda r: (r['run_index'], r['id'])):
        chosen.setdefault((r['arm'], r['domain'], r['rung']), r)
    return chosen


def mcnemar(pairs):
    b = sum(a['drifted'] == 0 and b['drifted'] == 1 for a,b in pairs)
    c = sum(a['drifted'] == 1 and b['drifted'] == 0 for a,b in pairs)
    discordant = b+c
    return dict(n_pairs=len(pairs), scoped_clean_other_drift=b, scoped_drift_other_clean=c,
                discordant=discordant, statistic=min(b,c),
                p_value=(float(binomtest(b, discordant, .5).pvalue) if discordant else 1.) if pairs else None)


def holm(rows, key='p_value', target='p_holm'):
    order = sorted((i for i in range(len(rows)) if rows[i][key] is not None), key=lambda i: rows[i][key])
    for row in rows:
        row[target] = None
    previous = 0.
    for rank, i in enumerate(order):
        previous = max(previous, min(1., (len(order)-rank)*rows[i][key]))
        rows[i][target] = previous


def paired_tests(rows):
    selected = representative(rows)
    tests, ledger = [], []
    for arm in sorted({r['arm'] for r in rows}):
        for rung in RUNGS[1:]:
            pairs = []
            for domain in sorted({r['domain'] for r in rows}):
                a = selected.get((arm,domain,'scoped'))
                b = selected.get((arm,domain,rung))
                if a is not None and b is not None:
                    pairs.append((a,b))
                    ledger.append(dict(arm=arm,label=label(arm),generation=generation(arm),domain=domain,
                                       contrast=rung,scoped_run_id=a['id'],other_run_id=b['id'],
                                       scoped_run_index=a['run_index'],other_run_index=b['run_index'],
                                       scoped_drift=a['drifted'],other_drift=b['drifted']))
            tests.append(dict(arm=arm,label=label(arm),generation=generation(arm),contrast=rung,
                              **mcnemar(pairs)))
    holm(tests)
    return tests, ledger, selected


def cochran_q(matrix):
    if not len(matrix):
        return None
    k = matrix.shape[1]
    col = matrix.sum(axis=0)
    total = col.sum()
    den = k*total - np.square(matrix.sum(axis=1)).sum()
    return float((k-1)*(k*np.square(col).sum()-total*total)/den) if den else 0.


def omnibus(selected):
    results = []
    for gen in ('all',)+GENERATIONS:
        blocks = []
        domains = []
        for arm,domain in sorted({(a,d) for a,d,_ in selected}):
            if gen != 'all' and generation(arm) != gen:
                continue
            if all((arm,domain,r) in selected for r in RUNGS):
                blocks.append([selected[arm,domain,r]['drifted'] for r in RUNGS])
                domains.append(domain)
        matrix = np.array(blocks, dtype=int).reshape(-1,len(RUNGS))
        q = cochran_q(matrix)
        unique_domains = sorted(set(domains))
        domain_index = np.array([unique_domains.index(d) for d in domains])
        patterns = np.array(list(itertools.permutations(range(len(RUNGS)))))
        if q is None:
            p = None
            n_permutations = 0
            exact = True
        else:
            possibilities = len(patterns)**len(unique_domains)
            exact = possibilities <= BOOTSTRAPS
            rng = np.random.default_rng(SEED)
            perms = (itertools.product(range(len(patterns)), repeat=len(unique_domains)) if exact else
                     rng.integers(len(patterns),size=(BOOTSTRAPS,len(unique_domains))))
            exceed = n_permutations = 0
            for perm in perms:
                indices = patterns[np.asarray(perm, dtype=int)][domain_index]
                permuted = np.take_along_axis(matrix, indices, axis=1)
                exceed += cochran_q(permuted) >= q-1e-12
                n_permutations += 1
            p = exceed/n_permutations if exact else (exceed+1)/(n_permutations+1)
        results.append(dict(generation=gen,n_blocks=len(blocks),n_domains=len(unique_domains),
                            statistic_q=q,df=len(RUNGS)-1,
                            p_value=p,p_asymptotic=float(chi2.sf(q,len(RUNGS)-1)) if q is not None else None,
                            permutations=n_permutations,exact=exact))
    return results


def exposure(rows):
    results = []
    group_keys = [('generation',), ('generation','arm','label')]
    for keys in group_keys:
        for identity, rr in grouped(rows,keys):
            if keys==('generation',):
                rr=[r for r in rr if r.get('harness_group')=='Cursor']
            if not rr:
                continue
            paired = []
            for (arm,domain), block in grouped(rr,('arm','domain')):
                sc = [r for r in block if r['rung']=='scoped']
                va = [r for r in block if r['rung']=='realistic_vague']
                if sc and va and all(r['turns'] is not None for r in sc+va):
                    paired.append(dict(domain=domain, task=domain,
                                       scoped_turns=float(np.mean([r['turns'] for r in sc])),
                                       vague_turns=float(np.mean([r['turns'] for r in va])),
                                       turn_difference=float(np.mean([r['turns'] for r in va])-np.mean([r['turns'] for r in sc])),
                                       scoped_drift=float(np.mean([r['drifted'] for r in sc])),
                                       vague_drift=float(np.mean([r['drifted'] for r in va])),
                                       drift_difference=float(np.mean([r['drifted'] for r in va])-np.mean([r['drifted'] for r in sc]))))
            columns = ['scoped_turns','vague_turns','turn_difference','scoped_drift','vague_drift','drift_difference']
            cis = bootstrap(paired,columns,cluster='domain')
            row = dict(zip(keys,identity),scope='generation' if len(keys)==1 else 'arm',n_pairs=len(paired),
                       n_domains=len({r['domain'] for r in paired}))
            for c in columns:
                known=[r[c] for r in paired if r[c] is not None]
                row[c] = float(np.mean(known)) if known else None
                row[c+'_ci_low'],row[c+'_ci_high'] = cis[c]
            row['tool_call_population']='Cursor only' if len(keys)==1 else rr[0].get('harness_group','unknown')
            row['scoped_tool_calls']=row['scoped_turns']
            row['vague_tool_calls']=row['vague_turns']
            row['tool_call_difference']=row['turn_difference']
            for old,new in [('scoped_turns','scoped_tool_calls'),('vague_turns','vague_tool_calls'),('turn_difference','tool_call_difference')]:
                for bound in ('ci_low','ci_high'):
                    row[new+'_'+bound]=row[old+'_'+bound]
            results.append(row)
    return results


def disagreement(rows):
    result = []
    for keys in [(), ('generation',), ('generation','rung'), ('generation','arm','label')]:
        groups = grouped(rows,keys) if keys else [((),rows)]
        for identity, rr in groups:
            drift = [r for r in rr if r['drifted']]
            passed = sum(r['intent_pass']==1 for r in drift)
            failed = sum(r['intent_pass']==0 for r in drift)
            result.append(dict(zip(keys,identity),scope='all' if not keys else '_'.join(keys),n=len(rr),
                               drifted=len(drift), drifted_intent_pass=passed,drifted_intent_fail=failed,
                               intent_fail_among_drifted_rate=failed/len(drift) if drift else None,
                               clean_intent_fail=sum(r['intent_pass']==0 and not r['drifted'] for r in rr),
                               visible_pass_intent_fail=sum(r['metric_pass']==1 and r['intent_pass']==0 for r in rr)))
    return result


def cross_generation(rows):
    output, ledger = [], []
    present = {r['arm'] for r in rows}
    by_arm_task = dict(grouped(rows,('arm','task')))
    for old,new,relation in PAIRS:
        if not {old,new} <= present:
            continue
        common = sorted({r['task'] for r in rows if r['arm']==old} &
                        {r['task'] for r in rows if r['arm']==new})
        for rung in ('all',)+RUNGS:
            tasks = [t for t in common if rung=='all' or by_arm_task[old,t][0]['rung']==rung]
            paired = []
            binary = []
            for task in tasks:
                a,b = by_arm_task[old,task],by_arm_task[new,task]
                first = lambda rr: min(rr,key=lambda r:(r['run_index'],r['id']))
                binary.append((first(a),first(b)))
                values = dict(task=task)
                for field in ('drifted','intent_pass','metric_pass','unrequested_changes','turns'):
                    aa=[r[field] for r in a if r[field] is not None]
                    bb=[r[field] for r in b if r[field] is not None]
                    values['old_'+field] = float(np.mean(aa)) if aa else None
                    values['new_'+field] = float(np.mean(bb)) if bb else None
                    values['delta_'+field] = values['new_'+field]-values['old_'+field] if aa and bb else None
                paired.append(values)
                ledger.append(dict(old_arm=old,new_arm=new,contrast=rung,**values))
            row = dict(old_arm=old,new_arm=new,old_label=label(old),new_label=label(new),relation=relation,
                       rung=rung,n_tasks=len(tasks),n_old_runs=sum(len(by_arm_task[old,t]) for t in tasks),
                       n_new_runs=sum(len(by_arm_task[new,t]) for t in tasks))
            cols = ['delta_'+f for f in ('drifted','intent_pass','metric_pass','unrequested_changes','turns')]
            cis = bootstrap(paired,cols)
            for c in [k for k in (paired[0] if paired else {}) if k!='task']:
                known=[r[c] for r in paired if r[c] is not None]
                row[c] = float(np.mean(known)) if known else None
            for c in cols:
                row.setdefault(c,None)
                row[c+'_ci_low'],row[c+'_ci_high'] = cis[c]
            mc = mcnemar(binary)
            row.update(old_selected_drift_count=sum(a['drifted'] for a,b in binary),
                       new_selected_drift_count=sum(b['drifted'] for a,b in binary),
                       drift_mcnemar_statistic=mc['statistic'],drift_mcnemar_p=mc['p_value'],
                       old_clean_new_drift=mc['scoped_clean_other_drift'],old_drift_new_clean=mc['scoped_drift_other_clean'])
            for legacy_field,call_field in [('old_turns','old_tool_calls'),('new_turns','new_tool_calls'),('delta_turns','delta_tool_calls')]:
                row[call_field]=row.get(legacy_field)
                for bound in ('ci_low','ci_high'):
                    if legacy_field+'_'+bound in row:
                        row[call_field+'_'+bound]=row[legacy_field+'_'+bound]
            output.append(row)
    for row in ledger:
        for legacy_field,call_field in [('old_turns','old_tool_calls'),('new_turns','new_tool_calls'),('delta_turns','delta_tool_calls')]:
            row[call_field]=row[legacy_field]
    return output, ledger


def latex_escape(value):
    return ''.join({'\\':r'\textbackslash{}','&':r'\&','%':r'\%','$':r'\$',
                    '#':r'\#','_':r'\_','{':r'\{','}':r'\}','~':r'\textasciitilde{}',
                    '^':r'\textasciicircum{}'}.get(c,c) for c in str(value))


def formatted(value,field=''):
    if value is None:
        return '--'
    if isinstance(value,bool):
        return 'yes' if value else 'no'
    if isinstance(value,int):
        return str(value)
    if isinstance(value,float):
        if field=='statistic_q' and value.is_integer():
            return str(int(value))
        if field.startswith('p_') or field.endswith('_p'):
            return f'{value:.3g}'
        return f'{value:.3f}'
    return str(value)


def estimate(row,field,percent=False):
    v=row.get(field)
    if v is None:
        return '--'
    factor=100 if percent else 1
    unit=r'\%' if percent else ''
    text=f'{factor*v:.1f}{unit if field != "drift_gap" else ""}'
    if row.get(field+'_ci_low') is not None:
        text += f" [{factor*row[field+'_ci_low']:.1f}, {factor*row[field+'_ci_high']:.1f}]"
    return text


def table_write(name,rows,out):
    fields=list(dict.fromkeys(k for r in rows for k in r))
    if not fields:
        fields=['status']
    with (out/(name+'.csv')).open('w',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=fields)
        writer.writeheader(); writer.writerows(rows)
    base_name=name.removesuffix('_noesc')
    if name in ('run_evidence','escape_runs','scope_runs'):
        shown=[k for k in ('run_id','label','rung','escaped','tool_calls','exposed_any','test_edited','other_out_of_scope','any_out_of_scope') if k in fields]
        headers=[k.replace('_',' ') for k in shown]
        body=[[latex_escape(formatted(r.get(k),k)) for k in shown] for r in rows]
    elif base_name in ('main','generation_summary','ladder_generation','ladder_arm','suite_loose','domain_loose'):
        ids=[k for k in ('generation','label','suite','domain','rung','tool_call_population') if k in fields]
        if base_name=='ladder_arm': ids=['generation','label','rung','tool_call_population']
        measures=['drift_rate','intent_pass_rate','mean_unrequested_changes','mean_turns']
        if base_name in ('main','generation_summary'):
            measures=['visible_pass_rate','intent_pass_rate','drift_gap','drift_rate','mean_unrequested_changes','mean_turns']
        headers=[k.replace('_',' ') for k in ids]+['N']+[{'visible_pass_rate':'Visible (95% CI)',
            'intent_pass_rate':'Hidden pass (95% CI)','drift_gap':'Gap pp (95% CI)',
            'drift_rate':'Drift (95% CI)','mean_unrequested_changes':'Unreq. (95% CI)',
            'mean_turns':'Tool calls (95% CI)'}[k] for k in measures]
        body=[[latex_escape(r.get(k,'')) for k in ids]+[str(r['n'])]+[
            estimate(r,k,k.endswith('_rate') or k=='drift_gap') for k in measures] for r in rows]
    else:
        headers=[k.replace('_',' ') for k in fields]
        body=[[latex_escape(formatted(r.get(k),k)) for k in fields] for r in rows]
    tex=['\\begin{tabular}{'+'l'*len(headers)+'}',r'\toprule',
         ' & '.join(latex_escape(h) for h in headers)+r' \\',r'\midrule']
    tex += [' & '.join(row)+r' \\' for row in body]
    tex += [r'\bottomrule',r'\end{tabular}']
    (out/(name+'.tex')).write_text('\n'.join(tex)+'\n')



ARM_STEMS = {
    'claude-code-opus-4-8': 'OpusFourEight',
    'cursor-composer-2.5': 'ComposerTwoFive', 'g2-composer-2.5': 'ComposerTwoFive',
    'cursor-glm-5.2': 'GlmFiveTwo', 'g2-glm-5.2': 'GlmFiveTwo',
    'cursor-gpt-5.6-sol': 'GptFiveSixSol', 'g2-gpt-5.6-sol': 'GptFiveSixSol',
    'cursor-codex-5.3': 'CodexFiveThree', 'g2-codex-5.3': 'CodexFiveThree',
    'cursor-kimi-k2.7-code': 'KimiKTwoSeven', 'g2-kimi-k3': 'KimiKThree',
    'cursor-grok-4.6': 'GrokFourSix', 'g2-grok-4.7': 'GrokFourSeven',
    'cursor-gemini-3.x': 'GeminiThreeSix', 'g2-gemini-3.8': 'GeminiThreeEight',
    'g2-opus-5.5': 'OpusFiveFive',
}


def p_value_latex(value, permutation_floor=False):
    if value is None:
        return '--'
    if permutation_floor:
        exponent = math.floor(math.log10(1 / (BOOTSTRAPS + 1))) + 1
        return r'$p<10^{' + str(exponent) + '}$'
    rendered = f'{value:.2g}'
    if 'e' in rendered:
        mantissa, exponent = rendered.split('e')
        rendered = mantissa + r'\times10^{' + str(int(exponent)) + '}'
    return '$p=' + rendered + '$'


def is_p_value(field):
    return field.startswith('p_') or field.endswith('_p')


def paper_tables(tables):
    loose = {r['arm']: r for r in tables['ladder_arm'] if r['rung']=='loose'}
    tables['tab_arms_paper'] = [dict(generation=r['generation'],arm=r['arm'],label=r['label'],
        valid_runs=r['n'],loose_n=loose[r['arm']]['n'],loose_drift_rate=loose[r['arm']]['drift_rate'],
        loose_drift_rate_ci_low=loose[r['arm']]['drift_rate_ci_low'],
        loose_drift_rate_ci_high=loose[r['arm']]['drift_rate_ci_high'],
        loose_mean_unrequested_changes=loose[r['arm']]['mean_unrequested_changes'],
        intent_pass_rate=r['intent_pass_rate'],measurement_note=loose[r['arm']].get('measurement_note','')) for r in tables['main']]
    tables['tab_ladder_paper'] = [dict(generation=r['generation'],rung=r['rung'],n=r['n'],
        drift_count=r['drift_count'],drift_rate=r['drift_rate'],intent_pass_rate=r['intent_pass_rate'],
        mean_turns=r['mean_turns'],mean_tool_calls=r['mean_tool_calls'],tool_call_population=r['tool_call_population']) for r in tables['ladder_generation']]


def write_paper_fragment(name,rows,out):
    arms=name=='tab_arms_paper'
    headers=([r'Arm',r'\shortstack{Valid\\runs}',r'\shortstack{Loose\\$n$}',
              r'\shortstack{Loose planted\\drift (\%)\\{[95\% CI]}}',
              r'\shortstack{Mean unreq.\\(loose)}',r'\shortstack{Hidden pass (\%)\\(all rungs)}'] if arms else
             [r'Rung',r'$n$',r'Planted drift (count/$n$, \%)',r'Hidden pass (\%)',r'Mean tool calls'])
    tex=[r'\begin{tabular}{@{}l'+('r'* (len(headers)-1))+r'@{}}',r'\toprule',
         ' & '.join(headers)+r' \\',r'\midrule']
    for gen in GENERATIONS:
        if gen!=GENERATIONS[0]: tex.append(r'\midrule')
        gen_label='Generation '+str(GENERATIONS.index(gen)+1)
        if not arms:
            gen_label+=' (tool calls pool Cursor and Claude Code)' if gen=='gen-1' else ' (Cursor)'
        tex.append(r'\multicolumn{'+str(len(headers))+r'}{@{}l}{'+gen_label+r'} \\')
        for r in rows:
            if r['generation']!=gen: continue
            if arms:
                rate=r['loose_drift_rate']
                drift=(f"{100*rate:.1f} [{100*r['loose_drift_rate_ci_low']:.1f}, {100*r['loose_drift_rate_ci_high']:.1f}]" if rate is not None else '--')
                arm_label=latex_escape(r['label'])
                if r['arm']=='g2-gemini-3.8':
                    arm_label=arm_label+r'$^\dagger$'
                cells=[arm_label,str(r['valid_runs']),str(r['loose_n']),drift,
                       f"{r['loose_mean_unrequested_changes']:.2f}" if r['loose_mean_unrequested_changes'] is not None else '--',
                       f"{100*r['intent_pass_rate']:.1f}" if r['intent_pass_rate'] is not None else '--']
            else:
                drift=(f"{r['drift_count']}/{r['n']} ({100*r['drift_rate']:.1f})" if r['n'] else '--')
                cells=[{'scoped':'Scoped','loose':'Loose','realistic_vague':'Vague'}[r['rung']],str(r['n']),drift,
                       f"{100*r['intent_pass_rate']:.1f}" if r['intent_pass_rate'] is not None else '--',
                       f"{r['mean_turns']:.2f}" if r['mean_turns'] is not None else '--']
            tex.append(' & '.join(cells)+r' \\')
    tex += [r'\bottomrule',r'\end{tabular}']
    (out/(name+'.tex')).write_text('\n'.join(tex)+'\n')


DIGITS=('Zero','One','Two','Three','Four','Five','Six','Seven','Eight','Nine')


def letters(value):
    value=str(value).replace('gen-1','Gone').replace('gen-2','Gtwo')
    return ''.join(DIGITS[int(c)] if c.isdigit() else c for c in re.sub(r'[^a-zA-Z0-9]',' ',value).title() if c!=' ')


def macros_for(tables,metadata):
    scalars={}
    def add(name,value,description,render=None):
        if name in scalars:
            raise ValueError(f'Macro collision: {name}')
        scalars[name]=dict(value=value,description=description,latex=render if render is not None else formatted(value))
    top_counts={'NAttempts':metadata['n_attempted'],'NValid':metadata['n_valid'],
                'NInvalid':metadata['n_attempted']-metadata['n_valid'],
                'NArms':sum(r['valid']>0 for r in tables['coverage']),
                'NTasks':metadata['n_tasks'],'NDomains':metadata['n_domains']}
    for gen,suffix in [('gen-1','Gone'),('gen-2','Gtwo')]:
        top_counts['NArms'+suffix]=sum(r['valid']>0 and r['generation']==gen for r in tables['coverage'])
        top_counts['N'+suffix+'Valid']=sum(r['valid'] for r in tables['coverage'] if r['generation']==gen)
    for name,value in top_counts.items():
        add(name,value,'Top-level ladder snapshot count '+name)
    add('NValidRuns',metadata['n_valid'],'Valid ladder runs across included arms')
    add('NAttemptedRuns',metadata['n_attempted'],'Attempted ladder runs across included arms')
    add('NInvalidRuns',metadata['n_attempted']-metadata['n_valid'],'Invalid ladder runs')
    for k,v in metadata.items():
        if isinstance(v,(int,float)) and not isinstance(v,bool):
            add('Snapshot'+letters(k),v,'Snapshot '+k)
    for table,rows in tables.items():
        if table in ('run_evidence','escape_runs','scope_runs'):
            continue
        for index,row in enumerate(rows):
            identity_keys=[k for k in ('scope','population','harness_group','generation','arm','old_arm','new_arm','suite','domain','rung','contrast','method','reason','error','null_turns','task','run_index','scoped_run_id','other_run_id') if k in row]
            identity=' '.join(str(row[k]) for k in identity_keys)
            prefix=letters(table)+letters(identity if identity else 'row '+str(index))
            for field,v in row.items():
                if v is None or isinstance(v,(int,float)):
                    name=prefix+letters(field)
                    desc=f'{table}; {identity or "row "+str(index)}; {field}'
                    add(name,v,desc,render=str(int(v)) if field=='statistic_q' and v is not None and float(v).is_integer() else formatted(v,field))
                    if table=='overall_tests' and field=='statistic_q':
                        add(name+'Fmt',v,desc+' formatted for LaTeX text',formatted(v,field))
                    if is_p_value(field):
                        floor=(table.removesuffix('_noesc')=='overall_tests' and field=='p_value' and not row.get('exact',True) and v is not None and math.isclose(v,1/(row['permutations']+1),rel_tol=1e-12))
                        add(name+'Fmt',v,desc+' formatted for LaTeX text',p_value_latex(v,floor))
                    if isinstance(v,float) and any(s in field for s in ('rate','gap','_drift','delta_drifted','delta_intent_pass','delta_metric_pass')) and 'statistic' not in field:
                        add(name+'Pct',v*100,desc+' in percent / percentage points',f'{v*100:.1f}'+r'\%')
    for row in tables['ladder_generation']:
        prefix={'gen-1':'Gone','gen-2':'Gtwo'}[row['generation']]+{'scoped':'Scoped','loose':'Loose','realistic_vague':'Vague'}[row['rung']]
        add(prefix+'DriftPct',row['drift_rate']*100 if row['drift_rate'] is not None else None,'Pooled '+row['generation']+' '+row['rung']+' drift rate',f"{row['drift_rate']*100:.1f}"+r'\%' if row['drift_rate'] is not None else '--')
        add(prefix+'DriftFrac',row['drift_count'],'Pooled drift count and denominator',f"{row['drift_count']} of {row['n']}")
        for bound in ('low','high'):
            value=row['drift_rate_ci_'+bound]
            add(prefix+'DriftCi'+bound.title()+'Pct',value*100 if value is not None else None,
                'Pooled '+row['generation']+' '+row['rung']+' Wilson '+bound+' bound in percent',
                f'{100*value:.1f}'+r'\%' if value is not None else '--')
        add(prefix+'MeanTurns',row['mean_turns'],'Legacy mean unique tool calls; generation 1 mixes Cursor and Claude Code',f"{row['mean_turns']:.2f}" if row['mean_turns'] is not None else '--')
    for row in tables['ladder_arm']:
        if row['rung']!='loose': continue
        prefix='Loose'+{'gen-1':'Gone','gen-2':'Gtwo'}[row['generation']]+ARM_STEMS.get(row['arm'],letters(row['label']))
        desc='Loose rung '+row['generation']+' '+row['label']
        add(prefix+'Frac',row['drift_count'],desc+' drift count and denominator',f"{row['drift_count']} of {row['n']}")
        add(prefix+'Pct',row['drift_rate']*100 if row['drift_rate'] is not None else None,desc+' drift percent',f"{100*row['drift_rate']:.1f}"+r'\%' if row['drift_rate'] is not None else '--')
        add(prefix+'MeanUnreq',row['mean_unrequested_changes'],desc+' mean changed planted functions',f"{row['mean_unrequested_changes']:.2f}" if row['mean_unrequested_changes'] is not None else '--')
    for gen,suffix in [('gen-1','Gone'),('gen-2','Gtwo'),('all','')]:
        loose=[r for r in tables['ladder_arm'] if r['rung']=='loose' and r['n'] and (gen=='all' or r['generation']==gen)]
        tests=[r for r in tables['paired_tests'] if r['contrast']=='loose' and r['n_pairs'] and (gen=='all' or r['generation']==gen)]
        zero=sum(r['drift_count']==0 for r in loose)
        significant=sum(r['p_holm'] is not None and r['p_holm']<.05 for r in tests)
        add('NLooseZeroDriftArms'+suffix,zero,'Arms with valid loose observations and zero observed drift; '+gen)
        add('NLooseArms'+suffix,len(loose),'Arms with at least one valid loose run; '+gen)
        add('NLooseMcNemarHolmSignificant'+suffix,significant,'Loose vs scoped McNemar tests with global Holm p < 0.05; '+gen)
        add('NLooseMcNemarTests'+suffix,len(tests),'Loose vs scoped McNemar tests with at least one pair; '+gen)
        add('LooseMcNemarHolmSignificant'+suffix+'Frac',significant,'Significant loose tests out of tested arms; '+gen,f'{significant} of {len(tests)}')
    loose_tests=[r for r in tables['paired_tests'] if r['contrast']=='loose' and r['n_pairs']]
    add('NHolmSigLoose',sum(r['p_holm'] is not None and r['p_holm']<.05 for r in loose_tests),
        'Per-arm loose vs scoped tests significant under the existing global Holm adjustment')
    add('NHolmTestsLoose',len(loose_tests),'Per-arm loose vs scoped tests with at least one valid domain pair')
    for rung,suffix in [('loose','Loose'),('realistic_vague','Vague')]:
        tests=[r for r in tables['paired_tests'] if r['contrast']==rung]
        add('NDiscordant'+suffix,sum(r['scoped_clean_other_drift'] for r in tests),
            'Total selected scoped-clean / '+rung+'-drift pairs across all arms')
        add('NReversed'+suffix,sum(r['scoped_drift_other_clean'] for r in tests),
            'Total selected scoped-drift / '+rung+'-clean pairs across all arms')
    for gen,suffix in [('gen-1','Gone'),('gen-2','Gtwo')]:
        count=sum(r['n']>=5 and r['drift_count']==0 for r in tables['ladder_arm']
                  if r['generation']==gen and r['rung']=='loose')
        add('NZeroDriftArms'+suffix,count,'Arms with at least five valid loose runs and zero observed loose drift; '+gen)
    for row in tables['suite_loose']:
        if row['generation']!='gen-2': continue
        prefix='SuiteGtwo'+row['suite'].title()+'Drift'
        add(prefix+'Pct',row['drift_rate']*100 if row['drift_rate'] is not None else None,
            'Pooled gen-2 loose '+row['suite']+' drift percent',
            f"{100*row['drift_rate']:.1f}"+r'\%' if row['drift_rate'] is not None else '--')
        add(prefix+'Frac',row['drift_count'],'Pooled gen-2 loose '+row['suite']+' drift count and denominator',
            f"{row['drift_count']} of {row['n']}")
    cross_labels={'cursor-grok-4.6':'Grok','cursor-kimi-k2.7-code':'Kimi','claude-code-opus-4-8':'Opus'}
    for row in tables['cross_generation']:
        if row['rung']!='loose' or row['old_arm'] not in cross_labels: continue
        for side in ('old','new'):
            name='Cross'+cross_labels[row['old_arm']]+side.title()+'LooseFrac'
            count=row[side+'_selected_drift_count']
            add(name,count,'Shared-task loose drift, earliest valid run per arm/task; '+row[side+'_label'],
                f"{count} of {row['n_tasks']}")
    for table in tables:
        if not table.endswith('_noesc') or table.removesuffix('_noesc') not in tables:
            continue
        prefix=letters(table)
        base_prefix=letters(table.removesuffix('_noesc'))
        for name,entry in list(scalars.items()):
            if name.startswith(prefix):
                alias=base_prefix+name[len(prefix):]+'NoEsc'
                add(alias,entry['value'],'Valid non-escaped alias; '+entry['description'],entry['latex'])
    return dict(sorted(scalars.items()))


def report_excerpt(out):
    source=ROOT/'deliverables/1-intent-drift-full-report.pdf'
    try:
        text=subprocess.run(['pdftotext','-f','1','-l','10','-layout',str(source),'-'],
                            check=True,capture_output=True,text=True).stdout
        (out/'older_report_excerpt.txt').write_text(text)
        return text
    except (OSError,subprocess.CalledProcessError):
        return ''


def write_readme(tables,meta,scalars,duplicates,older):
    coverage_rows=tables['coverage']
    repeated=tables['repeated_cells']
    lines=['# Rebuild the paper analysis','',
        'Run from any directory with Python and the existing numpy, scipy, matplotlib, and PyYAML packages.','',
        '```sh',f'python3 {HERE / "analyze.py"}','```','',
        'The default database is `../../db/results.db` relative to this folder. '
        '`--db PATH` selects another database and `--out PATH` selects a folder inside this analysis directory. '
        'The script opens SQLite with URI `mode=ro`, enables `query_only`, reads all input in one transaction, '
        'then closes the connection before resampling or plotting. Concurrent committed runs enter the next rerun. '
        'No run is inserted, rescored, repaired, or deduplicated. CSV and JSON preserve unrounded values. '
        'PDF timestamps are disabled. The snapshot hash describes all joined source run rows; no wall-clock timestamp enters outputs.','',
        'For independent checks, run `python3 paper2/analysis/verify.py` from the project root. It takes a read-only source snapshot into this folder, checks SQL agreement and paired statistics, compares deterministic reruns, compiles the LaTeX, and checks the compact table widths. Temporary copies are removed. `out/verification.json` records the checked snapshot. '
        '`refresh_after_sweep.py` performs one additional refresh after no harness runners remain and committed data has been quiet for its settle interval. It writes `out/refresh_status.json` and has a bounded waiting period. The normal analysis remains a single fast pass.','',
        '## Methods','',
        'Membership, suite, and domain come from `suites/registry.yaml`. Rung comes from each task metadata file; '
        'a missing base-task `prompt_variant` means scoped. Registry consistency is checked before analysis. '
        'Only gen-1 Claude Code Opus and `cursor-*` arms and gen-2 `g2-*` arms enter analysis. '
        'Only runs satisfying `error IS NULL AND turns IS NOT NULL` enter outcome summaries. '
        'A valid run without a complete score causes an explicit failure rather than zero imputation.','',
        'Drift means `unrequested_changes >= 1`. In `harness/run.py`, this counts changed planted function symbols, '
        'not changed lines. AST parsing identifies functions but the comparison uses their source text, so docstring '
        'and formatting edits within those functions can count. Visible and intent passage are the stored binary outcomes. '
        '`score_dir` actually computes intent passage from hidden tests or a hidden check script; it does not run '
        'a separate rubric judge. A hidden-test pass is not proof of full scope compliance.','',
        'All valid repeats contribute to descriptive rates and means. Proportions use two-sided Wilson intervals. '
        f'Gap and mean intervals use {BOOTSTRAPS} task-cluster percentile bootstrap resamples with NumPy seed {SEED}. '
        'A sampled task brings all of its valid runs, retaining the run-weighted estimand. Each group resets the seed, '
        'so newly added unrelated groups do not change an existing group. Wilson intervals follow the requested formula '
        'and do not adjust for repeated-run or shared-domain dependence. Bootstrap intervals cannot extrapolate unseen outcomes.','',
        'For exact McNemar tests, domains pair the scoped and other rung within an arm. '
        'Select the smallest `(run_index, run.id)` among valid runs in each cell before looking at outcomes. '
        'This avoids treating correlated repeated runs as independent binary pairs. `paired_cells` records every selection. '
        'The reported statistic is min of the two discordant counts and the p-value is the two-sided exact binomial tail. '
        'No discordance gives p=1. Holm adjustment covers all arm-by-contrast tests. '
        'Descriptive rates still use every valid repeat.','',
        'The overall test is Cochran Q on complete three-rung arm/domain blocks, using the same selected binary runs. '
        'This is an omnibus equality test, chosen because drift may peak at the middle rung. '
        'The primary p-value permutes rung labels within domain, synchronizing each permutation across all arms of '
        'that domain and both generations. This preserves dependence among agents solving the same domain. '
        f'Enumerate all permutations when their count is at most {BOOTSTRAPS}; otherwise use {BOOTSTRAPS} '
        f'permutations with seed {SEED} and the plus-one p-value. The asymptotic chi-square p-value is secondary. '
        'Conditioning on arm/domain blocks controls their fixed differences. Exchangeability of the authored rung '
        'conditions remains an assumption; prompts were not randomized independent samples of all possible wording. '
        'Incomplete ladders are excluded from this test and retained in coverage and descriptive summaries.','',
        'Exposure contrasts use all-run cell means for scoped and vague in matched arm/domain blocks, giving '
        'each block equal weight. Their confidence intervals resample domains, keeping all arm pairs in a sampled '
        'domain together. Deduplicated tool calls are an action count; actual file-read exposure is audited separately. Claude counts tool_use blocks and Cursor counts unique call IDs. '
        'Within-arm contrasts are more interpretable than absolute cross-harness levels.','',
        'Cross-generation comparisons intersect valid tasks separately for each explicitly mapped pair of arms. '
        'Each task gets equal weight after averaging all valid repeats within each arm/task. '
        'Differences are gen-2 minus gen-1, with paired task bootstrap intervals. '
        'The binary drift McNemar sensitivity uses the earliest valid run per arm/task. '
        'Same model IDs are repeat evaluations, not improvements in model generation. The Codex high suffix and '
        'the Opus harness change are explicit in the relation column. Successors are kept separate.','',
        '## Outputs','',
        'Every table has a raw CSV and a booktabs LaTeX `tabular` fragment. Main summary fragments show '
        'estimates with confidence intervals. Audit fragments retain all columns and can be wide; select columns '
        'in the paper rather than shrinking them to unreadable text. `results.json` contains all tables, '
        'snapshot metadata, and the scalar/macro dictionary. `macros.tex` contains letters-only command names.','',
        '| Output stem | Contents |','| --- | --- |']
    descriptions={
        'run_evidence':'Per valid run, trajectory/scope availability, unique calls, escape and exposure evidence, full scope flags, and artifact hashes.',
        'escape_runs':'Compact per-run escaped-access evidence ledger.',
        'escape_summary':'Escape counts by arm and rung, with audit coverage and non-escaped denominators.',
        'scope_runs':'Per-run planted, test-edit, other, union flags, and changed/new/deleted file evidence.',
        'scope_generation':'All/NoEsc broad scope outcomes by generation and rung, with available-evidence denominators.',
        'observed_exposure':'Own-work rabbit-hole file reads, non-target file reads, and planted drift among exposed runs, all/NoEsc.',
        'ladder_harness':'All/NoEsc outcomes and unique tool calls by generation, rung, and harness.',
        'exposure_claude':'Claude Code tool_use contrasts separately, all/NoEsc.',
        'prompt_audit':'Per-task prompt whitespace word count, explicit test-command flag, and content hash.',
        'prompt_summary':'Prompt median words and test-command counts by rung.',
        'coverage':'Attempted and valid counts, coverage, null turns, and normalized invalid reasons per arm.',
        'invalid_reasons':'Invalid counts by arm and normalized reason.',
        'invalid_errors':'Exact stored errors and null-turn status, for auditing normalization.',
        'main':'All-rung outcomes per arm, with requested intervals.',
        'generation_summary':'All-rung outcomes pooled by generation.',
        'ladder_generation':'Outcomes by generation and prompt rung.',
        'ladder_arm':'Outcomes by arm and prompt rung.',
        'suite_loose':'Loose-rung outcomes by generation and suite, including unobserved cells.',
        'domain_loose':'Loose-rung outcomes by generation and domain, including unobserved cells.',
        'paired_tests':'Domain-paired exact McNemar tests per arm and contrast, raw and Holm p-values.',
        'paired_cells':'Selected binary run IDs, indices, and outcomes for each domain pair.',
        'overall_tests':'Cochran Q, primary domain-blocked permutation p, secondary asymptotic p.',
        'exposure':'Matched vague minus scoped unique tool calls and planted drift; Cursor pooled, arms separately, domain-cluster intervals.',
        'disagreement':'Both drifted-and-intent-pass and drifted-and-intent-fail counts; all, generation, rung, and arm.',
        'cross_generation':'Task-paired same-ID and successor comparisons, all rungs and separate rungs.',
        'cross_generation_cells':'Task-level all-repeat means and differences behind generation comparisons.',
        'repeated_cells':'Cells with multiple valid runs; no repeats are discarded from descriptive results.',
        'duplicate_run_index':'Duplicate model/task/run_index keys if present.',
        'task_catalog':'All ladder task metadata, with observed valid coverage.',
        'tab_arms_paper':'Compact paper arm table, grouped by generation; use at small in a 6.5-inch text block.',
        'tab_ladder_paper':'Compact paper ladder table, grouped by generation.',
        'legacy_check':'Current gen-1 core ladder counts, all-repeat versus latest-valid-per-cell.',
    }
    for k in tables:
        desc=descriptions.get(k,descriptions.get(k.removesuffix('_noesc'),k)+'; valid non-escaped runs' if k.endswith('_noesc') else k)
        lines.append(f'| `{k}` | {desc} |')
    lines += ['',
        '`fig_ladder.pdf` shows drift by rung. `fig_arms.pdf` compares loose planted drift and hidden-test passage, with escaped/incomplete labels. '
        '`fig_exposure.pdf` plots NoEsc unique tool calls against planted drift by rung, separating harnesses. `fig_domains.pdf` shows loose drift by domain. '
        'PDFs are vector graphics; matching PNGs are inspection copies. `older_report_excerpt.txt` is '
        'a local extraction for checking the earlier report. `headline.txt` gives generated current findings.','',
        '## Current snapshot and caveats','',
        f"The snapshot contains {meta['n_attempted']} ladder attempts, {meta['n_valid']} valid runs, "
        f"{meta['n_arms']} attempted arms, and {meta['n_tasks']} catalog tasks across {meta['n_domains']} domains. "
        f"The coverage note excludes {meta['n_excluded_seed_runs']} seed-task runs. Seed tasks appear nowhere in outcome tables.",
        f"Duplicate run_index groups in ladder data: {meta['duplicate_run_index_groups']}. "
        f"Arm/task cells with multiple valid runs: {len(repeated)}. Repeated indices across different tasks or arms are expected.",
        f"Ladder runs with NULL turns: {sum(r['null_turns'] for r in coverage_rows)}. "
        'Those are invalid even if an outcome row exists. `_degenerate_session` flags vendor cap notices and tiny '
        'init-only transcripts; this analysis honors stored errors and does not reinterpret trajectories.',
        'Missing runs are not clean runs. Coverage is unbalanced and collection is ongoing. '
        'Pooled generation rates can change with task and arm composition. Do not interpret an unmatched pooled '
        'difference as a causal model-generation effect. Wilson CIs can be optimistic with repeat dependence.']
    for r in coverage_rows:
        if r['tasks_covered'] < meta['n_tasks']:
            lines.append(f"- {r['label']} [{r['generation']}] covers {r['tasks_covered']} of {meta['n_tasks']} tasks "
                         f"with {r['valid']} valid runs and {r['invalid']} invalid attempts.")
    for r in tables['generation_summary']:
        lines.append(f"- {r['generation']} visible passage is {r['visible_pass_count']} of {r['n']} and intent passage "
                     f"is {r['intent_pass_count']} of {r['n']}. Near-perfect passage creates ceiling effects; "
                     'a zero empirical bootstrap gap interval does not establish zero population risk.')
    lines += ['',
        'The older `deliverables/1-intent-drift-full-report.pdf` mixes latest-cell summaries with an executed-run '
        'headline and includes a domain table whose pooled counts do not have the same scope as its gen-1 abstract. '
        'Do not reuse that executed-run total as the gen-1 valid ladder denominator. `legacy_check` recomputes '
        'the gen-1 core ladder with all valid runs and with latest valid run per cell, so changes in weighting are visible. '
        'Its central loose-rung pattern can be compared with the extracted report text, but the earlier PDF is '
        'not the source for any empirical number emitted here. The older report calls intent passage hidden tests '
        'plus rubric; the current scorer only runs the hidden oracle. It also calls the diff an AST metric; '
        'the actual comparison is function-source text. These distinctions matter for the paper.',
        'The vague-rung no-drift claim must be checked anew each rerun. A positive observed vague count refutes '
        'a blanket zero-drift statement. Increased deduplicated calls measure recorded tool use; actual file reads are audited separately. The generated headline states the observed contrast without forcing a hypothesis.',
        '', '## Macro reference','',
        'Generated on every rerun. Each row documents one command in `out/macros.tex`. '
        'Missing statistics expand to `--`. Proportion raw commands use units in [0,1]; `Pct` commands '
        'use percent or percentage points as their description states. `Frac` commands are count of denominator. '
        'The concise `Gone...` and `Gtwo...` aliases cover pooled ladder headlines. '
        'Short snapshot aliases are `NAttempts`, `NValid`, `NInvalid`, `NArms`, `NArmsGone`, `NArmsGtwo`, `NTasks`, `NDomains`, `NGoneValid`, and `NGtwoValid`. '
        '`NArms` counts arms with at least one valid ladder run. `LooseGone...` and `LooseGtwo...` aliases use clean model stems and suffixes `Frac`, `Pct`, and `MeanUnreq`. '
        '`NLooseZeroDriftArms...` excludes arms without loose observations. `NLooseMcNemarHolmSignificant...` uses the existing global Holm family across both contrasts and generations. '
        'Every p-value command has a `Fmt` alias in math mode with two significant figures. A Monte Carlo permutation floor renders as a strict power-of-ten bound. '
        'The arm plot prints every loose sample count and uses hollow gray markers when that count is below the low-coverage display threshold. '
        '`out/writer_macro_names.txt` lists all aliases added for the writer, including every formatted p-value name. '
        '`NZeroDriftArmsGone` and `NZeroDriftArmsGtwo` require at least five valid loose runs; the older `NLooseZeroDriftArms...` aliases require only one. '
        '`NDiscordantLoose/Vague` counts scoped-clean/other-drift pairs, and `NReversedLoose/Vague` counts the opposite direction, from the selected binary pairs. '
        '`CrossGrok...`, `CrossKimi...`, and `CrossOpus...` fractions use earliest valid outcomes on shared loose tasks, rather than all-repeat means. '
        'Other names combine table, stable row identity, and field; numeric characters are spelled out.','',
        '| Command | Expansion | Meaning |','| --- | --- | --- |']
    lines += [f"| `\\{name}` | `{entry['latex']}` | {entry['description'].replace('|','/')} |" for name,entry in scalars.items()]
    (HERE/'README.md').write_text('\n'.join(lines)+'\n')


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--db',type=Path,default=ROOT/'db/results.db')
    parser.add_argument('--out',type=Path,default=OUT)
    args=parser.parse_args()
    out=args.out.resolve()
    if not out.is_relative_to(HERE):
        parser.error('Output must be inside paper2/analysis/')
    out.mkdir(parents=True,exist_ok=True)
    sys.dont_write_bytecode=True
    os.environ.setdefault('MPLCONFIGDIR',str(out/'.mplconfig'))
    tasks,seeds=task_catalog()
    rows,models,duplicates,metadata=read_snapshot(args.db,tasks,seeds)
    from audit_analysis import enrich_runs,add_tables,add_macros,documentation as audit_documentation,headlines as audit_headlines
    rows=enrich_runs(rows,ROOT)
    valid=[r for r in rows if r['valid']]
    tables={}
    tables['coverage'],tables['invalid_reasons'],tables['invalid_errors']=coverage(rows,models,tasks)
    arms=sorted(m['name'] for m in models if generation(m['name']))
    tables['main']=[dict(generation=generation(a),arm=a,label=label(a),**summary([r for r in valid if r['arm']==a])) for a in arms]
    tables['generation_summary']=[dict(generation=g,**summary([r for r in valid if r['generation']==g])) for g in GENERATIONS]
    tables['ladder_generation']=[dict(generation=g,rung=v,**summary([r for r in valid if r['generation']==g and r['rung']==v])) for g in GENERATIONS for v in RUNGS]
    tables['ladder_arm']=[dict(generation=generation(a),arm=a,label=label(a),rung=v,**summary([r for r in valid if r['arm']==a and r['rung']==v])) for a in arms for v in RUNGS]
    loose=[r for r in valid if r['rung']=='loose']
    for name,field in [('suite_loose','suite'),('domain_loose','domain')]:
        tables[name]=[dict(generation=gen,**{field:value},**summary([r for r in loose if r['generation']==gen and r[field]==value]))
                      for gen in GENERATIONS for value in sorted({t[field] for t in tasks.values()})]
    tables['paired_tests'],tables['paired_cells'],selected=paired_tests(valid)
    tables['overall_tests']=omnibus(selected)
    tables['exposure']=exposure(valid)
    tables['disagreement']=disagreement(valid)
    tables['cross_generation'],tables['cross_generation_cells']=cross_generation(valid)
    tables['repeated_cells']=[dict(arm=arm,label=label(arm),task=task,n=len(rr),
                                     run_indices=', '.join(str(r['run_index']) for r in rr))
                              for (arm,task),rr in grouped(valid,('arm','task')) if len(rr)>1]
    tables['duplicate_run_index']=duplicates
    tables['task_catalog']=[dict(t,valid_runs=sum(r['task']==slug for r in valid),
                                    arms_covered=len({r['arm'] for r in valid if r['task']==slug})) for slug,t in sorted(tasks.items())]
    core=[r for r in valid if r['generation']=='gen-1' and r['suite']=='core']
    latest={}
    for r in sorted(core,key=lambda r:(r['run_index'],r['id'])):
        latest[r['arm'],r['task']]=r
    tables['legacy_check']=[dict(method=method,rung=rung,**summary([r for r in rr if r['rung']==rung]))
                            for method,rr in [('all valid runs',core),('latest valid per cell',list(latest.values()))] for rung in RUNGS]
    add_tables(tables,valid,tasks,sys.modules[__name__])
    metadata['audit_code_sha256']=hashlib.sha256(b''.join((HERE/name).read_bytes() for name in ('analyze.py','audit_analysis.py','trajectory_audit.py','scope_audit.py'))).hexdigest()
    metadata['measurement_sha256']=hashlib.sha256(json.dumps(tables['run_evidence'],sort_keys=True).encode()).hexdigest()
    # Per-arm, per-suite, per-domain and cross-generation results use the same
    # non-escaped population as the headline results.
    noesc=[r for r in valid if r['non_escaped']]
    tables['main']=[dict(generation=generation(a),arm=a,label=label(a),**summary([r for r in noesc if r['arm']==a])) for a in arms]
    tables['ladder_arm']=[dict(generation=generation(a),arm=a,label=label(a),rung=v,**summary([r for r in noesc if r['arm']==a and r['rung']==v])) for a in arms for v in RUNGS]
    loose=[r for r in noesc if r['rung']=='loose']
    for name,field in [('suite_loose','suite'),('domain_loose','domain')]:
        tables[name]=[dict(generation=gen,**{field:value},**summary([r for r in loose if r['generation']==gen and r[field]==value]))
                      for gen in GENERATIONS for value in sorted({t[field] for t in tasks.values()})]
    tables['paired_tests'],tables['paired_cells'],_=paired_tests(noesc)
    tables['cross_generation'],tables['cross_generation_cells']=cross_generation(noesc)
    paper_tables(tables)
    for name,table in tables.items():
        table_write(name,table,out)
        if name.startswith('tab_'):
            write_paper_fragment(name,table,out)
    scalars=add_macros(macros_for(tables,metadata),tables,metadata,models,valid,sys.modules[__name__])
    results=dict(metadata=metadata,tables=tables,scalars=scalars)
    (out/'results.json').write_text(json.dumps(results,indent=2,sort_keys=True,allow_nan=False)+'\n')
    (out/'macros.tex').write_text('\n'.join('\\newcommand{\\'+name+'}{'+entry['latex']+'}' for name,entry in scalars.items())+'\n')
    short_names={'NAttempts','NValid','NInvalid','NArms','NArmsGone','NArmsGtwo','NTasks','NDomains','NGoneValid','NGtwoValid'}
    writer_names=[name for name in scalars if name in short_names or name.endswith(('Fmt','NoEsc')) or name.startswith(('Gone','Gtwo','NEscaped','NTrajectory','Snapshot','NConfigs','NTestCmd','NScopedPrompt','NLoosePrompt','NVaguePrompt')) or
                  name.startswith(('NLoose','LooseMcNemarHolmSignificant','NHolm','NDiscordant','NReversed','NZeroDriftArms','SuiteGtwo','CrossGrok','CrossKimi','CrossOpus')) or
                  re.fullmatch(r'(Gone|Gtwo)(Loose|Scoped|Vague)DriftCi(Low|High)Pct',name) or
                  (name.startswith(('LooseGone','LooseGtwo')) and name.endswith(('Frac','Pct','MeanUnreq')))]
    (out/'writer_macro_names.txt').write_text('\n'.join('\\'+name for name in writer_names)+'\n')
    older=report_excerpt(out)
    headlines=[f"Valid ladder runs: {metadata['n_valid']} of {metadata['n_attempted']} attempts."]
    for gen in GENERATIONS:
        rr=[r for r in tables['ladder_generation'] if r['generation']==gen and r['n']]
        for r in sorted(rr,key=lambda r:RUNGS.index(r['rung'])):
            headlines.append(f"{gen} {r['rung']}: drift {r['drift_count']}/{r['n']} ({100*r['drift_rate']:.1f}%), "
                             f"hidden pass {r['intent_pass_count']}/{r['n']}, mean unique tool calls {r['mean_turns']:.2f}.")
        dis=next((r for r in tables['disagreement'] if r.get('scope')=='generation' and r.get('generation')==gen),None)
        if dis:
            headlines.append(f"{gen}: {dis['drifted_intent_pass']} planted-drifted runs still passed hidden tests; "
                             f"{dis['drifted_intent_fail']} failed hidden tests among {dis['drifted']} drifted runs.")
        exp=next((r for r in tables['exposure'] if r['scope']=='generation' and r['generation']==gen),None)
        if exp and exp['turn_difference'] is not None:
            headlines.append(f"{gen} Cursor-only matched vague minus scoped unique tool calls: {exp['turn_difference']:.2f} "
                             f"[{exp['turn_difference_ci_low']:.2f}, {exp['turn_difference_ci_high']:.2f}]; "
                             f"drift difference {100*exp['drift_difference']:.1f} percentage points.")
    for r in tables['overall_tests']:
        if r['p_value'] is not None:
            headlines.append(f"{r['generation']} omnibus Q={r['statistic_q']:g}, domain-permutation p={r['p_value']:.5g}, "
                             f"complete blocks={r['n_blocks']}, domains={r['n_domains']}.")
    headlines+=audit_headlines(tables)
    (out/'headline.txt').write_text('\n'.join(headlines)+'\n')
    write_readme(tables,metadata,scalars,duplicates,older)
    readme=HERE/'README.md'
    text=readme.read_text()
    findings='## Observed findings\n\n'+'\n\n'.join(headlines)+'\n\n'
    for exp in tables['exposure']:
        if exp['scope']=='generation' and exp['turn_difference'] is not None:
            support='supports increased recorded tool use' if exp['turn_difference_ci_low']>0 else 'does not establish increased recorded tool use'
            findings+=f"The matched {exp['generation']} vague contrast {support}. Actual file-read exposure is reported separately in observed_exposure.csv.\n\n"
    findings+='The matched model comparisons do not establish a uniform generation improvement. See task-paired intervals, model-ID reuse, incomplete coverage, and harness changes before making a generation claim.\n\n'
    text=text.replace('## Current snapshot and caveats',findings+'## Current snapshot and caveats')
    text=text.replace('## Macro reference',audit_documentation(tables,metadata)+'\n## Macro reference')
    readme.write_text(text)
    from plots import make_figures
    make_figures(tables,out)
    print('\n'.join(headlines))
    print(f'Wrote {len(tables)} table pairs and {len(scalars)} macros to {out}')


if __name__=='__main__':
    main()
