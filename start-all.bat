@echo off
echo ========================================
echo   LifeRPG - 生活游戏化系统
echo ========================================
echo.

echo [1/2] 启动后端服务...
start "LifeRPG Backend" cmd /k "cd /d %~dp0backend && python main.py"

echo [2/2] 启动前端服务...
start "LifeRPG Frontend" cmd /k "cd /d %~dp0frontend && npm run dev"

echo.
echo ========================================
echo   启动完成！
echo   后端: http://localhost:8000
echo   前端: http://localhost:5173
echo ========================================
echo.
echo 按任意键关闭此窗口...
pause > nul
