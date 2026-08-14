#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Full 7-dimension batch scoring test on the 15 jobs."""
import json, sys, os
os.chdir(r'E:\Trae CN\AI-Kart-Live\job-tracker')
sys.path.insert(0, '.')
from batch_score_v2 import process_job

DATA = r'E:\Trae CN\AI-Kart-Live\执行方案\爬虫结果_20260809\jobs_ai_agent_with_jd.json'
with open(DATA, encoding='utf-8') as f:
    jobs = json.load(f)['data']

results = [process_job(j) for j in jobs]
dev = [r for r in results if r.get('type') == 'dev']
active = [r for r in dev if not r.get('veto')]
vetoed = [r for r in dev if r.get('veto')]
active.sort(key=lambda x: x.get('total_score', 0), reverse=True)

print("=" * 80)
print(f"7维打分结果: 总计{len(jobs)} | dev{len(dev)} | veto{len(vetoed)} | active{len(active)}")
print("=" * 80)
for i, r in enumerate(active, 1):
    jd = r.get('score_jd_match', 0)
    lb = r.get('location_bonus', 0)
    cov = r.get('jd_match_coverage', 0)
    dmg = r.get('jd_match_hard_damage', [])
    gaps = r.get('jd_match_gaps', [])
    scores = f"{r['score_hard']}+{r['score_project']}+{r['score_level']}+{r['score_salary']}+{r['score_scale']}+{r['score_growth']}+{jd}+{lb}"
    print(f"{i}. [{r['verdict']}] total={r['total_score']} ({scores}) | cov={cov:.0%}{' dmg='+str(dmg) if dmg else ''}{' gap='+str(gaps) if gaps else ''}")
    print(f"   {r['title'][:50]} | {r['company'][:25]} | {r['salary']} | {r['location']}")
    if r.get('growth_potential'):
        print(f"   前景: {r['growth_potential']}")
    print()

if vetoed:
    print("否决:")
    for r in vetoed:
        print(f"  [{r.get('veto','?')}] {r['title'][:50]} | {r['salary']}")
