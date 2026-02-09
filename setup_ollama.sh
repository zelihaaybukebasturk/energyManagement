#!/bin/bash

echo "========================================"
echo "Ollama Kurulum ve Yapılandırma"
echo "========================================"
echo ""

echo "1. Ollama kurulumunu kontrol ediliyor..."
if ! command -v ollama &> /dev/null; then
    echo "Ollama bulunamadı!"
    echo ""
    echo "Lütfen Ollama'yı kurun:"
    echo "1. https://ollama.ai adresine gidin"
    echo "2. İşletim sisteminiz için installer'ı indirin"
    echo "3. Kurulumu tamamlayın"
    echo "4. Bu scripti tekrar çalıştırın"
    echo ""
    exit 1
fi

echo "Ollama bulundu!"
echo ""

echo "2. Ollama versiyonu kontrol ediliyor..."
ollama --version
echo ""

echo "3. Ollama servisi başlatılıyor..."
ollama serve &
sleep 3
echo ""

echo "4. Model indiriliyor (llama3.2)..."
echo "Bu biraz zaman alabilir..."
ollama pull llama3.2
echo ""

echo "5. Ortam değişkenleri ayarlanıyor..."
export LLM_PROVIDER=ollama
export OLLAMA_BASE_URL=http://localhost:11434
export OLLAMA_MODEL=llama3.2

# Add to .bashrc or .zshrc
if [ -f ~/.bashrc ]; then
    echo "" >> ~/.bashrc
    echo "# Ollama Configuration" >> ~/.bashrc
    echo "export LLM_PROVIDER=ollama" >> ~/.bashrc
    echo "export OLLAMA_BASE_URL=http://localhost:11434" >> ~/.bashrc
    echo "export OLLAMA_MODEL=llama3.2" >> ~/.bashrc
fi

if [ -f ~/.zshrc ]; then
    echo "" >> ~/.zshrc
    echo "# Ollama Configuration" >> ~/.zshrc
    echo "export LLM_PROVIDER=ollama" >> ~/.zshrc
    echo "export OLLAMA_BASE_URL=http://localhost:11434" >> ~/.zshrc
    echo "export OLLAMA_MODEL=llama3.2" >> ~/.zshrc
fi

echo ""
echo "========================================"
echo "Kurulum tamamlandı!"
echo "========================================"
echo ""
echo "Ollama yapılandırması:"
echo "- Provider: ollama"
echo "- Base URL: http://localhost:11434"
echo "- Model: llama3.2"
echo ""
echo "Not: Yeni bir terminal penceresi açmanız gerekebilir"
echo "     ortam değişkenlerinin yüklenmesi için."
echo ""
