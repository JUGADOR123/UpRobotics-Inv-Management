import time
import cv2
import numpy as np
import requests
from PyQt5.QtCore import QThread, pyqtSignal
from PyQt5.QtGui import QImage
from PIL import Image
import io

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.159 Safari/537.36',
    'Accept': 'image/webp,*/*',
    'Referer': 'https://www.mouser.com'
}


def fetch_image(url, retries=3, backoff=1.0):
    for attempt in range(retries):
        try:
            response = requests.get(url, stream=False, timeout=10, headers=headers)
            response.raise_for_status()
            return response
        except requests.exceptions.RequestException as e:
            if attempt < retries - 1:
                time.sleep(backoff)
                backoff *= 2  # Exponential backoff
            else:
                raise e


class ImageLoaderThread(QThread):
    image_loaded = pyqtSignal(QImage)
    new_url = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.url = None
        self.new_url.connect(self.set_url)

    def set_url(self, url):
        if not url:
            print("No valid link received")
            self.image_loaded.emit(QImage())
            return
        if self.isRunning():
            print("Thread already running. Waiting to restart.")
            self.wait()
        self.url = url
        self.start()

    def run(self):
        if self.url:
            try:
                print(f"Loading image from URL: {self.url}")
                response = fetch_image(self.url)
                response.raise_for_status()

                content_type = response.headers.get('Content-Type', '')
                print(f"Content-Type: {content_type}")

                # Load the image as RGB format based on its content type
                if 'webp' in content_type:
                    image = Image.open(io.BytesIO(response.content))
                    if image.mode != 'RGB':
                        image = image.convert('RGB')
                    rgb_image = np.array(image)
                else:
                    image_array = np.asarray(bytearray(response.content), dtype=np.uint8)
                    rgb_image = cv2.imdecode(image_array, cv2.IMREAD_COLOR)

                # Additional validation checks and logging
                try:
                    if rgb_image is not None and rgb_image.size > 0 and len(
                            rgb_image.shape) == 3 and rgb_image.dtype == np.uint8:
                        height, width, channel = rgb_image.shape
                        print(f"Image shape: {rgb_image.shape}")
                        bytes_per_line = 3 * width
                        q_image = QImage(rgb_image.data, width, height, bytes_per_line, QImage.Format_RGB888)

                        # Debugging: Comment out the following line if emitting a blank QImage fixes the crash
                        self.image_loaded.emit(q_image)
                        # Uncomment below for debugging to see if sending a blank QImage avoids the crash
                        # self.image_loaded.emit(QImage())

                        # Clear memory if needed
                        del rgb_image
                        QThread.msleep(10)  # Optional: slight delay for event loop stability
                    else:
                        print("Warning: Loaded image is None, empty, or has unexpected format.")
                        self.image_loaded.emit(QImage())
                except Exception as e:
                    print(f"Error during QImage conversion: {e}")
                    self.image_loaded.emit(QImage())

            except requests.exceptions.RequestException as e:
                print(f"Request failed: {e}")
                self.image_loaded.emit(QImage())
            except Exception as e:
                print(f"Error processing image: {e}")
                self.image_loaded.emit(QImage())
