#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Quick test: run jd_matcher on the 15 jobs from jobs_ai_agent_with_jd.json"""
import json, sys, os
os.chdir(r'E:\Trae CN\AI-Kart-Live\job-tracker')
sys.path.insert(0, '.')
from jd_matcher import match_jd

DATA = r'E:\Trae CN\AI-Kart-Live\执行方案\爬虫结果_20260809\jobs_ai_agent_with_jd.json'
with open(DATA, encoding='utf-8') as f:
    jobs = json.load(f)['data']

results = []
for j in jobs:
    title = j.get('title','')
    jd_text = j.get('jd_full','') + '\n' + j.get('requirements','')
    r = match_jd(jd_text=jd_text, jd_title=title)
    results.append((j, r))
    v = r['verdict']
    s = r['score']
    cov = r['coverage']
    dmg = r['hard_damage']
    gaps = r['gaps']
    hits = list(r['hits'].keys())
    print(f"[{v:11}] score={s:3} cov={cov:.0%} dmg={dmg} hits={len(hits)}{' GAP:'+str(gaps) if gaps else ''} | {title}")

# Summary
dev_jobs = [x for x in results if 'Agent' in x[0].get('title','') or '工程师' in x[0].get('title','') or '开发' in x[0].get('title','')]
vetoed = [x for x in results if x[1]['verdict'] == 'veto']
weak = [x for x in results if x[1]['verdict'] == 'weak_match']
print(f"\n总计:{len(results)} veto:{len(vetoed)} weak:{len(weak)} strong:{sum(1 for x in results if x[1]['verdict']=='strong_match')} match:{sum(1 for x in results if x[1]['verdict']=='match')}")
