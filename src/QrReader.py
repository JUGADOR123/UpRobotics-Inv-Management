import cv2
import numpy as np
import requests
from PyQt5.QtCore import QSize, Qt
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import QLabel, QMainWindow, QTextEdit, QGridLayout, QPushButton, QWidget, QSizePolicy

from pyzbar.pyzbar import decode
from src.CameraThread import CameraThread
from src.ImageLoader import ImageLoaderThread
from src.PdfLoaderThread import PdfLoaderThread
from src.Utils import set_feed, extract_part_data, build_part_data


class QrReader(QMainWindow):
    def __init__(self):
        super().__init__()
        self.image_loader_thread = None
        self.setMaximumSize(QSize(1920, 1080))
        self.resize(1920, 1080)
        self.display_size = (640, 360)

        # Elements
        self.setWindowTitle("Inventory Management")
        self.rawCamera = QLabel()
        self.boundingBoxCamera = QLabel()
        self.infoBox = QTextEdit()
        self.infoBox.setReadOnly(True)
        self.imageLabel = QLabel()

        # PDF Reader placeholder
        self.pdfReaderLabel = QLabel("PDF Reader Placeholder")
        self.pdfReaderLabel.setAlignment(Qt.AlignCenter)

        # Label placeholders
        self.scannedCodesLabel = QLabel("Scanned Codes:")
        self.mouserHitsLabel = QLabel("Found on Mouser:")
        self.notFoundLabel = QLabel("Not found on Mouser:")
        self.scannedCodesCounterLabel = QLabel("0")
        self.foundCodesCounterLabel = QLabel("0")
        self.notFoundCodesCounterLabel = QLabel("0")

        # Buttons
        self.settingsButton = QPushButton("Open Camera Settings")
        self.settingsButton.clicked.connect(self.open_camera_settings)
        self.exportButton = QPushButton("Export CSV")
        self.exitButton = QPushButton("Exit")
        self.exitButton.clicked.connect(self.close)

        # Setting up the layout
        layout = QGridLayout()

        # Top Row
        layout.addWidget(self.rawCamera, 0, 0, 2, 2)
        layout.addWidget(self.boundingBoxCamera, 0, 2, 2, 2)
        layout.addWidget(self.pdfReaderLabel, 0, 4, 6, 2)

        # Middle Row
        layout.addWidget(self.imageLabel, 2, 0, 1, 2)
        layout.addWidget(self.infoBox, 2, 2, 4, 2)

        # Label placeholders
        layout.addWidget(self.scannedCodesLabel, 3, 0)
        layout.addWidget(self.scannedCodesCounterLabel, 3, 1)
        layout.addWidget(self.mouserHitsLabel, 4, 0)
        layout.addWidget(self.foundCodesCounterLabel, 4, 1)
        layout.addWidget(self.notFoundLabel, 5, 0)
        layout.addWidget(self.notFoundCodesCounterLabel, 5, 1)

        # Bottom row with buttons
        layout.addWidget(self.settingsButton, 6, 0, 1, 2)
        layout.addWidget(self.exportButton, 6, 2, 1, 2)
        layout.addWidget(self.exitButton, 6, 4, 1, 2)

        # Setting up central widget
        central_widget = QWidget()
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)

        # Initialize components
        self.camera_thread = CameraThread()
        self.camera_thread.frame_captured.connect(self.process_frame)
        self.camera_thread.start()

        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        #Data
        self.detected_Codes = set()
        self.part_data_list = []
        self.found_codes = 0
        self.not_found_codes = 0


        self.showFullScreen()

    def detect_codes(self, image):
        detections = decode(image)
        if detections:
            for code in detections:
                code_data = code.data.decode('utf-8')
                if code_data not in self.detected_Codes:
                    print(f'Type: {code.type}, Data: {code_data}')
                    self.detected_Codes.add(code_data)
                    self.scannedCodesCounterLabel.setText(f'{len(self.detected_Codes)}')
                    if code.type == 'QRCODE':
                        part_data = extract_part_data(code_data)
                        part_data = build_part_data(part_data.get('pm'), part_data.get('qty'))
                        if part_data:
                            display_text = "\n".join([f"{key}: {value}" for key, value in part_data.items()])
                            self.found_codes +=1
                            self.foundCodesCounterLabel.setText(f"{self.found_codes}")
                            self.infoBox.setText(display_text)
                            self.load_image_from_url(part_data['ImagePath'])
                        else:
                            self.infoBox.setText("Not found on Mouser")
                            self.not_found_codes += 1
                            self.notFoundCodesCounterLabel.setText(f"{self.not_found_codes}")

                            self.imageLabel.clear()
            return detections
        return []

    def load_pdf_from_url(self, url):
        self.pdf_loader_thread = PdfLoaderThread(url)
        self.pdf_loader_thread.pdf_loaded.connect(self.display_pdf)
        self.pdf_loader_thread.start()
    def load_image_from_url(self, url):
        self.image_loader_thread = ImageLoaderThread(url)
        self.image_loader_thread.image_loaded.connect(self.display_image)

        #print("Starting image loader thread")  # Debug print
        self.image_loader_thread.start()

    def display_image(self, q_image):
        # Convert the QImage to a QPixmap
        pixmap = QPixmap.fromImage(q_image)

        # Scale the pixmap to fit the imageLabel while maintaining the aspect ratio
        scaled_pixmap = pixmap.scaled(self.imageLabel.size(), aspectRatioMode=Qt.KeepAspectRatio,
                                      transformMode=Qt.SmoothTransformation)

        # Set the scaled pixmap to the imageLabel
        self.imageLabel.setPixmap(scaled_pixmap)

        # Optionally, adjust the label size to match the pixmap size if you want it to be dynamic
        self.imageLabel.setFixedSize(scaled_pixmap.size())

    def process_frame(self, frame):
        captured_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        raw_feed = cv2.resize(captured_frame, self.display_size)
        cv2.putText(raw_feed, "Raw Feed", (10, 10), cv2.FONT_HERSHEY_PLAIN, 1, (255, 0, 0), 1)
        set_feed(raw_feed, self.rawCamera)

        detection_feed = cv2.resize(captured_frame, self.display_size)
        detections = self.detect_codes(detection_feed)
        cv2.putText(detection_feed, f'Detections: {len(detections)}', (10, 10), cv2.FONT_HERSHEY_PLAIN, 1, (255, 0, 0), 1)

        for qr_code in detections:
            points = qr_code.polygon
            if len(points) > 4:
                hull = cv2.convexHull(np.array([point for point in points], dtype=np.float32))
                hull = list(map(tuple, np.squeeze(hull)))
            else:
                hull = points
            n = len(hull)
            for j in range(n):
                pt1 = tuple(map(int, hull[j]))
                pt2 = tuple(map(int, hull[(j + 1) % n]))
                cv2.line(detection_feed, pt1, pt2, (0, 255, 60), 5)

        set_feed(detection_feed, self.boundingBoxCamera)
        self.update_info(detections)

    def closeEvent(self, event):
        self.camera_thread.release()
        self.camera_thread.wait()
        event.accept()

    def update_info(self, decoded_objects):
        try:
            for obj in decoded_objects:
                code_data = obj.data.decode('utf-8')
                if code_data not in self.detected_Codes:
                    self.detected_Codes.add(code_data)
                    self.infoBox.append(f'Type: {obj.type}, Data: {code_data}\n')
        except Exception as e:
            print(f"Error in update_info: {e}")

    def open_camera_settings(self):
        self.camera_thread.cap.set(cv2.CAP_PROP_SETTINGS, 1)
