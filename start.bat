@echo off
echo Starting LifeRPG Backend...
start cmd /k "cd backend && python main.py"

timeout /t 2 /nobreak > nul

echo Starting LifeRPG Frontend...
start cmd /k "cd frontend && npm run dev"

echo Done!
