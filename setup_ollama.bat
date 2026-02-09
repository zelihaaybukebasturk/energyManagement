@echo off
echo ========================================
echo Ollama Kurulum ve Yapılandırma
echo ========================================
echo.

echo 1. Ollama kurulumunu kontrol ediliyor...
where ollama >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo Ollama bulunamadi!
    echo.
    echo Lutfen Ollama'yi kurun:
    echo 1. https://ollama.ai adresine gidin
    echo 2. Windows icin installer'i indirin
    echo 3. Kurulumu tamamlayin
    echo 4. Bu scripti tekrar calistirin
    echo.
    pause
    exit /b 1
)

echo Ollama bulundu!
echo.

echo 2. Ollama versiyonu kontrol ediliyor...
ollama --version
echo.

echo 3. Ollama servisi baslatiliyor...
start "Ollama Service" cmd /k "ollama serve"
timeout /t 3 /nobreak >nul
echo.

echo 4. Model indiriliyor (llama3.2)...
echo Bu biraz zaman alabilir...
ollama pull llama3.2
echo.

echo 5. Ortam degiskenleri ayarlaniyor...
setx LLM_PROVIDER "ollama" >nul 2>&1
setx OLLAMA_BASE_URL "http://localhost:11434" >nul 2>&1
setx OLLAMA_MODEL "llama3.2" >nul 2>&1

set LLM_PROVIDER=ollama
set OLLAMA_BASE_URL=http://localhost:11434
set OLLAMA_MODEL=llama3.2

echo.
echo ========================================
echo Kurulum tamamlandi!
echo ========================================
echo.
echo Ollama yapilandirmasi:
echo - Provider: ollama
echo - Base URL: http://localhost:11434
echo - Model: llama3.2
echo.
echo Not: Yeni bir terminal penceresi acmaniz gerekebilir
echo      ortam degiskenlerinin yuklenmesi icin.
echo.
pause
