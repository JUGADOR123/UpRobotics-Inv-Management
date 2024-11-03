import cv2
import numpy as np
from PyQt5.QtCore import QThread, pyqtSignal

properties = {
    "CAP_PROP_FRAME_WIDTH": cv2.CAP_PROP_FRAME_WIDTH,
    "CAP_PROP_FRAME_HEIGHT": cv2.CAP_PROP_FRAME_HEIGHT,
    "CAP_PROP_FPS": cv2.CAP_PROP_FPS,
    "CAP_PROP_BRIGHTNESS": cv2.CAP_PROP_BRIGHTNESS,
    "CAP_PROP_CONTRAST": cv2.CAP_PROP_CONTRAST,
    "CAP_PROP_SATURATION": cv2.CAP_PROP_SATURATION,
    "CAP_PROP_HUE": cv2.CAP_PROP_HUE,
    "CAP_PROP_GAIN": cv2.CAP_PROP_GAIN,
    "CAP_PROP_EXPOSURE": cv2.CAP_PROP_EXPOSURE,
    "CAP_PROP_AUTOFOCUS": cv2.CAP_PROP_AUTOFOCUS,
    "CAP_PROP_FOCUS": cv2.CAP_PROP_FOCUS,
}

class CameraThread(QThread):
    frame_captured = pyqtSignal(np.ndarray)

    def run(self):
        self.cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 4096)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 2160)
        self.cap.set(cv2.CAP_PROP_AUTOFOCUS, 1)

        for prop, prop_id in properties.items():
            print(f"{prop}: {self.cap.get(prop_id)}")

        while True:
            ret, frame = self.cap.read()
            if ret:
                self.frame_captured.emit(frame)

    def release(self):
        self.cap.release()