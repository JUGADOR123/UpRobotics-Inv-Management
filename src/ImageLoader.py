import time
from PyQt5.QtCore import QThread, pyqtSignal, QObject
from PyQt5.QtNetwork import QNetworkAccessManager, QNetworkRequest
from PyQt5.QtGui import QImage
from PyQt5.QtCore import QUrl

class AsyncImageLoader(QObject):
    image_loaded = pyqtSignal(QImage)

    def __init__(self):
        super().__init__()
        self.manager = QNetworkAccessManager()
        self.manager.finished.connect(self.on_image_loaded)

    def load_image(self, url):
        request = QNetworkRequest(QUrl(url))
        self.manager.get(request)

    def on_image_loaded(self, reply):
        if reply.error() == 0:  # No error
            data = reply.readAll()
            image = QImage()
            if image.loadFromData(data):
                self.image_loaded.emit(image)
            else:
                print("Loaded data is not a valid image.")
                self.image_loaded.emit(QImage())  # Emit a blank image on failure
        else:
            print(f"Error loading image: {reply.errorString()}")
            self.image_loaded.emit(QImage())  # Emit a blank image on error
