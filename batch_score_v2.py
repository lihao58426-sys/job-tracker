#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
v2.0 打分流程：爬虫原始数据 → 分类 → 六维打分 → 发展前景 → 导入就绪
================================================================
"""

import json
import os
import re
import argparse
from typing import Optional
import sys

# JD 能力匹配引擎
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from jd_matcher import match_jd

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(SCRIPT_DIR, "..", "执行方案", "爬虫结果_20260809", "jobs_ai_agent_full.json")
OUT = os.path.join(SCRIPT_DIR, "import_ready_v2.json")

# ============================================================
# 配置：用户画像
# ============================================================
# 用户画像（隐私字段已脱敏为示例占位值，本地实际使用请改回真实策略）
USER_PROFILE = {
    "years_exp": 1,                    # 示例：工作年限
    "target_role": "AI开发/AI Agent工程师",
    "skills": ["Python", "FastAPI", "React", "LangChain", "RAG", "SQLite", "Docker", "Vue3"],
    "projects": 6,                     # 示例：相关项目数
    "target_cities": ["上海", "杭州"],   # 示例：目标城市
    "expected_salary_min": 15,         # 示例：期望月薪下限（K）
}

# 目标城市（示例占位值，本地使用请改回真实目标城市）
TARGET_CITIES = ["上海", "杭州"]

# 六维权重说明（不做加权，仅做评分参考）
# ① 硬能力匹配度：JD要求的技能 vs 用户技能栈
# ② 项目经验契合度：行业/业务 vs AI项目经验
# ③ 经验层级适配度：JD 要求年限 vs 候选者经验
# ④ 薪资期望适配度：按 v2.0 rubric
# ⑤ 企业规模适配度：公司规模 vs 新人友好度
# ⑥ 成长空间适配度：公司赛道/技术方向的前景


def parse_salary_min(salary_str: str) -> int:
    """解析薪资下限（K/月）。支持日薪/时薪转换。"""
    s = salary_str.strip().lower()
    # 日薪：200-250元/天 → 转月薪 (日薪 × 22天 / 1000)
    day_match = re.match(r'(\d+)\s*-\s*(\d+)\s*元/天', s)
    if day_match:
        return int(int(day_match.group(1)) * 22 / 1000)
    # 时薪：30-50元/时 → 转月薪 (时薪 × 8时 × 22天 / 1000)
    hour_match = re.match(r'(\d+)\s*-\s*(\d+)\s*元/时', s)
    if hour_match:
        return int(int(hour_match.group(1)) * 8 * 22 / 1000)
    # 去掉 14薪/15薪等
    s = re.sub(r'·\d+薪', '', s).strip()
    # 提取 K 制数字
    m = re.match(r'(\d+)\s*-\s*(\d+)', s)
    if m:
        return int(m.group(1))
    return 0


def fix_location(location: str, company: str) -> str:
    """修正爬虫数据中异常的城市字段。
    例如 company="清闲智能创新(深圳)有限公司" location="Rust方向"
    → 从公司名提取城市 → "深圳"
    """
    loc = location.strip()
    # 已知城市列表（中国主要城市）
    KNOWN_CITIES = [
        "深圳", "广州", "北京", "上海", "杭州", "苏州", "西安",
        "长沙", "武汉", "南京", "成都", "重庆", "天津", "合肥",
        "郑州", "厦门", "福州", "青岛", "大连", "温州",
    ]
    # 如果 location 包含已知城市 → 正常
    if any(c in loc for c in KNOWN_CITIES):
        return loc
    # 从公司名提取
    for city in KNOWN_CITIES:
        if city in company:
            return city
    return loc


def salary_score(min_k: int, salary_str: str, title: str = "", jd_text: str = "") -> int:
    """v2.2 薪资打分
    title: 岗位标题，用于从标题中补充福利信号（如双休）。
    jd_text: JD正文，预留接口。
    """
    if min_k == 0:
        return 5  # 面议/未知，默认中间值
    if min_k < 10:
        return -1  # 一票否决

    # 基础分（v3.0: 30K以上加速递减——市场惯性：高薪岗=高经验门槛）
    if min_k < 12:
        base = 7          # 10-12K：偏低但可接受
    elif min_k <= 18:
        base = 9          # 12-18K：最佳区间
    elif min_k <= 25:
        base = 8          # 18-25K：微幅上探
    elif min_k <= 30:
        base = 7          # 25-30K：上探区，竞争开始激烈
    elif min_k <= 40:
        base = 5          # 30-40K：明显溢价，通常要3-5年经验
    elif min_k <= 50:
        base = 3          # 40-50K：高位区，高级/资深岗
    else:
        base = 1          # 50K+：基本不抱期望

    # 福利修正（从 salary_str 和 jd_text 中提取）
    combined = salary_str + " " + title + " " + jd_text

    # 加分项
    if any(tag in combined for tag in ["14薪", "15薪", "16薪", "13薪"]):
        base = min(base + 1, 10)
    if "双休" in combined:
        base = min(base + 1, 10)
    if "公积金全额" in combined or "全额公积金" in combined or "全额缴纳" in combined:
        base = min(base + 1, 10)
    if "弹性工作" in combined or "不打卡" in combined:
        base = min(base + 1, 10)

    # 扣分项
    if "大小周" in combined:
        base = max(base - 1, 1)
    if "单休" in combined:
        base = max(base - 2, 1)
    if "996" in combined or "加班" in combined:
        base = max(base - 1, 1)
    if any(tag in combined for tag in ["五险一金不全", "试用期不缴社保", "不缴公积金"]):
        base = max(base - 2, 1)

    return base


def is_salary_negotiable(salary_str: str) -> bool:
    """判断是否薪资面议"""
    s = salary_str.strip().lower()
    if not s:
        return True
    return any(kw in s for kw in ["面议", "面谈", "open", "negotiable", "薪资可谈"])


IRRELEVANT_KEYWORDS = [
    "财务经理", "财务主管", "营业员", "前台", "客服", "销售经理", "销售代表",
    "行政专员", "行政助理", "出纳", "会计", "人事专员", "HR实习生",
    "招聘专员", "司机", "保安", "保洁", "厨师", "服务员", "店员",
    "市场推广", "地推", "电话销售", "保险", "房产中介",
]


def categorize(title: str, salary: str, exp: str) -> str:
    """岗位分类：dev / pm / architect / other / irrelevant"""
    t = title.lower()
    # 排除明显无关
    if any(kw in t for kw in IRRELEVANT_KEYWORDS):
        return "irrelevant"
    # 架构师
    if "架构师" in t:
        return "architect"
    # 产品经理
    if "产品经理" in t or "产品岗" in t or "产品工程师" in t:
        return "pm"
    # 实习（非应届实习岗归为 other）
    if "实习" in t:
        return "other"
    # 高级/资深/应届 → 全归 dev
    if any(kw in t for kw in ["开发", "工程师", "工程", "engineer", "全栈", "应用", "应届"]):
        return "dev"
    if "agent" in t and "产品" not in t:
        return "dev"
    # 默认
    return "other"


def check_veto(title: str, edu: str, exp: str, salary_str: str) -> Optional[str]:
    """一票否决检查。返回否决原因，不否决返回 None。"""
    t = title.lower()
    e = exp.strip().lower()
    ed = edu.strip().lower()

    # 1. 仅限2026应届/当年校招 → 否决（非应届生不能投）
    if any(kw in t for kw in ["仅限2026应届", "仅限当年校招", "2026届应届", "26届应届"]):
        return f"仅限应届/校招: {title}"

    # 2. 纯"硕士"硬性要求 → 否决（不含"及以上""优先""本科及以上"）
    if "硕士" in ed:
        if not any(soft in ed for soft in ["及以上", "优先", "本科及以上", "本科及"]):
            return f"硬性硕士要求: {edu}"

    # 3. 经验硬性要求 >= 5年 → 否决（不含"3-5年""5年以下"）
    if any(pat in e for pat in ["5-10年", "5年以上", "5年及以上", "5-10", "5年以上"]):
        return f"经验要求过高: {exp}"

    # 4. 薪资 < 10K → 否决
    min_k = parse_salary_min(salary_str)
    if min_k > 0 and min_k < 10:
        return f"薪资下限过低: {salary_str}"

    return None


def score_hard_skills(title: str, exp: str, company: str) -> int:
    """① 硬能力匹配度：看岗位对技术栈的要求"""
    t = title.lower()
    score = 5  # 起点
    # 应届生友好 → 门槛低
    if "应届生优先" in t or "应届生友好" in t or "应届" in t:
        score += 1
    # Agent 相关的岗位，用户有 LangChain/RAG 项目经验
    if "agent" in t or "智能体" in t:
        score += 2
    if "rag" in t or "大模型" in t:
        score += 1
    if "python" in t:
        score += 1
    if "全栈" in t or "fullstack" in t or "full stack" in t:
        score += 1
    if "应用" in t:
        score += 1
    if "应届" in t or "实习" in t:
        score += 1

    # 高级/资深标签 → 默认扣分，但应届友好/经验不限的豁免
    is_senior = "高级" in t or "资深" in t or "senior" in t.lower()
    is_junior_friendly = "应届" in t or "经验不限" in exp or "不限" in exp
    if is_senior and not is_junior_friendly:
        score -= 2
    if "架构" in t:
        score -= 2
    if "硕士" in t:
        score -= 1

    # Rust/C++ 按核心程度扣分
    if "rust方向" in t.lower() or "c++开发" in t:
        score -= 2  # 核心刚需
    elif "rust" in t.lower() and "方向" not in t.lower():
        score -= 1  # 附属技术栈
    elif "c++" in t and "开发" not in t:
        score -= 1

    return max(1, min(score, 10))


# 传统行业列表（可被数字化岗豁免）
TRADITIONAL_INDUSTRIES = [
    "医疗器械", "装饰装修", "批发/零售", "机械/设备", "医疗机构",
    "整车制造", "咨询服务", "学术/科研",
]

# 高前景行业
HIGH_GROWTH_INDUSTRIES = [
    "互联网", "计算机软件", "IT服务", "科技金融",
    "云计算/大数据", "电子/半导体/集成电路",
]


def score_project_fit(title: str, industry: str, company: str) -> int:
    """② 项目经验契合度：业务方向与用户AI项目的匹配度"""
    score = 5
    t = title.lower()
    # Agent 方向 → 直接命中用户的项目经验
    if "agent" in t or "智能体" in t:
        score += 3
    if "ai" in t and ("应用" in t or "工程师" in t):
        score += 2
    # 互联网/软件 → 行业匹配
    if industry in HIGH_GROWTH_INDUSTRIES:
        score += 1
    # 传统行业 → 扣分，但数字化岗豁免
    if industry in TRADITIONAL_INDUSTRIES:
        is_digital_role = any(kw in t for kw in ["ai", "agent", "数字化", "大模型", "智能", "数据"])
        if not is_digital_role:
            score -= 2  # 纯传统岗
        # 数字化岗不扣分（传统企业内部的 AI 部门）
    if "rag" in t or "大模型" in t:
        score += 1
    return max(1, min(score, 10))


def score_level_fit(exp: str, edu: str) -> int:
    """③ 经验层级适配度：JD 年限 vs 候选者经验"""
    exp_lower = exp.strip().lower()
    if "经验不限" in exp_lower or "不限" in exp_lower:
        return 9
    if "应届" in exp_lower or "实习" in exp_lower:
        return 9
    if any(pat in exp_lower for pat in ["1年", "1-2", "1-3", "1-4"]):
        return 7  # 1年+门槛，可尝试
    if "2年" in exp_lower or "2-3" in exp_lower:
        return 6  # 2年门槛稍高但非硬阻
    if "5年以下" in exp_lower:
        return 6  # 宽口径，不等同于5年
    if "3年" in exp_lower or "3-5" in exp_lower:
        return 5  # 3年以上门槛较高
    if "5年" in exp_lower or "5-10" in exp_lower:
        return 2  # 基本没戏（应在否决阶段拦截）
    return 5  # 默认


def score_scale(funding: str, scale: str, industry: str) -> int:
    """⑤ 企业规模适配度：只看团队人数，小团队更看重能力而非履历"""
    s = scale.strip()
    # 部分数据放在 funding 字段（如"500-999人"）
    combined = f"{s} {funding}".lower()
    if "1-49" in combined:
        return 8
    if "50-99" in combined:
        return 8
    if "100-499" in combined:
        return 7
    if "500-999" in combined:
        return 6
    if "1000-2000" in combined:
        return 5
    if "2000-5000" in combined:
        return 4
    if "5000-10000" in combined or "5000-10000" in combined:
        return 3
    if "10000" in combined:
        return 2
    return 5  # 无信息默认中位


def score_growth(title: str, industry: str, funding: str, company: str, location: str) -> int:
    """⑥ 成长空间适配度：赛道 + 融资阶段 + 城市，不再点名特定公司"""
    score = 5
    t = title.lower()

    # 技术方向热度
    if "agent" in t or "智能体" in t:
        score += 2
    elif "大模型" in t or "rag" in t:
        score += 2
    elif "ai" in t:
        score += 1

    # 行业前景
    if industry in HIGH_GROWTH_INDUSTRIES:
        score += 1
    if industry in ["新能源", "新能源汽车", "智能硬件/消费电子"]:
        score += 1

    # 传统行业 AI 数字化岗 → 有增量，不减分
    is_digital_role = any(kw in t for kw in ["ai", "agent", "数字化", "大模型", "智能", "数据"])
    if industry in TRADITIONAL_INDUSTRIES and not is_digital_role:
        score -= 1

    # 融资阶段加成（从 scale 拆分出来，独立算）
    funding_lower = funding.strip().lower()
    if any(s in funding_lower for s in ["a轮", "天使", "b轮"]):
        score += 1  # 早期/成长期，上升空间大
    if any(s in funding_lower for s in ["c轮", "d轮及以上"]):
        score += 1  # 后期独角兽，即将IPO

    # 目标城市 + 高前景行业组合加成
    is_target_city = any(c in location for c in TARGET_CITIES)
    if is_target_city and industry in HIGH_GROWTH_INDUSTRIES:
        score += 1

    return max(1, min(score, 10))


def assess_growth_potential(title: str, industry: str, funding: str, company: str, location: str) -> str:
    """发展前景评估（定性）——基于赛道/行业/城市，不点名特定公司"""
    signals = []
    t = title.lower()

    # 技术赛道
    if "agent" in t or "智能体" in t:
        signals.append("[Agent赛道] 2026最热方向")
    elif "大模型" in t or "rag" in t:
        signals.append("[大模型赛道] 技术前沿")

    # 行业标签
    if industry in HIGH_GROWTH_INDUSTRIES:
        signals.append(f"[{industry}] 高前景行业")
    elif industry in TRADITIONAL_INDUSTRIES:
        is_digital = any(kw in t for kw in ["ai", "agent", "数字化", "大模型", "智能"])
        if is_digital:
            signals.append(f"[{industry}] 传统企业数字化部门")
        else:
            signals.append(f"[{industry}] 需确认是否有数字化方向")

    # 融资阶段
    funding_lower = funding.strip().lower()
    if any(s in funding_lower for s in ["a轮", "天使"]):
        signals.append("[早期] 成长空间大、风险并存")
    elif any(s in funding_lower for s in ["b轮"]):
        signals.append("[成长期] 产品验证中、团队扩张")
    elif any(s in funding_lower for s in ["c轮", "d轮及以上"]):
        signals.append("[后期独角兽] 商业化阶段")
    elif "上市" in funding_lower:
        signals.append("[上市] 体系成熟、背书价值高")

    # 城市
    is_target_city = any(c in location for c in TARGET_CITIES)
    if is_target_city and industry in HIGH_GROWTH_INDUSTRIES:
        signals.append("[目标城市+高前景行业] 目标组合")
    elif is_target_city:
        signals.append("[目标城市] 加分")

    return " | ".join(signals) if signals else "需进一步调研"


def get_location_bonus(location: str) -> int:
    """目标城市 +1"""
    if not location:
        return 0
    loc = location.strip()
    if any(c in loc for c in TARGET_CITIES):
        return 1
    return 0


def process_job(job: dict) -> dict:
    """处理单条记录"""
    title = job.get("title", "")
    salary = job.get("salary", "")
    location = job.get("location", "")
    exp = job.get("experience", "")
    edu = job.get("education", "")
    company = job.get("company", "")
    industry = job.get("industry", "")
    funding = job.get("funding", "")
    scale = job.get("scale", "")
    url = job.get("url", "")

    # 修正异常城市字段（如 location="Rust方向" → 从公司名提取城市）
    location = fix_location(location, company)

    job_type = categorize(title, salary, exp)

    if job_type == "irrelevant":
        return {"title": title, "company": company, "type": "irrelevant",
                "salary": salary, "location": location, "url": url, "skipped": True}

    # 一票否决检查
    veto_reason = check_veto(title, edu, exp, salary)

    min_k = parse_salary_min(salary)
    salary_s = salary_score(min_k, salary, title=title)
    salary_negotiable = is_salary_negotiable(salary)

    result = {
        "title": title,
        "company": company,
        "type": job_type,
        "salary": salary,
        "location": location,
        "exp": exp,
        "edu": edu,
        "industry": industry,
        "funding": funding,
        "scale": scale,
        "url": url,
        "salary_min_k": min_k,
        "salary_negotiable": salary_negotiable,
    }

    if job_type == "dev":
        score_hard = score_hard_skills(title, exp, company)
        score_project = score_project_fit(title, industry, company)
        score_level = score_level_fit(exp, edu)
        score_salary = salary_s
        score_scale_val = score_scale(funding, scale, industry)
        score_growth_val = score_growth(title, industry, funding, company, location)

        # ---- ⑦ JD-能力匹配度（新维度）----
        jd_full = job.get('jd_full', '') or job.get('description', '') or job.get('jd_body', '')
        jd_req = job.get('requirements', '')
        jd_text = f"{jd_full}\n{jd_req}" if (jd_full or jd_req) else title
        jd_match = match_jd(
            jd_text=jd_text,
            jd_title=title,
            jd_education=edu,
            jd_experience=exp,
            jd_salary=salary,
        )
        hard_damage = jd_match.get("hard_damage", [])
        coverage = jd_match.get("coverage", 0)
        matcher_verdict = jd_match.get("verdict", "match")
        matcher_hits = jd_match.get("hits", {})
        matcher_gaps = jd_match.get("gaps", [])

        # 覆盖 → 分数 (0-10)
        if matcher_verdict == "veto":
            score_jd_match = 0
        elif not matcher_hits and not hard_damage:
            score_jd_match = 5  # 信息不足，中性分
        elif coverage >= 0.7:
            score_jd_match = 9
        elif coverage >= 0.5:
            score_jd_match = 7
        elif coverage >= 0.3:
            score_jd_match = 5
        else:
            score_jd_match = 3

        # 硬伤扣分（标题里出现C++/嵌入式等，说明方向不对）
        if hard_damage:
            score_jd_match = max(0, score_jd_match - len(hard_damage) * 3)

        location_bonus = get_location_bonus(location)
        total = (score_hard + score_project + score_level + score_salary +
                 score_scale_val + score_growth_val + score_jd_match + location_bonus)

        # 评级（加上第⑦维后阈值不变：>=45 高度，>=35 中度）
        if veto_reason:
            verdict = "否决"
            total = 0
        elif matcher_verdict == "veto":
            verdict = "否决"
            total = 0
            veto_reason = veto_reason or f"硬伤关键词: {hard_damage}"
        elif total >= 55:
            verdict = "高度适配"
        elif total >= 45:
            verdict = "中度适配"
        else:
            verdict = "不推荐投递"

        # 覆盖降级：JD匹配差但其他维度高 → 降一级
        if verdict == "高度适配" and coverage < 0.3 and matcher_hits:
            verdict = "中度适配"

        result.update({
            "score_hard": score_hard,
            "score_project": score_project,
            "score_level": score_level,
            "score_salary": score_salary,
            "score_scale": score_scale_val,
            "score_growth": score_growth_val,
            "score_jd_match": score_jd_match,
            "location_bonus": location_bonus,
            "total_score": total,
            "verdict": verdict,
            "veto": veto_reason,
            "growth_potential": assess_growth_potential(
                title, industry, funding, company, location
            ),
            # JD 匹配详情
            "jd_match_coverage": round(coverage, 2),
            "jd_match_hard_damage": hard_damage,
            "jd_match_gaps": matcher_gaps,
        })
    elif job_type in ("pm", "architect"):
        result.update({
            "verdict": f"非开发岗({job_type})",
            "growth_potential": assess_growth_potential(
                title, industry, funding, company, location
            ),
        })
    else:
        result.update({
            "verdict": "跳过",
        })

    return result


def main():
    parser = argparse.ArgumentParser(description="v2.2 AI岗位批量打分")
    parser.add_argument("input", nargs="?", default=SRC,
                        help=f"爬虫JSON文件路径 (默认: {SRC})")
    parser.add_argument("-o", "--output", default=OUT,
                        help=f"输出文件路径 (默认: {OUT})")
    args = parser.parse_args()

    src = args.input
    out = args.output

    if not os.path.exists(src):
        print(f"[错误] 找不到文件: {src}")
        sys.exit(1)

    with open(src, "r", encoding="utf-8") as f:
        raw = json.load(f)

    jobs = raw.get("data", [])
    print(f"共 {len(jobs)} 条原始数据\n")

    results = []
    dev_results = []
    vetoed = []
    skipped = []

    for job in jobs:
        r = process_job(job)
        results.append(r)
        if r.get("skipped"):
            skipped.append(r)
        elif r.get("type") == "dev":
            dev_results.append(r)
            if r.get("veto"):
                vetoed.append(r)

    # dev 结果按总分排序（否决的排最后）
    dev_results.sort(key=lambda x: (0 if x.get("veto") else 1, x.get("total_score", 0)), reverse=True)
    vetoed.sort(key=lambda x: x.get("total_score", 0), reverse=True)

    # 打印摘要
    print("=" * 70)
    print("处理结果")
    print("=" * 70)
    print(f"  总数: {len(jobs)}")
    print(f"  开发岗: {len(dev_results)} 条")
    print(f"  产品经理: {sum(1 for r in results if r.get('type') == 'pm')} 条")
    print(f"  架构师: {sum(1 for r in results if r.get('type') == 'architect')} 条")
    print(f"  无关/其他: {sum(1 for r in results if r.get('type') in ('other', 'irrelevant'))} 条")
    print(f"  否决: {len(vetoed)} 条 (薪资{sum(1 for r in vetoed if '薪资' in str(r.get('veto','')))} | "
          f"硕士{sum(1 for r in vetoed if '硕士' in str(r.get('veto','')))} | "
          f"经验{sum(1 for r in vetoed if '经验' in str(r.get('veto','')))} | "
          f"应届{sum(1 for r in vetoed if '应届' in str(r.get('veto','')))} )")
    negotiable_count = sum(1 for r in dev_results if r.get("salary_negotiable"))
    if negotiable_count:
        print(f"  薪资面议: {negotiable_count} 条 (需确认)")
    print()

    # Top 15 开发岗（排除否决）
    active_dev = [r for r in dev_results if not r.get("veto")]
    print("=" * 70)
    print(f"开发岗 TOP 15 (按总分降序)")
    print("=" * 70)
    for i, r in enumerate(active_dev[:15], 1):
        loc_bonus = r.get("location_bonus", 0)
        jd = r.get("score_jd_match", 0)
        scores = f"{r['score_hard']}+{r['score_project']}+{r['score_level']}+{r['score_salary']}+{r['score_scale']}+{r['score_growth']}+{jd}"
        nego = " [面议]" if r.get("salary_negotiable") else ""
        cov = r.get("jd_match_coverage", 0)
        damage = r.get("jd_match_hard_damage", [])
        damage_str = f" !{damage}" if damage else ""
        print(f"{i:2}. [{r['verdict']:4}] {r['title'][:40]:40} | {r['company'][:20]:20} | "
              f"{r['location']:12} | {r['salary']:15} | "
              f"总分{r['total_score']:2}({scores}+{loc_bonus}目标城市) 覆盖{cov:.0%}{damage_str}{nego}")
        if r.get("growth_potential"):
            print(f"    前景: {r['growth_potential']}")
        gaps = r.get("jd_match_gaps", [])
        if gaps:
            print(f"    技能缺口: {gaps}")

    # 否决列表
    if vetoed:
        print()
        print("=" * 70)
        print(f"否决 ({len(vetoed)} 条)")
        print("=" * 70)
        for r in vetoed:
            print(f"  [{r.get('veto','?')}] {r['title'][:45]:45} | {r['company'][:20]:20} | {r['salary']:12} | {r['location']:10}")

    print()

    # 非开发岗
    non_dev = [r for r in results if r.get("type") in ("pm", "architect")]
    if non_dev:
        print("=" * 70)
        print(f"非开发岗 ({len(non_dev)} 条)")
        print("=" * 70)
        for r in non_dev:
            print(f"  [{r['type']:10}] {r['title'][:45]:45} | {r['company'][:20]:20} | {r['salary']:12} | {r['location']:10}")
            if r.get("growth_potential"):
                print(f"    前景: {r['growth_potential']}")

    print()

    # 跳过
    if skipped:
        print("=" * 70)
        print(f"跳过 ({len(skipped)} 条)")
        print("=" * 70)
        for r in skipped:
            print(f"  {r['title'][:40]:40} | {r['company']}")

    # 生成导入文件
    import_data = []
    for r in dev_results:
        if r.get("veto"):
            continue  # 否决的不导入
        jd = r.get("score_jd_match", 0)
        loc_bonus = r.get("location_bonus", 0)
        import_data.append({
            "title": r["title"],
            "company": r["company"],
            "type": "dev",
            "salary": r["salary"],
            "location": r["location"],
            "url": r["url"],
            "channel": "猎聘",
            "score_hard": r["score_hard"],
            "score_project": r["score_project"],
            "score_level": r["score_level"],
            "score_salary": r["score_salary"],
            "score_scale": r["score_scale"],
            "score_growth": r["score_growth"],
            "score_jd_match": jd,
            "verdict": r["verdict"],
            "salary_negotiable": r.get("salary_negotiable", False),
            "reason": f"前景: {r.get('growth_potential', '')} | "
                      f"{r['score_hard']}+{r['score_project']}+{r['score_level']}+"
                      f"{r['score_salary']}+{r['score_scale']}+{r['score_growth']}+"
                      f"{jd}+{loc_bonus}目标城市 = {r['total_score']}",
            "exp": r.get("exp", ""),
            "scale": r.get("scale", ""),
            # JD 匹配详情
            "jd_coverage": r.get("jd_match_coverage", 0),
            "jd_hard_damage": r.get("jd_match_hard_damage", []),
            "jd_gaps": r.get("jd_match_gaps", []),
        })

    with open(out, "w", encoding="utf-8") as f:
        json.dump(import_data, f, ensure_ascii=False, indent=2)

    print()
    print(f"[OK] 导入文件已生成: {out}")
    print(f"   共 {len(import_data)} 条开发岗 (已排除否决项)")
    print()
    print("下一步: 打开浏览器 http://localhost:5173 -> 导入 JSON -> 粘贴文件内容")
    print()
    print("用法: python batch_score_v2.py [爬虫JSON路径] [-o 输出路径]")


if __name__ == "__main__":
    main()
