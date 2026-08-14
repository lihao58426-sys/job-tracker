#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
求职跟踪系统 - 批量 JSON 导入路由
支持 scored_batch.json 格式的批量导入。
v2.1: 增加 URL 去重 + 公司/岗位模糊去重。
"""

import json
import re
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from database import get_conn, dict_from_row
from scorer import (
    parse_salary_range, get_location_bonus, compute_total_score, get_verdict,
)

router = APIRouter(prefix="/api/import", tags=["import"])


class ImportJobItem(BaseModel):
    """单条导入记录（匹配 scored_batch.json 格式）。"""
    title: str = ""
    type: str = Field(default="dev", alias="type")
    score_hard: Optional[float] = None
    score_project: Optional[float] = None
    score_level: Optional[float] = None
    score_salary: Optional[float] = None
    score_scale: Optional[float] = None
    score_growth: Optional[float] = None
    score_jd_match: Optional[float] = None
    jd_coverage: Optional[float] = None
    jd_hard_damage: str | list = ""
    jd_gaps: str | list = ""
    verdict: str = ""
    reason: str = ""
    salary: str = ""
    location: str = ""
    exp: str = ""
    company: str = ""
    scale: str = ""
    url: str = ""
    channel: str = "猎聘"

    model_config = {"populate_by_name": True}


class ImportResult(BaseModel):
    total: int
    created: int
    skipped: int
    duplicates: int = 0
    errors: list[str] = []


def _normalize(s: str) -> str:
    """去空格、去括号内容、去常见后缀，用于模糊比对。"""
    s = s.strip().lower()
    s = re.sub(r'[（(][^)）]*[)）]', '', s)  # 去掉括号内容
    s = re.sub(r'[^一-鿿\w]', '', s)   # 只保留中文+英文+数字
    return s


def _next_id_at(conn, date_str: str) -> str:
    """按指定日期生成 ID。"""
    parts = date_str.split("-")
    mmdd = parts[0] + parts[1] if len(parts) >= 2 else datetime.now().strftime("%m%d")
    row = conn.execute(
        "SELECT id FROM applications WHERE id LIKE ? ORDER BY id DESC LIMIT 1",
        (f"{mmdd}-%",)
    ).fetchone()
    if not row:
        return f"{mmdd}-01"
    last_num = int(row["id"].split("-")[1])
    return f"{mmdd}-{last_num + 1:02d}"


def _check_duplicate(conn, url: str, company: str, position: str) -> Optional[str]:
    """检查是否重复。返回已存在的 ID 或 None。"""
    # 第一层：URL 精确匹配（最可靠）
    if url and url.strip():
        existing = conn.execute(
            "SELECT id, company, position FROM applications WHERE url = ? AND url != ''",
            (url.strip(),)
        ).fetchone()
        if existing:
            return f"URL重复: {url} → 已有 [{existing['id']}] {existing['company']} {existing['position']}"

    # 第二层：公司+岗位 模糊匹配
    norm_company = _normalize(company)
    norm_position = _normalize(position)
    if norm_company and norm_position:
        candidates = conn.execute(
            "SELECT id, company, position, url FROM applications"
        ).fetchall()
        for row in candidates:
            if _normalize(row["company"]) == norm_company and _normalize(row["position"]) == norm_position:
                return f"公司+岗位重复: {company} {position} → 已有 [{row['id']}]"

    return None


@router.post("/batch")
def import_batch(jobs: list[ImportJobItem]) -> ImportResult:
    """批量导入岗位列表（带去重）。"""
    conn = get_conn()
    now = datetime.now().strftime("%m-%d %H:%M")
    today = datetime.now().strftime("%m-%d")

    result = ImportResult(total=len(jobs), created=0, skipped=0, duplicates=0)

    # 先加载已有 URL 和公司岗位做缓存
    existing_urls = set(
        row["url"] for row in conn.execute("SELECT url FROM applications WHERE url != ''").fetchall()
    )
    existing_pairs = set(
        (_normalize(row["company"]), _normalize(row["position"]))
        for row in conn.execute("SELECT company, position FROM applications").fetchall()
    )

    for job in jobs:
        try:
            # 跳过非开发岗
            if job.type in ("pm", "architect", "other", "irrelevant"):
                result.skipped += 1
                continue

            company = job.company
            position = job.title

            if not company or not position:
                result.errors.append(f"跳过空白: {job.title}")
                result.skipped += 1
                continue

            # ---- 去重检查 ----
            dup_reason = None
            url = (job.url or "").strip()
            if url and url in existing_urls:
                dup_reason = f"URL重复: {url}"
            elif (_normalize(company), _normalize(position)) in existing_pairs:
                dup_reason = f"公司+岗位重复: {company} {position}"

            if dup_reason:
                result.duplicates += 1
                continue  # 静默跳过重复

            # 解析薪资
            min_k, max_k = parse_salary_range(job.salary)
            location_bonus = get_location_bonus(job.location)

            scores_dict = {
                "score_hard": job.score_hard or 0,
                "score_project": job.score_project or 0,
                "score_level": job.score_level or 0,
                "score_salary": job.score_salary or 0,
                "score_scale": job.score_scale or 0,
                "score_growth": job.score_growth or 0,
                "score_jd_match": job.score_jd_match or 0,
            }
            total_info = compute_total_score(scores_dict, job.location)
            verdict = job.verdict or get_verdict(total_info["total_score"])[0]

            job_id = _next_id_at(conn, today)

            conn.execute("""
                INSERT INTO applications (
                    id, date, company, position, salary_range, salary_min, salary_max,
                    location, location_bonus, url, channel, resume_version, status,
                    score_hard, score_project, score_level, score_salary, score_scale, score_growth,
                    score_jd_match, jd_coverage, jd_hard_damage, jd_gaps,
                    total_score, verdict, job_type, notes,
                    last_updated
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'v1', '未投递',
                          ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                          ?, ?, ?, ?,
                          ?)
            """, (
                job_id, today, company, position,
                job.salary, min_k or 0, max_k or 0,
                job.location, location_bonus,
                url, job.channel or '猎聘',
                scores_dict["score_hard"], scores_dict["score_project"],
                scores_dict["score_level"], scores_dict["score_salary"],
                scores_dict["score_scale"], scores_dict["score_growth"],
                scores_dict["score_jd_match"],
                job.jd_coverage or 0,
                json.dumps(job.jd_hard_damage, ensure_ascii=False) if isinstance(job.jd_hard_damage, list) else (job.jd_hard_damage or ""),
                json.dumps(job.jd_gaps, ensure_ascii=False) if isinstance(job.jd_gaps, list) else (job.jd_gaps or ""),
                total_info["total_score"], verdict, job.type,
                f"规模: {job.scale} | {job.reason}",
                now,
            ))

            conn.execute(
                "INSERT INTO status_history (application_id, date, status, note) VALUES (?, ?, '未投递', '')",
                (job_id, today)
            )

            # 更新缓存
            if url:
                existing_urls.add(url)
            existing_pairs.add((_normalize(company), _normalize(position)))

            result.created += 1

        except Exception as e:
            result.errors.append(f"导入 {job.title} 失败: {str(e)}")
            result.skipped += 1

    conn.commit()
    return result
