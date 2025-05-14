# SIAF - Ses ve Işık Adaptif Filtreleme Sistemi

SIAF, çevresel ses ve ışık koşullarını analiz ederek otomatik adaptif filtreleme yapan bir sistemdir. Sistem, kullanıcı geri bildirimleriyle öğrenerek ses filtreleme parametrelerini optimize eder ve ortam ışığına göre ekran parlaklığını ayarlar.

## 🚀 Özellikler

### Ses Modülü
- Canlı ses filtreleme
- Otomatik frekans analizi
- Kullanıcı geri bildirimine dayalı öğrenme
- OBS entegrasyonu ile ses kaydı
- Mel spectrogram görselleştirme

### Işık Modülü
- Ortam ışığı ölçümü
- Otomatik ekran parlaklığı ayarlama
- PWM flicker analizi
- Kamera entegrasyonu

## 📋 Gereksinimler

### Yazılım Gereksinimleri
- Python 3.8 veya üzeri
- OBS Studio
- FFmpeg

### Donanım Gereksinimleri
- Mikrofon
- Kamera
- Ses kartı (Voicemeeter ve VB-CABLE önerilir)

## 🛠️ Kurulum

1. Python bağımlılıklarını yükleyin:
```bash
pip install -r requirements.txt
```

2. OBS Studio'yu yükleyin ve WebSocket sunucusunu etkinleştirin:
   - OBS Studio'yu açın
   - Araçlar > WebSocket Sunucu Ayarları
   - Sunucuyu etkinleştirin
   - Port: 4444
   - Şifre: 121361

3. FFmpeg'i yükleyin ve sistem PATH'ine ekleyin

4. Voicemeeter ve VB-CABLE'ı yükleyin (ses filtreleme için)

### VoiceMeeter Yapılandırması

VoiceMeeter ayarlarını yüklemek için:

1. VoiceMeeter'ı açın
2. Menüden "Menu" > "Load Settings" seçeneğine tıklayın
3. `config/voicemeeter_settings.xml` dosyasını seçin

Not: VoiceMeeter ayarları projenin `config` klasöründe bulunmaktadır. Bu ayarlar:
- Ses seviyesi ayarları
- Filtreleme parametreleri
içermektedir.

Kullanıcının, kullanmak istediği çıkış cihazını (Kulaklık, hoparlör) uygulamanın A1 Hardware Out kısmında seçmesi gerekiyor. (WDM önerilir)

## 💻 Kullanım

### GUI Modu
```bash
python src/mainGui.py
```

### CLI Modu
```bash
python src/mainCli.py
```

## 📁 Proje Yapısı

```
projectSIAF/
├── src/
│   ├── SesModul/
│   │   ├── sesPanel.py      # Ses modülü GUI
│   │   ├── sesIsleyici.py   # Ses işleme mantığı
│   │   ├── frekansAnalizi.py # Frekans analizi
│   │   ├── canliFiltre.py   # Canlı ses filtreleme
│   │   ├── filtre.py        # DSP filtreleme
│   │   ├── model.py         # Öğrenme modeli
│   │   └── sesKayit.py      # OBS kayıt yönetimi
│   ├── IsikModul/
│   │   ├── isikPanel.py     # Işık modülü GUI
│   │   └── isikIsleyici.py  # Işık işleme mantığı
│   ├── Controller/
│   │   └── multimodal_controller.py # Modül kontrolcüsü
│   ├── mainGui.py           # Ana GUI uygulaması
│   └── mainCli.py           # Komut satırı uygulaması
├── config/
│   └── voicemeeter_settings.xml  # VoiceMeeter ses ayarları
├── data/
│   ├── kaydedilen_sesler/   # Kaydedilen ses dosyaları
│   ├── filtered_audio/      # Filtrelenmiş ses dosyaları
│   └── logs/                # Sistem logları
├── requirements.txt         # Python bağımlılıkları
└── README.md               # Bu dosya
```

## 🔧 Yapılandırma

### Ses Filtreleme Parametreleri
- Varsayılan düşük frekans sınırı: 50 Hz
- Varsayılan yüksek frekans sınırı: 2000 Hz
- Kayıt süresi: 5 saniye

### Işık Modülü Parametreleri
- Parlaklık seviyeleri: 20% - 80%
- Ölçüm aralığı: 5 saniye

## 📝 Lisans

Bu proje [MIT Lisansı](LICENSE) altında lisanslanmıştır.

## 👥 Katkıda Bulunma

1. Bu depoyu fork edin
2. Yeni bir özellik dalı oluşturun (`git checkout -b yeni-ozellik`)
3. Değişikliklerinizi commit edin (`git commit -am 'Yeni özellik: X'`)
4. Dalınıza push yapın (`git push origin yeni-ozellik`)
5. Bir Pull Request oluşturun

## ⚠️ Bilinen Sorunlar

- OBS WebSocket bağlantısı bazen başarısız olabilir
- Kamera erişimi bazı sistemlerde sorun çıkarabilir
- Ses filtreleme performansı donanıma bağlı olarak değişebilir

## 📞 İletişim

Sorularınız veya önerileriniz için lütfen bir issue açın. 