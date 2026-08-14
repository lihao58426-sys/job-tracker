#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
求职跟踪系统 - v2.0 打分逻辑
薪资下限解析 + 目标城市地点加分 + 否决检查
"""

import re

# ============================================================
# 地点加分
# ============================================================

# 目标城市加分映射（示例占位值，本地使用请改回真实目标城市）
LOCATION_BONUS_MAP = {
    "上海": 1, "杭州": 1,
    "上海市": 1, "杭州市": 1,
    "shanghai": 1, "hangzhou": 1,
}


def get_location_bonus(location: str) -> int:
    """检查地点是否在目标城市，返回加分。"""
    if not location:
        return 0
    loc_clean = location.strip().replace(" ", "")
    for key, bonus in LOCATION_BONUS_MAP.items():
        if key in loc_clean:
            return bonus
    return 0


# ============================================================
# 薪资解析
# ============================================================

def parse_salary_range(salary_str: str) -> tuple[int | None, int | None]:
    """从薪资字符串中解析 (min, max)，单位 K。
    支持：'15-30k'、'12-24k·13薪'、'80-110k'、'200-250元/天' 等。"""
    if not salary_str:
        return None, None
    s = salary_str.lower().replace("（", "(").replace("）", ")")
    # 匹配 "数字-数字k"
    m = re.match(r'(\d+)\s*[-~]\s*(\d+)\s*k', s)
    if m:
        return int(m.group(1)), int(m.group(2))
    # 匹配 "数字k" 单值
    m = re.match(r'(\d+)\s*k', s)
    if m:
        val = int(m.group(1))
        return val, val
    # 元/天 格式（忽略，无法比较）
    return None, None


def check_salary_veto(salary_str: str) -> tuple[bool, str]:
    """v2.0：薪资下限 < 10K → 一票否决。"""
    min_k, _ = parse_salary_range(salary_str)
    if min_k is not None and min_k < 10:
        return True, f"薪资下限 {min_k}K < 10K，交完五险在外地无法维持基本生活"
    return False, ""


def compute_total_score(scores: dict, location: str) -> dict:
    """计算总分 = 七维之和 + 地点加分。返回 {total, bonus, dim_total}。"""
    dim_total = sum(scores.values())
    bonus = get_location_bonus(location)
    return {
        "dim_total": dim_total,
        "location_bonus": bonus,
        "total_score": dim_total + bonus,
    }


# ============================================================
# 评级
# ============================================================

def get_verdict(total_score: float) -> tuple[str, str]:
    """根据总分返回 (评级标签, 行动建议)。"""
    if total_score >= 55:
        return "高度适配", "优先投递，精心准备简历定制和面试"
    elif total_score >= 45:
        return "中度适配", "可以投，但需策略性调整简历重点，面试需额外补课"
    else:
        return "不推荐投递", "通过率极低，把精力留给更匹配的岗位"
