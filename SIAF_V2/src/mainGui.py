import sys
import os

# Projenin kök dizinini Python'un modül arama yoluna ekle
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

import threading
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout,
    QPushButton, QStackedWidget, QLabel, QStyleFactory, QFrame, QSizePolicy, QGridLayout
)
from PyQt5.QtCore import Qt, QSettings
from PyQt5.QtGui import QFont, QPalette, QColor
from SesModul.sesPanel import SoundPanel
from IsikModul.isikPanel import LightPanel

class ThemeManager:
    def __init__(self):
        self.settings = QSettings('SIAF', 'Theme')
        self.current_theme = self.settings.value('theme', 'light')

    def apply_theme(self, app):
        if self.current_theme == 'dark':
            self.apply_dark_theme(app)
        else:
            self.apply_light_theme(app)

    def toggle_theme(self, app):
        self.current_theme = 'dark' if self.current_theme == 'light' else 'light'
        self.settings.setValue('theme', self.current_theme)
        self.apply_theme(app)

    def apply_dark_theme(self, app):
        palette = QPalette()
        palette.setColor(QPalette.Window, QColor(24, 24, 24))
        palette.setColor(QPalette.WindowText, Qt.white)
        palette.setColor(QPalette.Base, QColor(32, 32, 32))
        palette.setColor(QPalette.AlternateBase, QColor(40, 40, 40))
        palette.setColor(QPalette.ToolTipBase, QColor(40, 40, 40))
        palette.setColor(QPalette.ToolTipText, Qt.white)
        palette.setColor(QPalette.Text, Qt.white)
        palette.setColor(QPalette.Button, QColor(32, 32, 32))
        palette.setColor(QPalette.ButtonText, Qt.white)
        palette.setColor(QPalette.BrightText, QColor(255, 0, 0))
        palette.setColor(QPalette.Link, QColor(42, 130, 218))
        palette.setColor(QPalette.Highlight, QColor(42, 130, 218))
        palette.setColor(QPalette.HighlightedText, Qt.white)

        app.setStyleSheet("""
            QWidget {
                background-color: #181818;
                color: #F5F5F5;
            }
            QFrame {
                background-color: #23272A;
                border-radius: 15px;
                border: 1px solid #23272A;
            }
            QStackedWidget {
                background-color: transparent;
            }
            QPushButton {
                background-color: #E0E0E0;
                color: #000000;
                border: none;
                border-radius: 15px;
                font-size: 16px;
                font-weight: bold;
                font-family: 'Segoe UI', Arial;
                padding: 20px;
                margin: 10px;
                min-height: 120px;
            }
            QPushButton:hover {
                background-color: #D0D0D0;
            }
            QPushButton:pressed {
                background-color: #C0C0C0;
            }
            QLabel {
                color: #F5F5F5;
            }
            QComboBox {
                background-color: #23272A;
                color: #F5F5F5;
                border: 1px solid #444;
                border-radius: 4px;
                padding: 5px;
            }
            QComboBox:hover {
                border: 1px solid #2196F3;
            }
            QComboBox::drop-down {
                border: none;
            }
            QProgressBar {
                border: 2px solid #444;
                border-radius: 5px;
                text-align: center;
                background-color: #23272A;
            }
            QProgressBar::chunk {
                background-color: #2196F3;
                border-radius: 3px;
            }
            QCheckBox {
                color: #F5F5F5;
            }
            QCheckBox::indicator {
                width: 20px;
                height: 20px;
                background-color: #23272A;
                border: 1px solid #444;
                border-radius: 4px;
            }
            QCheckBox::indicator:checked {
                background-color: #2196F3;
                border: 1px solid #2196F3;
            }
            /* Ana container ve header */
            QFrame[objectName="main_container"] {
                background-color: #23272A;
                border: 1px solid #23272A;
            }
            QFrame[objectName="header"] {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #23272A, stop:1 #1976D2);
                border-radius: 15px;
            }
            QFrame[objectName="buttons_container"] {
                background-color: #23272A;
                border: 1px solid #23272A;
            }
            QLabel[objectName="footer"] {
                color: #888;
            }
        """)
        app.setPalette(palette)

    def apply_light_theme(self, app):
        palette = QPalette()
        palette.setColor(QPalette.Window, QColor(245, 245, 245))
        palette.setColor(QPalette.WindowText, QColor(33, 33, 33))
        palette.setColor(QPalette.Base, QColor(255, 255, 255))
        palette.setColor(QPalette.AlternateBase, QColor(233, 233, 233))
        palette.setColor(QPalette.ToolTipBase, QColor(255, 255, 255))
        palette.setColor(QPalette.ToolTipText, QColor(33, 33, 33))
        palette.setColor(QPalette.Text, QColor(33, 33, 33))
        palette.setColor(QPalette.Button, QColor(245, 245, 245))
        palette.setColor(QPalette.ButtonText, QColor(33, 33, 33))
        palette.setColor(QPalette.BrightText, QColor(255, 0, 0))
        palette.setColor(QPalette.Link, QColor(33, 150, 243))
        palette.setColor(QPalette.Highlight, QColor(33, 150, 243))
        palette.setColor(QPalette.HighlightedText, QColor(255, 255, 255))

        app.setStyleSheet("""
            QWidget {
                background-color: #F5F5F5;
                color: #212121;
            }
            QFrame {
                background-color: #FFFFFF;
                border-radius: 15px;
                border: 1px solid #e0e0e0;
            }
            QStackedWidget {
                background-color: transparent;
            }
            QPushButton {
                background-color: #E0E0E0;
                color: #000000;
                border: none;
                border-radius: 15px;
                font-size: 16px;
                font-weight: bold;
                font-family: 'Segoe UI', Arial;
                padding: 20px;
                margin: 10px;
                min-height: 120px;
            }
            QPushButton:hover {
                background-color: #D0D0D0;
            }
            QPushButton:pressed {
                background-color: #C0C0C0;
            }
            QLabel {
                color: #212121;
            }
            QComboBox {
                background-color: #FFFFFF;
                color: #212121;
                border: 1px solid #BDBDBD;
                border-radius: 4px;
                padding: 5px;
            }
            QComboBox:hover {
                border: 1px solid #2196F3;
            }
            QComboBox::drop-down {
                border: none;
            }
            QProgressBar {
                border: 2px solid #E0E0E0;
                border-radius: 5px;
                text-align: center;
                background-color: #F5F5F5;
            }
            QProgressBar::chunk {
                background-color: #2196F3;
                border-radius: 3px;
            }
            QCheckBox {
                color: #212121;
            }
            QCheckBox::indicator {
                width: 20px;
                height: 20px;
                background-color: #FFFFFF;
                border: 1px solid #BDBDBD;
                border-radius: 4px;
            }
            QCheckBox::indicator:checked {
                background-color: #2196F3;
                border: 1px solid #2196F3;
            }
            QFrame[objectName="main_container"] {
                background-color: #FFFFFF;
                border: 1px solid #e0e0e0;
            }
            QFrame[objectName="header"] {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #2196F3, stop:1 #1976D2);
                border-radius: 15px;
            }
            QFrame[objectName="buttons_container"] {
                background-color: #f8f9fa;
                border: 1px solid #e0e0e0;
            }
            QLabel[objectName="footer"] {
                color: #757575;
            }
        """)
        app.setPalette(palette)

class AnaEkran(QWidget):
    def __init__(self, stack, baslik_guncelle, baslat_callback, theme_manager):
        super().__init__()
        self.stack = stack
        self.baslik_guncelle = baslik_guncelle
        self.baslat_callback = baslat_callback
        self.theme_manager = theme_manager

        self.setup_ui()

    def setup_ui(self):
        # Ana container
        main_container = QFrame()
        main_container.setObjectName("main_container")
        main_layout = QVBoxLayout(main_container)
        main_layout.setSpacing(16)
        main_layout.setContentsMargins(24, 24, 24, 24)

        # Logo ve başlık
        header = QFrame()
        header.setObjectName("header")
        header_layout = QVBoxLayout(header)
        header_layout.setSpacing(8)

        title = QLabel("SIAF - Ses ve Işık Analiz Filtresi")
        title.setStyleSheet("""
            QLabel {
                font-size: 22px;
                font-weight: bold;
                font-family: 'Segoe UI', Arial;
            }
        """)
        title.setAlignment(Qt.AlignCenter)

        subtitle = QLabel("Profesyonel Ses ve Işık Filtreleme Sistemi")
        subtitle.setStyleSheet("""
            QLabel {
                font-size: 15px;
                font-family: 'Segoe UI', Arial;
            }
        """)
        subtitle.setAlignment(Qt.AlignCenter)

        header_layout.addWidget(title)
        header_layout.addWidget(subtitle)
        main_layout.addWidget(header)

        # Butonlar için container
        buttons_container = QFrame()
        buttons_container.setObjectName("buttons_container")
        buttons_layout = QGridLayout(buttons_container)
        buttons_layout.setSpacing(20)
        buttons_layout.setContentsMargins(20, 20, 20, 20)

        button_style = """
            QPushButton {
                border-radius: 15px;
                font-size: 16px;
                font-weight: bold;
                font-family: 'Segoe UI', Arial;
                padding: 20px;
                min-height: 120px;
            }
        """

        self.btn_calistir = QPushButton("🚀 Sistemi Başlat")
        self.btn_ses = QPushButton("🎙️ Ses Modülü")
        self.btn_isik = QPushButton("💡 Işık Modülü")
        self.btn_theme = QPushButton("🌓 Tema Değiştir")

        for btn in [self.btn_calistir, self.btn_ses, self.btn_isik, self.btn_theme]:
            btn.setStyleSheet(button_style)
            btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
            btn.setFont(QFont('Segoe UI', 16, QFont.Bold))
            btn.setCursor(Qt.PointingHandCursor)

        # Grid layout'a butonları ekle
        buttons_layout.addWidget(self.btn_calistir, 0, 0)
        buttons_layout.addWidget(self.btn_ses, 0, 1)
        buttons_layout.addWidget(self.btn_isik, 1, 0)
        buttons_layout.addWidget(self.btn_theme, 1, 1)

        main_layout.addWidget(buttons_container)
        main_layout.addStretch(1)

        # Alt bilgi
        footer = QLabel("© 2025 SIAF - Tüm Hakları Saklıdır")
        footer.setObjectName("footer")
        footer.setStyleSheet("""
            QLabel {
                font-size: 12px;
                font-family: 'Segoe UI', Arial;
                padding: 6px;
            }
        """)
        footer.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(footer)

        # Ana layout'a container'ı ekle
        self.layout = QVBoxLayout()
        self.layout.setContentsMargins(16, 16, 16, 16)
        self.layout.addWidget(main_container)
        self.setLayout(self.layout)

        # Buton bağlantıları
        self.btn_calistir.clicked.connect(self.baslat_callback)
        self.btn_ses.clicked.connect(lambda: self.panel_degistir(1, "🎙️ Ses Modülü"))
        self.btn_isik.clicked.connect(lambda: self.panel_degistir(2, "💡 Işık Modülü"))
        self.btn_theme.clicked.connect(self.tema_degistir)

    def panel_degistir(self, index, ad):
        self.stack.setCurrentIndex(index)
        self.baslik_guncelle(f"🧭 Aktif Modül: {ad}")

    def tema_degistir(self):
        self.theme_manager.toggle_theme(QApplication.instance())
        # Zincirleme olarak ana pencere ve aktif panelin temasını güncelle
        main_window = self.parentWidget()
        while main_window and not isinstance(main_window, QMainWindow):
            main_window = main_window.parentWidget()
        if main_window and hasattr(main_window, 'apply_theme'):
            main_window.apply_theme()

class AnaPencere(QMainWindow):
    def __init__(self):
        super().__init__()
        self.theme_manager = ThemeManager()
        self.setup_ui()
        self.showMaximized()  # Tam ekran olarak aç

    def setup_ui(self):
        self.setWindowTitle("SIAF - Ses ve Işık Analiz Filtresi")
        self.setMinimumSize(1200, 800)  # Minimum pencere boyutu

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        self.baslik = QLabel("🧭 Aktif Modül: Ana Menü")
        self.baslik.setAlignment(Qt.AlignCenter)
        self.baslik.setStyleSheet("""
            QLabel {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #2196F3, stop:1 #1976D2);
                color: white;
                padding: 5px;
                border-radius: 10px;
                margin: 5px;
                font-size: 18px;
                font-weight: bold;
                font-family: 'Segoe UI', Arial;
            }
        """)

        self.stack = QStackedWidget()
        self.stack.setStyleSheet("""
            QStackedWidget {
                background-color: transparent;
            }
        """)

        self.sound_panel = SoundPanel(self.geri_don)
        self.light_panel = LightPanel(self.geri_don)

        self.stack.addWidget(AnaEkran(self.stack, self.baslik_guncelle, self.modulleri_baslat, self.theme_manager))
        self.stack.addWidget(self.sound_panel)
        self.stack.addWidget(self.light_panel)

        layout = QVBoxLayout()
        layout.setSpacing(15)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.addWidget(self.baslik)
        layout.addWidget(self.stack)
        self.central_widget.setLayout(layout)

    def apply_theme(self):
        # Ana pencere styleSheet'ini sıfırla ve tekrar ata
        self.setStyleSheet("")
        self.central_widget.setStyleSheet("")
        self.stack.setStyleSheet("")
        # Tema yöneticisinden uygulama genelini güncelle
        self.theme_manager.apply_theme(QApplication.instance())
        # Aktif paneli bul ve onun temasını da güncelle
        current_index = self.stack.currentIndex()
        if current_index == 1:
            self.sound_panel.apply_theme()
        elif current_index == 2:
            self.light_panel.apply_theme()

    def baslik_guncelle(self, text):
        self.baslik.setText(text)

    def geri_don(self):
        self.stack.setCurrentIndex(0)
        self.baslik.setText("🧭 Aktif Modül: Ana Menü")

    def modulleri_baslat(self):
        print("[✅] Kullanıcı başlattı, modüller eş zamanlı başlatılıyor...")
        threading.Thread(target=self.sound_panel.baslat_ses_analizi, daemon=True).start()
        threading.Thread(target=self.light_panel.baslat_isik_izleme, daemon=True).start()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle(QStyleFactory.create('Fusion'))

    theme_manager = ThemeManager()
    theme_manager.apply_theme(app)

    pencere = AnaPencere()
    pencere.show()
    sys.exit(app.exec_())
