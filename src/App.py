import sys
import cv2
from PyQt5.QtWidgets import QApplication, QLabel, QVBoxLayout, QWidget, QTextEdit, QGridLayout
from PyQt5.QtCore import QTimer
from PyQt5.QtGui import QImage, QPixmap
from pyzbar.pyzbar import decode
import numpy as np
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
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            self.set_raw_feed(rgb_frame)

    def set_raw_feed(self,frame):
        h,w,ch = frame.shape
        bytes_per_line = ch * w
        qt_image = QImage(frame.data,w,h,bytes_per_line,QImage.Format_RGB888)
        self.rawCamera.setPixmap(QPixmap.fromImage(qt_image))

