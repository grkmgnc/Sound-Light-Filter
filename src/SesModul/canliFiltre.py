import os
import time
import soundfile as sf
import pyaudio
import numpy as np
from src.SesModul.filtre import DSPFiltreleme  # int16 giriş-çıkış uyumlu sürüm

class CanliSesFiltreleme:
    def __init__(self, lowcut=50, highcut=2000, rate=48000, chunk_size=2048,
                 output_dir="data/filtered_audio", stop_event=None):
        self.lowcut = lowcut
        self.highcut = highcut
        self.rate = rate
        self.chunk_size = chunk_size
        self.output_dir = output_dir
        self.stop_event = stop_event or self._create_default_stop_event()
        self.max_files = 50  # Maksimum dosya sayısı

        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)

        self.p = pyaudio.PyAudio()
        self.input_device_keywords = ["CABLE Output"]
        self.output_device_keywords = ["Voicemeeter Input"]
        self.input_device_index = self._find_device(self.input_device_keywords, is_input=True)
        self.output_device_index = self._find_device(self.output_device_keywords, is_input=False)
        self.min_hz=None
        self.max_hz=None

    def _create_default_stop_event(self):
        import threading
        return threading.Event()

    def _find_device(self, name_keywords, is_input=True):
        if isinstance(name_keywords, str):
            name_keywords = [name_keywords]

        for i in range(self.p.get_device_count()):
            dev_info = self.p.get_device_info_by_index(i)
            device_name = dev_info.get('name', '').lower()
            if ((is_input and dev_info.get('maxInputChannels') > 0) or
                (not is_input and dev_info.get('maxOutputChannels') > 0)):
                if any(keyword.lower() in device_name for keyword in name_keywords):
                    print(f"[cihaz seçimi] Bulundu: {dev_info['name']} (index: {i})")
                    return i

        print(f"[cihaz seçimi] Uygun cihaz bulunamadı: {name_keywords}")
        return None

    def analiz_frekans_araligi(self, data_int16, rate):
        if data_int16.dtype == np.int16:
            data = data_int16.astype(np.float32) / 32768.0
        else:
            data = data_int16

        data = data - np.mean(data)  # DC bileşeni çıkar

        fft_result = np.fft.rfft(data)
        fft_magnitude = np.abs(fft_result)
        freqs = np.fft.rfftfreq(len(data), 1.0 / rate)

        # ⚠️ Daha sert eşik
        threshold = np.max(fft_magnitude) * 0.3  # %30'un altını sayma
        aktif_frekanslar = freqs[fft_magnitude > threshold]

        if len(aktif_frekanslar) == 0:
            return 0.0, 0.0

        return np.min(aktif_frekanslar), np.max(aktif_frekanslar)

    def cleanup_old_files(self):
        """Eski filtrelenmiş ses dosyalarını temizler."""
        try:
            files = sorted([os.path.join(self.output_dir, f) for f in os.listdir(self.output_dir) 
                          if f.endswith('.wav')], key=os.path.getctime)
            if len(files) > self.max_files:
                for old_file in files[:-self.max_files]:
                    try:
                        os.remove(old_file)
                        print(f"Eski filtrelenmiş dosya silindi: {old_file}")
                    except Exception as e:
                        print(f"Filtrelenmiş dosya silinirken hata oluştu: {e}")
        except Exception as e:
            print(f"Filtrelenmiş dosya temizleme işlemi sırasında hata oluştu: {e}")

    def start_stream(self):
        print("[start_stream] Başladı")
        input_stream = None
        output_stream = None
        filtered_frames = []

        try:
            input_stream = self.p.open(
                format=pyaudio.paInt16,
                channels=1,
                rate=self.rate,
                input=True,
                input_device_index=self.input_device_index,
                frames_per_buffer=self.chunk_size
            )

            output_stream = self.p.open(
                format=pyaudio.paInt16,
                channels=1,
                rate=self.rate,
                output=True,
                output_device_index=self.output_device_index,
                frames_per_buffer=self.chunk_size
            )

            dsp = DSPFiltreleme(lowcut=self.lowcut, highcut=self.highcut, rate=self.rate)
            dsp.reset()
            print("[start_stream] Giriş akışı açık. Döngüye giriliyor...")

            while not self.stop_event.is_set():
                try:
                    raw = input_stream.read(self.chunk_size, exception_on_overflow=False)
                    input_data = np.frombuffer(raw, dtype=np.int16)
                    print(f"[DEBUG] input max: {np.max(input_data):.5f}")
                    filtered = dsp.filtrele(input_data)
                    print(f"[DEBUG] filtered max: {np.max(filtered):.5f}")
                    self.min_hz, self.max_hz = self.analiz_frekans_araligi(filtered, self.rate)
                    print(f"[Frekans] Min: {self.min_hz:.2f} Hz | Max: {self.max_hz:.2f} Hz")

                    output_stream.write(filtered.tobytes())

                    # Sadece son 5 saniyelik sesi tut
                    if len(filtered_frames) >= int(self.rate / self.chunk_size) * 5:
                        filtered_frames.pop(0)
                    filtered_frames.append(filtered.copy())
                    time.sleep(0.001)
                except Exception as e:
                    print(f"[❌] Akış hatası: {e}")
                    break
            print("[start_stream] stop_event algılandı. Döngü sonlandırılıyor...")

        except Exception as e:
            import traceback
            print(f"[start_stream] HATA: {e}")
            traceback.print_exc()
        finally:
            print("[start_stream] finally bloğu çalışıyor. Kapanış işlemleri yapılıyor.")
            if input_stream:
                input_stream.stop_stream()
                input_stream.close()
            if output_stream:
                output_stream.stop_stream()
                output_stream.close()
            self.p.terminate()

            if filtered_frames:
                final_audio = np.concatenate(filtered_frames)
                timestamp = time.strftime("%Y%m%d-%H%M%S")
                output_filename = os.path.join(self.output_dir, f"filtered_audio_{timestamp}.wav")
                sf.write(output_filename, final_audio, self.rate)
                print(f"[start_stream] Filtrelenmiş ses kaydedildi: {output_filename}")
                # Eski dosyaları temizle
                self.cleanup_old_files()
            else:
                print("[start_stream] Kayıt yapılacak ses bulunamadı.")
