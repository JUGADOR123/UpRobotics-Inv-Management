import cv2
import numpy as np
import requests
from PyQt5.QtCore import QThread, pyqtSignal
from PyQt5.QtGui import QImage
from PIL import Image
import io

# Headers for the HTTP request
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.159 Safari/537.36',
    'Accept': 'image/webp,*/*',
    'Referer': 'https://www.mouser.com'
}

class ImageLoaderThread(QThread):
    image_loaded = pyqtSignal(QImage)

    def __init__(self, url):
        super().__init__()
        self.url = url

    def run(self):
        try:
            response = requests.get(self.url, stream=True, timeout=10, headers=headers)
            response.raise_for_status()

            if 'webp' in response.headers.get('Content-Type'):
                image = Image.open(io.BytesIO(response.content))
                if image.mode != 'RGB':
                    image = image.convert('RGB')
                rgb_image = np.array(image)
            else:
                image_array = np.asarray(bytearray(response.content), dtype=np.uint8)
                rgb_image = cv2.imdecode(image_array, cv2.IMREAD_COLOR)

            if rgb_image is not None:
                height, width, channel = rgb_image.shape
                bytes_per_line = 3 * width
                q_image = QImage(rgb_image.data, width, height, bytes_per_line, QImage.Format_RGB888)
                self.image_loaded.emit(q_image)
        except requests.exceptions.RequestException as e:
            print(f"Request failed: {e}")
