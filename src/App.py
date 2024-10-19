import sys
import cv2
from PyQt5.QtWidgets import QApplication, QLabel, QVBoxLayout, QWidget, QTextEdit, QGridLayout
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

            # ---- Grayscale conversion ----
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

            # ---- Light Gaussian Blur (reduce noise without affecting barcodes too much) ----
            blurred = cv2.GaussianBlur(gray, (3, 3), 0)  # Smaller kernel to avoid over-blurring barcodes

            # ---- Adaptive thresholding (post-processed image) ----
            adaptive_thresh = cv2.adaptiveThreshold(
                blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 11, 2
            )

            # ---- Edge detection (to preserve sharp details like barcodes) ----
            edges = cv2.Canny(adaptive_thresh, 50, 150)  # Adjust thresholds to fine-tune

            # ---- Light morphological operations to reduce small noise ----
            kernel = np.ones((2, 2), np.uint8)  # Smaller kernel to minimize merging barcode lines
            morph = cv2.morphologyEx(edges, cv2.MORPH_CLOSE, kernel)

            # ---- Convert single-channel (grayscale) morph image back to 3-channel (for visualization) ----
            contour_frame = cv2.cvtColor(morph, cv2.COLOR_GRAY2BGR)

            # ---- Detections (QR/barcodes) ----
            detections = detect_codes(captured_frame)
            cv2.putText(contour_frame, f'Detections: {len(detections)}', (10, 10), cv2.FONT_HERSHEY_PLAIN, 1,
                        (50, 150, 0), 1)

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
                    cv2.line(contour_frame, pt1, pt2, (255, 0, 0),
                             1)  # Draw detection boxes on the post-processed image

            # ---- Display post-processed feed with detection boxes ----
            self.set_bounding_box_feed(contour_frame)

            # ---- Also update raw feed ----
            raw_feed = captured_frame.copy()
            cv2.putText(raw_feed, "Raw Feed", (10, 10), cv2.FONT_HERSHEY_PLAIN, 1, (255, 0, 0), 1)
            self.set_raw_feed(raw_feed)

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
