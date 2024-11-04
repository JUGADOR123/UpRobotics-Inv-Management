import cv2
import numpy as np
from PyQt5.QtCore import QThread, pyqtSignal

class CameraThread(QThread):
    frame_captured = pyqtSignal(np.ndarray)

    FRAME_WIDTH = 4096
    FRAME_HEIGHT = 2160

    def __init__(self):
        super().__init__()
        self.cap = None
        self.running = True

    def run(self):
        self.cap = cv2.VideoCapture(1, cv2.CAP_DSHOW)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.FRAME_WIDTH)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.FRAME_HEIGHT)
        self.cap.set(cv2.CAP_PROP_AUTOFOCUS, 1)
        self.cap.set(cv2.CAP_PROP_CONTRAST, 105)
        self.cap.set(cv2.CAP_PROP_SHARPNESS, 125)
        self.cap.set(cv2.CAP_PROP_BRIGHTNESS, 130)
        self.cap.set(cv2.CAP_PROP_SATURATION, 130)

        while self.running:  # Run while the flag is True
            ret, frame = self.cap.read()
            if ret:
                self.frame_captured.emit(frame)

    def release(self):
        self.running = False  # Stop the loop in run
        if self.cap is not None:
            self.cap.release()
