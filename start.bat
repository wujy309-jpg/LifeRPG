@echo off
echo ========================================
echo    LifeRPG - 生活游戏化系统
echo ========================================
echo.
echo 正在启动服务器...
echo.
echo 访问地址: http://localhost:8000
echo API文档: http://localhost:8000/docs
echo.
echo 按 Ctrl+C 停止服务器
echo ========================================
echo.

cd backend
python main.py
pause
