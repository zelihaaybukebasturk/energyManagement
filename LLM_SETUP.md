# LLM Kurulum Rehberi

Bu sistem, AI destekli açıklamalar için çeşitli LLM sağlayıcılarını destekler.

## 🚀 Hızlı Başlangıç

### Seçenek 1: OpenAI (Önerilen - En İyi Sonuçlar)

1. **API Key Alın**
   - https://platform.openai.com/api-keys adresinden API key oluşturun

2. **Paketi Yükleyin**
   ```bash
   pip install openai
   ```

3. **Ortam Değişkenlerini Ayarlayın**
   ```bash
   # Windows
   set OPENAI_API_KEY=your-api-key-here
   set LLM_PROVIDER=openai

   # Linux/Mac
   export OPENAI_API_KEY=your-api-key-here
   export LLM_PROVIDER=openai
   ```

4. **Varsayılan Model**: `gpt-4o-mini` (maliyet-etkin)
   - Farklı bir model kullanmak için `backend/llm_client.py` dosyasını düzenleyin

### Seçenek 2: Anthropic Claude

1. **API Key Alın**
   - https://console.anthropic.com/ adresinden API key oluşturun

2. **Paketi Yükleyin**
   ```bash
   pip install anthropic
   ```

3. **Ortam Değişkenlerini Ayarlayın**
   ```bash
   export ANTHROPIC_API_KEY=your-api-key-here
   export LLM_PROVIDER=anthropic
   ```

### Seçenek 3: Ollama (Yerel, Ücretsiz) - **ÖNERİLEN**

**Otomatik Kurulum (Kolay):**

Windows:
```bash
setup_ollama.bat
```

Linux/Mac:
```bash
chmod +x setup_ollama.sh
./setup_ollama.sh
```

**Manuel Kurulum:**

1. **Ollama'yı Yükleyin**
   - https://ollama.ai adresinden indirin ve kurun

2. **Model İndirin**
   ```bash
   ollama pull llama3.2
   # veya
   ollama pull mistral
   # veya
   ollama pull codellama
   ```

3. **Ollama'yı Başlatın**
   ```bash
   ollama serve
   ```

4. **Ortam Değişkenlerini Ayarlayın**
   
   Windows:
   ```bash
   set LLM_PROVIDER=ollama
   set OLLAMA_BASE_URL=http://localhost:11434
   set OLLAMA_MODEL=llama3.2
   ```
   
   Linux/Mac:
   ```bash
   export LLM_PROVIDER=ollama
   export OLLAMA_BASE_URL=http://localhost:11434
   export OLLAMA_MODEL=llama3.2
   ```

**Not:** Sistem varsayılan olarak Ollama'yı otomatik algılar ve kullanır (eğer başka bir LLM yapılandırılmamışsa).

## 🌍 Dil Yönetimi (2 Aşamalı: Analiz + Türkçe Çeviri)

Bu projede çıktıların Türkçe olması için iki aşamalı bir akış desteklenir:

- **Ana model (Analiz/Senaryo)**: `LLM_PROVIDER` + `OLLAMA_MODEL` (veya OpenAI/Anthropic)
- **İkinci model (Türkçe çeviri)**: `TRANSLATION_OLLAMA_MODEL` (Ollama üzerinden ayrı bir çağrı)

Örnek (Windows):

```powershell
set LLM_PROVIDER=ollama
set OLLAMA_MODEL=llama3.2

set TRANSLATION_OLLAMA_MODEL=llama3.2
```

Not: İkinci model ayarlı değilse sistem çeviri için `deep-translator` (Google Translate) ile geriye dönük bir yedek yol kullanabilir.

## 🧠 Knowledge Base’i Zenginleştirme ve “Modeli Uyarlama”

Bu projede “eğitme” ihtiyacını azaltmak için **RAG** yaklaşımı kullanılır:
- `knowledge_base/` altındaki JSON içerikleri RAG tarafından bağlama eklenir.
- Yeni “what-if” yorumları için `whatif_playbook.json` eklendi.

İsterseniz Ollama’da enerji danışmanı tarzını sabitlemek için “custom model” oluşturabilirsiniz (tam fine-tune değildir; sistem prompt/parametre uyarlamasıdır):

```powershell
ollama create 3gen-energy-tr -f Modelfile.energy-tr
```

Sonra projede:

```powershell
set OLLAMA_MODEL=3gen-energy-tr
```

### Seçenek 4: LLM Olmadan (Şablon Tabanlı)

LLM kurulumu yapmazsanız, sistem otomatik olarak şablon tabanlı açıklamalar kullanır. Bu durumda:
- ✅ API key gerekmez
- ✅ Ücretsizdir
- ✅ Hemen çalışır
- ⚠️ Daha az esnek ve kişiselleştirilmiş açıklamalar

## 🔧 Yapılandırma

### Ortam Değişkenleri

`.env` dosyası oluşturun (veya sistem ortam değişkenlerini kullanın):

```bash
# LLM Provider seçimi
LLM_PROVIDER=openai  # veya anthropic, ollama

# OpenAI
OPENAI_API_KEY=sk-...

# Anthropic
ANTHROPIC_API_KEY=sk-ant-...

# Ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.2
```

### Kod İçinde Kullanım

```python
from backend.llm_client import get_llm_client

# Otomatik algılama
llm = get_llm_client()

# Manuel seçim
llm = get_llm_client(provider="openai")
```

## 📊 Model Karşılaştırması

| Provider | Model | Maliyet | Hız | Kalite | Yerel |
|----------|-------|---------|-----|--------|-------|
| OpenAI | gpt-4o-mini | Düşük | Hızlı | Yüksek | ❌ |
| OpenAI | gpt-4o | Orta | Orta | Çok Yüksek | ❌ |
| Anthropic | claude-3-haiku | Düşük | Hızlı | Yüksek | ❌ |
| Anthropic | claude-3-opus | Yüksek | Yavaş | Çok Yüksek | ❌ |
| Ollama | llama3.2 | Ücretsiz | Orta | İyi | ✅ |
| Ollama | mistral | Ücretsiz | Hızlı | İyi | ✅ |

## 🧪 Test Etme

LLM'in çalışıp çalışmadığını test etmek için:

```bash
python test_system.py
```

API yanıtında `"llm_used": true` görünüyorsa LLM başarıyla kullanılıyor demektir.

## ❓ Sorun Giderme

### "LLM integration is not configured" mesajı
- Ortam değişkenlerinin doğru ayarlandığından emin olun
- API key'lerin geçerli olduğunu kontrol edin
- Paketlerin yüklü olduğunu doğrulayın

### Ollama bağlantı hatası
- Ollama'nın çalıştığından emin olun: `ollama serve`
- Port 11434'ün açık olduğunu kontrol edin
- Model'in indirildiğini doğrulayın: `ollama list`

### API rate limit hatası
- Daha yavaş bir model kullanın
- İstekler arasında bekleme ekleyin
- API planınızı kontrol edin

## 💡 Öneriler

- **Geliştirme için**: Ollama (ücretsiz, yerel)
- **Demo için**: OpenAI gpt-4o-mini (düşük maliyet, iyi kalite)
- **Production için**: OpenAI gpt-4o veya Anthropic Claude (en iyi kalite)
