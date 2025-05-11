import cv2
import numpy as np
import screen_brightness_control as sbc
import time

class IsikModul:
    def __init__(self):
        pass

    def run(self):
        print("[Işık CLI] Işık izleme başlatıldı.")
        while True:
            ortam = self.ortam_isik_olc()
            pwm_durum = self.pwm_flicker_fft()

            if ortam < 30:
                self.parlaklik_ayarla(20)
            elif ortam < 60:
                self.parlaklik_ayarla(30)
            elif ortam < 90:
                self.parlaklik_ayarla(40)
            elif ortam < 120:
                self.parlaklik_ayarla(50)
            elif ortam < 150:
                self.parlaklik_ayarla(60)
            elif ortam < 180:
                self.parlaklik_ayarla(70)
            else:
                self.parlaklik_ayarla(80)

            print(f"[Işık CLI] PWM durumu: {pwm_durum}")
            time.sleep(5)

    def ortam_isik_olc(self):
        cap = cv2.VideoCapture(0)
        ret, frame = cap.read()
        cap.release()
        if not ret:
            print("[⚠] Kamera erişilemedi.")
            return 0
        gri = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        parlaklik = np.mean(gri)
        print(f"[💡] Ortam Işığı: {parlaklik:.2f}")
        return parlaklik

    def parlaklik_ayarla(self, value):
        sbc.set_brightness(value)
        print(f"[🔦] Parlaklık ayarlandı: {value}%")

    def pwm_flicker_fft(self):
        cap = cv2.VideoCapture(0)
        parlakliklar = []
        baslangic = time.time()
        while time.time() - baslangic < 1.5:
            ret, frame = cap.read()
            if not ret:
                continue
            gri = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            parlakliklar.append(np.mean(gri))
        cap.release()

        if len(parlakliklar) < 10:
            return "🟡 PWM verisi yetersiz"

        fps = len(parlakliklar) / 1.5
        parlaklik_array = np.array(parlakliklar)
        fft = np.abs(np.fft.fft(parlaklik_array - np.mean(parlaklik_array)))
        frekanslar = np.fft.fftfreq(len(fft), d=1 / fps)

        pozitif = frekanslar > 0
        fft = fft[pozitif]
        frekanslar = frekanslar[pozitif]

        flicker_aralik = (frekanslar > 3) & (frekanslar < 20)
        fft_aralik = fft[flicker_aralik]

        if len(fft_aralik) == 0:
            return "🟡 PWM tespit edilemedi"

        en_yuksek = np.max(fft_aralik)
        return "⚠️ PWM Flicker tespit edildi!" if en_yuksek > 5 else "✅ PWM Flicker yok"
