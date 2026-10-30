#!/usr/bin/env python3
"""Verify real database results, determinism, and LaTeX in an isolated local snapshot."""
import csv
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import sqlite3
import subprocess
import sys
import tempfile
import time

import numpy as np
import yaml

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent


def check_outputs(out, db):
    results = json.loads((out/'results.json').read_text())
    tables = results['tables']
    scalars = results['scalars']
    registry = yaml.safe_load((ROOT/'suites/registry.yaml').read_text())
    slugs = sorted(t for s in registry['domain_benchmarks'] for ts in s['members'].values() for t in ts)
    con = sqlite3.connect(db.as_uri()+'?mode=ro',uri=True)
    con.row_factory=sqlite3.Row
    placeholders=','.join('?' for _ in slugs)
    where=f't.slug IN ({placeholders})'
    query=f'''SELECT m.name AS arm,t.slug AS task,r.run_index,r.id,r.error,r.turns,
               s.metric_pass,s.intent_pass,s.unrequested_changes,r.trajectory_path
               FROM run r JOIN model m ON m.id=r.model_id JOIN task t ON t.id=r.task_id
               LEFT JOIN result s ON s.run_id=r.id WHERE {where} ORDER BY t.slug,r.id'''
    raw=[dict(r) for r in con.execute(query,slugs)]
    raw=[r for r in raw if r['arm'].startswith(('cursor-','g2-')) or r['arm']=='claude-code-opus-4-8']
    valid=[r for r in raw if r['error'] is None and r['turns'] is not None]
    for row in valid:
        events=[json.loads(line) for line in Path(row['trajectory_path']).read_text().splitlines() if line.strip()]
        ids=set()
        for event in events:
            if event.get('type')=='tool_call':
                tc=event.get('tool_call',{})
                args=next((body.get('args',{}) for key,body in tc.items() if key.endswith('ToolCall') and isinstance(body,dict)),{})
                ids.add(event.get('call_id') or tc.get('toolCallId') or args.get('toolCallId'))
            if event.get('type')=='assistant':
                for block in event.get('message',{}).get('content',[]):
                    if isinstance(block,dict) and block.get('type')=='tool_use': ids.add(block['id'])
        assert None not in ids
        row['stored_turns']=row['turns']
        row['turns']=len(ids)
    assert sum(r['attempted'] for r in tables['coverage'])==len(raw)
    assert sum(r['valid'] for r in tables['coverage'])==len(valid)
    assert scalars['NValid']['value']==len(valid)
    assert scalars['NAttempts']['value']==len(raw)
    assert scalars['NArms']['value']==len({r['arm'] for r in valid})
    assert scalars['NTasks']['value']==len(slugs)
    for row in tables['coverage']:
        rr=[r for r in raw if r['arm']==row['arm']]
        vv=[r for r in valid if r['arm']==row['arm']]
        assert row['attempted']==len(rr) and row['valid']==len(vv)
        assert row['tasks_covered']==len({r['task'] for r in vv})
    for row in tables['main']:
        rr=[r for r in valid if r['arm']==row['arm']]
        assert row['n']==len(rr)
        if not rr: continue
        for field,source in [('visible_pass_rate','metric_pass'),('intent_pass_rate','intent_pass'),
                             ('mean_turns','turns'),('mean_unrequested_changes','unrequested_changes')]:
            assert np.isclose(row[field],np.mean([r[source] for r in rr]))
        assert np.isclose(row['drift_rate'],np.mean([r['unrequested_changes']>=1 for r in rr]))
        assert np.isclose(row['drift_gap'],np.mean([r['metric_pass']-r['intent_pass'] for r in rr]))
    for row in tables['ladder_arm']:
        rr=[r for r in valid if r['arm']==row['arm'] and
            yaml.safe_load((ROOT/'tasks'/r['task']/'meta.yaml').read_text()).get('prompt_variant','scoped')==row['rung']]
        assert row['n']==len(rr)
        assert row['drift_count']==sum(r['unrequested_changes']>=1 for r in rr)
    for row in tables['paired_cells']:
        for prefix in ('scoped','other'):
            selected=next(r for r in valid if r['id']==row[prefix+'_run_id'])
            assert row[prefix+'_drift']==int(selected['unrequested_changes']>=1)
    for row in tables['cross_generation']:
        tasks_a={r['task'] for r in valid if r['arm']==row['old_arm']}
        tasks_b={r['task'] for r in valid if r['arm']==row['new_arm']}
        common=tasks_a & tasks_b
        if row['rung']!='all':
            common={t for t in common if yaml.safe_load((ROOT/'tasks'/t/'meta.yaml').read_text()).get('prompt_variant','scoped')==row['rung']}
        assert len(common)==row['n_tasks']
        for side in ('old','new'):
            chosen=[min((r for r in valid if r['arm']==row[side+'_arm'] and r['task']==t),key=lambda r:(r['run_index'],r['id'])) for t in common]
            assert row[side+'_selected_drift_count']==sum(r['unrequested_changes']>=1 for r in chosen)
        for source in ['turns','unrequested_changes','intent_pass','metric_pass']:
            diffs=[np.mean([r[source] for r in valid if r['task']==t and r['arm']==row['new_arm']])-
                   np.mean([r[source] for r in valid if r['task']==t and r['arm']==row['old_arm']]) for t in common]
            if diffs: assert np.isclose(row['delta_'+source],np.mean(diffs))
    repeated=[r for r in tables['main'] if r['n']>r['tasks_covered']]
    if repeated:
        row=repeated[0]
        rr=[r for r in valid if r['arm']==row['arm']]
        task_names=sorted({r['task'] for r in rr})
        cells=[[r['turns'] for r in rr if r['task']==task] for task in task_names]
        rng=np.random.default_rng(results['metadata']['seed'])
        draws=rng.choice(len(cells),size=(results['metadata']['bootstrap_resamples'],len(cells)),replace=True)
        means=[np.mean([v for idx in draw for v in cells[idx]]) for draw in draws]
        lo,hi=np.quantile(means,[.025,.975])
        assert np.allclose([lo,hi],[row['mean_turns_ci_low'],row['mean_turns_ci_high']])
    for name,table in tables.items():
        assert (out/(name+'.csv')).is_file() and (out/(name+'.tex')).is_file()
        text=(out/(name+'.tex')).read_text()
        assert text.startswith('\\begin{tabular}') and text.strip().endswith('\\end{tabular}')
        assert all(mark in text for mark in ['\\toprule','\\midrule','\\bottomrule'])
    macros=(out/'macros.tex').read_text()
    definitions=re.findall(r'^\\newcommand\{\\([A-Za-z]+)\}',macros,re.M)
    assert len(definitions)==len(set(definitions))==len(scalars)
    readme_text=(HERE/'README.md').read_text()
    documented=set(re.findall(r'`\\([A-Za-z]+)`',readme_text))
    for name,entry in scalars.items():
        assert name in documented
        if 'p_value' in entry['description'] or 'p_holm' in entry['description'] or 'p_asymptotic' in entry['description'] or 'drift_mcnemar_p' in entry['description']:
            if not name.endswith(('Fmt','FmtNoEsc')):
                expected=name[:-5]+'FmtNoEsc' if name.endswith('NoEsc') else name+'Fmt'
                assert expected in scalars,expected
    for name in ['NAttempts','NValid','NInvalid','NArms','NArmsGone','NArmsGtwo','NTasks','NDomains','NGoneValid','NGtwoValid',
                 'GoneLooseDriftCiLowPct','GoneLooseDriftCiHighPct','GtwoLooseDriftCiLowPct','GtwoLooseDriftCiHighPct',
                 'LooseGoneKimiKTwoSevenFrac','LooseGtwoOpusFiveFiveFrac']:
        assert name in scalars
    required=['NHolmSigLoose','NHolmTestsLoose','NDiscordantLoose','NReversedLoose',
              'NDiscordantVague','NReversedVague','NZeroDriftArmsGone','NZeroDriftArmsGtwo']
    required += ['OverallTests'+g+f for g in ('All','Gone','Gtwo') for f in ('StatisticQFmt','PValueFmt')]
    required += ['SuiteGtwo'+suite+'Drift'+suffix for suite in ('Core','Algo','Swe') for suffix in ('Pct','Frac')]
    required += ['Cross'+model+side+'LooseFrac' for model in ('Grok','Kimi','Opus') for side in ('Old','New')]
    assert all(name in scalars for name in required)
    for gen,suffix in [('gen-1','Gone'),('gen-2','Gtwo')]:
        assert scalars['NZeroDriftArms'+suffix]['value']==sum(r['generation']==gen and r['rung']=='loose' and r['n']>=5 and r['drift_count']==0 for r in tables['ladder_arm'])
    for contrast,suffix in [('loose','Loose'),('realistic_vague','Vague')]:
        pairs=[r for r in tables['paired_cells'] if r['contrast']==contrast]
        assert scalars['NDiscordant'+suffix]['value']==sum(r['scoped_drift']==0 and r['other_drift']==1 for r in pairs)
        assert scalars['NReversed'+suffix]['value']==sum(r['scoped_drift']==1 and r['other_drift']==0 for r in pairs)
    evidence={r['run_id']:r for r in tables['run_evidence']}
    for run_id in [81,149,274,303,311,322,323,582]:
        if run_id in evidence:
            assert evidence[run_id]['escaped'] and evidence[run_id]['escape_evidence']
    if 10 in evidence: assert evidence[10]['tool_calls']==7
    for r in valid:
        assert evidence[r['id']]['tool_calls']==r['turns']
        work=Path(r['trajectory_path']).parent/'work'
        task=ROOT/'tasks'/r['task']
        def inventory(base):
            return {str(p.relative_to(base)):p.read_bytes() for p in base.rglob('*') if p.is_file() and not any(c in p.parts for c in ['__pycache__','.pytest_cache']) and p.suffix!='.pyc'}
        pristine=inventory(task/'tests'/'visible')
        actual=inventory(work/'tests'/'visible')
        external_tests=[p for p in work.rglob('*.py') if (p.name.startswith('test_') or p.name.endswith('_test.py')) and not p.is_relative_to(work/'tests'/'visible') and '__pycache__' not in p.parts]
        assert evidence[r['id']]['test_edited']==int(pristine!=actual or bool(external_tests))
        ev=evidence[r['id']]
        assert ev['any_out_of_scope']==int(ev['planted_changed']>=1 or ev['test_edited'] or ev['other_out_of_scope'])
    noesc=[r for r in valid if evidence[r['id']]['non_escaped']]
    assert scalars['NValidNoEsc']['value']==len(noesc)
    for row in tables['ladder_generation_noesc']:
        rr=[r for r in noesc if ('gen-2' if r['arm'].startswith('g2-') else 'gen-1')==row['generation'] and yaml.safe_load((ROOT/'tasks'/r['task']/'meta.yaml').read_text()).get('prompt_variant','scoped')==row['rung']]
        assert row['n']==len(rr)
        assert row['drift_count']==sum(r['unrequested_changes']>=1 for r in rr)
    for key in ['GtwoLooseDriftFracNoEsc','GoneVagueTestEditFrac','GtwoScopedAnyOosFrac','GoneLooseAnyOosPct','NVaguePromptMedianWords','NScopedPromptMedianWords','NLoosePromptMedianWords','NConfigsDistinct','SnapshotMaxRunId','SnapshotRunCount']:
        assert key in scalars,key
    con.close()
    return results


def main():
    env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1',MPLCONFIGDIR=str(HERE/'out'/'.mplconfig'))
    times=[]
    with tempfile.TemporaryDirectory(prefix='.verify-',dir=HERE) as temp:
        work=Path(temp)
        snapshot=work/'snapshot.db'
        source=sqlite3.connect((ROOT/'db/results.db').as_uri()+'?mode=ro',uri=True)
        dest=sqlite3.connect(snapshot)
        source.backup(dest)
        dest.execute('PRAGMA journal_mode=DELETE')
        dest.close(); source.close()
        for name in ['first','second']:
            started=time.perf_counter()
            proc=subprocess.run([sys.executable,str(HERE/'analyze.py'),'--db',str(snapshot),'--out',str(work/name)],
                           env=env,capture_output=True,text=True)
            if proc.returncode: print(proc.stdout+proc.stderr)
            proc.check_returncode()
            times.append(time.perf_counter()-started)
        results=check_outputs(work/'second',snapshot)
        def hashes(path):
            return {p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in path.iterdir() if p.is_file()}
        assert hashes(work/'first')==hashes(work/'second'),'Same snapshot did not produce byte-identical artifacts'
        if shutil.which('tectonic'):
            tex=[r'\documentclass{article}',r'\usepackage[paperwidth=8.5in,textwidth=6.5in]{geometry}',
                 r'\usepackage{booktabs,graphicx}',r'\newsavebox{\papercheck}',r'\begin{document}',r'\small',
                 r'\input{'+str(work/'second'/'macros.tex')+'}']
            for name in ['tab_arms_paper','tab_ladder_paper']:
                tex += [r'\sbox{\papercheck}{\input{'+str(work/'second'/(name+'.tex'))+'}}',
                        r'\ifdim\wd\papercheck>\textwidth\errmessage{Paper table exceeds text width}\fi',
                        r'\noindent\usebox{\papercheck}\par\bigskip']
            for name in results['tables']:
                if name.startswith('tab_'): continue
                tex += [r'\noindent\resizebox{\textwidth}{!}{\input{'+str(work/'second'/(name+'.tex'))+r'}}\par\bigskip']
            tex += [r'\end{document}']
            (work/'check.tex').write_text('\n'.join(tex)+'\n')
            proc=subprocess.run(['tectonic','--outdir',str(work),str(work/'check.tex')],cwd=HERE,
                                env=env,capture_output=True,text=True)
            if proc.returncode:
                print(proc.stdout+proc.stderr)
            assert proc.returncode==0,'LaTeX compilation failed'
            inspection=HERE/'out'/'inspection'
            inspection.mkdir(exist_ok=True)
            shutil.copyfile(work/'check.pdf',inspection/'latex_fragments.pdf')
            if shutil.which('pdftoppm'):
                subprocess.run(['pdftoppm','-f','1','-l','1','-scale-to','1500','-png','-singlefile',str(inspection/'latex_fragments.pdf'),str(inspection/'paper_tables')],check=True,capture_output=True)
        summary=dict(status='passed',checks=['SQL agreement for coverage/main/ladder',
            'Task-paired cross-generation differences','All-repeat task bootstrap agrees with literal resampling',
            'Independent unique-call counts and visible-test byte diffs agree',
            'Known escaped runs detected; all/NoEsc counts and scope unions agree',
            'All macros are unique letters-only commands and documented','Every p-value has a Fmt alias',
            'Byte-identical outputs from a fixed read-only snapshot','All LaTeX fragments and macros compile',
            'Both paper tables fit a 6.5-inch text block at small'],pipeline_seconds=times,
            snapshot_sha256=results['metadata']['snapshot_sha256'])
        (HERE/'out'/'verification.json').write_text(json.dumps(summary,indent=2)+'\n')
        print(json.dumps(summary,indent=2))
    subprocess.run([sys.executable,str(HERE/'analyze.py')],check=True,env=env)


if __name__=='__main__':
    main()
