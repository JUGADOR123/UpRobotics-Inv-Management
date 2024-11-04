import sys
from PyQt5.QtWidgets import QApplication
from src.QrReader import QrReader as App

if __name__ == "__main__":
    print("Starting Up...")
    app = QApplication(sys.argv)
    print("Application Started")
    window = App()
    print("Window Created")
    window.show()
    sys.exit(app.exec())