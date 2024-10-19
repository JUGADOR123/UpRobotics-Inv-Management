import sys
import cv2
from PyQt5.QtWidgets import QLabel,  QWidget, QTextEdit, QGridLayout
from PyQt5.QtCore import QTimer
from PyQt5.QtGui import QImage, QPixmap
from pyzbar.pyzbar import decode
import numpy as np


def detect_codes(image):
    detections = decode(image)
    if len(detections)>0:
        for code in detections:
            print(f'Type: {code.type} , Data: {code.data}')
        return detections
    return []


class QrReader(QWidget):
    def __init__(self):
        super().__init__()
        #layout
        self.setWindowTitle("Inventory Management")
        self.rawCamera = QLabel()
        self.boundingBoxCamera = QLabel()
        self.infoBox = QTextEdit()
        self.infoBox.setReadOnly(True)
        self.partData = QTextEdit()
        self.partData.setReadOnly(True)
        self.partData.setPlainText("MPN: aaaaa \nName: bbbbb \nType: cccc")

        layout = QGridLayout()
        layout.addWidget(self.rawCamera, 0, 0)
        layout.addWidget(self.boundingBoxCamera, 0, 1)
        layout.addWidget(self.infoBox, 1, 0)
        layout.addWidget(self.partData, 1, 1)
        self.setLayout(layout)

        self.cap = cv2.VideoCapture(0)
        if not self.cap.isOpened():
            print("Error: Could not open camera.")
            sys.exit()

        # Timer to update frame
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_frame)
        self.timer.start(10)  # Trigger every 10ms
        self.detected_Codes = set()

    def update_frame(self):
        ret, frame = self.cap.read()
        if ret:
            # Convert frame to RGB
            captured_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

            # ---- Display raw feed ----
            raw_feed = captured_frame.copy()
            cv2.putText(raw_feed, "Raw Feed", (10, 10), cv2.FONT_HERSHEY_PLAIN, 1, (255, 0, 0), 1)
            self.set_raw_feed(raw_feed)

            # ---- Detections (QR/barcodes) ----
            detection_feed = captured_frame.copy()
            detections = detect_codes(detection_feed)
            cv2.putText(detection_feed, f'Detections: {len(detections)}', (10, 10), cv2.FONT_HERSHEY_PLAIN, 1,
                        (255, 0, 0), 1)
            for qr_code in detections:
                points = qr_code.polygon
                if len(points) > 4:
                    hull = cv2.convexHull(np.array([point for point in points], dtype=np.float32))
                    hull = list(map(tuple, np.squeeze(hull)))
                else:
                    hull = points
                n = len(hull)
                for j in range(0, n):
                    pt1 = tuple(map(int, hull[j]))  # Convert to tuple of integers
                    pt2 = tuple(map(int, hull[(j + 1) % n]))  # Next point, also converted
                    cv2.line(detection_feed, pt1, pt2, (0, 255, 60, 2),5)  # Draw detection boxes on the captured image

            # ---- Display detection feed with boxes ----
            self.set_bounding_box_feed(detection_feed)
            # Update the info text with detection data
            self.update_info(detections)

        #frame.release()
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
        self.cap.release()
        event.accept()

    def update_info(self, decoded_objects):
        data = ''
        try:
            for obj in decoded_objects:
                code_data = obj.data.decode('utf-8')
                # Only add new codes to the set
                if code_data not in self.detected_Codes:
                    self.detected_Codes.add(code_data)
                    self.infoBox.append(f'Type: {obj.type} , Data: {code_data}\n')
        except Exception as e:
            print(f"Error in update_info: {e}")
