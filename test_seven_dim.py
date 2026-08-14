#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Test 7-dimension scoring by walking workspace, finding scraped data, and running batch_score_v2."""

import os, sys, json

# Ensure we're in the job-tracker directory
os.chdir(r'E:\Trae CN\AI-Kart-Live\job-tracker')
sys.path.insert(0, '.')

# Step 1: Walk workspace to find scraped JSON files
BASE = r'E:\Trae CN\AI-Kart-Live'
json_files = []
for root, dirs, files in os.walk(BASE):
    # Skip large irrelevant dirs
    dirs[:] = [d for d in dirs if d not in ('.git', 'node_modules', '__pycache__', '.venv', 'venv')]
    for f in files:
        if f.endswith('.json') and 'job' in f.lower():
            fp = os.path.join(root, f)
            sz = os.path.getsize(fp)
            if sz > 1000:  # Skip placeholder files
                json_files.append((fp, sz))

json_files.sort(key=lambda x: x[1], reverse=True)
print("Found JSON files:")
for fp, sz in json_files:
    print(f"  {sz:>8}B  {fp}")

if not json_files:
    print("ERROR: No data files found!")
    sys.exit(1)

# Step 2: Load the largest file (has JD body text)
src = json_files[0][0]
print(f"\nLoading: {src}")
with open(src, 'r', encoding='utf-8') as f:
    raw = json.load(f)

jobs = raw.get('data', [])
print(f"Total jobs in file: {len(jobs)}")

# Step 3: Import and run
from batch_score_v2 import process_job

# Process first 20 jobs
test_count = min(20, len(jobs))
print(f"\nProcessing first {test_count} jobs...\n")

results = []
for i, job in enumerate(jobs[:test_count]):
    try:
        r = process_job(job)
        results.append(r)
    except Exception as e:
        print(f"  ERROR on job {i+1}: {e}")
        import traceback
        traceback.print_exc()

# Separate by type
dev_results = [r for r in results if r.get('type') == 'dev']
vetoed = [r for r in dev_results if r.get('veto')]
active = [r for r in dev_results if not r.get('veto')]
skipped = [r for r in results if r.get('skipped')]

# Sort active by total score descending
active.sort(key=lambda x: x.get('total_score', 0), reverse=True)

print("=" * 80)
print("RESULTS SUMMARY")
print("=" * 80)
print(f"  Total processed: {len(results)}")
print(f"  Dev jobs: {len(dev_results)}")
print(f"  Vetoed: {len(vetoed)}")
print(f"  Active dev: {len(active)}")
print(f"  Skipped (irrelevant): {len(skipped)}")
print()

# Show TOP 15 active dev
print("=" * 80)
print(f"TOP {min(15, len(active))} ACTIVE DEV JOBS (7-dimension scoring)")
print("=" * 80)
for i, r in enumerate(active[:15], 1):
    loc_bonus = r.get('location_bonus', 0)
    jd_score = r.get('score_jd_match', 0)
    coverage = r.get('jd_match_coverage', 0)
    damage = r.get('jd_match_hard_damage', [])
    gaps = r.get('jd_match_gaps', [])

    # Score breakdown: ①+②+③+④+⑤+⑥+⑦+目标城市
    scores = f"{r['score_hard']}+{r['score_project']}+{r['score_level']}+{r['score_salary']}+{r['score_scale']}+{r['score_growth']}+{jd_score}+{loc_bonus}"

    print(f"{i:2}. [{r['verdict']:6}] {r['title'][:42]:42} | {r['company'][:18]:18}")
    print(f"    七维: {scores} = {r['total_score']} | 薪资: {r['salary']:15} | 地点: {r['location']:10}")
    print(f"    JD匹配: 覆盖{coverage:.0%} 得分{jd_score}", end="")
    if damage:
        print(f" 硬伤:{damage}", end="")
    if gaps:
        print(f" 缺口:{gaps}", end="")
    print()
    if r.get('growth_potential'):
        print(f"    前景: {r['growth_potential']}")
    print()

# Show vetoed
if vetoed:
    print("=" * 80)
    print(f"VETOED ({len(vetoed)})")
    print("=" * 80)
    for r in vetoed:
        print(f"  [{r.get('veto','?')}] {r['title'][:45]} | {r['company'][:20]} | {r['salary']:12}")

# Step 4: JD matcher quick test on a sample
print("\n" + "=" * 80)
print("JD MATCHER DIRECT TEST (first dev job)")
print("=" * 80)
if dev_results:
    from jd_matcher import quick_match
    first = dev_results[0]
    # Use the raw job data to get JD body text
    raw_job = jobs[0]
    jd_body = raw_job.get('jd_body', raw_job.get('description', ''))
    jd_title = raw_job.get('title', '')
    jd_text = f"{jd_title} {jd_body}" if jd_body else jd_title
    print(f"Job: {jd_title}")
    if jd_body:
        print(f"JD body length: {len(jd_body)} chars")
        print(f"JD preview: {jd_body[:200]}...")
    print()
    print(quick_match(jd_text, jd_title))
