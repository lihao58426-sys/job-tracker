#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
求职跟踪系统 - 数据库层
SQLite 单文件，零配置。建表 + 基本 CRUD 封装。
"""

import sqlite3
import os
import json
from datetime import datetime

DB_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(DB_DIR, "tracker.db")


def get_conn():
    """获取数据库连接（启用 WAL 模式 + 外键）。"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db():
    """建表（幂等，IF NOT EXISTS）。"""
    conn = get_conn()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS applications (
            id TEXT PRIMARY KEY,
            date TEXT NOT NULL DEFAULT '',
            company TEXT NOT NULL,
            position TEXT NOT NULL,
            salary_range TEXT DEFAULT '',
            salary_min INTEGER DEFAULT 0,
            salary_max INTEGER DEFAULT 0,
            location TEXT DEFAULT '',
            location_bonus INTEGER DEFAULT 0,
            url TEXT DEFAULT '',
            channel TEXT DEFAULT '',
            resume_version TEXT DEFAULT 'v1',
            status TEXT DEFAULT '未投递',
            -- 六维打分
            score_hard REAL DEFAULT 0,
            score_project REAL DEFAULT 0,
            score_level REAL DEFAULT 0,
            score_salary REAL DEFAULT 0,
            score_scale REAL DEFAULT 0,
            score_growth REAL DEFAULT 0,
            score_jd_match REAL DEFAULT 0,
            jd_coverage REAL DEFAULT 0,
            jd_hard_damage TEXT DEFAULT '',
            jd_gaps TEXT DEFAULT '',
            total_score REAL DEFAULT 0,
            verdict TEXT DEFAULT '',
            -- 公司调研
            research_core_business TEXT DEFAULT '',
            research_tech_stack TEXT DEFAULT '',
            research_team_features TEXT DEFAULT '',
            research_match_advantages TEXT DEFAULT '',
            research_weakness_strategy TEXT DEFAULT '',
            -- 其他
            job_type TEXT DEFAULT '',
            notes TEXT DEFAULT '',
            last_updated TEXT DEFAULT '',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS status_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            application_id TEXT NOT NULL,
            date TEXT NOT NULL DEFAULT '',
            status TEXT NOT NULL DEFAULT '',
            note TEXT DEFAULT '',
            FOREIGN KEY (application_id) REFERENCES applications(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS daily_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT UNIQUE NOT NULL,
            content TEXT DEFAULT '{}',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );
    """)
    # v3.0 迁移：添加七维打分 + JD 匹配字段
    for col, col_type in [
        ("score_jd_match", "REAL DEFAULT 0"),
        ("jd_coverage", "REAL DEFAULT 0"),
        ("jd_hard_damage", "TEXT DEFAULT ''"),
        ("jd_gaps", "TEXT DEFAULT ''"),
    ]:
        try:
            conn.execute(f"ALTER TABLE applications ADD COLUMN {col} {col_type}")
        except sqlite3.OperationalError:
            pass  # 列已存在

    conn.commit()
    conn.close()


def dict_from_row(row) -> dict:
    """sqlite3.Row → dict。"""
    if row is None:
        return None
    return dict(row)


def dicts_from_rows(rows) -> list[dict]:
    """sqlite3.Row 列表 → dict 列表。"""
    return [dict(r) for r in rows]
