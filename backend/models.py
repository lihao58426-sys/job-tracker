#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
求职跟踪系统 - Pydantic 模型
请求/响应的数据结构定义。
"""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


# ============================================================
# 六维打分
# ============================================================

class ScoresIn(BaseModel):
    score_hard: float = Field(default=0, ge=0, le=10, description="① 硬能力匹配度")
    score_project: float = Field(default=0, ge=0, le=10, description="② 项目经验契合度")
    score_level: float = Field(default=0, ge=0, le=10, description="③ 经验层级适配度")
    score_salary: float = Field(default=0, ge=0, le=10, description="④ 薪资期望适配度")
    score_scale: float = Field(default=0, ge=0, le=10, description="⑤ 企业规模适配度")
    score_growth: float = Field(default=0, ge=0, le=10, description="⑥ 成长空间适配度")
    score_jd_match: float = Field(default=0, ge=0, le=10, description="⑦ JD-能力匹配度")


class ScoresOut(ScoresIn):
    total_score: float = 0
    location_bonus: int = 0


# ============================================================
# 公司调研
# ============================================================

class ResearchIn(BaseModel):
    core_business: str = Field(default="", alias="research_core_business")
    tech_stack: str = Field(default="", alias="research_tech_stack")
    team_features: str = Field(default="", alias="research_team_features")
    match_advantages: str = Field(default="", alias="research_match_advantages")
    weakness_strategy: str = Field(default="", alias="research_weakness_strategy")

    model_config = {"populate_by_name": True}


class ResearchOut(BaseModel):
    core_business: str = ""
    tech_stack: str = ""
    team_features: str = ""
    match_advantages: str = ""
    weakness_strategy: str = ""


# ============================================================
# 状态历史
# ============================================================

class StatusHistoryIn(BaseModel):
    status: str
    note: str = ""


class StatusHistoryOut(BaseModel):
    id: int
    application_id: str
    date: str
    status: str
    note: str = ""


# ============================================================
# 投递记录
# ============================================================

class ApplicationCreate(BaseModel):
    """新增一条投递记录。"""
    company: str
    position: str
    date: str = Field(default_factory=lambda: datetime.now().strftime("%m-%d"))
    salary_range: str = ""
    location: str = ""
    url: str = ""
    channel: str = ""
    resume_version: str = "v1"
    status: str = "未投递"
    scores: ScoresIn = Field(default_factory=ScoresIn)
    verdict: str = ""
    job_type: str = ""
    notes: str = ""
    # 公司调研
    research_core_business: str = ""
    research_tech_stack: str = ""
    research_team_features: str = ""
    research_match_advantages: str = ""
    research_weakness_strategy: str = ""


class ApplicationUpdate(BaseModel):
    """更新投递记录（所有字段可选）。"""
    date: Optional[str] = None
    salary_range: Optional[str] = None
    location: Optional[str] = None
    url: Optional[str] = None
    channel: Optional[str] = None
    resume_version: Optional[str] = None
    status: Optional[str] = None
    scores: Optional[ScoresIn] = None
    verdict: Optional[str] = None
    job_type: Optional[str] = None
    notes: Optional[str] = None
    research_core_business: Optional[str] = None
    research_tech_stack: Optional[str] = None
    research_team_features: Optional[str] = None
    research_match_advantages: Optional[str] = None
    research_weakness_strategy: Optional[str] = None


class ApplicationOut(BaseModel):
    """完整投递记录（响应）。"""
    id: str
    date: str
    company: str
    position: str
    salary_range: str = ""
    salary_min: int = 0
    salary_max: int = 0
    location: str = ""
    location_bonus: int = 0
    url: str = ""
    channel: str = ""
    resume_version: str = "v1"
    status: str = "未投递"
    scores: ScoresOut = Field(default_factory=ScoresOut)
    verdict: str = ""
    job_type: str = ""
    notes: str = ""
    # 公司调研
    research_core_business: str = ""
    research_tech_stack: str = ""
    research_team_features: str = ""
    research_match_advantages: str = ""
    research_weakness_strategy: str = ""
    # 状态历史
    status_history: list[StatusHistoryOut] = []
    last_updated: str = ""
    created_at: str = ""


class ApplicationListOut(BaseModel):
    """列表概览（精简字段）。"""
    id: str
    date: str
    company: str
    position: str
    salary_range: str
    location: str
    location_bonus: int
    status: str
    total_score: float
    verdict: str
    job_type: str
    url: str


# ============================================================
# 统计
# ============================================================

class DashboardStats(BaseModel):
    total: int = 0
    active: int = 0
    interviewing: int = 0
    offered: int = 0
    rejected: int = 0
    by_status: dict = {}
    by_verdict: dict = {}
    by_location: dict = {}
    top5: list[ApplicationListOut] = []


# ============================================================
# 每日日志
# ============================================================

class DailyLogCreate(BaseModel):
    date: str = Field(default_factory=lambda: datetime.now().strftime("%m-%d"))
    content: str = "{}"


class DailyLogOut(BaseModel):
    id: int
    date: str
    content: str
    created_at: str = ""
