import sys
from time import sleep

from PyQt5.QtWidgets import QApplication

from src.QrReader import QrReader as App, QrReader

if __name__ == "__main__":
    print("Starting Up...")
    sleep(5)
    app = QApplication(sys.argv)
    window = QrReader()
    window.show()
    sys.exit(app.exec_())

