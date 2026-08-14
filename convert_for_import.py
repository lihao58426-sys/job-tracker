#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
把 applications.json 转成导入系统能识别的格式。
用法：python convert_for_import.py
输出：import_ready.json（复制内容粘贴到网页导入框）
"""

import json
import sys
import os

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(SCRIPT_DIR, "..", "执行方案", "岗位打分工具", "applications.json")
OUT = os.path.join(SCRIPT_DIR, "import_ready.json")

# 六维得分中文 → 英文字段名映射
SCORE_MAP = {
    "硬能力匹配度": "score_hard",
    "项目经验契合度": "score_project",
    "经验层级适配度": "score_level",
    "薪资期望适配度": "score_salary",
    "企业规模适配度": "score_scale",
    "成长空间适配度": "score_growth",
}


def convert_one(item: dict) -> dict:
    """单条记录转换。"""
    scores = item.get("scores", {})
    research = item.get("research", {})

    # 六维得分展平
    flat_scores = {}
    for cn_name, en_name in SCORE_MAP.items():
        flat_scores[en_name] = scores.get(cn_name, 0)

    # 拼接调研为备注
    research_parts = []
    if research.get("核心业务"):
        research_parts.append(f"核心业务: {research['核心业务']}")
    if research.get("技术栈"):
        research_parts.append(f"技术栈: {research['技术栈']}")
    if research.get("团队特点"):
        research_parts.append(f"团队特点: {research['团队特点']}")
    if research.get("匹配优势"):
        research_parts.append(f"匹配优势: {research['匹配优势']}")
    if research.get("短板应对"):
        research_parts.append(f"短板应对: {research['短板应对']}")

    reason_parts = [item.get("notes", "")]
    if research_parts:
        reason_parts.append(" | ".join(research_parts))

    return {
        "title": item.get("position", ""),
        "company": item.get("company", ""),
        "type": "dev",
        "salary": item.get("salary_range", ""),
        "location": item.get("location", ""),
        "url": item.get("url", ""),
        "channel": item.get("channel", "猎聘"),
        **flat_scores,
        "verdict": item.get("verdict", ""),
        "reason": " | ".join(filter(None, reason_parts)),
        "exp": "",
        "scale": "",
    }


def main():
    if not os.path.exists(SRC):
        print(f"[错误] 找不到源文件：{SRC}")
        sys.exit(1)

    with open(SRC, "r", encoding="utf-8") as f:
        data = json.load(f)

    applications = data.get("applications", [])
    if not applications:
        print("[错误] applications.json 中没有 applications 数组")
        sys.exit(1)

    converted = [convert_one(item) for item in applications]

    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(converted, f, ensure_ascii=False, indent=2)

    print(f"✅ 转换完成！{len(converted)} 条记录 → {OUT}")
    print()
    print("下一步：")
    print(f"  1. 用记事本打开 {OUT}")
    print("  2. 全选复制内容（Ctrl+A Ctrl+C）")
    print("  3. 在 http://localhost:5173 点「📥 导入 JSON」")
    print("  4. 粘贴到输入框（Ctrl+V），点「导入」")


if __name__ == "__main__":
    main()
