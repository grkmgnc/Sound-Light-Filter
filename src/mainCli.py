from SesModul.sesIsleyici import SesModul
from IsikModul.isikIsleyici import IsikModul
from Controller.multimodal_controller import MultimodalController

if __name__ == "__main__":
    sound = SesModul()
    light = IsikModul()
    controller = MultimodalController(sound, light)
    controller.start()
