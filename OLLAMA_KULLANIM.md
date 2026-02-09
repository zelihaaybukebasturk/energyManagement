# Ollama Kullanım Rehberi

Ollama indirildi. Sistemi kullanmak için aşağıdaki adımları izleyin.

## 1. Model indirme

**Seçenek A: Küçük model (hızlı indirme, ~500 MB)**  
Yeni bir terminal/PowerShell açın ve:

```powershell
& "$env:LOCALAPPDATA\Programs\Ollama\ollama.exe" pull tinyllama
```

**Seçenek B: Varsayılan model llama3.2 (~2 GB)**  
İndirme uzun sürebilir, terminali kapatmayın:

```powershell
& "$env:LOCALAPPDATA\Programs\Ollama\ollama.exe" pull llama3.2
```

İndirme bittiğinde "success" benzeri bir mesaj görürsünüz.

## 2. Ollama servisini çalıştırma

- Ollama genelde kurulumla birlikte arka planda çalışır.
- Çalışmıyorsa: **Ollama uygulamasını** masaüstü veya Başlat menüsünden açın; servis otomatik başlar.
- Elle başlatmak isterseniz:

```powershell
Start-Process "$env:LOCALAPPDATA\Programs\Ollama\ollama.exe" -ArgumentList "serve"
```

## 3. Uygulamanın Ollama modelini seçmesi

Proje varsayılan olarak **llama3.2** kullanır.  
**tinyllama** indirdiyseniz, ortam değişkeni ile modeli değiştirin:

```powershell
$env:OLLAMA_MODEL = "tinyllama"
```

Kalıcı yapmak için (isteğe bağlı):

```powershell
[System.Environment]::SetEnvironmentVariable("OLLAMA_MODEL", "tinyllama", "User")
```

## 4. Projeyi çalıştırma

1. Backend:
   ```powershell
   python start_server.py
   ```

2. Yeni bir terminalde frontend:
   ```powershell
   python serve_frontend.py
   ```

3. Tarayıcıda: **http://localhost:8080**

## 5. Kontrol

Ollama’nın çalıştığını ve modelleri görmek için:

```powershell
python check_ollama.py
```

Veya doğrudan:

```powershell
& "$env:LOCALAPPDATA\Programs\Ollama\ollama.exe" list
```

---

**Özet:**  
1) `ollama pull tinyllama` veya `ollama pull llama3.2`  
2) Ollama uygulaması açık olsun (veya `ollama serve`)  
3) `python start_server.py` ve `python serve_frontend.py`  
4) http://localhost:8080
