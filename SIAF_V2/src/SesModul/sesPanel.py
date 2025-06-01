import threading
import time
import os
import json
from PyQt5.QtWidgets import (
    QWidget, QLabel, QPushButton, QVBoxLayout, QProgressBar, QComboBox, QCheckBox, QMessageBox,
    QHBoxLayout, QFrame, QLineEdit
)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QObject, QSettings
from PyQt5.QtGui import QFont, QPalette, QColor
from .sesIsleyici import SesModul
from .frekansAnalizi import FrekansAnalizi
from .canliFiltre import CanliSesFiltreleme


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
        self.setWindowTitle("Ses Modülü Kontrol Paneli")

        self.module = SesModul()
        self.module.recording_finished.connect(self.kayit_bitti)

        self.geri_don_fonksiyonu = geri_don_fonksiyonu
        self.worker_signals = WorkerSignals()
        self.worker_signals.progress.connect(self.update_status)
        self.worker_signals.model_updated.connect(self.update_model_parameters)
        self.worker_signals.create_bars.connect(self.olustur_yeni_barlar)
        self.worker_signals.update_combo.connect(lambda: self.combo.setCurrentIndex(0))
        self.worker_signals.update_feedback.connect(self.update_feedback_status)
        self.worker_signals.recording_finished.connect(self.kayit_bitti)

        self.recording_thread = None
        self.log_thread = None
        self.stop_event = threading.Event()

        self.renkler = ["#2196F3", "#F44336", "#4CAF50", "#FF9800", "#9C27B0"]
        self.renk_index = 0
        self.kayit_sayac = 1
        self.aktif_barlar = []
        self.ilk_bar_olusturuldu = False

        self.log_path = os.path.join("data", "logs", "frekans_log.jsonl")
        os.makedirs(os.path.dirname(self.log_path), exist_ok=True)
        self.log_file = os.path.join("data", "logs", "app_log.json")
        os.makedirs(os.path.dirname(self.log_file), exist_ok=True)
        self.bar_sonlandi = True

        # Ana layout'u oluştur
        self.main_layout = QVBoxLayout()
        self.setLayout(self.main_layout)

        # UI'ı kur
        self.setup_ui()

    def setup_ui(self):
        # Ana container
        main_container = QFrame()
        main_layout = QVBoxLayout(main_container)

        # Header
        header = QFrame()
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(5, 5, 5, 5)

        btn_geri = QPushButton("<< Geri Dön")
        btn_geri.clicked.connect(self.geri_don)
        btn_geri.setMinimumHeight(20)
        btn_geri.setMinimumWidth(150)
        header_layout.addWidget(btn_geri)

        title = QLabel("🎙️ Ses Filtreleme Paneli")
        title.setMinimumHeight(25)
        header_layout.addWidget(title)
        header_layout.addStretch()

        main_layout.addWidget(header)

        # Filtre toggle
        self.filter_container = QFrame()
        filter_layout = QHBoxLayout(self.filter_container)

        self.filtre_toggle = QCheckBox("🔄 Canlı Filtrelemeyi Aç/Kapat")
        self.filtre_toggle.setChecked(True)
        self.filtre_toggle.setMinimumHeight(60)
        self.filtre_toggle.stateChanged.connect(self.filtre_durumunu_degistir)
        filter_layout.addWidget(self.filtre_toggle)

        main_layout.addWidget(self.filter_container)

        # Feedback section
        self.feedback_container = QFrame()
        feedback_layout = QVBoxLayout(self.feedback_container)
        feedback_layout.setSpacing(10)

        # ComboBox ve buton için yatay layout
        input_layout = QHBoxLayout()
        input_layout.setSpacing(10)

        self.combo = QComboBox()
        self.combo.addItems(["(Boş)", "0 - Normal", "1 - Rahatsız Edici"])
        self.combo.setMinimumHeight(80)

        self.send_btn = QPushButton("Geri Bildirimi Gönder")
        self.send_btn.clicked.connect(self.feedback_gonder)

        input_layout.addWidget(self.combo)
        input_layout.addWidget(self.send_btn)

        self.bildirim_durumu = QLabel("")

        self.bilgi_label = QLabel("🔔 Anlık problem yaşadığınız bir sese geri bildirim verecekseniz bir sonraki geri bildirim barını bekleyiniz. 🔔")
        self.bilgi_label.setAlignment(Qt.AlignCenter)
        self.bilgi_label.setMinimumHeight(80)

        feedback_layout.addLayout(input_layout)
        feedback_layout.addWidget(self.bildirim_durumu)
        feedback_layout.addWidget(self.bilgi_label)

        main_layout.addWidget(self.feedback_container)
        main_layout.addStretch()

        self.main_layout.addWidget(main_container)

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
        if not self.bar_sonlandi:
            self.write_log_to_json(f"[{time.strftime('%H:%M:%S')}] Yeni barlar oluşturulmaya başlanamadı çünkü önceki işlem devam ediyor.")
            return

        try:
            self.bar_sonlandi = False
            self.write_log_to_json(f"[{time.strftime('%H:%M:%S')}] Yeni barlar oluşturuluyor...")

            for widget in self.aktif_barlar[:]:
                if widget and not widget.isHidden():
                    widget.deleteLater()
                    self.aktif_barlar.remove(widget)

            renk = self.get_next_color()
            sayac = self.kayit_sayac
            self.kayit_sayac += 1

            bar_container = QFrame()
            # Varsayılan stil, tema fonksiyonu ile güncellenecek
            bar_layout = QVBoxLayout(bar_container)

            fb_label = QLabel(f"Geri Bildirim {sayac}")
            fb_label.setStyleSheet("")  # Tema fonksiyonu ile güncellenecek

            fb_bar = QProgressBar()
            fb_bar.setMaximum(100)
            fb_bar.setValue(0)
            fb_bar.setMinimumHeight(25)
            fb_bar.setTextVisible(False)
            fb_bar.setStyleSheet(f"""
                QProgressBar {{
                    border: 2px solid #ddd;
                    border-radius: 5px;
                    text-align: center;
                    background-color: #f0f0f0;
                }}
                QProgressBar::chunk {{
                    background-color: {renk};
                    border-radius: 3px;
                }}
            """)

            bar_layout.addWidget(fb_label)
            bar_layout.addWidget(fb_bar)

            self.main_layout.addWidget(bar_container)
            self.aktif_barlar.extend([bar_container])

            self.write_log_to_json(f"[{time.strftime('%H:%M:%S')}] Geri bildirim barı oluşturuldu.")

            fb_timer = QTimer(self)
            fb_state = {"value": 0}

            def update_feedback():
                try:
                    fb_state["value"] = (fb_state["value"] + 1) % 100
                    fb_bar.setValue(fb_state["value"])
                except Exception as e:
                    self.worker_signals.error.emit(f"Geri bildirim bar güncelleme hatası: {str(e)}")
                    fb_timer.stop()

            fb_timer.setInterval(100)
            fb_timer.timeout.connect(update_feedback)
            fb_timer.start()

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
                # Canlı filtrelemeyi tekrar başlat
                lc, hc = self.module.load_model_parameters()
                self.module.canli_filtre = CanliSesFiltreleme(lowcut=lc, highcut=hc, stop_event=self.module.stop_event)
                self.module.canli_filtre_thread = threading.Thread(target=self.module.canli_filtre.start_stream, daemon=True)
                self.module.canli_filtre_thread.start()
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

    def geri_don(self):
        """Ana menüye dön"""
        self.geri_don_fonksiyonu()
