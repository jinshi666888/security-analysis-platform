@echo off
echo 启动后端服务 (http://127.0.0.1:8000)
cd /d %~dp0backend
C:\Users\Administrator\.workbuddy\binaries\python\versions\3.13.12\python.exe -m uvicorn app.main:app --host 0.0.0.0 --port 8000
pause
