#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Test 7-dim scoring - write results to file to avoid terminal encoding issues."""
import os, sys, json, io

os.chdir(r'E:\Trae CN\AI-Kart-Live\job-tracker')
sys.path.insert(0, '.')

# Find data file
BASE = r'E:\Trae CN\AI-Kart-Live'
src = None
for root, dirs, files in os.walk(BASE):
    dirs[:] = [d for d in dirs if d not in ('.git','node_modules','__pycache__','.venv','venv')]
    for f in files:
        if f == 'jobs_ai_agent_with_jd.json':
            src = os.path.join(root, f)
            break
    if src: break

with open(src, 'r', encoding='utf-8') as f:
    raw = json.load(f)
jobs = raw.get('data', [])

# Monkey-patch process_job to use jd_full
from batch_score_v2 import process_job
from jd_matcher import match_jd

# Test: run match_jd with jd_full as jd_text on first dev job
out_lines = []
for i, job in enumerate(jobs):
    title = job.get('title', '')
    jd_full = job.get('jd_full', '')
    req = job.get('requirements', '')
    combined_jd = f"{jd_full}\n{req}"

    # Classify
    from batch_score_v2 import categorize
    jt = categorize(title, job.get('salary',''), job.get('experience','') or '')

    out_lines.append(f"Job {i+1}: type={jt} | {title}")

    if jt == 'dev' and combined_jd.strip():
        result = match_jd(
            jd_text=combined_jd,
            jd_title=title,
        )
        out_lines.append(f"  Verdict: {result['verdict']} | Score: {result['score']} | Coverage: {result['coverage']:.0%}")
        out_lines.append(f"  Hard damage: {result['hard_damage']}")
        out_lines.append(f"  Gaps: {result['gaps']}")
        out_lines.append(f"  Hits: {list(result['hits'].keys())}")
        if result['missing_must_have']:
            out_lines.append(f"  Missing must_have: {[m['skill'] for m in result['missing_must_have']]}")
        if result['interview_stories']:
            out_lines.append(f"  Stories: {[s['project'] for s in result['interview_stories']]}")
        out_lines.append(f"  Coverage detail: JD requires={result['coverage_detail'].get('jd_requires',[])}, You have={result['coverage_detail'].get('you_have',[])}, Miss={result['coverage_detail'].get('you_miss',[])}")
        out_lines.append("")

# Write to file
out_path = r'E:\Trae CN\AI-Kart-Live\job-tracker\test_output.txt'
with open(out_path, 'w', encoding='utf-8') as f:
    f.write('\n'.join(out_lines))

print(f"Done. Results written to: {out_path}")
print(f"Lines: {len(out_lines)}")
# Print first few lines to confirm
for line in out_lines[:5]:
    # Replace chars that might crash GBK
    safe = line.encode('ascii', errors='replace').decode('ascii')
    print(safe)
