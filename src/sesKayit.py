import time
import obswebsocket
from obswebsocket import obsws, requests


class SesKayit:
    def __init__(self, host="localhost", port=4444, password="", duration=5):
        """
        OBS WebSocket API ile ses kaydını başlatıp durduracak sınıf.

        host: OBS WebSocket sunucusunun adresi.
        port: WebSocket portu (varsayılan: 4444).
        password: WebSocket şifresi.
        duration: Her kaydın süresi (varsayılan 5 saniye).
        """
        self.host = host
        self.port = port
        self.password = password
        self.duration = duration
        self.ws = obsws(self.host, self.port, self.password)

    def connect(self):
        """OBS WebSocket'e bağlan."""
        try:
            self.ws.connect()
            print("OBS'ye bağlanıldı.")
        except Exception as e:
            print(f"OBS'ye bağlanırken hata oluştu: {e}")

    def disconnect(self):
        """OBS WebSocket bağlantısını sonlandır."""
        self.ws.disconnect()
        print("OBS bağlantısı kapatıldı.")

    def start_recording(self):
        """OBS kaydını başlat."""
        try:
            self.ws.call(requests.StartRecording())
            print("OBS kaydı başlatıldı.")
        except Exception as e:
            print(f"Kaydı başlatırken hata oluştu: {e}")

    def stop_recording(self):
        """OBS kaydını durdur."""
        try:
            self.ws.call(requests.StopRecording())
            print("OBS kaydı durduruldu.")
        except Exception as e:
            print(f"Kaydı durdururken hata oluştu: {e}")

    def start_and_stop_recording(self):
        """5 saniyelik ses kaydını başlatır ve durdurur."""
        # Kaydı başlat
        self.start_recording()

        # 5 saniye bekleyin (ses kaydının süresi)
        time.sleep(self.duration)

        # Kaydı durdur
        self.stop_recording()

    def record_indefinitely(self):
        """Program çalıştığı sürece 5 saniyelik kayıtlar başlatır ve durdurur."""
        try:
            while True:
                print("Yeni bir 5 saniyelik kayıt başlatılıyor...")
                self.start_and_stop_recording()  # 5 saniyelik kayıt başlat
                time.sleep(1)  # Kayıtlar arasına kısa bir bekleme süresi ekleyebilirsiniz
        except KeyboardInterrupt:
            print("Program sonlandırıldı.")
            self.disconnect()  # Bağlantıyı sonlandır


