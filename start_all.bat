@echo off
echo Starting AI-Driven Building Energy Efficiency System...
echo.

echo Starting backend server...
start "Backend Server" cmd /k "python start_server.py"

timeout /t 3 /nobreak >nul

echo Starting frontend server...
start "Frontend Server" cmd /k "python serve_frontend.py"

echo.
echo Both servers are starting...
echo Backend API: http://localhost:8000
echo Frontend: http://localhost:8080
echo.
echo Press any key to exit this window (servers will continue running)...
pause >nul
