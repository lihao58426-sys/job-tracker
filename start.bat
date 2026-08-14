@echo off
chcp 65001 >nul
title 求职跟踪系统

cd /d "%~dp0backend"

echo ========================================
echo   求职跟踪系统 v2.0
echo ========================================
echo.

REM 检查前端是否已构建
if exist "static\index.html" (
    echo [OK] 前端已构建 → 单进程模式
    echo.
    echo 启动服务: http://localhost:8004
    echo.
    start "" http://localhost:8004
    python main.py
) else (
    echo [提示] 前端尚未构建，仅启动 API 服务。
    echo       API 地址: http://localhost:8004/docs
    echo.
    echo 构建前端（需要 Node.js）：
    echo   cd ..\frontend
    echo   npm install
    echo   npm run build
    echo.
    echo 或使用 Docker：
    echo   cd ..
    echo   docker-compose up -d
    echo.
    echo 启动 API 服务...
    start "" http://localhost:8004/docs
    python -m uvicorn main:app --host 0.0.0.0 --port 8004
)

pause
