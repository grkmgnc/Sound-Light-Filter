import threading

class MultimodalController:
    def __init__(self, sound_module, light_module):
        self.sound_module = sound_module
        self.light_module = light_module

    def start(self):
        sound_thread = threading.Thread(target=self.sound_module.run)
        light_thread = threading.Thread(target=self.light_module.run)

        print("MultimodalController: Modüller başlatılıyor...")
        sound_thread.start()
        light_thread.start()

        sound_thread.join()
        light_thread.join()
        print("MultimodalController: Modüller tamamlandı.")