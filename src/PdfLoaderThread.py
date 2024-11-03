import requests
from PyQt5.QtCore import QThread, pyqtSignal, QByteArray
class PdfLoaderThread(QThread):
    pdf_loaded = pyqtSignal(QByteArray)

    def __init__(self, pdf_url):
        super().__init__()
        self.pdf_url = pdf_url

    def run(self):
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.159 Safari/537.36',
            'Referer': 'https://www.mouser.com'
        }

        try:
            response = requests.get(self.pdf_url, headers=headers)
            response.raise_for_status()  # Check for HTTP errors
            pdf_data = QByteArray(response.content)
            self.pdf_loaded.emit(pdf_data)
        except requests.RequestException as e:
            print(f"Failed to fetch PDF: {e}")