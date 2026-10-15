@echo off
echo ============================================
echo 启动 Security Analysis Platform
echo ============================================
echo.
echo 后端: http://127.0.0.1:8000
echo 前端: http://localhost:5173
echo.

start "Backend" cmd /k "cd /d %~dp0backend && C:\Users\Administrator\.workbuddy\binaries\python\versions\3.13.12\python.exe -m uvicorn app.main:app --host 0.0.0.0 --port 8000"

timeout /t 3 /nobreak >nul

start "Frontend" cmd /k "cd /d %~dp0frontend && npm run dev"

echo 两个服务已在新窗口启动。
echo 默认账号: admin / admin123
pause
