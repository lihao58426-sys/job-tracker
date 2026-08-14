import os, sys, json

os.chdir(r'E:\Trae CN\AI-Kart-Live\job-tracker')
sys.path.insert(0, '.')

# Find by walking (avoiding bash encoding mangle of Chinese path)
src = None
for root, dirs, files in os.walk(r'E:\Trae CN\AI-Kart-Live'):
    for f in files:
        if f == 'jobs_ai_agent_full.json':
            src = os.path.join(root, f)
            break
    if src:
        break

if not src:
    print('File not found!')
    sys.exit(1)

print(f'Found: {src}')

with open(src, 'r', encoding='utf-8') as f:
    raw = json.load(f)
jobs = raw.get('data', [])

from batch_score_v2 import process_job

dev_results = []
vetoed = []
for job in jobs[:15]:
    r = process_job(job)
    if r.get('type') == 'dev':
        dev_results.append(r)
        if r.get('veto'):
            vetoed.append(r)

dev_results.sort(key=lambda x: (0 if x.get('veto') else 1, x.get('total_score', 0)), reverse=True)

print()
print('=' * 70)
print('七维打分测试 (前15条)')
print('=' * 70)
for i, r in enumerate(dev_results, 1):
    jd = r.get('score_jd_match', 0)
    lb = r.get('location_bonus', 0)
    cov = r.get('jd_match_coverage', 0)
    damage = r.get('jd_match_hard_damage', [])
    dmg = f' !!排除:{damage}' if damage else ''
    gaps = r.get('jd_match_gaps', [])
    gap_str = f' 缺口:{gaps}' if gaps else ''

    print(f'{i}. [{r["verdict"]}] {r["title"][:45]}')
    scores = f'{r["score_hard"]}+{r["score_project"]}+{r["score_level"]}+{r["score_salary"]}+{r["score_scale"]}+{r["score_growth"]}+{jd}+{lb}'
    print(f'   七维: {scores} = {r["total_score"]} | 覆盖{cov:.0%}{dmg}{gap_str}')
    print()

print(f'否决: {len(vetoed)}')
for r in vetoed:
    print(f'  [{r.get("veto","?")}] {r["title"][:40]}')
