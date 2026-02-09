"""
Ollama bağlantısını kontrol eden script
"""

import requests
import sys

def check_ollama():
    """Ollama servisinin çalışıp çalışmadığını kontrol et."""
    base_url = "http://localhost:11434"
    
    print("Ollama bağlantısı kontrol ediliyor...")
    print(f"URL: {base_url}")
    print()
    
    try:
        # Check if Ollama is running
        response = requests.get(f"{base_url}/api/tags", timeout=5)
        if response.status_code == 200:
            models = response.json().get("models", [])
            print("✅ Ollama servisi çalışıyor!")
            print()
            print("İndirilmiş modeller:")
            if models:
                for model in models:
                    name = model.get("name", "Unknown")
                    size = model.get("size", 0) / (1024**3)  # Convert to GB
                    print(f"  - {name} ({size:.2f} GB)")
            else:
                print("  (Henüz model indirilmemiş)")
            print()
            print("Önerilen modeli indirmek için:")
            print("  ollama pull llama3.2")
            return True
        else:
            print(f"❌ Ollama servisi yanıt vermiyor (Status: {response.status_code})")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ Ollama servisine bağlanılamıyor!")
        print()
        print("Ollama'yı başlatmak için:")
        print("  ollama serve")
        return False
    except Exception as e:
        print(f"❌ Hata: {e}")
        return False

if __name__ == "__main__":
    success = check_ollama()
    sys.exit(0 if success else 1)
