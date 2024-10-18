import sys
from time import sleep

from PyQt5.QtWidgets import QApplication

from src.App import QrReader as App, QrReader

if __name__ == "__main__":
    print("Starting Up...")
    sleep(10)
    app = QApplication(sys.argv)
    window = QrReader()
    window.show()
    sys.exit(app.exec_())

