#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
合并猎聘 raw 爬虫文件并去重。

输入：本目录（爬虫json/）下所有 猎聘-*.json（raw 文件，含 data 数组）。
     每条 data 元素应含 keywords 字段（标记来源关键词）；若无则用文件名推断。
去重：① URL 精确去重  ② 公司+岗位 模糊去重。
输出：猎聘-合并_去重.json

用法：
    python merge.py                     # 处理目录下所有 猎聘-*.json
    python merge.py 猎聘-8-13.json      # 只处理指定文件
"""
import json
import re
import glob
import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))


def _normalize(s: str) -> str:
    """去空格、去括号内容、去非中文英文数字，用于模糊比对。"""
    s = s.strip().lower()
    s = re.sub(r'[（(][^)）]*[)）]', '', s)
    s = re.sub(r'[^一-鿿\w]', '', s)
    return s


def load_raw_files(paths):
    """读取 raw 文件，返回 (all_rows, total_raw)。"""
    all_rows = []
    for f in paths:
        with open(f, encoding="utf-8") as fp:
            d = json.load(fp)
        rows = d.get("data", [])
        # 文件级 keyword（旧格式 {keyword: "MCP"}）作为兜底
        file_kw = d.get("keyword", "")
        for r in rows:
            r = dict(r)
            kws = r.get("keywords") or ([file_kw] if file_kw else [])
            r["keywords"] = sorted(set(kws))
            all_rows.append(r)
    return all_rows


def main():
    if len(sys.argv) > 1:
        paths = [os.path.join(BASE, a) for a in sys.argv[1:]]
    else:
        paths = sorted(
            glob.glob(os.path.join(BASE, "猎聘-*.json"))
        )
        # 排除"去重"结果文件，避免重复处理
        paths = [p for p in paths if "_去重" not in p]

    if not paths:
        print("[错误] 未找到 猎聘-*.json 文件")
        return

    all_rows = load_raw_files(paths)
    total_raw = len(all_rows)

    seen_url = {}
    seen_pair = {}
    unique = []
    dup_count = 0

    for r in all_rows:
        url = (r.get("url") or "").strip()
        company = r.get("company") or ""
        title = r.get("title") or ""
        n_pair = (_normalize(company), _normalize(title))

        # ① URL 精确去重
        if url and url in seen_url:
            seen_url[url]["keywords"] = sorted(
                set(seen_url[url]["keywords"] + r.get("keywords", []))
            )
            dup_count += 1
            continue

        # ② 公司+岗位 模糊去重
        if n_pair[0] and n_pair[1] and n_pair in seen_pair:
            seen_pair[n_pair]["keywords"] = sorted(
                set(seen_pair[n_pair]["keywords"] + r.get("keywords", []))
            )
            dup_count += 1
            continue

        if url:
            seen_url[url] = r
        if n_pair[0] and n_pair[1]:
            seen_pair[n_pair] = r
        unique.append(r)

    out = {
        "source": "猎聘",
        "total_raw": total_raw,
        "total_unique": len(unique),
        "data": unique,
    }
    out_path = os.path.join(BASE, "猎聘-合并_去重.json")
    with open(out_path, "w", encoding="utf-8") as fp:
        json.dump(out, fp, ensure_ascii=False, indent=2)

    print(f"raw={total_raw} unique={len(unique)} dup={dup_count}")
    print(f"输出: {out_path}")


if __name__ == "__main__":
    main()
