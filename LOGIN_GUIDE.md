# Login ve UI Güncellemeleri

Modern login sistemi ve güncellenmiş UI eklendi.

## 🎨 Yeni Özellikler

### 1. Login Sayfası (`frontend/login.html`)
- Modern, responsive tasarım
- Gradient arka plan
- Animasyonlu giriş formu
- Hata mesajları gösterimi
- Demo modu seçeneği

### 2. Dashboard Sayfası (`frontend/dashboard.html`)
- Modern navbar (üst menü)
- Kullanıcı bilgisi ve çıkış butonu
- Güncellenmiş analiz formu
- Daha iyi görselleştirme
- Responsive tasarım

### 3. Authentication Backend
- JWT token tabanlı authentication
- `/auth/login` endpoint
- `/auth/me` endpoint (kullanıcı bilgisi)
- Güvenli şifre hashleme (bcrypt)

## 🔐 Varsayılan Kullanıcılar

**Admin:**
- Kullanıcı adı: `admin`
- Şifre: `admin123`

**Demo:**
- Kullanıcı adı: `demo`
- Şifre: `demo123`

**Not:** Production'da mutlaka şifreleri değiştirin!

## 🚀 Kullanım

1. **Backend'i başlatın:**
   ```bash
   python start_server.py
   ```

2. **Frontend'i başlatın:**
   ```bash
   python serve_frontend.py
   ```

3. **Tarayıcıda açın:**
   - `http://localhost:8080/login.html` veya
   - `http://localhost:8080` (otomatik login'e yönlendirir)

4. **Giriş yapın:**
   - Yukarıdaki kullanıcı adı/şifre ile giriş yapın
   - Veya "Demo Modu" ile giriş yapmadan devam edin

## 📦 Gerekli Paketler

```bash
pip install python-jose[cryptography] passlib[bcrypt]
```

Eğer paketler yüklü değilse, sistem basit token tabanlı authentication kullanır (JWT olmadan).

## 🎯 Özellikler

- ✅ Modern, responsive UI
- ✅ JWT token authentication
- ✅ Güvenli şifre hashleme
- ✅ Kullanıcı oturum yönetimi
- ✅ Demo modu desteği
- ✅ Otomatik yönlendirme
- ✅ Hata yönetimi

## 🔄 Sayfa Yapısı

```
/login.html → Giriş sayfası
  ↓ (giriş başarılı)
/dashboard.html → Ana analiz sayfası
```

## 💡 Notlar

- Token localStorage'da saklanır
- Token süresi: 30 gün (JWT kullanılıyorsa)
- Demo modu: Giriş yapmadan kullanım için
- Çıkış: Navbar'daki "Çıkış" butonu
