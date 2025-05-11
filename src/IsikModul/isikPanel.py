import sys
import cv2
import numpy as np
import screen_brightness_control as sbc
from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QVBoxLayout, QSlider,
    QPushButton, QDesktopWidget
)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QObject
from PyQt5.QtGui import QFont
import time
import threading

class WorkerSignals(QObject):
    finished = pyqtSignal()
    error = pyqtSignal(str)
    progress = pyqtSignal(str)
    light_update = pyqtSignal(float, int, str)  # ortam, parlaklik, pwm_durum

class PopupPanel(QWidget):
    def __init__(self, kontrol_paneli):
        super().__init__()
        self.kontrol_paneli = kontrol_paneli

        # Pencere ayarları
        self.setWindowFlags(Qt.Tool | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setFixedSize(400, 140)

        # Font ayarları
        font = QFont("Arial", 10, QFont.Bold)

        # Etiketler
        self.label_ortam = QLabel("💡 Ortam Işığı: -", self)
        self.label_parlaklik = QLabel("🔦 Parlaklık: -", self)
        self.label_pwm = QLabel("🌀 PWM: -", self)

        for lbl in [self.label_ortam, self.label_parlaklik, self.label_pwm]:
            lbl.setFont(font)
            lbl.setStyleSheet("""
                padding: 0px;
                color: #212121;
                background-color: #ffffff;
                border: 1px solid #cccccc;
                border-radius: 6px;
            """)

        # Ayar butonu
        self.btn_ayar = QPushButton("⚙️", self)
        self.btn_ayar.setFixedSize(32, 32)
        self.btn_ayar.setStyleSheet("""
            QPushButton {
                border: 1px solid #cccccc;
                background-color: #ffffff;
                border-radius: 16px;
                font-size: 14pt;
            }
            QPushButton:hover {
                background-color: #f0f0f0;
            }
        """)
        self.btn_ayar.clicked.connect(self.kontrol_paneli.show)

        # Layout
        layout = QVBoxLayout()
        layout.addWidget(self.label_ortam)
        layout.addWidget(self.label_parlaklik)
        layout.addWidget(self.label_pwm)
        layout.addWidget(self.btn_ayar, alignment=Qt.AlignRight)
        self.setLayout(layout)

        # Pencereyi göster ve konumlandır
        self.move_to_corner()
        self.show()
        self.raise_()  # Pencereyi en üste getir
        print("[💡] Popup panel oluşturuldu ve gösterildi")

    def move_to_corner(self):
        """Pencereyi ekranın sağ alt köşesine konumlandır"""
        try:
            ekran = QDesktopWidget().availableGeometry()
            x = ekran.right() - self.width() - 20
            y = ekran.bottom() - self.height() - 20
            self.move(x, y)
            print(f"[💡] Popup panel konumlandırıldı: x={x}, y={y}")
        except Exception as e:
            print(f"[⚠] Pencere konumlandırma hatası: {str(e)}")

    def guncelle(self, ortam, parlaklik, pwm):
        """Popup panel'i güncelle - ana thread'de çalışır"""
        try:
            print(f"[💡] Popup güncelleme başladı - Ortam: {ortam:.1f}, Parlaklık: {parlaklik}, PWM: {pwm}")
            
            # Değerleri güncelle
            self.label_ortam.setText(f"💡 Ortam Işığı: {ortam:.1f}")
            self.label_parlaklik.setText(f"🔦 Parlaklık: {parlaklik}%")
            self.label_pwm.setText(f"🌀 PWM: {pwm}")

            # Pencereyi yeniden göster ve en üste getir
            self.show()
            self.raise_()
            
            print("[💡] Popup güncelleme tamamlandı")
        except Exception as e:
            print(f"[⚠] Popup güncelleme hatası: {str(e)}")

    def closeEvent(self, event):
        """Pencere kapatıldığında"""
        print("[💡] Popup kapatma olayı tetiklendi")
        event.ignore()  # Pencereyi kapatma, sadece gizle
        self.hide()


class LightPanel(QWidget):
    def __init__(self, geri_don_fonksiyonu):
        super().__init__()
        self.setWindowTitle("Işık Modülü Kontrol Paneli")
        self.setGeometry(400, 300, 500, 250)
        self.setStyleSheet("background-color: #f0f4f8; font-family: Arial;")
        self.geri_don = geri_don_fonksiyonu

        # Worker sinyalleri
        self.worker_signals = WorkerSignals()
        self.worker_signals.light_update.connect(self.update_light_values)
        self.worker_signals.progress.connect(self.update_status)

        # Thread kontrolü için
        self.light_thread = None
        self.stop_event = threading.Event()
        
        # Kamera için global değişken
        self.camera = None

        # GUI bileşenleri
        self.setup_gui()

        # Popup panel
        print("[💡] Popup panel oluşturuluyor...")
        self.popup = PopupPanel(kontrol_paneli=self)
        print("[💡] Popup panel oluşturuldu")

    def baslat(self):
        """Ana pencereden çağrılacak başlatma metodu"""
        print("[💡] Işık izleme başlatılıyor...")
        self.baslat_isik_izleme()

    def durdur(self):
        """Ana pencereden çağrılacak durdurma metodu"""
        print("[💡] Işık izleme durduruluyor...")
        self.durdur_isik_izleme()

    def setup_gui(self):
        font_baslik = QFont("Arial", 10, QFont.Bold)
        font_etiket = QFont("Arial", 9)

        btn_geri = QPushButton("🔙 Geri Dön")
        btn_geri.clicked.connect(self.geri_don)

        self.label_sonuc = QLabel("Durum: Hazır")
        self.label_sonuc.setAlignment(Qt.AlignCenter)
        self.label_sonuc.setFont(font_baslik)

        self.label_ortam = QLabel("💡 Ortam Işığı: -")
        self.label_ortam.setAlignment(Qt.AlignCenter)
        self.label_ortam.setFont(font_etiket)

        self.label_slider = QLabel()
        self.label_slider.setAlignment(Qt.AlignCenter)
        self.label_slider.setFont(font_etiket)

        self.slider = QSlider(Qt.Horizontal)
        self.slider.setRange(0, 100)
        self.slider.setValue(sbc.get_brightness(display=0)[0])
        self.slider.valueChanged.connect(self.parlaklik_degistir)
        self.label_slider.setText(f"🔦 Parlaklık: {self.slider.value()}%")

        layout = QVBoxLayout()
        layout.addWidget(btn_geri)
        layout.addWidget(self.label_sonuc)
        layout.addWidget(self.label_ortam)
        layout.addWidget(self.label_slider)
        layout.addWidget(self.slider)
        self.setLayout(layout)

    def update_status(self, message):
        """Durum mesajlarını güncelle - ana thread'de çalışır"""
        print(message)
        self.label_sonuc.setText(message)

    def update_light_values(self, ortam, parlaklik, pwm_durum):
        """Işık değerlerini güncelle - ana thread'de çalışır"""
        try:
            print(f"[💡] LightPanel - Değerler alındı: Ortam={ortam:.1f}, Parlaklık={parlaklik}, PWM={pwm_durum}")
            
            # PWM durumunu sakla
            self.pwm_durum = pwm_durum
            
            # Ana panel'i güncelle
            self.label_ortam.setText(f"💡 Ortam Işığı: {ortam:.1f}")
            
            # Popup'ı güncelle
            if hasattr(self, 'popup') and self.popup:
                print("[💡] Popup güncelleniyor...")
                self.popup.guncelle(ortam, parlaklik, pwm_durum)
            else:
                print("[⚠] Popup bulunamadı!")
            
            # Slider'ı güncelle (eğer otomatik modda ise)
            if not self.slider.isSliderDown():  # Kullanıcı slider'ı hareket ettirmiyorsa
                self.slider.setValue(parlaklik)
                self.label_slider.setText(f"🔦 Parlaklık: {parlaklik}% (otomatik)")
            
            print("[💡] LightPanel - GUI güncellendi")
        except Exception as e:
            print(f"[⚠] Işık değerleri güncelleme hatası: {str(e)}")
            self.worker_signals.error.emit(f"Işık değerleri güncelleme hatası: {str(e)}")

    def baslat_isik_izleme(self):
        """Işık izleme thread'ini başlat"""
        def isik_izleme_dongusu():
            try:
                print("[💡] Işık izleme döngüsü başlatıldı")
                pwm_check_counter = 0  # PWM kontrolü için sayaç
                
                # Kamerayı başlat
                if self.camera is None:
                    self.camera = cv2.VideoCapture(0)
                    if not self.camera.isOpened():
                        print("[⚠] Kamera başlatılamadı!")
                        return
                
                while not self.stop_event.is_set():
                    try:
                        # Ortam ışığını ölç
                        ortam_parlaklik = self.ortam_isik_olc()
                        print(f"[💡] Ortam ışığı ölçüldü: {ortam_parlaklik:.1f}")
                        
                        # PWM kontrolünü her 5 ölçümde bir yap
                        pwm_durum = "✅ PWM kontrol ediliyor..."
                        if pwm_check_counter >= 5:
                            pwm_durum = self.pwm_flicker_fft()
                            print(f"[💡] PWM durumu: {pwm_durum}")
                            pwm_check_counter = 0
                        pwm_check_counter += 1
                        
                        # Mevcut parlaklığı al
                        parlaklik = sbc.get_brightness(display=0)[0]
                        print(f"[💡] Mevcut parlaklık: {parlaklik}%")
                        
                        # Ana thread'de GUI'yi güncelle
                        print("[💡] Işık değerleri gönderiliyor...")
                        self.worker_signals.light_update.emit(ortam_parlaklik, parlaklik, pwm_durum)
                        print("[💡] Işık değerleri gönderildi")
                        
                        # Parlaklık seviyesine göre otomatik ayarlama
                        if not self.slider.isSliderDown():  # Kullanıcı slider'ı hareket ettirmiyorsa
                            if ortam_parlaklik < 30:
                                sbc.set_brightness(20)
                            elif ortam_parlaklik < 60:
                                sbc.set_brightness(30)
                            elif ortam_parlaklik < 90:
                                sbc.set_brightness(40)
                            elif ortam_parlaklik < 120:
                                sbc.set_brightness(50)
                            elif ortam_parlaklik < 150:
                                sbc.set_brightness(60)
                            elif ortam_parlaklik < 180:
                                sbc.set_brightness(70)
                            else:
                                sbc.set_brightness(80)
                            print(f"[💡] Parlaklık otomatik ayarlandı (ortam: {ortam_parlaklik:.1f})")
                        
                        time.sleep(2)  # 2 saniyede bir güncelle
                    except Exception as e:
                        print(f"[⚠] Döngü içi hata: {str(e)}")
                        time.sleep(2)  # Hata durumunda da bekle
            except Exception as e:
                print(f"[⚠] Işık izleme hatası: {str(e)}")
                self.worker_signals.error.emit(f"Işık izleme hatası: {str(e)}")
            finally:
                # Kamerayı kapat
                if self.camera is not None:
                    self.camera.release()
                    self.camera = None

        # Eğer önceki thread varsa durdur
        if self.light_thread and self.light_thread.is_alive():
            print("[💡] Önceki thread durduruluyor...")
            self.stop_event.set()
            self.light_thread.join(timeout=1.0)

        # Yeni thread'i başlat
        print("[💡] Yeni thread başlatılıyor...")
        self.stop_event.clear()
        self.light_thread = threading.Thread(target=isik_izleme_dongusu, daemon=True)
        self.light_thread.start()
        print("[💡] Işık izleme başlatıldı")

    def durdur_isik_izleme(self):
        """Işık izleme thread'ini durdur"""
        if self.light_thread and self.light_thread.is_alive():
            self.stop_event.set()
            self.light_thread.join(timeout=1.0)
            self.worker_signals.progress.emit("[💡] Işık izleme durduruldu")

    def ortam_isik_olc(self):
        """Ortam ışığını ölç - worker thread'de çalışır"""
        try:
            if self.camera is None or not self.camera.isOpened():
                print("[⚠] Kamera erişilemedi.")
                return 0

            ret, frame = self.camera.read()
            if not ret:
                print("[⚠] Kamera erişilemedi.")
                return 0

            gri = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            parlaklik = np.mean(gri)
            print(f"[💡] Ortam ışığı ölçüldü: {parlaklik:.1f}")

            return parlaklik
        except Exception as e:
            print(f"[⚠] Ortam ışık ölçüm hatası: {str(e)}")
            return 0

    def pwm_flicker_fft(self):
        """PWM flicker durumunu kontrol et - worker thread'de çalışır"""
        try:
            if self.camera is None or not self.camera.isOpened():
                return "❌ Kamera erişilemedi"

            parlakliklar = []
            baslangic = time.time()
            while time.time() - baslangic < 1.0:  # 1 saniye
                ret, frame = self.camera.read()
                if not ret:
                    continue
                gri = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                parlakliklar.append(np.mean(gri))
                time.sleep(0.05)  # 50ms bekle

            if len(parlakliklar) < 10:
                return "🟡 PWM verisi yetersiz"

            fps = len(parlakliklar) / 1.0
            parlaklik_array = np.array(parlakliklar)
            fft = np.abs(np.fft.fft(parlaklik_array - np.mean(parlaklik_array)))
            frekanslar = np.fft.fftfreq(len(fft), d=1/fps)

            pozitif = frekanslar > 0
            frekanslar = frekanslar[pozitif]
            fft = fft[pozitif]

            flicker_aralik = (frekanslar > 3) & (frekanslar < 20)
            fft_aralik = fft[flicker_aralik]

            if len(fft_aralik) == 0:
                return "🟡 PWM tespit edilemedi"

            en_yuksek = np.max(fft_aralik)

            if en_yuksek > 5:
                return "⚠️ PWM Flicker tespit edildi!"
            else:
                return "✅ PWM Flicker yok"
        except Exception as e:
            print(f"[⚠] PWM analiz hatası: {str(e)}")
            return "❌ PWM analiz hatası"

    def parlaklik_degistir(self, value):
        """Slider değeri değiştiğinde çağrılır - ana thread'de çalışır"""
        try:
            # Parlaklığı ayarla
            sbc.set_brightness(value)
            
            # GUI'yi güncelle
            self.label_slider.setText(f"🔦 Parlaklık: {value}% (manuel)")
            
            # Popup'ı güncelle (mevcut ortam ışığı değerini kullan)
            if hasattr(self, 'popup') and self.popup:
                # Mevcut ortam ışığı değerini al
                ortam = 0
                if self.camera is not None and self.camera.isOpened():
                    ret, frame = self.camera.read()
                    if ret:
                        gri = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                        ortam = np.mean(gri)
                
                # PWM durumunu al
                pwm = "✅ PWM kontrol ediliyor..."
                if hasattr(self, 'pwm_durum'):
                    pwm = self.pwm_durum
                
                # Popup'ı güncelle
                self.popup.guncelle(ortam, value, pwm)
            
            print(f"[💡] Parlaklık manuel olarak ayarlandı: {value}%")
        except Exception as e:
            print(f"[⚠] Parlaklık değiştirme hatası: {str(e)}")
            self.worker_signals.error.emit(f"Parlaklık değiştirme hatası: {str(e)}")

    def closeEvent(self, event):
        """Widget kapatıldığında thread'leri temizle"""
        self.durdur_isik_izleme()
        if hasattr(self, 'popup') and self.popup:
            self.popup.hide()
        if self.camera is not None:
            self.camera.release()
            self.camera = None
        event.ignore()
        self.hide()


