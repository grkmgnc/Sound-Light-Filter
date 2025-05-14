import sys
import cv2
import numpy as np
import screen_brightness_control as sbc
from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QVBoxLayout, QSlider,
    QPushButton, QDesktopWidget, QFrame, QHBoxLayout
)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QObject, QSettings
from PyQt5.QtGui import QFont, QPalette, QColor
import time
import threading

class WorkerSignals(QObject):
    finished = pyqtSignal()
    error = pyqtSignal(str)
    progress = pyqtSignal(str)
    light_update = pyqtSignal(float, int, str)  # ortam, parlaklik, pwm_durum

class PopupPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent, Qt.Window | Qt.FramelessWindowHint)
        self.parent = parent
        self.setup_ui()
        self.setWindowFlags(Qt.Window | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setFixedSize(220, 160)
        self.move_to_corner()
        self.show()
        self.raise_()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(7)

        container = QFrame()
        container_layout = QVBoxLayout(container)
        container_layout.setSpacing(7)
        container_layout.setContentsMargins(8, 8, 8, 8)

        # Başlık
        title = QLabel("<span style='font-size:17px; font-weight:bold; color:#FFD600;'>💡 Işık Durumu</span>")
        title.setAlignment(Qt.AlignCenter)
        container_layout.addWidget(title)

        # Işık değeri
        self.light_label = QLabel(f"<span style='font-size:14px;'>🔆 Işık Değeri: 0</span>")
        self.light_label.setAlignment(Qt.AlignCenter)
        container_layout.addWidget(self.light_label)

        # Durum
        self.status_label = QLabel(f"<span style='font-size:14px;'>🔄 Durum: Normal</span>")
        self.status_label.setAlignment(Qt.AlignCenter)
        container_layout.addWidget(self.status_label)

        # Ayarlar butonu (sadece simge)
        self.settings_btn = QPushButton("⚙️")
        self.settings_btn.setFixedSize(32, 32)
        self.settings_btn.setCursor(Qt.PointingHandCursor)
        container_layout.addWidget(self.settings_btn, alignment=Qt.AlignCenter)

        layout.addWidget(container)
        self.setLayout(layout)

        self.settings_btn.clicked.connect(self.open_settings)

    def open_settings(self):
        try:
            if self.parent:
                main_window = self.parent.window()
                if main_window:
                    main_window.stack.setCurrentIndex(2)
                    main_window.baslik.setText("🧭 Aktif Modül: 💡 Işık Modülü")
                    main_window.showNormal()
                    main_window.activateWindow()
                    main_window.raise_()
                    print("[💡] Ayarlar butonuna tıklandı, ışık modülüne geçildi ve ana pencere öne getirildi")
                else:
                    print("[⚠] Ana pencere bulunamadı")
            else:
                print("[⚠] Parent widget bulunamadı")
        except Exception as e:
            print(f"[⚠] Ayarlar butonu hatası: {str(e)}")

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
        try:
            self.light_label.setText(f"<span style='font-size:14px;'>🔆 Işık Değeri: {ortam:.1f}</span>")
            self.status_label.setText(f"<span style='font-size:14px;'>🔄 Durum: {pwm}</span>")
            self.show()
            self.raise_()
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
        self.setGeometry(400, 300, 600, 400)
        self.geri_don = geri_don_fonksiyonu

        self.worker_signals = WorkerSignals()
        self.worker_signals.light_update.connect(self.update_light_values)
        self.worker_signals.progress.connect(self.update_status)

        self.light_thread = None
        self.stop_event = threading.Event()
        self.camera = None

        self.setup_ui()
        print("[💡] Popup panel oluşturuluyor...")
        self.popup = PopupPanel(parent=self)
        print("[💡] Popup panel oluşturuldu")

    def setup_ui(self):
        main_container = QFrame()
        layout = QVBoxLayout(main_container)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # Header
        header = QFrame()
        header_layout = QHBoxLayout(header)

        btn_geri = QPushButton("🔙 Geri Dön")
        btn_geri.clicked.connect(self.geri_don)
        header_layout.addWidget(btn_geri)

        title = QLabel("💡 Işık Modülü Kontrol Paneli")
        header_layout.addWidget(title)
        header_layout.addStretch()

        layout.addWidget(header)

        # Status container
        status_container = QFrame()
        status_layout = QVBoxLayout(status_container)
        status_layout.setSpacing(10)

        self.label_sonuc = QLabel("Durum: Hazır")
        self.label_sonuc.setAlignment(Qt.AlignCenter)

        self.label_ortam = QLabel("💡 Ortam Işığı: -")
        self.label_ortam.setAlignment(Qt.AlignCenter)

        status_layout.addWidget(self.label_sonuc)
        status_layout.addWidget(self.label_ortam)

        layout.addWidget(status_container)

        # Slider container
        slider_container = QFrame()
        slider_layout = QVBoxLayout(slider_container)
        slider_layout.setSpacing(10)

        self.label_slider = QLabel()
        self.label_slider.setAlignment(Qt.AlignCenter)

        self.slider = QSlider(Qt.Horizontal)
        self.slider.setRange(0, 100)
        self.slider.setValue(sbc.get_brightness(display=0)[0])
        self.slider.valueChanged.connect(self.parlaklik_degistir)
        self.label_slider.setText(f"🔦 Parlaklık: {self.slider.value()}%")

        slider_layout.addWidget(self.label_slider)
        slider_layout.addWidget(self.slider)

        layout.addWidget(slider_container)
        layout.addStretch()

        self.setLayout(layout)

    def baslat(self):
        """Ana pencereden çağrılacak başlatma metodu"""
        print("[💡] Işık izleme başlatılıyor...")
        self.baslat_isik_izleme()

    def durdur(self):
        """Ana pencereden çağrılacak durdurma metodu"""
        print("[💡] Işık izleme durduruluyor...")
        self.durdur_isik_izleme()

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


