#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
求职跟踪系统 - FastAPI 入口
============================
单进程模式：python main.py  →  http://localhost:8004（后端 + 前端静态文件）
开发模式：  uvicorn main:app --reload --port 8004  +  npm run dev（Vite :5173）
Docker模式：docker-compose up（后端 :8004 + Nginx :5173）
"""

import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from database import init_db
from routes import jobs, stats, import_jobs

app = FastAPI(
    title="求职跟踪系统",
    description="AI 开发岗投递跟踪 —— 六维打分 + 状态管理 + 公司调研",
    version="2.0.0",
)

# CORS（开发环境允许前端跨域）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册 API 路由
app.include_router(jobs.router)
app.include_router(stats.router)
app.include_router(import_jobs.router)

# 静态文件目录（前端构建产物输出到这里）
STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")
_frontend_built = os.path.isdir(STATIC_DIR) and os.path.isfile(os.path.join(STATIC_DIR, "index.html"))


@app.on_event("startup")
def startup():
    """启动时初始化数据库。"""
    init_db()
    print("[job-tracker] 数据库初始化完成")
    if _frontend_built:
        print("[job-tracker] 前端已就绪 → 打开 http://localhost:8004 即可使用")


@app.get("/api/health")
def health():
    return {"status": "ok", "version": "2.0.0", "frontend": _frontend_built}


# ---- SPA 静态文件服务（仅在 API 路由之后注册，避免拦截 API 请求） ----

if _frontend_built:
    from fastapi.responses import FileResponse

    @app.get("/{full_path:path}")
    async def serve_frontend(full_path: str):
        """
        SPA fallback：所有非 /api/ 的 GET 请求 → 尝试返回静态文件 → 否则 index.html。
        仅处理 GET 请求，不影响 API 的 POST/PUT/DELETE。
        """
        file_path = os.path.join(STATIC_DIR, full_path)
        if os.path.isfile(file_path):
            return FileResponse(file_path)
        return FileResponse(os.path.join(STATIC_DIR, "index.html"))


if __name__ == "__main__":
    import uvicorn
    print("=" * 55)
    print("  求职跟踪系统 v2.0")
    print(f"  打开浏览器 → http://localhost:8004")
    print("=" * 55)
    uvicorn.run(app, host="0.0.0.0", port=8004)

