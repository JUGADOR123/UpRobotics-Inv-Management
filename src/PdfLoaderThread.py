import requests
from PyQt5.QtCore import QByteArray, pyqtSignal, QThread


class PdfLoaderThread(QThread):
    pdf_loaded = pyqtSignal(QByteArray)

    def __init__(self, pdf_url):
        super().__init__()
        self.pdf_url = pdf_url

    def run(self):
        if self.pdf_url.startswith("data:text/html"):
            # If the URL is the blank placeholder, emit an empty QByteArray
            print("No PDF URL provided, emitting blank data for placeholder.")
            self.pdf_loaded.emit(QByteArray())
            return

        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.159 Safari/537.36',
            'Referer': 'https://www.mouser.com'
        }

        try:
            print(f"Fetching PDF from: {self.pdf_url}")
            response = requests.get(self.pdf_url, headers=headers, timeout=10)
            response.raise_for_status()
            pdf_data = QByteArray(response.content)
            print("PDF fetched successfully, emitting signal.")
            self.pdf_loaded.emit(pdf_data)
        except requests.RequestException as e:
            print(f"Failed to fetch PDF: {e}")
            self.pdf_loaded.emit(QByteArray())  # Emit empty QByteArray on error