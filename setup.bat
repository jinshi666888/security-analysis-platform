@echo off
echo ============================================
echo Security Analysis Platform - 环境安装
echo ============================================

echo.
echo === 安装后端依赖 ===
cd /d %~dp0backend
C:\Users\Administrator\.workbuddy\binaries\python\versions\3.13.12\python.exe -m pip install -r requirements.txt

echo.
echo === 安装前端依赖 ===
cd /d %~dp0frontend
call npm install

echo.
echo ============================================
echo 安装完成！
echo ============================================
pause
