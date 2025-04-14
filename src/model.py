import json
from src.frequencyAnalysis import FrekansAnalizi


class ModelEgitimi:
    def __init__(self, lowcut=20, highcut=3000, learning_rate=1.0):
        """
        Modelin eğitilmesi için parametreler:
        - lowcut: Başlangıç düşük frekans sınırı.
        - highcut: Başlangıç yüksek frekans sınırı.
        - learning_rate: Modelin geri bildirimlere tepki verme hızı.
        """
        self.lowcut = lowcut
        self.highcut = highcut
        self.learning_rate = learning_rate

    def egit(self, ses_verisi, kullanici_geri_bildirim):
        """
        Modeli eğitir. Kullanıcı geri bildirimi ile eşikleri günceller.
        - ses_verisi: Kaydedilen ses dosyası.
        - kullanici_geri_bildirim: 1 (rahatsız edici) veya 0 (normal)
        """
        # Frekans analizi yap
        frekans_analizi = FrekansAnalizi(lowcut=self.lowcut, highcut=self.highcut)
        S_dB, low_energy, high_energy, min_frekans, max_frekans = frekans_analizi.analiz_et(ses_verisi)

        # Eğer sesin frekansı lowcut ile highcut arasında ise, doğrudan eşikleri güncelle
        if self.lowcut <= min_frekans <= self.highcut and self.lowcut <= max_frekans <= self.highcut:
            if kullanici_geri_bildirim == 1:  # Rahatsız edici ses
                if low_energy > high_energy:  # Eğer düşük frekans enerjisi daha yüksekse
                    self.lowcut = min_frekans  # Lowcut'ı güncelle
                else:
                    self.highcut = max_frekans  # Highcut'ı güncelle
            elif kullanici_geri_bildirim == 0:  # Normal ses
                if low_energy < high_energy:  # Eğer düşük frekans enerjisi daha düşükse
                    self.lowcut = min_frekans  # Lowcut'ı güncelle
                else:
                    self.highcut = max_frekans  # Highcut'ı güncelle
        else:
            # Eğer sesin frekansı lowcut ve highcut dışında ise, learning rate ile kademeli güncelleme yap
            if kullanici_geri_bildirim == 1:  # Rahatsız edici ses
                if min_frekans > self.lowcut:  # Eğer düşük frekans enerjisi daha yüksekse
                    self.lowcut += self.learning_rate  # Eşik yukarı kaydırılır
                if max_frekans < self.highcut:  # Eğer yüksek frekans enerjisi daha düşükse
                    self.highcut -= self.learning_rate  # Eşik aşağı kaydırılır
            elif kullanici_geri_bildirim == 0:  # Normal ses
                if low_energy < high_energy:  # Eğer düşük frekans enerjisi daha düşükse
                    self.lowcut -= self.learning_rate  # Eşik aşağı kaydırılır
                else:
                    self.highcut += self.learning_rate  # Eşik yukarı kaydırılır

        print(f"Güncellenmiş Lowcut: {self.lowcut}, Highcut: {self.highcut}")

        # Model parametrelerini kaydedelim
        self.save_model_parameters()

    def save_model_parameters(self):
        """Model parametrelerini dosyaya kaydeder"""
        params = {
            'lowcut': self.lowcut,
            'highcut': self.highcut
        }
        with open('model_params.json', 'w') as f:
            json.dump(params, f)
        print("Model parametreleri kaydedildi.")

    def load_model_parameters(self):
        """Model parametrelerini dosyadan yükler"""
        try:
            with open('model_params.json', 'r') as f:
                params = json.load(f)
                self.lowcut = params.get('lowcut', self.lowcut)  # Eğer dosya yoksa varsayılan değeri kullan
                self.highcut = params.get('highcut', self.highcut)  # Eğer dosya yoksa varsayılan değeri kullan
                print(f"Model parametreleri yüklendi: Lowcut: {self.lowcut}, Highcut: {self.highcut}")
        except FileNotFoundError:
            print("Model parametre dosyası bulunamadı, varsayılan parametreler kullanılacak.")
