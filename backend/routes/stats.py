#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
求职跟踪系统 - 仪表盘统计路由
"""

from fastapi import APIRouter
from database import get_conn, dicts_from_rows
from models import DashboardStats, ApplicationListOut

router = APIRouter(prefix="/api/stats", tags=["stats"])


@router.get("/dashboard")
def get_dashboard() -> DashboardStats:
    """仪表盘统计数据。"""
    conn = get_conn()
    apps = dicts_from_rows(conn.execute("SELECT * FROM applications").fetchall())

    total = len(apps)
    by_status = {}
    for a in apps:
        s = a["status"]
        by_status[s] = by_status.get(s, 0) + 1

    active = total - by_status.get("挂掉", 0) - by_status.get("已拒", 0) - by_status.get("入职", 0)
    interviewing = sum(1 for a in apps if a["status"] in ["一面", "二面", "三面", "HR面"])
    offered = by_status.get("Offer", 0) + by_status.get("入职", 0)
    rejected = by_status.get("挂掉", 0) + by_status.get("已拒", 0)

    by_verdict = {}
    for a in apps:
        v = a["verdict"] or "未评分"
        by_verdict[v] = by_verdict.get(v, 0) + 1

    by_location = {}
    for a in apps:
        loc = a["location"] or "未知"
        # 取城市名
        city = loc.split("-")[0] if "-" in loc else loc
        by_location[city] = by_location.get(city, 0) + 1

    # Top 5 按总分
    sorted_apps = sorted(apps, key=lambda a: a["total_score"] or 0, reverse=True)
    top5_rows = sorted_apps[:5]
    top5 = [
        ApplicationListOut(
            id=a["id"], date=a["date"] or "", company=a["company"], position=a["position"],
            salary_range=a["salary_range"] or "", location=a["location"] or "",
            location_bonus=a["location_bonus"] or 0, status=a["status"] or "已投递",
            total_score=a["total_score"] or 0, verdict=a["verdict"] or "",
            job_type=a["job_type"] or "", url=a["url"] or "",
        )
        for a in top5_rows
    ]

    return DashboardStats(
        total=total, active=active, interviewing=interviewing,
        offered=offered, rejected=rejected,
        by_status=by_status, by_verdict=by_verdict, by_location=by_location,
        top5=top5,
    )


@router.get("/funnel")
def get_funnel():
    """投递漏斗数据（给 ECharts）。"""
    conn = get_conn()
    apps = dicts_from_rows(conn.execute("SELECT status FROM applications").fetchall())

    stages = [
        ("未投递", "未投递"),
        ("已投递", "已投递"),
        ("已读", "已读"),
        ("筛过", "筛过/笔试"),
        ("面试", "面试中"),  # 合并 一面~HR面
        ("Offer", "Offer/入职"),
    ]

    funnel = []
    for stage_key, stage_label in stages:
        if stage_key == "面试":
            count = sum(1 for a in apps if a["status"] in ["一面", "二面", "三面", "HR面"])
        elif stage_key == "Offer":
            count = sum(1 for a in apps if a["status"] in ["Offer", "入职"])
        elif stage_key == "筛过":
            count = sum(1 for a in apps if a["status"] in ["筛过", "笔试"])
        else:
            count = sum(1 for a in apps if a["status"] == stage_key)
        funnel.append({"name": stage_label, "value": count})

    return funnel
