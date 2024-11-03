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

class ImageLoaderThread(QThread):
    image_loaded = pyqtSignal(QImage)

    def __init__(self, url):
        super().__init__()
        self.url = url

    def run(self):
        #print("Entered run method")  # Debug
        try:
            print(f"Attempting to load image from URL: {self.url}")
            response = requests.get(self.url, stream=True, timeout=10, headers=headers)  # Add a timeout
            response.raise_for_status()  # Raises an HTTPError for bad status codes

            #print(f"Downloaded content size: {len(response.content)} bytes")  # Log the size of the downloaded content
            content_type = response.headers.get('Content-Type')
            #print(f"Content-Type: {content_type}")  # Check the content type

            if 'image' not in content_type:
                print("Downloaded content is not an image.")
                return

            #print("Image downloaded successfully, processing image data")
            #with open('downloaded_image.jpg', 'wb') as f:
            #    f.write(response.content)
            #print("Image saved as 'downloaded_image.jpg' for inspection.")

            # Log raw image data
            #print("Raw image data sample:", response.content[:100])  # Log first 100 bytes

            # Check if the image is in WebP format
            if 'webp' in content_type:
                #print("Detected WebP format, using Pillow to process the image.")
                # Load image using Pillow
                image = Image.open(io.BytesIO(response.content))
                #print(f"Image mode before conversion: {image.mode}")  # Log image mode
                if image.mode != 'RGB':
                    image = image.convert('RGB')
                #print("Image size after conversion:", image.size)  # Log image size
                # Convert to numpy array
                rgb_image = np.array(image)
            else:
                # Handle other formats (e.g., JPEG, PNG) with OpenCV
                image_array = np.asarray(bytearray(response.content), dtype=np.uint8)
                rgb_image = cv2.imdecode(image_array, cv2.IMREAD_COLOR)

                if rgb_image is None:
                    print("Failed to decode image from downloaded data.")
                    return

            height, width, channel = rgb_image.shape
            bytes_per_line = 3 * width

            # Create QImage and ensure correct format
            q_image = QImage(rgb_image.data, width, height, bytes_per_line, QImage.Format_RGB888)

            if q_image.isNull():
                print("QImage conversion failed, result is null.")
                return

            print("Emitting loaded image")  # Confirm we're about to emit
            self.image_loaded.emit(q_image)

        except requests.exceptions.RequestException as e:
            print(f"Request failed: {e}")  # Catch network/SSL errors
        except Exception as e:
            print(f"Error loading image: {e}")