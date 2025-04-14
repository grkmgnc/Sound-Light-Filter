import os
import time
import subprocess
from src.frequencyAnalysis import FrekansAnalizi
from src.sesKayit import SesKayit  # OBS tabanlı ses kaydı sınıfı

class Main:
    def __init__(self):
        self.ses_kaydi = SesKayit(duration=5, password="121361")
        self.frekans_analizi = FrekansAnalizi()

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

        self.ses_kaydi.connect()

    def convert_to_wav(self, input_path, output_path):
        """OBS'nin oluşturduğu video dosyasından .wav çıkar."""
        if not self.is_ffmpeg_installed():
            print("FFmpeg bulunamadı. Lütfen FFmpeg'i yükleyin ve PATH'e ekleyin.")
            return  # FFmpeg yüklü değilse fonksiyonu sonlandır

        subprocess.call([
            "ffmpeg", "-y", "-i", input_path,
            "-vn", "-acodec", "pcm_s16le", "-ar", "44100", "-ac", "1",
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

    def run(self):
        try:
            while True:
                # OBS ile 5 saniyelik kayıt al
                self.ses_kaydi.start_and_stop_recording()
                time.sleep(3)

                # En son kaydedilen video dosyasını bul
                latest_video = self.get_latest_obs_recording()
                if not latest_video:
                    print("OBS kayıt dosyası bulunamadı!")
                    continue

                # WAV dosyasına dönüştür
                timestamp = int(time.time())
                wav_path = os.path.join(self.output_dir, f"obs_kayit_{timestamp}.wav")
                self.convert_to_wav(latest_video, wav_path)

                # Frekans analizi yap
                self.frekans_analizi.analiz_et(wav_path)

                # Kullanıcı geri bildirimi vs.
                kullanici_geri_bildirim = 1
                # self.model_egitimi.egit(wav_path, kullanici_geri_bildirim)

                time.sleep(1)

        except KeyboardInterrupt:
            print("Program sonlandırıldı.")
            self.ses_kaydi.disconnect()

if __name__ == "__main__":
    # Main sınıfını başlat ve çalıştır
    app = Main()
    app.run()
