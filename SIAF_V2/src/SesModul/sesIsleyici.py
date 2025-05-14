import json
import os
import time
import subprocess
from .frekansAnalizi import FrekansAnalizi
from .sesKayit import SesKayit  # OBS tabanlı ses kaydı sınıfı
from .model import ModelEgitimi
from .canliFiltre import CanliSesFiltreleme
import threading
from collections import deque
from PyQt5.QtCore import QObject, pyqtSignal

class SesModul(QObject):
    recording_finished = pyqtSignal()  # Ses kaydı bittiğinde tetiklenecek sinyal

    def __init__(self):
        super().__init__()
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
        self.ilk_kayit_islem_gordumu = False  # İlk kaydın işlenip işlenmediğini takip etmek için

        # OBS video dosyaları için klasör yolu
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

        # Analiz edilecek .wav dosyalarının kaydedileceği klasör
        self.output_dir = os.path.join(os.getcwd(), "data", "kaydedilen_sesler")
        os.makedirs(self.output_dir, exist_ok=True)

        # Maksimum dosya sayısı
        self.max_files = 50  # Her klasör için maksimum dosya sayısı
        self.max_obs_files = 20  # OBS video dosyaları için maksimum sayı

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

    def geri_bildirim_ekle(self, feedback):
        if feedback not in ("0", "1"):
            print("[⚠] Geçersiz geri bildirim. Sadece '0' (normal) veya '1' (rahatsız edici) girilebilir.")
            return

        with self.geri_bildirim_lock:
            for kayit in reversed(self.kayitlar):
                if not kayit.get("feedback"):
                    kayit["feedback"] = feedback
                    print(f"[📝] Geri Bildirim Eşlendi → {kayit['timestamp']}: {feedback}")
                    return

            print("[ℹ] Tüm kayıtlar zaten geri bildirim aldı. Yeni geri bildirim bekleniyor.")

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

    def start_and_stop_recording(self):
        """5 saniyelik ses kaydını başlatır ve durdurur."""
        # Kaydı başlat
        self.ses_kaydi.start_recording()

        # 5 saniye bekleyin (ses kaydının süresi)
        time.sleep(self.ses_kaydi.duration)

        # Kaydı durdur (sinyal otomatik olarak tetiklenecek)
        self.ses_kaydi.stop_recording()

    def cleanup_old_files(self):
        """Eski ses dosyalarını temizler."""
        try:
            # Kaydedilen sesler klasörünü temizle
            files = sorted([os.path.join(self.output_dir, f) for f in os.listdir(self.output_dir)
                          if f.endswith('.wav')], key=os.path.getctime)
            if len(files) > self.max_files:
                for old_file in files[:-self.max_files]:
                    try:
                        os.remove(old_file)
                        print(f"Eski dosya silindi: {old_file}")
                    except Exception as e:
                        print(f"Dosya silinirken hata oluştu: {e}")

        except Exception as e:
            print(f"Dosya temizleme işlemi sırasında hata oluştu: {e}")

    def cleanup_obs_files(self):
        """OBS'nin oluşturduğu eski video dosyalarını temizler."""
        if not self.obs_output_dir:
            return

        try:
            # Video dosyalarını bul ve tarihe göre sırala
            files = sorted([os.path.join(self.obs_output_dir, f) for f in os.listdir(self.obs_output_dir)
                          if f.endswith(('.mkv', '.mp4', '.mov'))], key=os.path.getctime)

            # Maksimum dosya sayısını aşan eski dosyaları sil
            if len(files) > self.max_obs_files:
                for old_file in files[:-self.max_obs_files]:
                    try:
                        os.remove(old_file)
                        print(f"Eski OBS video dosyası silindi: {old_file}")
                    except Exception as e:
                        print(f"OBS video dosyası silinirken hata oluştu: {e}")

        except Exception as e:
            print(f"OBS dosya temizleme işlemi sırasında hata oluştu: {e}")

    def run(self):
        try:
            #self.ses_kaydi.get_obs_install_path()
            #self.ses_kaydi.start_obs()
            self.ses_kaydi.connect()
            lc, hc = self.load_model_parameters()
            print("→ İlk CanliSesFiltreleme başlatılıyor...")
            self.canli_filtre = CanliSesFiltreleme(lowcut=lc, highcut=hc, stop_event=self.stop_event)
            self.canli_filtre_thread = threading.Thread(target=self.canli_filtre.start_stream, daemon=True)
            self.canli_filtre_thread.start()
            while True:
                # OBS ile 5 saniyelik kayıt al
                self.start_and_stop_recording()
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

                # Eski dosyaları temizle
                self.cleanup_old_files()
                self.cleanup_obs_files()  # OBS video dosyalarını temizle

                # İlk kayıt işlem gördüyse veya bu ilk kayıt değilse sinyali tetikle
                if self.ilk_kayit_islem_gordumu or len(self.kayitlar) > 1:
                    pass  # Sinyali kaldırdık
                else:
                    self.ilk_kayit_islem_gordumu = True

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



