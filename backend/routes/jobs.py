#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
求职跟踪系统 - 投递记录 CRUD 路由
"""

from fastapi import APIRouter, HTTPException, Query
from datetime import datetime
from pydantic import BaseModel
from database import get_conn, dict_from_row, dicts_from_rows
from models import (
    ApplicationCreate, ApplicationUpdate, ApplicationOut, ApplicationListOut,
    ScoresOut, StatusHistoryIn, StatusHistoryOut,
)
from scorer import (
    parse_salary_range, get_location_bonus, compute_total_score, get_verdict,
)

router = APIRouter(prefix="/api/jobs", tags=["jobs"])

VALID_STATUSES = ["已投递", "已读", "筛过", "笔试", "一面", "二面", "三面", "HR面", "Offer", "入职", "已拒", "挂掉"]


def _next_id(conn) -> str:
    """生成下一个 ID：MMDD-NN"""
    today = datetime.now().strftime("%m%d")
    row = conn.execute(
        "SELECT id FROM applications WHERE id LIKE ? ORDER BY id DESC LIMIT 1",
        (f"{today}-%",)
    ).fetchone()
    if not row:
        return f"{today}-01"
    last_num = int(row["id"].split("-")[1])
    return f"{today}-{last_num + 1:02d}"


def _app_to_out(row: dict) -> ApplicationOut:
    """数据库行 → ApplicationOut，含状态历史。"""
    conn = get_conn()
    histories = dicts_from_rows(conn.execute(
        "SELECT * FROM status_history WHERE application_id=? ORDER BY id",
        (row["id"],)
    ))
    scores = ScoresOut(
        score_hard=row["score_hard"] or 0,
        score_project=row["score_project"] or 0,
        score_level=row["score_level"] or 0,
        score_salary=row["score_salary"] or 0,
        score_scale=row["score_scale"] or 0,
        score_growth=row["score_growth"] or 0,
        score_jd_match=row["score_jd_match"] or 0,
        total_score=row["total_score"] or 0,
        location_bonus=row["location_bonus"] or 0,
    )
    return ApplicationOut(
        id=row["id"],
        date=row["date"] or "",
        company=row["company"],
        position=row["position"],
        salary_range=row["salary_range"] or "",
        salary_min=row["salary_min"] or 0,
        salary_max=row["salary_max"] or 0,
        location=row["location"] or "",
        location_bonus=row["location_bonus"] or 0,
        url=row["url"] or "",
        channel=row["channel"] or "",
        resume_version=row["resume_version"] or "v1",
        status=row["status"] or "已投递",
        scores=scores,
        verdict=row["verdict"] or "",
        job_type=row["job_type"] or "",
        notes=row["notes"] or "",
        research_core_business=row["research_core_business"] or "",
        research_tech_stack=row["research_tech_stack"] or "",
        research_team_features=row["research_team_features"] or "",
        research_match_advantages=row["research_match_advantages"] or "",
        research_weakness_strategy=row["research_weakness_strategy"] or "",
        status_history=[StatusHistoryOut(**h) for h in histories],
        last_updated=row["last_updated"] or "",
        created_at=row["created_at"] or "",
    )


# ============================================================
# GET /api/jobs — 列表（支持筛选 + 排序）
# ============================================================

@router.get("")
def list_jobs(
    status: str = Query(default="", description="按状态筛选"),
    verdict: str = Query(default="", description="按评级筛选"),
    location: str = Query(default="", description="按地点模糊搜索"),
    job_type: str = Query(default="", description="按类型筛选 dev/pm/architect"),
    search: str = Query(default="", description="搜索公司/岗位名"),
    sort: str = Query(default="total_score_desc", description="排序 total_score_desc | date_desc | id_desc"),
) -> list[ApplicationListOut]:
    conn = get_conn()
    conditions = []
    params = []

    if status:
        conditions.append("status = ?")
        params.append(status)
    if verdict:
        conditions.append("verdict = ?")
        params.append(verdict)
    if location:
        conditions.append("location LIKE ?")
        params.append(f"%{location}%")
    if job_type:
        conditions.append("job_type = ?")
        params.append(job_type)
    if search:
        conditions.append("(company LIKE ? OR position LIKE ?)")
        params.extend([f"%{search}%", f"%{search}%"])

    where = " WHERE " + " AND ".join(conditions) if conditions else ""
    order_map = {
        "total_score_desc": "total_score DESC, id ASC",
        "date_desc": "date DESC, id ASC",
        "id_desc": "id DESC",
    }
    order = order_map.get(sort, "total_score DESC, id ASC")

    rows = dicts_from_rows(conn.execute(
        f"SELECT id, date, company, position, salary_range, location, location_bonus, "
        f"status, total_score, verdict, job_type, url FROM applications{where} ORDER BY {order}",
        params
    ))
    return [ApplicationListOut(**r) for r in rows]


# ============================================================
# GET /api/jobs/{id} — 详情
# ============================================================

@router.get("/{job_id}")
def get_job(job_id: str) -> ApplicationOut:
    conn = get_conn()
    row = dict_from_row(conn.execute(
        "SELECT * FROM applications WHERE id=?", (job_id,)
    ).fetchone())
    if not row:
        raise HTTPException(status_code=404, detail=f"未找到 ID 为 {job_id} 的记录")
    return _app_to_out(row)


# ============================================================
# POST /api/jobs — 新增
# ============================================================

@router.post("", status_code=201)
def create_job(data: ApplicationCreate) -> ApplicationOut:
    conn = get_conn()
    now = datetime.now().strftime("%m-%d %H:%M")

    # 解析薪资
    min_k, max_k = parse_salary_range(data.salary_range)
    # 地点加分
    location_bonus = get_location_bonus(data.location)
    # 计算总分
    scores_dict = {
        "score_hard": data.scores.score_hard,
        "score_project": data.scores.score_project,
        "score_level": data.scores.score_level,
        "score_salary": data.scores.score_salary,
        "score_scale": data.scores.score_scale,
        "score_growth": data.scores.score_growth,
    }
    total_info = compute_total_score(scores_dict, data.location)
    # 自动判定评价（如果未指定）
    verdict = data.verdict or get_verdict(total_info["total_score"])[0]

    job_id = _next_id(conn)

    conn.execute("""
        INSERT INTO applications (
            id, date, company, position, salary_range, salary_min, salary_max,
            location, location_bonus, url, channel, resume_version, status,
            score_hard, score_project, score_level, score_salary, score_scale, score_growth, score_jd_match,
            total_score, verdict, job_type, notes,
            research_core_business, research_tech_stack, research_team_features,
            research_match_advantages, research_weakness_strategy,
            last_updated
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        job_id, data.date, data.company, data.position,
        data.salary_range, min_k or 0, max_k or 0,
        data.location, location_bonus, data.url, data.channel, data.resume_version, data.status,
        data.scores.score_hard, data.scores.score_project, data.scores.score_level,
        data.scores.score_salary, data.scores.score_scale, data.scores.score_growth,
        data.scores.score_jd_match,
        total_info["total_score"], verdict, data.job_type, data.notes,
        data.research_core_business, data.research_tech_stack, data.research_team_features,
        data.research_match_advantages, data.research_weakness_strategy,
        now,
    ))

    # 初始化状态历史
    conn.execute(
        "INSERT INTO status_history (application_id, date, status, note) VALUES (?, ?, ?, '')",
        (job_id, data.date, data.status)
    )

    conn.commit()

    # 返回完整记录
    row = dict_from_row(conn.execute("SELECT * FROM applications WHERE id=?", (job_id,)).fetchone())
    return _app_to_out(row)


# ============================================================
# PUT /api/jobs/{id} — 更新
# ============================================================

@router.put("/{job_id}")
def update_job(job_id: str, data: ApplicationUpdate) -> ApplicationOut:
    conn = get_conn()
    existing = dict_from_row(conn.execute(
        "SELECT * FROM applications WHERE id=?", (job_id,)
    ).fetchone())
    if not existing:
        raise HTTPException(status_code=404, detail=f"未找到 ID 为 {job_id} 的记录")

    now = datetime.now().strftime("%m-%d %H:%M")
    updates = []
    params = []

    # 逐字段检查
    for field in ["date", "salary_range", "location", "url", "channel",
                   "resume_version", "verdict", "job_type", "notes",
                   "research_core_business", "research_tech_stack",
                   "research_team_features", "research_match_advantages",
                   "research_weakness_strategy"]:
        val = getattr(data, field, None)
        if val is not None:
            updates.append(f"{field}=?")
            params.append(val)

    # 薪资变更时重新解析
    if data.salary_range is not None:
        min_k, max_k = parse_salary_range(data.salary_range)
        updates.append("salary_min=?")
        params.append(min_k or 0)
        updates.append("salary_max=?")
        params.append(max_k or 0)

    # 地点变更时重新计算加分
    if data.location is not None:
        updates.append("location_bonus=?")
        params.append(get_location_bonus(data.location))

    # 打分变更时重新计算总分
    score_fields = []
    if data.scores is not None:
        for dim in ["score_hard", "score_project", "score_level",
                     "score_salary", "score_scale", "score_growth"]:
            val = getattr(data.scores, dim, None)
            if val is not None:
                updates.append(f"{dim}=?")
                params.append(val)
                score_fields.append(dim)

    # 状态变更
    if data.status is not None:
        if data.status != existing["status"]:
            conn.execute(
                "INSERT INTO status_history (application_id, date, status, note) VALUES (?, ?, ?, '')",
                (job_id, datetime.now().strftime("%m-%d"), data.status)
            )
        updates.append("status=?")
        params.append(data.status)

    if not updates:
        raise HTTPException(status_code=400, detail="没有需要更新的字段")

    # 重新计算总分（如果打分或地点变了）
    if data.scores is not None or data.location is not None:
        new_location = data.location if data.location is not None else existing["location"]
        scores_dict = {
            "score_hard": data.scores.score_hard if data.scores is not None else existing["score_hard"],
            "score_project": data.scores.score_project if data.scores is not None else existing["score_project"],
            "score_level": data.scores.score_level if data.scores is not None else existing["score_level"],
            "score_salary": data.scores.score_salary if data.scores is not None else existing["score_salary"],
            "score_scale": data.scores.score_scale if data.scores is not None else existing["score_scale"],
            "score_growth": data.scores.score_growth if data.scores is not None else existing["score_growth"],
        }
        total_info = compute_total_score(scores_dict, new_location)
        updates.append("total_score=?")
        params.append(total_info["total_score"])
        updates.append("location_bonus=?")
        params.append(total_info["location_bonus"])

    updates.append("last_updated=?")
    params.append(now)
    params.append(job_id)

    conn.execute(
        f"UPDATE applications SET {', '.join(updates)} WHERE id=?",
        params
    )
    conn.commit()

    row = dict_from_row(conn.execute("SELECT * FROM applications WHERE id=?", (job_id,)).fetchone())
    return _app_to_out(row)


# ============================================================
# PUT /api/jobs/{id}/status — 快捷状态更新
# ============================================================

@router.put("/{job_id}/status")
def update_status(job_id: str, data: StatusHistoryIn) -> ApplicationOut:
    conn = get_conn()
    existing = dict_from_row(conn.execute(
        "SELECT * FROM applications WHERE id=?", (job_id,)
    ).fetchone())
    if not existing:
        raise HTTPException(status_code=404, detail=f"未找到 ID 为 {job_id} 的记录")

    now = datetime.now()
    date_str = now.strftime("%m-%d")

    conn.execute(
        "INSERT INTO status_history (application_id, date, status, note) VALUES (?, ?, ?, ?)",
        (job_id, date_str, data.status, data.note)
    )
    conn.execute(
        "UPDATE applications SET status=?, last_updated=? WHERE id=?",
        (data.status, now.strftime("%m-%d %H:%M"), job_id)
    )
    conn.commit()

    row = dict_from_row(conn.execute("SELECT * FROM applications WHERE id=?", (job_id,)).fetchone())
    return _app_to_out(row)


# ============================================================
# DELETE /api/jobs/{id} — 删除
# ============================================================

@router.delete("/{job_id}", status_code=204)
def delete_job(job_id: str):
    conn = get_conn()
    existing = conn.execute("SELECT id FROM applications WHERE id=?", (job_id,)).fetchone()
    if not existing:
        raise HTTPException(status_code=404, detail=f"未找到 ID 为 {job_id} 的记录")
    conn.execute("DELETE FROM applications WHERE id=?", (job_id,))
    conn.commit()
    return None


# ============================================================
# DELETE /api/jobs/batch — 批量删除
# ============================================================

class BatchDeleteRequest(BaseModel):
    ids: list[str]

@router.post("/batch-delete", status_code=200)
def batch_delete_jobs(data: BatchDeleteRequest):
    """批量删除投递记录。"""
    if not data.ids:
        raise HTTPException(status_code=400, detail="ids 不能为空")
    conn = get_conn()
    deleted = 0
    errors = []
    for id_ in data.ids:
        try:
            cur = conn.execute("DELETE FROM applications WHERE id = ?", (id_,))
            if cur.rowcount > 0:
                deleted += 1
        except Exception as e:
            errors.append(f"{id_}: {str(e)}")
    conn.commit()
    return {"deleted": deleted, "errors": errors, "ids": data.ids}
