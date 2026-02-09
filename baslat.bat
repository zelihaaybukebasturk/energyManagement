@echo off
title 3GEN Energy - Baslat
echo.
echo Ollama kullaniliyor. Backend baslatiliyor...
echo.

set LLM_PROVIDER=ollama
set OLLAMA_BASE_URL=http://localhost:11434
set OLLAMA_MODEL=llama3.2

start "Backend (API)" cmd /k "set LLM_PROVIDER=ollama && set OLLAMA_BASE_URL=http://localhost:11434 && set OLLAMA_MODEL=llama3.2 && python start_server.py"

timeout /t 4 /nobreak >nul

echo Frontend baslatiliyor...
start "Frontend" cmd /k "python serve_frontend.py"

echo.
echo ========================================
echo   Backend:  http://localhost:8000
echo   Frontend: http://localhost:8080
echo ========================================
echo.
echo Tarayicida http://localhost:8080 adresini acin.
echo Ollama uygulamasinin acik oldugundan emin olun.
echo.
pause
