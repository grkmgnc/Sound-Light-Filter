import librosa
import numpy as np
import librosa.display
import matplotlib.pyplot as plt
import threading
class FrekansAnalizi:
    def __init__(self, lowcut=50, highcut=2000, n_mels=128, hop_length=512):
        """
        Frekans analizi için parametreler:
        - n_mels: Mel frekans bandlarının sayısı.
        - hop_length: Her analiz penceresinin kayma mesafesi.
        - lowcut: Düşük frekans sınırı (rahatsız edici frekanslar için).
        - highcut: Yüksek frekans sınırı (rahatsız edici frekanslar için).
        """
        self.n_mels = n_mels
        self.hop_length = hop_length
        self.lowcut = lowcut
        self.highcut = highcut

    def _grafik_ac(self, S_dB, sr, ses_verisi):
        """Mel Spectrogram grafiğini yeni bir thread üzerinde aç."""
        # Önceki tüm grafikleri kapat
        plt.close('all')

        # Yeni grafik oluştur
        plt.figure(figsize=(10, 6))
        librosa.display.specshow(S_dB, sr=sr, x_axis='time', y_axis='mel')
        plt.colorbar(format='%+2.0f dB')
        plt.title(f"Mel Spectrogram - {ses_verisi}")
        plt.xlabel('Zaman (saniye)')
        plt.ylabel('Mel frekansları')
        plt.tight_layout()  # Görselleştirmeyi daha düzenli yapar
        plt.show()

    def analiz_et(self, ses_verisi):
        """Mel Spectrogram oluştur ve low, high frekansları tespit et."""
        y, sr = librosa.load(ses_verisi, sr=None)

        # Mel spectrogram oluştur
        S = librosa.feature.melspectrogram(y=y, sr=sr, n_mels=self.n_mels, hop_length=self.hop_length)
        S_dB = librosa.power_to_db(S, ref=np.max)
        # Enerji yoğunluğunun yüksek olduğu frekansları bulma
        energy_per_band = np.sum(S, axis=1)  # Her bir frekans bandındaki toplam enerji
        active_bands = np.where(energy_per_band > np.max(energy_per_band) * 0.01)[0]  # Enerji yoğunluğu %1'den fazla olan frekanslar
        mel_frequencies = librosa.mel_frequencies(n_mels=self.n_mels, fmin=0, fmax=sr // 2)
        active_frequencies = mel_frequencies[active_bands]
        min_frekans = np.min(active_frequencies)  # Aktif frekanslar arasındaki minimum frekans
        max_frekans = np.max(active_frequencies)  # Aktif frekanslar arasındaki maksimum frekans

        # Mel frekansları hesapla

        valid_frequencies = np.where((mel_frequencies >= min_frekans) & (mel_frequencies <= max_frekans))[0]
        mel_frequencies_in_range = mel_frequencies[valid_frequencies]
        print()
        print(f"**********Minimum yoğun frekans: {min_frekans} Hz**********")
        print(f"**********Maksimum yoğun frekans: {max_frekans} Hz**********")
        print()
        # Low ve High frekansları belirle
        # Mel frekansları aralığı içinde lowcut ve highcut'a karşılık gelen indeksleri bulun
        averagecut=(self.lowcut + self.highcut)/2
        low_frequencies = np.where((mel_frequencies_in_range >= self.lowcut)&(mel_frequencies_in_range<=averagecut))[0]
        high_frequencies = np.where((mel_frequencies_in_range <= self.highcut)&(mel_frequencies_in_range>=averagecut))[0]
        low_frequencies_out=np.where((mel_frequencies_in_range >= min_frekans)&(mel_frequencies_in_range<=self.lowcut))[0]
        high_frequencies_out=np.where((mel_frequencies_in_range >= self.highcut)&(mel_frequencies_in_range<=max_frekans))[0]

        # Enerji yoğunluğu ile ağırlıklı enerji hesaplamaları — BOYUT UYUMLU
        def weighted_energy(freq_indices):
            if freq_indices.size == 0:
                return 0
            weights = energy_per_band[freq_indices][:, np.newaxis]  # shape: (bands, 1)
            energy = S[freq_indices, :]  # shape: (bands, time)
            return np.sum(energy * weights)

        low_energy = weighted_energy(low_frequencies)
        high_energy = weighted_energy(high_frequencies)
        low_energy_out = weighted_energy(low_frequencies_out)
        high_energy_out = weighted_energy(high_frequencies_out)
        #grafik_thread = threading.Thread(target=self._grafik_ac, args=(S_dB, sr, ses_verisi))
        #grafik_thread.daemon = True  # Ana program bitince thread de sonlansın
        #grafik_thread.start()
        #self._grafik_ac(S_dB,sr,ses_verisi)
        return S_dB, low_energy, high_energy, min_frekans, max_frekans,low_energy_out,high_energy_out