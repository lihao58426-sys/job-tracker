#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
JD 匹配引擎 v1.0
基于 skills_matrix.json，对 JD 进行三层匹配：
  ① 硬伤检测 → 出现排除关键词直接 veto/扣分
  ② 正向匹配 → JD 提到的技能，你覆盖了多少
  ③ 反向覆盖 → JD 硬要求的技能，你的字典覆盖了多少

用法：
  from jd_matcher import match_jd
  result = match_jd("JD正文...")
  print(result["verdict"], result["score"], result["coverage"])
"""

import json
import os
import re

MATRIX_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "skills_matrix.json")

# 内置降级矩阵：当外部 skills_matrix.json 缺失时使用。
# 仅含通用技能关键词与排除规则，不含个人求职策略（薪资/城市/年限等），
# 保证引擎可独立运行/演示，同时避免泄露隐私。
_FALLBACK_MATRIX = {
    "hard_skills": {
        "python_development": {"keywords": ["Python", "asyncio", "类型注解"], "weight": 5, "must_have": True, "level": 3, "evidence": "Python 主力开发，异步 / 类型注解"},
        "fastapi_backend": {"keywords": ["FastAPI", "RESTful API", "REST API", "Pydantic"], "weight": 4, "must_have": True, "level": 3, "evidence": "FastAPI 后端开发"},
        "llm_framework": {"keywords": ["LangChain", "LCEL", "Function Calling", "工具调用"], "weight": 5, "must_have": False, "level": 3, "evidence": "LangChain Agent / LCEL"},
        "agent_development": {"keywords": ["AI Agent", "智能体", "MCP", "Agent开发"], "weight": 5, "must_have": False, "level": 3, "evidence": "Agent + MCP Server"},
        "rag_development": {"keywords": ["RAG", "检索增强生成", "向量检索", "ChromaDB", "向量数据库", "embedding"], "weight": 5, "must_have": False, "level": 3, "evidence": "RAG 知识库 / 向量检索"},
        "sql_database": {"keywords": ["SQL", "SQLite", "PostgreSQL", "数据库"], "weight": 4, "must_have": True, "level": 3, "evidence": "SQLite / PostgreSQL"},
        "react_frontend": {"keywords": ["React", "TypeScript", "Hooks", "前端"], "weight": 3, "must_have": False, "level": 2, "evidence": "React + TypeScript"},
        "docker_devops": {"keywords": ["Docker", "容器化", "Docker Compose"], "weight": 4, "must_have": False, "level": 3, "evidence": "Docker 部署"},
        "web_scraping": {"keywords": ["Playwright", "爬虫", "数据采集", "浏览器自动化"], "weight": 4, "must_have": False, "level": 3, "evidence": "Playwright 自动化采集"},
    },
    "exclude_keywords": {
        "safe_compounds": {"list": ["单元测试", "自动化测试", "测试用例", "测试驱动", "集成测试", "端到端测试"]},
        "roles_i_avoid": ["测试", "运维", "实习生", "实习", "校招", "销售", "客服", "行政", "财务", "前台"],
        "languages_i_dont_do": ["C++", "C#", "Java", "Go", "Rust", "Scala", "Kotlin", "PHP", "Ruby", "Swift", "Objective-C"],
        "domains_i_avoid": ["嵌入式", "驱动开发", "PLC", "FPGA", "游戏开发", "区块链", "网络安全"],
        "frameworks_i_avoid": ["Spring", "Django", ".NET", "Angular", "Flask", "Laravel"],
    },
    "project_evidence": [],
}


def load_matrix() -> dict:
    """加载能力矩阵；外部 skills_matrix.json 缺失时回退到内置精简矩阵。"""
    try:
        with open(MATRIX_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, OSError):
        return _FALLBACK_MATRIX


def tokenize(text: str) -> str:
    """统一小写 + 去多余空格，用于大小写不敏感的匹配"""
    return text.lower().strip()


def find_hits(keywords: list[str], text: str) -> list[str]:
    """在文本中查找命中的关键词列表"""
    t = tokenize(text)
    hits = []
    for kw in keywords:
        if tokenize(kw) in t:
            hits.append(kw)
    return hits


# ── 语言替代列表检测 ──
# 当 JD 说 "Python / Go / Java 至少一门" 时，Python 用户不应该被 Go/Java 排除
_LANG_ALT_CUES = ["至少一门", "都可以", "任选一种", "任选", "均可", "一种即可", "其中一种", "任意一种", "任意", "精通其一"]
# 也匹配 "等至少一门"、"等都可以" 等变体（"等"字在语言列表和 cue 之间）
_LANG_ALT_CUES += [f"等{c}" for c in _LANG_ALT_CUES]
# 单独的"等"作为 cue，但要限定在语言列表后面（如 "java，python等"）
_LANG_ALT_CUES.append("等")
_MY_LANGUAGES = ["Python", "TypeScript"]

# 语言列表分隔符：/ 、 ， ,
_LANG_SEP_PATTERN = r'\s*[/、，,]\s*'


def _strip_lang_alternatives(text: str) -> str:
    """检测并移除语言替代列表（如 'rust / go / python 至少一门'），
    当用户的 Python 在列表中时，整个列表替换为占位符，避免误伤。
    注意：text 可能已经 lowercased，正则用 [a-z] 匹配。"""
    result = text
    _LANG_WORD = r'[A-Za-z][A-Za-z0-9+#]+'
    _LIST_RE = re.compile(rf'({_LANG_WORD}{_LANG_SEP_PATTERN})+{_LANG_WORD}')

    for cue in _LANG_ALT_CUES:
        search_from = 0
        while True:
            pos = result.find(cue, search_from)
            if pos < 0:
                break
            before_start = max(0, pos - 150)
            before = result[before_start:pos]
            all_matches = list(_LIST_RE.finditer(before))
            if not all_matches:
                search_from = pos + len(cue)  # 跳过这个不匹配的出现位置
                continue
            m = all_matches[-1]  # 取离 cue 最近的匹配
            lang_phrase_full = m.group()
            langs_in_list = re.split(_LANG_SEP_PATTERN, lang_phrase_full.strip())
            my_langs_lower = [l.lower() for l in _MY_LANGUAGES]
            if any(l.lower() in my_langs_lower for l in langs_in_list):
                phrase_start = before_start + m.start()
                phrase_end = pos + len(cue)
                placeholder = f"__LANGALT_{abs(hash(result[phrase_start:phrase_end])) % 10000}__"
                result = result[:phrase_start] + placeholder + result[phrase_end:]
                search_from = phrase_start + len(placeholder)
            else:
                search_from = pos + len(cue)  # Python 不在列表中，跳过
    return result


def _strip_roles_from_body(text: str, title: str) -> str:
    """从正文中移除角色类排除关键词（只保留标题中的匹配）。
    这样 '测试' 出现在 JD 正文里不会误伤，但 '测试工程师' 标题仍会触发。"""
    t_lower = tokenize(title)
    result = text
    # 不能在正文中匹配 roles_i_avoid → 从正文中移除这些词
    # 但词可能很长（如"实习生"），直接替换会破坏语义
    # 更安全的做法：把正文中的 roles 词替换为占位符
    matrix = load_matrix()
    roles_kw = matrix["exclude_keywords"].get("roles_i_avoid", [])
    safe = matrix["exclude_keywords"].get("safe_compounds", {}).get("list", [])
    for kw in roles_kw:
        kw_lower = tokenize(kw)
        # 跳过短词（<2字），容易误伤
        if len(kw) <= 1:
            continue
        # 只在非标题部分替换（正文）
        # find_hits 用的是子串匹配，需要把正文中的词替换掉
        body_start = result.lower().find(t_lower)
        if body_start >= 0:
            body = result[body_start + len(t_lower):]
            # 只替换独立的角色词（2-3字短词用词边界）
            if len(kw) <= 3:
                # 短词：用占位符替换整词
                placeholder = f"__ROLE_{abs(hash(kw)) % 10000}__"
                # 用正则替换（大小写不敏感）
                result = re.sub(
                    re.escape(kw), placeholder, result,
                    count=0, flags=re.IGNORECASE
                )
    return result


# ── 匹配结果类型 ──
# verdict: "strong_match" | "match" | "weak_match" | "veto"
# score: 正向匹配加权分
# coverage: JD硬要求覆盖率 (0.0~1.0)
# gaps: 你缺的关键技能
# hits: 命中的技能标签详情
# hard_damage: 硬伤关键词


def match_jd(jd_text: str, jd_title: str = "", jd_education: str = "",
             jd_experience: str = "", jd_salary: str = "") -> dict:
    """
    对一条 JD 执行完整匹配分析。

    参数：
      jd_text:       JD 正文（职位描述+任职要求）
      jd_title:      职位标题
      jd_education:  学历要求字段
      jd_experience: 经验要求字段
      jd_salary:     薪资字段

    返回：
      {
        "verdict": "strong_match" | "match" | "weak_match" | "veto",
        "score": int,           # 正向匹配加权分
        "max_score": int,       # 满分（所有must_have技能权重和）
        "coverage": float,      # JD要求覆盖率 0~1
        "coverage_detail": {},  # 覆盖详情
        "hits": {},             # 命中的技能标签
        "missing_must_have": [],# 缺失的硬性要求
        "gaps": [],             # 你缺的技能
        "hard_damage": [],      # 命中的排除关键词
        "interview_stories": [],# 可用的面试项目
      }
    """
    matrix = load_matrix()
    hard_skills = matrix["hard_skills"]
    exclude = matrix["exclude_keywords"]
    projects = matrix["project_evidence"]

    # 合并所有可搜索文本
    search_text = f"{jd_title} {jd_text} {jd_education} {jd_experience} {jd_salary}"
    search_lower = tokenize(search_text)

    result = {
        "verdict": "match",
        "score": 0,
        "max_score": 0,
        "coverage": 0.0,
        "coverage_detail": {},
        "hits": {},
        "missing_must_have": [],
        "gaps": [],
        "hard_damage": [],
        "interview_stories": [],
    }

    # ═══════════════════════════════════════
    # ① 硬伤检测
    # ═══════════════════════════════════════
    # Step 1: 安全复合词替换（如"单元测试"→防误伤）
    safe_compounds = exclude.get("safe_compounds", {}).get("list", [])
    sanitized_text = search_lower
    for i, sc in enumerate(safe_compounds):
        sc_lower = tokenize(sc)
        if sc_lower in sanitized_text:
            sanitized_text = sanitized_text.replace(sc_lower, f"__SAFE_{i}__")

    # Step 2: 语言替代列表检测（如 "Python / Go / Java 至少一门" → Python 可选，不排除 Go/Java）
    sanitized_text = _strip_lang_alternatives(sanitized_text)

    # Step 3: 角色类关键词只对标题匹配（"测试""运维"在 JD 正文 ≠ 测试岗/运维岗）
    roles_pool = exclude.get("roles_i_avoid", [])
    title_lower = tokenize(jd_title)
    role_hits_in_title = find_hits(roles_pool, title_lower)

    # Step 4: 技术栈排除（语言/领域/框架 → 全文本匹配）
    tech_pool = []
    for category in ["languages_i_dont_do", "domains_i_avoid", "frameworks_i_avoid"]:
        tech_pool.extend(exclude.get(category, []))

    tech_hard_damage = find_hits(tech_pool, sanitized_text)

    # Step 5: 合并硬伤（角色只在标题匹配，技术栈全文本匹配）
    hard_damage = role_hits_in_title + tech_hard_damage
    result["hard_damage"] = hard_damage

    if len(hard_damage) >= 2:
        result["verdict"] = "veto"
        result["score"] = -99
        return result

    # ═══════════════════════════════════════
    # ② 正向匹配——JD 要的，你会多少
    # ═══════════════════════════════════════
    for cat, cfg in hard_skills.items():
        hit_kw = find_hits(cfg["keywords"], search_text)
        if hit_kw:
            result["hits"][cat] = {
                "hit_keywords": hit_kw,
                "weight": cfg["weight"],
                "must_have": cfg["must_have"],
                "level": cfg["level"],
                "evidence": cfg["evidence"][:80],
            }
            result["score"] += cfg["weight"] * len(hit_kw)

    # 硬伤扣分
    if hard_damage:
        result["score"] -= 10 * len(hard_damage)

    # ═══════════════════════════════════════
    # ③ must_have 检查
    # ═══════════════════════════════════════
    for cat, cfg in hard_skills.items():
        if cfg["must_have"]:
            result["max_score"] += cfg["weight"]
            if cat not in result["hits"]:
                result["missing_must_have"].append({
                    "skill": cat,
                    "keywords": cfg["keywords"][:5],
                    "evidence": cfg["evidence"][:80],
                    "suggestion": f"面试时主动提及: {cfg['evidence'][:60]}",
                })

    if result["missing_must_have"]:
        # 不直接否决——JD可能隐含要求但没出现精确关键词
        # 降级 + 扣分即可
        if result["verdict"] != "veto":
            result["verdict"] = "weak_match"
        result["score"] = max(0, result["score"] - 5 * len(result["missing_must_have"]))

    # ═══════════════════════════════════════
    # ④ 反向覆盖——JD 要求的，你覆盖了多少
    # ═══════════════════════════════════════
    # 从 search_text 提取所有可能的技能关键词
    all_matrix_kw = []
    kw_to_cat = {}
    for cat, cfg in hard_skills.items():
        for kw in cfg["keywords"]:
            all_matrix_kw.append(kw)
            kw_to_cat[kw.lower()] = cat

    # JD 中出现的技能关键词
    jd_skills_found = find_hits(all_matrix_kw, search_text)

    # 按技能类别去重
    jd_categories = set()
    for kw in jd_skills_found:
        cat = kw_to_cat.get(kw.lower(), "")
        if cat:
            jd_categories.add(cat)

    # 你命中的类别
    your_categories = set(result["hits"].keys())

    # 你有但水平弱的（level <= 2）
    weak_hits = []
    for cat in jd_categories & your_categories:
        if hard_skills[cat]["level"] <= 2:
            weak_hits.append(cat)

    # JD 要但你完全没有的
    missing_categories = jd_categories - your_categories
    result["gaps"] = sorted(missing_categories)

    # 覆盖率
    if jd_categories:
        result["coverage"] = len(your_categories) / len(jd_categories)
        result["coverage_detail"] = {
            "jd_requires": sorted(jd_categories),
            "you_have": sorted(your_categories),
            "you_miss": sorted(missing_categories),
            "weak_areas": sorted(weak_hits),
        }

    # ═══════════════════════════════════════
    # ⑤ 覆盖率降级
    # ═══════════════════════════════════════
    if result["verdict"] != "veto":
        if result["coverage"] < 0.3:
            result["verdict"] = "weak_match"
            result["score"] = max(0, result["score"] - 15)
        elif result["coverage"] < 0.5:
            result["verdict"] = "weak_match"
            result["score"] = max(0, result["score"] - 8)
        elif result["coverage"] >= 0.7:
            result["verdict"] = "strong_match"

    # 硬伤弱匹配
    if hard_damage and result["verdict"] != "veto":
        result["verdict"] = "weak_match"

    # ═══════════════════════════════════════
    # ⑥ 生成面试素材
    # ═══════════════════════════════════════
    hit_categories = set(result["hits"].keys())
    for proj in projects:
        proj_kw_set = set(kw.lower() for kw in proj["keywords"])
        if proj_kw_set & hit_categories:
            result["interview_stories"].append({
                "project": proj["name"],
                "fit_keywords": sorted(proj_kw_set & hit_categories),
                "highlights": proj["highlights"][:3],
            })

    return result


# ═══════════════════════════════════════
# 便捷函数：快速看一条 JD 的匹配结果
# ═══════════════════════════════════════

def quick_match(jd_text: str, jd_title: str = "") -> str:
    """返回人类可读的匹配报告"""
    r = match_jd(jd_text, jd_title)

    verdict_label = {"strong_match": "[STRONG]", "match": "[MATCH]", "weak_match": "[WEAK]", "veto": "[VETO]"}
    label = verdict_label.get(r["verdict"], "[?]")

    lines = [
        f"{label} 判定: {r['verdict']} | 得分: {r['score']} | 覆盖率: {r['coverage']:.0%}",
        f"",
    ]

    if r["hard_damage"]:
        lines.append(f"[!!] 硬伤: {r['hard_damage']}")

    if r["hits"]:
        lines.append("[OK] 命中技能:")
        for cat, info in r["hits"].items():
            must = " [MUST]" if info["must_have"] else ""
            lines.append(f"   {cat}: {info['hit_keywords']} (weight={info['weight']}{must})")

    if r["gaps"]:
        lines.append(f"[GAP] 缺口: {r['gaps']}")

    if r["missing_must_have"]:
        lines.append("[MISS] 缺失硬性要求:")
        for m in r["missing_must_have"]:
            lines.append(f"   {m['skill']}: {m['suggestion']}")

    weak = r.get("coverage_detail", {}).get("weak_areas", [])
    if weak:
        lines.append(f"[WEAK] 有但弱: {weak}")

    if r["interview_stories"]:
        lines.append("[STORY] 可用面试项目:")
        for s in r["interview_stories"][:2]:
            lines.append(f"   {s['project']}: {', '.join(s['highlights'][:2])}")

    lines.append(f"\n覆盖详情: JD要求 {len(r['coverage_detail'].get('jd_requires',[]))} 项 → 你覆盖 {len(r['coverage_detail'].get('you_have',[]))} 项")

    return "\n".join(lines)


# ═══════════════════════════════════════
# CLI 测试
# ═══════════════════════════════════════

if __name__ == "__main__":
    # 模拟一条测试 JD
    test_jd = """
职位描述：
负责公司 AI Agent 平台的架构设计与开发，基于 LangChain 构建智能体应用。
使用 FastAPI 开发 RESTful API，对接企业内部系统。
负责 RAG 知识库系统的搭建与优化，使用 ChromaDB 作为向量数据库。
编写单元测试，使用 Docker 进行容器化部署。

任职要求：
1. 精通 Python，3年以上后端开发经验
2. 熟悉 LangChain、LCEL，有 Agent 开发经验
3. 了解 RAG 原理，有 ChromaDB 或类似向量数据库使用经验
4. 熟悉 FastAPI、PostgreSQL
5. 有 Docker 容器化部署经验
6. 熟悉 Git 版本管理
"""

    print("=" * 60)
    print("测试 JD 匹配")
    print("=" * 60)
    print(quick_match(test_jd, "AI Agent 开发工程师"))
    print()

    # 模拟一条 不匹配 的 JD
    bad_jd = """
职位描述：
负责嵌入式系统软件开发，使用 C++ 进行驱动开发。
熟悉 PLC 编程，有 FPGA 开发经验者优先。
负责系统运维和测试工作。

任职要求：
1. 精通 C++，3年以上嵌入式开发经验
2. 熟悉 Linux 内核驱动开发
3. 了解 PLC、FPGA
"""
    print("=" * 60)
    print("测试 不匹配 JD")
    print("=" * 60)
    print(quick_match(bad_jd, "嵌入式开发工程师"))
