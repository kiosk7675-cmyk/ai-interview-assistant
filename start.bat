@echo off
chcp 65001 >nul
title InterviewPrep Server
echo ====================================
echo   InterviewPrep 面试备考助手
echo ====================================
echo.

cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
    echo [错误] 未找到虚拟环境，请检查 .venv 目录
    pause
    exit /b 1
)

echo [启动中] 正在加载模型和服务...
echo [访问] 首页: http://localhost:9900
echo [访问] 面试备考: http://localhost:9900/interview
echo [访问] API文档: http://localhost:9900/docs
echo.
echo 按 Ctrl+C 停止服务
echo ====================================
echo.

.venv\Scripts\python.exe -m uvicorn app.main:app --host 0.0.0.0 --port 9900

pause
