import sys
import threading
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout,
    QPushButton, QStackedWidget, QLabel
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from SesModul.sesPanel import SoundPanel
from IsikModul.isikPanel import LightPanel

class AnaEkran(QWidget):
    def __init__(self, stack, baslik_guncelle, baslat_callback):
        super().__init__()
        self.stack = stack
        self.baslik_guncelle = baslik_guncelle
        self.baslat_callback = baslat_callback

        self.setStyleSheet("background-color: #fdf6e3; font-family: Arial;")
        font = QFont("Arial", 10, QFont.Bold)

        self.btn_calistir = QPushButton("🚀 Çalıştır")
        self.btn_ses = QPushButton("🎙️ Ses Modülü")
        self.btn_isik = QPushButton("💡 Işık Modülü")

        for btn in [self.btn_calistir, self.btn_ses, self.btn_isik]:
            btn.setFont(font)
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #ffffff;
                    border: 1px solid #cccccc;
                    padding: 10px;
                    border-radius: 8px;
                }
                QPushButton:hover {
                    background-color: #e6f2ff;
                }
            """)

        self.btn_calistir.clicked.connect(self.baslat_callback)
        self.btn_ses.clicked.connect(lambda: self.panel_degistir(1, "🎙️ Ses Modülü"))
        self.btn_isik.clicked.connect(lambda: self.panel_degistir(2, "💡 Işık Modülü"))

        layout = QVBoxLayout()
        layout.addStretch()
        layout.addWidget(self.btn_calistir, alignment=Qt.AlignCenter)
        layout.addWidget(self.btn_ses, alignment=Qt.AlignCenter)
        layout.addWidget(self.btn_isik, alignment=Qt.AlignCenter)
        layout.addStretch()
        self.setLayout(layout)

    def panel_degistir(self, index, ad):
        self.stack.setCurrentIndex(index)
        self.baslik_guncelle(f"🧭 Aktif Modül: {ad}")


class AnaPencere(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Multimodal GUI")
        self.setGeometry(300, 150, 600, 500)

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        self.baslik = QLabel("🧭 Aktif Modül: Ana Menü")
        self.baslik.setAlignment(Qt.AlignCenter)
        self.baslik.setFont(QFont("Arial", 11, QFont.Bold))
        self.baslik.setStyleSheet("""
            QLabel {
                background-color: #e0e0e0;
                border-bottom: 1px solid #bbbbbb;
                padding: 8px;
            }
        """)

        self.stack = QStackedWidget()

        # panel objeleri oluşturuluyor (başlangıçta hiçbir şey çalışmaz)
        self.sound_panel = SoundPanel(self.geri_don)
        self.light_panel = LightPanel(self.geri_don)

        self.stack.addWidget(AnaEkran(self.stack, self.baslik_guncelle, self.modulleri_baslat))  # 0
        self.stack.addWidget(self.sound_panel)  # 1
        self.stack.addWidget(self.light_panel)  # 2

        layout = QVBoxLayout()
        layout.addWidget(self.baslik)
        layout.addWidget(self.stack)
        self.central_widget.setLayout(layout)

    def baslik_guncelle(self, text):
        self.baslik.setText(text)

    def geri_don(self):
        self.stack.setCurrentIndex(0)
        self.baslik.setText("🧭 Aktif Modül: Ana Menü")

    def modulleri_baslat(self):
        print("[✅] Kullanıcı başlattı, modüller eş zamanlı başlatılıyor...")
        # Ses analiz thread içinde
        threading.Thread(target=self.sound_panel.baslat_ses_analizi, daemon=True).start()
        # Işık analizi ayrı thread'de
        threading.Thread(target=self.light_panel.baslat_isik_izleme, daemon=True).start()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    pencere = AnaPencere()
    pencere.show()
    sys.exit(app.exec_())
