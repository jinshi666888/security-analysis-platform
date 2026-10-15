@echo off
echo 启动前端服务 (http://localhost:5173)
cd /d %~dp0frontend
call npm run dev
pause
