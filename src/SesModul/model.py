import json
from src.SesModul.frekansAnalizi import FrekansAnalizi


class ModelEgitimi:
    def __init__(self, lowcut=50, highcut=2000, learning_rate=1.0):
        """
        Modelin eğitilmesi için parametreler:
        - lowcut: Başlangıç düşük frekans sınırı.
        - highcut: Başlangıç yüksek frekans sınırı.
        - learning_rate: Modelin geri bildirimlere tepki verme hızı.
        """
        self.lowcut = lowcut
        self.highcut = highcut
        self.learning_rate = learning_rate
        self.load_model_parameters()
    def egit(self, ses_verisi, kullanici_geri_bildirim):
        """
        Modeli eğitir. Kullanıcı geri bildirimi ile eşikleri günceller.
        - ses_verisi: Kaydedilen ses dosyası.
        - kullanici_geri_bildirim: 1 (rahatsız edici) veya 0 (normal)
        """
        # Frekans analizi yap
        frekans_analizi = FrekansAnalizi(lowcut=self.lowcut, highcut=self.highcut)
        S_dB, low_energy, high_energy, min_frekans, max_frekans,low_energy_out,high_energy_out = frekans_analizi.analiz_et(ses_verisi)

        # Eğer kullanıcı geri bildirimi 1 (rahatsız edici ses) ise sadece lowcut ve highcut aralığındaki frekansları kontrol edip doğrudan eşikleri güncelle
        if kullanici_geri_bildirim == 1:  # Rahatsız edici ses. NOT: Bu kısım daha çok canlı filtre aktifkenki model eğitimine uygundur.
            if self.lowcut <= min_frekans <= self.highcut and self.lowcut <= max_frekans <= self.highcut:
                if low_energy > high_energy:  # Eğer düşük frekans enerjisi daha yüksekse
                    self.lowcut = min_frekans  # Lowcut'ı güncelle
                else:
                    self.highcut = max_frekans  # Highcut'ı güncelle
            elif self.lowcut <= min_frekans <= self.highcut < max_frekans:
                if low_energy>high_energy:
                    self.lowcut=min_frekans
                else:
                    self.highcut-=self.learning_rate*10 # Test edilmeli
            elif min_frekans<self.lowcut<=max_frekans<=self.highcut:
                if high_energy>low_energy:
                    self.highcut=max_frekans
                else:
                    self.lowcut+=self.learning_rate*10 # Test edilmeli
            self.save_model_parameters()
        # Eğer kullanıcı geri bildirimi 0 (normal ses) ise lowcut ve highcut aralığı dışındaki frekansları kontrol et ve learning rate ile kademeli güncelleme yap
        elif kullanici_geri_bildirim==0: # Normal ses. NOT: Bu kısım daha çok canlı filtre inaktifken eğitime uygundur.
            if min_frekans<self.lowcut and max_frekans>self.highcut:
                if low_energy_out>high_energy_out:  # Eğer aralık dışındaki düşük enerji, aralık dışındaki yüksek enerjiden fazlaysa
                    self.lowcut -= self.learning_rate  # Lowcut aşağı kaydırılır
                else:  # Eğer aralık dışındaki yüksek enerji, aralık dışındaki düşük enerjiden fazlaysa
                    self.highcut += self.learning_rate  # Highcut yukarı kaydırılır
            elif min_frekans<self.lowcut<=max_frekans<=self.highcut:
                if low_energy_out > high_energy and low_energy_out>low_energy:  # Eğer aralık dışındaki düşük enerji, aralık içindeki enerjilerden fazlaysa
                    self.lowcut -= self.learning_rate  # Lowcut aşağı kaydırılır
            elif self.lowcut<=min_frekans<=self.highcut<max_frekans:
                if high_energy_out> low_energy and high_energy_out>high_energy: # Eğer aralık dışındaki yüksek enerji, aralık içindeki enerjilerden fazlaysa
                    self.highcut += self.learning_rate  # Highcut yukarı kaydırılır
            self.save_model_parameters()
        print(f"Güncellenmiş Lowcut: {self.lowcut}, Highcut: {self.highcut}")

        # Model parametrelerini kaydedelim
        #self.save_model_parameters()

        return self.lowcut, self.highcut

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