@echo off
echo ========================================
echo    LifeRPG - 开发模式
echo ========================================
echo.

echo [1/2] 启动后端服务器...
start "LifeRPG Backend" cmd /k "cd backend && python main.py"

echo [2/2] 启动前端开发服务器...
start "LifeRPG Frontend" cmd /k "cd frontend && npm run dev"

echo.
echo ========================================
echo    开发服务器已启动！
echo ========================================
echo.
echo 前端: http://localhost:5173
echo 后端: http://localhost:8000
echo API文档: http://localhost:8000/docs
echo.
echo 关闭此窗口不会停止服务器
echo 请手动关闭各个终端窗口
echo ========================================
pause
