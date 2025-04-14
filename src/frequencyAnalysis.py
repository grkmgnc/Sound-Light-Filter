import librosa
import numpy as np
import librosa.display
import matplotlib.pyplot as plt

class FrekansAnalizi:
    def __init__(self, n_mels=128, hop_length=512, lowcut=200, highcut=3000):
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

    def analiz_et(self, ses_verisi):
        """Mel Spectrogram oluştur ve low, high frekansları tespit et."""
        y, sr = librosa.load(ses_verisi, sr=None)

        # Mel spectrogram oluştur
        S = librosa.feature.melspectrogram(y=y, sr=sr, n_mels=self.n_mels, hop_length=self.hop_length)
        S_dB = librosa.power_to_db(S, ref=np.max)

        # Mel frekansları hesapla
        mel_frequencies = librosa.mel_frequencies(n_mels=self.n_mels, fmin=0, fmax=sr // 2)
        mel_frequencies2 = librosa.mel_frequencies(n_mels=self.n_mels, fmin=self.lowcut, fmax=self.highcut)
        min_frekans = mel_frequencies2[0]  # Minimum Mel frekansı
        max_frekans = mel_frequencies2[-1]  # Maksimum Mel frekansı
        print(f"Minimum Mel frekansı: {min_frekans} Hz")
        print(f"Maksimum Mel frekansı: {max_frekans} Hz")
        # Low ve High frekansları belirle
        # Mel frekansları aralığı içinde lowcut ve highcut'a karşılık gelen indeksleri bulun
        low_frequencies = np.where(mel_frequencies >= self.lowcut)[0]
        high_frequencies = np.where(mel_frequencies >= self.highcut)[0]

        # Mel Spectrogram'da low ve high frekanslardaki enerji yoğunluğunu çıkar
        low_energy = np.sum(S[low_frequencies, :], axis=0) if low_frequencies.size > 0 else np.zeros(S.shape[1])
        high_energy = np.sum(S[high_frequencies, :], axis=0) if high_frequencies.size > 0 else np.zeros(S.shape[1])

        # Görselleştirme
        plt.figure(figsize=(10, 6))
        librosa.display.specshow(S_dB, sr=sr, x_axis='time', y_axis='mel')
        plt.colorbar(format='%+2.0f dB')
        plt.title(f"Mel Spectrogram - {ses_verisi}")
        plt.xlabel('Zaman (saniye)')
        plt.ylabel('Mel frekansları')
        plt.tight_layout()  # Görselleştirmeyi daha düzenli yapar
        plt.show()

        return S_dB, low_energy, high_energy, min_frekans, max_frekans
