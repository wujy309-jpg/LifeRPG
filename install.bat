@echo off
echo ========================================
echo    LifeRPG - 生活游戏化系统
echo ========================================
echo.

echo [1/3] 安装后端依赖...
cd backend
pip install -r requirements.txt
cd ..

echo.
echo [2/3] 安装前端依赖...
cd frontend
npm install
cd ..

echo.
echo [3/3] 构建前端...
cd frontend
npm run build
cd ..

echo.
echo ========================================
echo    安装完成！
echo ========================================
echo.
echo 运行 start.bat 启动服务器
echo.
pause
