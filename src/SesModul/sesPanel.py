import threading
import time
import os
import json
from PyQt5.QtWidgets import (
    QWidget, QLabel, QPushButton, QVBoxLayout, QProgressBar, QComboBox, QCheckBox, QMessageBox
)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QObject
from src.SesModul.sesIsleyici import SesModul
from src.SesModul.frekansAnalizi import FrekansAnalizi
from src.SesModul.canliFiltre import CanliSesFiltreleme


class WorkerSignals(QObject):
    finished = pyqtSignal()
    error = pyqtSignal(str)
    progress = pyqtSignal(str)
    model_updated = pyqtSignal(float, float)
    create_bars = pyqtSignal()
    update_combo = pyqtSignal()
    update_feedback = pyqtSignal(str)
    recording_finished = pyqtSignal()


class SoundPanel(QWidget):
    def __init__(self, geri_don_fonksiyonu):
        super().__init__()
        self.setWindowTitle("Ses Filtreleme Paneli")
        self.setStyleSheet("background-color: #fdf6e3;")

        self.module = SesModul()
        self.module.recording_finished.connect(self.kayit_bitti)  # Sinyali bağla
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        # Geri dön fonksiyonu
        self.geri_don = geri_don_fonksiyonu

        # Worker sinyalleri
        self.worker_signals = WorkerSignals()
        self.worker_signals.progress.connect(self.update_status)
        self.worker_signals.model_updated.connect(self.update_model_parameters)
        self.worker_signals.create_bars.connect(self.olustur_yeni_barlar)
        self.worker_signals.update_combo.connect(lambda: self.combo.setCurrentIndex(0))
        self.worker_signals.update_feedback.connect(self.update_feedback_status)
        self.worker_signals.recording_finished.connect(self.kayit_bitti)

        # Thread kontrolü için
        self.recording_thread = None
        self.log_thread = None
        self.stop_event = threading.Event()

        # Bar yönetimi için değişkenler
        self.renkler = ["blue", "red", "green", "orange", "purple"]
        self.renk_index = 0
        self.kayit_sayac = 1
        self.aktif_barlar = []  # Aktif barları takip etmek için
        self.ilk_bar_olusturuldu = False  # İlk barın oluşturulup oluşturulmadığını takip etmek için

        # GUI bileşenleri
        self.setup_gui()

        self.log_path = os.path.join("data", "logs", "frekans_log.jsonl")
        os.makedirs(os.path.dirname(self.log_path), exist_ok=True)
        self.log_file = os.path.join("data", "logs", "app_log.json")
        os.makedirs(os.path.dirname(self.log_file), exist_ok=True)
        self.bar_sonlandi = True  # Barların oluşturulması tamamlandığında geçerli olacak

    def write_log_to_json(self, message):
        try:
            if os.path.exists(self.log_file):
                with open(self.log_file, "r") as f:
                    try:
                        logs = json.load(f)
                    except json.JSONDecodeError:
                        logs = []  # Eğer JSON geçersizse, boş liste başlat
            else:
                logs = []  # Dosya yoksa boş liste başlat

            log_entry = {
                'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
                'message': message
            }
            logs.append(log_entry)

            # 150'den fazla log varsa, sadece son 150'yi sakla
            if len(logs) > 150:
                logs = logs[-150:]

            with open(self.log_file, "w") as f:
                json.dump(logs, f, indent=4)  # JSON formatında kaydet
        except Exception as e:
            print(f"Log kaydetme hatası: {e}")

    def setup_gui(self):
        # Geri dön butonu
        btn_geri = QPushButton("🔙 Geri Dön")
        btn_geri.clicked.connect(self.geri_don)
        self.layout.insertWidget(0, btn_geri)

        # Canlı filtreleme toggle
        self.filtre_toggle = QCheckBox("🔄 Canlı Filtrelemeyi Aç/Kapat")
        self.filtre_toggle.setChecked(True)
        self.filtre_toggle.stateChanged.connect(self.filtre_durumunu_degistir)
        self.layout.addWidget(self.filtre_toggle)

        # Geri bildirim bileşenleri
        self.combo = QComboBox()
        self.combo.addItems(["(Boş)", "0 - Normal", "1 - Rahatsız Edici"])
        self.send_btn = QPushButton("Geri Bildirimi Gönder")
        self.send_btn.clicked.connect(self.feedback_gonder)
        self.bildirim_durumu = QLabel("")
        self.bildirim_durumu.setStyleSheet("color: green; font-weight: bold;")

        self.bilgi_label = QLabel("🔔 Anlık problem yaşadığınız bir sese geri bildirim verecekseniz bir sonraki geri bildirim barını bekleyiniz. 🔔")
        self.bilgi_label.setAlignment(Qt.AlignCenter)
        self.bilgi_label.setStyleSheet("""
                color: #d35400;
                font-size: 13px;
                font-weight: bold;
                padding: 8px;
                border: 1px solid #ccc;
                border-radius: 5px;
                background-color: #fcf3cf;
            """)

        self.layout.addWidget(self.combo)
        self.layout.addWidget(self.send_btn)
        self.layout.addWidget(self.bildirim_durumu)
        self.layout.addWidget(self.bilgi_label)
    def update_status(self, message):
        """Durum mesajlarını güncelle - ana thread'de çalışır"""
        print(message)

    def update_feedback_status(self, message):
        """Geri bildirim durumunu güncelle - ana thread'de çalışır"""
        self.bildirim_durumu.setText(message)
        QTimer.singleShot(3000, lambda: self.bildirim_durumu.setText(""))

    def update_model_parameters(self, lc, hc):
        """Model parametrelerini güncelle - ana thread'de çalışır"""
        if self.module.canli_filtre_thread and self.module.canli_filtre_thread.is_alive():
            self.module.stop_event.set()
            time.sleep(0.05)

        self.module.stop_event.clear()
        self.module.canli_filtre = CanliSesFiltreleme(lowcut=lc, highcut=hc, stop_event=self.module.stop_event)
        self.module.canli_filtre_thread = threading.Thread(target=self.module.canli_filtre.start_stream,
                                                           daemon=True)
        self.module.canli_filtre_thread.start()

    def get_next_color(self):
        renk = self.renkler[self.renk_index % len(self.renkler)]
        self.renk_index += 1
        return renk

    def temizle_widgetlar(self, *widgets):
        """Widget'ları güvenli bir şekilde temizle - ana thread'de çalışır"""
        try:
            # Barların yok edilme zamanını logla
            log_msg = f"Barlar temizleniyor... [{time.strftime('%H:%M:%S')}]"
            self.write_log_to_json(log_msg)  # JSON logu
            for widget in widgets:
                if widget and not widget.isHidden():
                    widget.deleteLater()
                    if widget in self.aktif_barlar:
                        self.aktif_barlar.remove(widget)
            # Barların yok edilme zamanını logla
            log_msg = f"Barlar temizlendi... [{time.strftime('%H:%M:%S')}]"
            self.write_log_to_json(log_msg)  # JSON logu
        except Exception as e:
            self.worker_signals.error.emit(f"Widget temizleme hatası: {str(e)}")

    def olustur_yeni_barlar(self):
        """Yeni kayıt ve geri bildirim barlarını oluştur - ana thread'de çalışır"""
        if not self.bar_sonlandi:
            self.write_log_to_json(f"[{time.strftime('%H:%M:%S')}] Yeni barlar oluşturulmaya başlanamadı çünkü önceki işlem devam ediyor.")
            return

        try:
            self.bar_sonlandi = False
            self.write_log_to_json(f"[{time.strftime('%H:%M:%S')}] Yeni barlar oluşturuluyor...")

            # Önceki barları temizle
            for widget in self.aktif_barlar[:]:
                if widget and not widget.isHidden():
                    widget.deleteLater()
                    self.aktif_barlar.remove(widget)

            renk = self.get_next_color()
            sayac = self.kayit_sayac
            self.kayit_sayac += 1

            # Geri bildirim barı
            fb_label = QLabel(f"Geri Bildirim {sayac}")
            fb_bar = QProgressBar()
            fb_bar.setMaximum(100)  # İlerleme çubuğu için maksimum değer
            fb_bar.setValue(0)
            fb_bar.setMinimumHeight(20)
            fb_bar.setTextVisible(False)  # Yüzde göstergesini gizle
            fb_bar.setStyleSheet(f"""
                QProgressBar {{
                    border: 2px solid #999999;
                    border-radius: 5px;
                    text-align: center;
                    background-color: #f0f0f0;
                }}
                QProgressBar::chunk {{
                    background-color: {renk};
                    border-radius: 5px;
                }}
            """)
            fb_label.show()
            fb_bar.show()
            self.layout.addWidget(fb_label)
            self.layout.addWidget(fb_bar)
            self.aktif_barlar.extend([fb_label, fb_bar])

            self.write_log_to_json(f"[{time.strftime('%H:%M:%S')}] Geri bildirim barı oluşturuldu.")

            # Timer'ları oluştur
            fb_timer = QTimer(self)
            fb_state = {"value": 0}

            def update_feedback():
                try:
                    fb_state["value"] = (fb_state["value"] + 1) % 100
                    fb_bar.setValue(fb_state["value"])

                except Exception as e:
                    self.worker_signals.error.emit(f"Geri bildirim bar güncelleme hatası: {str(e)}")
                    fb_timer.stop()

            fb_timer.setInterval(100)  # Daha sık güncelleme için 100ms
            fb_timer.timeout.connect(update_feedback)
            fb_timer.start()  # Bar oluşturulur oluşturulmaz başlat

            self.bar_sonlandi = True
        except Exception as e:
            self.worker_signals.error.emit(f"Bar oluşturma hatası: {str(e)}")

    def baslat_kayit_dongusu(self):
        """Kayıt döngüsünü başlat"""
        def process_recording():
            try:
                lc, hc = self.module.load_model_parameters()
                self.worker_signals.progress.emit("[🔁] İlk canlı filtreleme thread'i başlatılıyor...")

                self.module.canli_filtre = CanliSesFiltreleme(lowcut=lc, highcut=hc, stop_event=self.module.stop_event)
                self.module.canli_filtre_thread = threading.Thread(target=self.module.canli_filtre.start_stream,
                                                                   daemon=True)
                self.module.canli_filtre_thread.start()

                while not self.stop_event.is_set():
                    try:
                        self.worker_signals.progress.emit(f"[🎙️] Ses Kaydı {self.kayit_sayac} başlatılıyor...")

                        # Ses kaydını başlat
                        self.module.ses_kaydi.start_and_stop_recording()  # 5 saniye kayıt + 1 saniye bekleme
                        self.worker_signals.progress.emit("[✅] Ses kaydı tamamlandı")

                        latest_video = self.module.get_latest_obs_recording()
                        if not latest_video:
                            self.worker_signals.progress.emit("[⚠] OBS kayıt dosyası bulunamadı!")
                            continue

                        timestamp = int(time.time())
                        wav_path = os.path.join(self.module.output_dir, f"obs_kayit_{timestamp}.wav")
                        self.module.convert_to_wav(latest_video, wav_path)
                        self.worker_signals.progress.emit("[✅] WAV dönüşümü tamamlandı")

                        self.module.kayitlar.append({
                            "timestamp": timestamp,
                            "path": wav_path,
                            "feedback": None
                        })

                        # Kayıt tamamlandığında sinyali tetikle
                        self.worker_signals.recording_finished.emit()

                        # Geri bildirim için bekleme (6 saniye)
                        time.sleep(6)
                        self.worker_signals.update_combo.emit()

                        if len(self.module.kayitlar) >= 1:
                            onceki_kayit = self.module.kayitlar[0]
                            if onceki_kayit.get("feedback"):
                                lc, hc = self.module.model_egitim.egit(onceki_kayit["path"], onceki_kayit["feedback"])
                                self.worker_signals.progress.emit(f"[📊] Model güncellendi → Lowcut: {lc}, Highcut: {hc}")
                                self.worker_signals.model_updated.emit(lc, hc)
                            else:
                                self.worker_signals.progress.emit("[ℹ] Önceki kayda geri bildirim alınmadı.")
                                lc, hc = self.module.load_model_parameters()
                        else:
                            lc, hc = self.module.load_model_parameters()

                        analizci = FrekansAnalizi(lowcut=lc, highcut=hc)
                        analizci.analiz_et(wav_path)
                        self.worker_signals.progress.emit("[✅] Frekans analizi tamamlandı")

                    except Exception as e:
                        self.worker_signals.error.emit(f"Kayıt döngüsü hatası: {str(e)}")
                        time.sleep(1)  # Hata durumunda kısa bir bekleme

            except Exception as e:
                self.worker_signals.error.emit(f"Kayıt işlemi hatası: {str(e)}")

        # Ana işlem thread'ini başlat
        self.recording_thread = threading.Thread(target=process_recording, daemon=True)
        self.recording_thread.start()

    def baslat_frekans_loglayici(self):
        """Frekans loglayıcı thread'ini başlat"""
        def loglayici():
            try:
                while not self.stop_event.is_set():
                    time.sleep(1)
                    filtre = self.module.canli_filtre
                    if filtre and hasattr(filtre, "min_hz") and hasattr(filtre, "max_hz"):
                        log = {
                            "timestamp": int(time.time()),
                            "min_freq": round(filtre.min_hz, 2),
                            "max_freq": round(filtre.max_hz, 2)
                        }

                        with open(self.log_path, "a") as f:
                            f.write(json.dumps(log) + "\n")

                        with open(self.log_path, "r") as f:
                            lines = f.readlines()

                        if len(lines) > 150:
                            with open(self.log_path, "w") as f:
                                f.writelines(lines[-150:])

                        self.worker_signals.progress.emit(f"[📁] Log eklendi ({len(lines)} satır): {log}")
            except Exception as e:
                self.worker_signals.error.emit(f"Loglama hatası: {str(e)}")

        self.log_thread = threading.Thread(target=loglayici, daemon=True)
        self.log_thread.start()

    def baslat_ses_analizi(self):
        """Ses analizi işlemini başlat"""
        self.worker_signals.progress.emit("[🔍] Ses analizi başlatılıyor...")
        connection = self.module.ses_kaydi.connect()
        if not connection:
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Warning)
            msg.setText(
                "OBS'yi arkada açmanız gerekiyor. Websocket server ayarlarını da doğru yaptığınızdan emin olun.")
            msg.setWindowTitle("OBS Uyarısı")
            msg.setStandardButtons(QMessageBox.Ok)
            msg.exec_()
            return

        self.worker_signals.progress.emit("[✅] OBS bağlantısı başarılı, kayıt döngüsü başlatılıyor...")
        self.baslat_kayit_dongusu()
        self.worker_signals.progress.emit("[✅] Kayıt döngüsü başlatıldı")

        self.worker_signals.progress.emit("[🔄] Frekans loglayıcı başlatılıyor...")
        self.baslat_frekans_loglayici()
        self.worker_signals.progress.emit("[✅] Frekans loglayıcı başlatıldı")

        self.worker_signals.progress.emit("[🎉] Tüm bileşenler başarıyla başlatıldı!")

    def durdur_ses_analizi(self):
        """Ses analizi thread'lerini durdur"""
        self.stop_event.set()
        if self.recording_thread and self.recording_thread.is_alive():
            self.recording_thread.join(timeout=1.0)
        if self.log_thread and self.log_thread.is_alive():
            self.log_thread.join(timeout=1.0)
        self.worker_signals.progress.emit("[🛑] Ses analizi durduruldu")

    def feedback_gonder(self):
        """Geri bildirim gönder"""
        try:
            secim = self.combo.currentText()
            if secim.startswith("1") or secim.startswith("0"):
                deger = secim.split(" - ")[0]
                self.module.geri_bildirim_ekle(deger)
                self.worker_signals.update_feedback.emit("✓ Geri bildirim alındı")
            else:
                self.worker_signals.update_feedback.emit("⚠ Geri bildirim seçilmedi")
        except Exception as e:
            self.worker_signals.error.emit(f"Geri bildirim hatası: {str(e)}")

    def filtre_durumunu_degistir(self, state):
        """Filtre durumunu değiştir"""
        try:
            if state == Qt.Checked:
                self.module.stop_event.clear()
                self.worker_signals.progress.emit("[🎚️] Canlı filtreleme: AÇIK")
            else:
                self.module.stop_event.set()
                self.worker_signals.progress.emit("[🎚️] Canlı filtreleme: KAPALI")
        except Exception as e:
            self.worker_signals.error.emit(f"Filtre durumu değiştirme hatası: {str(e)}")

    def kayit_bitti(self):
        """Ses kaydı bittiğinde çağrılacak fonksiyon"""
        # Önceki barları temizle
        for widget in self.aktif_barlar[:]:
            if widget and not widget.isHidden():
                widget.deleteLater()
                self.aktif_barlar.remove(widget)
        # Yeni bar oluştur
        self.worker_signals.create_bars.emit()

    def closeEvent(self, event):
        """Widget kapatıldığında thread'leri temizle"""
        self.durdur_ses_analizi()
        super().closeEvent(event)
