import os
import time
import soundfile as sf
import pyaudio
import numpy as np
from src.filtre import DSPFiltreleme

class CanliSesFiltreleme:
    def __init__(self, lowcut=50, highcut=2000 , rate=44100, chunk_size=1024, output_dir="data/filtered_audio",stop_event=None):
        """
        - model_egitimi: ModelEgitimi sınıfı örneği
        - rate: Sesin örnekleme hızı
        - chunk_size: Ses parçası boyutu
        """
        self.lowcut=lowcut
        self.highcut=highcut
        self.rate = rate
        self.chunk_size = chunk_size
        self.output_dir=output_dir
        self.stop_event = stop_event
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)
        self.p = pyaudio.PyAudio()
        self.outputDeviceNames= ["Hoparlor","Hoparl","Speakers","Speaker","Headphone","Kulaklik"]
        # Giriş ve çıkış cihazlarını otomatik belirle
        self.input_device_index = self._find_device("CABLE Output",)
        self.output_device_index = self._find_device(self.outputDeviceNames, is_input=False)  # gerekirse özelleştirilir

    def _find_device(self, name_keywords, is_input=True):
        """
        Cihaz listesinde adı verilen anahtar kelimelerden birini içeren ilk cihazın index'ini döndür.
        name_keywords: str ya da list[str]
        """
        if isinstance(name_keywords, str):
            name_keywords = [name_keywords]  # Tek kelimeyi listeye çevir

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

    def start_stream(self):
        print("[start_stream] Başladı")
        try:
            stream = pyaudio.PyAudio().open(
                format=pyaudio.paInt16,
                channels=1,
                rate=self.rate,
                input=True,
                output=True,
                frames_per_buffer=self.chunk_size,
                input_device_index=self.input_device_index,
                output_device_index=self.output_device_index,
                #output_device_index=1
                stream_callback=None,
                start=True
            )

            dsp_filtreleme = DSPFiltreleme(lowcut=self.lowcut, highcut=self.highcut, rate=self.rate)
            filtered_frames = []

            print("[start_stream] Giriş akışı açık. Döngüye giriliyor...")

            while not self.stop_event.is_set():

                input_data = np.frombuffer(stream.read(self.chunk_size), dtype=np.int16)
                filtered = dsp_filtreleme.filtrele(input_data.astype(np.float32))

                # Hafif bir kazanç uygulayıp clip koruması
                filtered *= 0.5
                filtered = np.clip(filtered, -1.0, 1.0)
                # Clipping olmaması için normalize et
                max_val = np.max(np.abs(filtered))
                if max_val > 0:
                    filtered = filtered / max_val
                # tekrar int16 yap (ses dosyasına yazmak ve oynatmak için)
                filtered_int16 = (filtered * 32767).astype(np.int16)

                stream.write(filtered_int16.tobytes())
                filtered_frames.append(filtered_int16.copy())

            print("[start_stream] stop_event algılandı. Döngü sonlandırılıyor...")

        except Exception as e:
            print(f"[start_stream] HATA: {e}")

        finally:
            print("[start_stream] finally bloğu çalışıyor. Kapanış işlemleri yapılıyor.")
            stream.stop_stream()
            stream.close()
            self.p.terminate()
            if filtered_frames:
                final_audio = np.concatenate(filtered_frames)
                max_val = np.max(np.abs(final_audio))
                if max_val > 0:
                    final_audio = final_audio / max_val
                final_audio_int16 = (final_audio * 32767).astype(np.int16)
                timestamp = time.strftime("%Y%m%d-%H%M%S")
                output_filename = os.path.join(self.output_dir, f"filtered_audio_{timestamp}.wav")
                sf.write(output_filename, final_audio_int16, self.rate)
                print(f"[start_stream] Filtrelenmiş ses kaydedildi: {output_filename}")
            else:
                print("[start_stream] Kayıt yapılacak ses bulunamadı.")
