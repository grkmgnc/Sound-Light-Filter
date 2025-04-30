import json
import os
import time
import subprocess
from src.frekansAnalizi import FrekansAnalizi
from src.sesKayit import SesKayit  # OBS tabanlı ses kaydı sınıfı
from src.model import ModelEgitimi
from src.canliFiltre import CanliSesFiltreleme
import threading
from collections import deque

class Main:
    def __init__(self):
        self.ses_kaydi = SesKayit(duration=5, password="121361")
        self.model_egitim = ModelEgitimi()
        self.canli_filtre_thread = None
        self.stop_event = threading.Event()
        self.canli_filtre = None
        self.lowcut = 50
        self.highcut = 2000
        self.kullanici_geri_bildirim = None  # Kullanıcı geri bildirimi
        self.geri_bildirim_thread = None
        # Son 2 kayıt (önceki ve şu anki) tutulur
        self.kayitlar = deque(maxlen=2)
        self.geri_bildirim_lock = threading.Lock()
        # OBS video dosyaları için klasör yolları
        video_folder_english = os.path.join(os.path.expanduser("~"), "Videos")
        video_folder_turkish = os.path.join(os.path.expanduser("~"), "Videolar")

        # Hangi klasörün var olduğunu kontrol et
        if os.path.exists(video_folder_english):
            self.obs_output_dir = video_folder_english
            print(f"OBS kayıtları {self.obs_output_dir} klasörüne kaydedilecektir.")
        elif os.path.exists(video_folder_turkish):
            self.obs_output_dir = video_folder_turkish
            print(f"OBS kayıtları {self.obs_output_dir} klasörüne kaydedilecektir.")
        else:
            print("Videos veya Videolar klasörü bulunamadı!")
            self.obs_output_dir = None

        # Eğer klasör bulunursa, devam et
        if not self.obs_output_dir:
            print("OBS klasörü bulunamadığı için işlem yapılamaz.")
            return

        # Analiz edilecek .wav dosyalarının kaydedileceği klasör
        self.output_dir = os.path.join(os.getcwd(), "data", "kaydedilen_sesler")
        os.makedirs(self.output_dir, exist_ok=True)



    def convert_to_wav(self, input_path, output_path):
        """OBS'nin oluşturduğu video dosyasından .wav çıkar."""
        if not self.is_ffmpeg_installed():
            print("FFmpeg bulunamadı. Lütfen FFmpeg'i yükleyin ve PATH'e ekleyin.")
            return  # FFmpeg yüklü değilse fonksiyonu sonlandır

        subprocess.call([
            "ffmpeg", "-y", "-i", input_path,
            "-vn", "-acodec", "pcm_s16le", "-ar", "48000", "-ac", "1",
            output_path
        ])

    def get_latest_obs_recording(self):
        """OBS'nin oluşturduğu en yeni video dosyasını bulur."""
        if not self.obs_output_dir:
            return None  # Eğer klasör bulunamıyorsa, None döndür

        files = [os.path.join(self.obs_output_dir, f)
                 for f in os.listdir(self.obs_output_dir)
                 if f.endswith(('.mkv', '.mp4', '.mov'))]
        return max(files, key=os.path.getctime) if files else None

    def is_ffmpeg_installed(self):
        try:
            # FFmpeg'in yüklü olup olmadığını kontrol etmek için
            subprocess.call(["ffmpeg", "-version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            return True
        except FileNotFoundError:
            return False

    def kullanici_geri_bildirim_thread(self):
        while True:
            feedback = input("Geri bildirim (1: rahatsız edici, 0: normal, Enter: boş bırak): ")
            with self.geri_bildirim_lock:
                for kayit in reversed(self.kayitlar):
                    if not kayit.get("feedback"):
                        kayit["feedback"] = feedback
                        print(f"Geri bildirim eşlendi → {kayit['timestamp']} için: {feedback}")
                        break
            time.sleep(6)

    def load_model_parameters(self):
        """Model parametrelerini dosyadan yükler"""
        try:
            with open('model_params.json', 'r') as f:
                params = json.load(f)
                self.lowcut = params.get('lowcut', self.lowcut)  # Eğer dosya yoksa varsayılan değeri kullan
                self.highcut = params.get('highcut', self.highcut)  # Eğer dosya yoksa varsayılan değeri kullan
                print(f"Model parametreleri yüklendi: Lowcut: {self.lowcut}, Highcut: {self.highcut}")
                return self.lowcut,self.highcut
        except FileNotFoundError:
            print("Model parametre dosyası bulunamadı, varsayılan parametreler kullanılacak.")
            return self.lowcut,self.highcut

    def run(self):
        try:
            #self.ses_kaydi.get_obs_install_path()
            #self.ses_kaydi.start_obs()
            self.ses_kaydi.connect()
            while True:
                # OBS ile 5 saniyelik kayıt al
                self.ses_kaydi.start_and_stop_recording()
                #time.sleep(3)

                # En son kaydedilen video dosyasını bul
                latest_video = self.get_latest_obs_recording()
                if not latest_video:
                    print("OBS kayıt dosyası bulunamadı!")
                    continue

                # WAV dosyasına dönüştür
                timestamp = int(time.time())
                wav_path = os.path.join(self.output_dir, f"obs_kayit_{timestamp}.wav")
                self.convert_to_wav(latest_video, wav_path)

                # Yeni kaydı ekle
                self.kayitlar.append({
                    "timestamp": timestamp,
                    "path": wav_path,
                    "feedback": None
                })

                if not (self.geri_bildirim_thread and self.geri_bildirim_thread.is_alive()):
                    self.geri_bildirim_thread = threading.Thread(target=self.kullanici_geri_bildirim_thread)
                    self.geri_bildirim_thread.start()  # Geri bildirim thread'ini başlat
                    # Önceki kayıt varsa, geri bildirim varsa eğit
                if len(self.kayitlar) >= 1:
                    onceki_kayit = self.kayitlar[0]
                    if onceki_kayit.get("feedback"):
                        lc, hc = self.model_egitim.egit(onceki_kayit["path"], onceki_kayit["feedback"])
                        print(f"Güncellenmiş lowcut: {lc}, highcut: {hc}")
                    else:
                        print("[⚠] Önceki kayda geri bildirim alınmadı.")
                        lc, hc = self.load_model_parameters()
                else:
                    print("[ℹ] İlk geri bildirim henüz alınamadı.")
                    lc, hc = self.load_model_parameters()
                # Frekans analizi yap
                frekans_analizi = FrekansAnalizi(lowcut=lc, highcut=hc)
                frekans_analizi.analiz_et(wav_path)

                if self.canli_filtre_thread and self.canli_filtre_thread.is_alive():
                    print("→ Eski canlı filtreleme thread'i tespit edildi, durduruluyor...")
                    self.stop_event.set()
                    self.canli_filtre_thread.join()
                    print("→ Eski thread başarıyla sonlandırıldı.")

                # Yeni thread için event sıfırlanıyor
                self.stop_event.clear()

                print("→ Yeni CanliSesFiltreleme nesnesi oluşturuluyor...")
                self.canli_filtre = CanliSesFiltreleme(lowcut=lc, highcut=hc, stop_event=self.stop_event)

                print("→ Yeni thread nesnesi oluşturuluyor...")
                self.canli_filtre_thread = threading.Thread(target=self.canli_filtre.start_stream, daemon=True)

                print("→ Yeni canlı filtreleme thread'i başlatılıyor...")
                self.canli_filtre_thread.start()
                print("→ Başlatıldı mı?:", self.canli_filtre_thread.is_alive())

                time.sleep(1)

        except KeyboardInterrupt:
            print("Program sonlandırıldı.")
            self.stop_event.set()
            if self.canli_filtre_thread and self.canli_filtre_thread.is_alive():
                self.canli_filtre_thread.join()
            self.ses_kaydi.disconnect()


if __name__ == "__main__":
    # Main sınıfını başlat ve çalıştır
    app = Main()
    app.run()
