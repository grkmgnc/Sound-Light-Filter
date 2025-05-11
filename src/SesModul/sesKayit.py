import os
import subprocess
import time
from obswebsocket import obsws, requests
import winreg

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
        self.obs_path=None

    def connect(self):
        """OBS WebSocket'e bağlan."""
        try:
            self.ws.connect()
            # Kayıt klasörünü ayarla
            if self.obs_path:
                obs_dir = os.path.dirname(self.obs_path)
                config_path = os.path.join(obs_dir, "config", "global.ini")
                if os.path.exists(config_path):
                    # OBS'nin kayıt klasörünü ayarla
                    self.ws.call(requests.SetFilenameFormatting("SIAF_obs/%Y-%m-%d %H-%M-%S"))
                    print("OBS kayıt klasörü ayarlandı.")
            print("OBS'ye bağlanıldı.")
            return True
        except Exception as e:
            print(f"OBS'ye bağlanırken hata oluştu: {e}")
            return False

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

    def get_obs_install_path(self):
        try:
            # Kayıt defterinden OBS'nin kurulu olduğu dizini al
            registry_path = r"SOFTWARE\OBS Studio"
            key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, registry_path)

            try:
                install_path, _ = winreg.QueryValueEx(key, "InstallLocation")
            except FileNotFoundError:
                install_path, _ = winreg.QueryValueEx(key, "Varsayılan")
            winreg.CloseKey(key)

        except Exception as e:
            print(f"OBS'nin kurulu olduğu yolu alırken bir hata oluştu: {e}")
            self.obs_path=r"C:\Program Files\obs-studio\bin\64bit\obs64.exe"
            if self.obs_path:
                print("Default yol alındı.")
            else:
                print("Yol alinamadi.")
            return None

        # OBS yolunu al
        self.obs_path = os.path.join(install_path, "bin", "64bit", "obs64.exe")
        if self.obs_path:
            print(f"OBS'nin kurulu olduğu yol: {self.obs_path}")
        else:
            print("OBS'nin kurulu olduğu yol alınamadı.")

    def start_obs(self):
        #working_directory = r"C:\Program Files\obs-studio"  # OBS'nin kurulu olduğu dizin
        # Çalışma dizinini ayarla
        #os.chdir(working_directory)
        #os.environ["OBS_PATH"] = r"C:\Program Files\obs-studio"
        # OBS'nin başlatılacak komutları
        params = ["--minimized"]

        try:
            # subprocess kullanarak OBS'yi arka planda başlatıyoruz
            subprocess.Popen([self.obs_path] + params, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            print("OBS başlatıldı.")
        except Exception as e:
            print(f"OBS başlatılırken bir hata oluştu: {e}")

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