from scipy.signal import butter, sosfilt
import numpy as np
class DSPFiltreleme:
    def __init__(self, lowcut=50, highcut=2000, rate=44100, order=2):
        self.lowcut = lowcut
        self.highcut = highcut
        self.rate = rate
        self.order = order
        self.sos = self._butter_bandpass()

    def _butter_bandpass(self):
        nyquist = 0.5 * self.rate
        low = self.lowcut / nyquist
        high = self.highcut / nyquist
        return butter(self.order, [low, high], btype='bandpass', output='sos')

    def filtrele(self, data):
        data = data.astype(np.float32)
        return sosfilt(self.sos, data)
