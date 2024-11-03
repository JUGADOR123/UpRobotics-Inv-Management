
import cv2
from PyQt5.QtCore import QSize
from PyQt5.QtWidgets import QLabel, QWidget, QTextEdit, QGridLayout, QPushButton
from PyQt5.QtGui import QImage, QPixmap
from pyzbar.pyzbar import decode
import numpy as np

from src.VideoCaptureThread import  CameraThread






class QrReader(QWidget):
    def __init__(self):
        super().__init__()
        self.setMaximumSize(QSize(1920, 1080))
        self.resize(1920, 1080)
        self.display_size = (960, 540)

        # Elements
        self.setWindowTitle("Inventory Management")
        self.rawCamera = QLabel()
        self.boundingBoxCamera = QLabel()
        self.infoBox = QTextEdit()
        self.infoBox.setReadOnly(True)
        self.partData = QTextEdit()
        self.partData.setReadOnly(True)
        self.partData.setPlainText("Manufacturer Part Numbers:\n")
        self.settingsButton = QPushButton("Open Camera Settings")
        self.settingsButton.clicked.connect(self.open_camera_settings)

        # Exit button
        self.exitButton = QPushButton("Exit")
        self.exitButton.clicked.connect(self.close)  # Connect to the close method

        self.showMaximized()
        self.showFullScreen()

        # Setting the layout
        layout = QGridLayout()
        layout.addWidget(self.rawCamera, 0, 0)
        layout.addWidget(self.boundingBoxCamera, 0, 1)
        layout.addWidget(self.infoBox, 1, 0)
        layout.addWidget(self.partData, 1, 1)
        layout.addWidget(self.settingsButton, 2, 0, 1, 1)
        layout.addWidget(self.exitButton, 2, 1, 1, 1)  # Add the exit button to the layout

        self.setLayout(layout)

        # Camera thread setup
        self.camera_thread = CameraThread()
        self.camera_thread.frame_captured.connect(self.process_frame)
        self.camera_thread.start()

        # Saving the codes
        self.detected_Codes = set()
        self.valid_codes = set()
        self.mpn = set()

    def extract_mpn(self, code_data):
        # Remove the curly braces and split the string into key-value pairs
        key_value_pairs = code_data.strip('{}').split(',')

        # Iterate through the pairs and return the value for 'pm' if found
        for pair in key_value_pairs:
            key, value = pair.split(':', 1)  # Split only on the first colon
            if key.strip() == 'pm':  # Check if the key is 'pm'
                return value.strip()  # Return the corresponding value

        return None  # Return None if 'pm' is not found

    def detect_codes(self, image):
        detections = decode(image)
        if detections:  # Checks if detections is not empty
            for code in detections:
                code_data = code.data.decode('utf-8')  # Decode the byte string to a normal string
                if code_data not in self.detected_Codes:
                    print(f'Type: {code.type}, Data: {code_data}')  # Print to console
                    self.detected_Codes.add(code_data)  # Add the string representation to the set
                    if code.type == 'QRCODE':
                        mpn = self.extract_mpn(code_data)
                        self.mpn.add(mpn)
                        self.partData.append(f"MPN: {mpn}\n")
            return detections
        return []

    def process_frame(self, frame):
        # Convert frame to RGB
        captured_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        # ---- Display raw feed ----
        raw_feed = cv2.resize(captured_frame, self.display_size)
        cv2.putText(raw_feed, "Raw Feed", (10, 10), cv2.FONT_HERSHEY_PLAIN, 1, (255, 0, 0), 1)
        self.set_raw_feed(raw_feed)

        # ---- Detections (QR/barcodes) ----
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

        # ---- Display detection feed with boxes ----
        self.set_bounding_box_feed(detection_feed)
        self.update_info(detections)

    def set_bounding_box_feed(self, frame):
        try:
            h, w, ch = frame.shape
            bytes_per_line = ch * w
            qt_image = QImage(frame.data, w, h, bytes_per_line, QImage.Format_RGB888)
            self.boundingBoxCamera.setPixmap(QPixmap.fromImage(qt_image))
        except Exception as e:
            print(f"Error in set_bounding_box_feed: {e}")

    def set_raw_feed(self, frame):
        try:
            h, w, ch = frame.shape
            bytes_per_line = ch * w
            qt_image = QImage(frame.data, w, h, bytes_per_line, QImage.Format_RGB888)
            self.rawCamera.setPixmap(QPixmap.fromImage(qt_image))
        except Exception as e:
            print(f"Error in set_raw_feed: {e}")

    def closeEvent(self, event):
        self.camera_thread.release()  # Release the camera thread
        self.camera_thread.wait()      # Wait for the thread to finish
        event.accept()

    def update_info(self, decoded_objects):
        try:
            for obj in decoded_objects:
                code_data = obj.data.decode('utf-8')
                if code_data not in self.detected_Codes:
                    self.detected_Codes.add(code_data)
                    self.infoBox.append(f'Type: {obj.type}, Data: {code_data}\n')  # Append to infoBox
        except Exception as e:
            print(f"Error in update_info: {e}")

    def open_camera_settings(self):
        # Open camera settings
        self.camera_thread.cap.set(cv2.CAP_PROP_SETTINGS, 1)