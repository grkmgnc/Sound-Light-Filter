from scipy.signal import butter, sosfilt, sosfilt_zi, cheby1
import numpy as np

class DSPFiltreleme:
    def __init__(self, lowcut=50, highcut=2000, rate=48000, order=6, max_gain=1.0):
        self.lowcut = lowcut
        self.highcut = highcut
        self.rate = rate
        self.order = order
        self.max_gain = max_gain
        self.sos = self._butter_bandpass()
        self.zi = sosfilt_zi(self.sos) * 0.0  # Başlangıç için sıfır iç durum

    def _butter_bandpass(self):
        nyquist = 0.5 * self.rate
        low = self.lowcut / nyquist
        high = self.highcut / nyquist
        return butter(self.order, [low, high], btype='bandpass', output='sos')
        #return cheby1(N=self.order, rp=0.5, Wn=[low, high], btype='bandpass', output='sos')
    def filtrele(self, data_int16):
        """int16 ses verisi alır, filtreler ve int16 olarak geri döner."""
        if data_int16.dtype != np.int16:
            raise ValueError("Filtreleme için yalnızca int16 veri kabul edilir.")

        # 1. Normalize: int16 → float32 (-1.0 ile 1.0 arası)
        data = data_int16.astype(np.float32) / 32768.0

        # 2. Bandpass filtre uygula
        filtered, self.zi = sosfilt(self.sos, data, zi=self.zi)

        # 3. Gain uygula (istenirse)

        max_val = np.max(np.abs(filtered))
        if max_val < 0.001:  # Çok daha düşük eşik
            return np.zeros_like(data_int16)   # Filtrelenmeden geri döndür & tam sessizlik

        gain = min(1.0 / max_val, self.max_gain)
        filtered *= gain

        # 4. float32 → int16 dönüşüm ve clipping
        output = np.clip(filtered * 32767, -32768, 32767).astype(np.int16)
        return output

    def reset(self):
        """Filtre iç durumunu sıfırlar (yeni bir kayıt veya segment için)."""
        self.zi = sosfilt_zi(self.sos) * 0.0