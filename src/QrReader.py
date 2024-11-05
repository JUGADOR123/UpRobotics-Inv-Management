import os
import tempfile
import csv
import cv2
import numpy as np
import time
from PyQt5.QtCore import QSize, Qt, pyqtSlot, QUrl, QByteArray, QStandardPaths
from PyQt5.QtWebEngine import QtWebEngine
from PyQt5.QtWebEngineWidgets import QWebEngineView, QWebEngineSettings
from PyQt5.QtWidgets import QLabel, QMainWindow, QTextEdit, QGridLayout, QPushButton, QWidget, QSizePolicy
from PyQt5.QtGui import QPixmap, QImage
from pyzbar.pyzbar import decode
from src.CameraThread import CameraThread
from src.ImageLoader import AsyncImageLoader
from src.PdfLoaderThread import PdfLoaderThread
from src.Utils import set_feed, extract_part_data, build_part_data



class QrReader(QMainWindow):
    def __init__(self):
        super().__init__()
        try:
            # Block 1: Initialize Detection and Data Structures
            print("Initializing detection and data structures...")
            self.detected_Codes = set()
            self.part_data_list = []
            self.found_codes = 0
            self.not_found_codes = 0
            self.last_detections = None
            self.code_timestamps = dict()
            self.load_or_create_files()
            print("Detection and data structures initialized.")

            # Block 2: Initialize Image Loader and Set Display Size
            print("Setting up image loader and display size...")
            self.pdf_loader_thread = None
            self.image_loader = AsyncImageLoader()
            self.image_loader.image_loaded.connect(self.display_image)
            self.setMaximumSize(QSize(1920, 1080))
            self.resize(1920, 1080)
            self.display_size = (640, 360)
            print("Image loader and display size set.")

            # Block 3: Set Window Properties
            print("Setting up window properties...")
            self.setWindowTitle("Inventory Management")
            self.rawCamera = QLabel()
            self.boundingBoxCamera = QLabel()
            self.infoBox = QTextEdit()
            self.infoBox.setReadOnly(True)
            self.imageLabel = QLabel()
            print("Window properties set.")

            # Block 4: Configure PDF Viewer
            print("Configuring PDF viewer...")
            self.pdfViewer = QWebEngineView()
            self.pdfViewer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
            self.pdf_loader_thread = None
            self.pdfSettings = self.pdfViewer.settings()
            self.pdfSettings.setAttribute(QWebEngineSettings.PluginsEnabled, True)
            self.pdfViewer.setMinimumSize(600, 400)
            self.pdfViewer.setAttribute(Qt.WA_OpaquePaintEvent)
            self.pdfViewer.setStyleSheet("background-color: white;")
            print("PDF viewer configured.")

            # Block 5: Initialize Labels for Scanned Code Counts
            print("Initializing labels for scanned code counts...")
            self.scannedCodesLabel = QLabel("Scanned Codes:")
            self.mouserHitsLabel = QLabel("Found on Mouser:")
            self.notFoundLabel = QLabel("Not found on Mouser:")
            self.scannedCodesCounterLabel = QLabel("0")
            self.foundCodesCounterLabel = QLabel("0")
            self.notFoundCodesCounterLabel = QLabel("0")
            print("Labels initialized.")

            # Block 6: Set up Buttons
            print("Setting up buttons...")
            self.settingsButton = QPushButton("Open Camera Settings")
            self.settingsButton.clicked.connect(self.open_camera_settings)
            self.exportButton = QPushButton("Export CSV")
            self.exitButton = QPushButton("Exit")
            self.exitButton.clicked.connect(self.close)
            print("Buttons set up.")

            # Block 7: Arrange Layout
            print("Arranging layout...")
            layout = QGridLayout()
            layout.addWidget(self.rawCamera, 0, 0, 2, 2)
            layout.addWidget(self.boundingBoxCamera, 0, 2, 2, 2)
            layout.addWidget(self.pdfViewer, 0, 4, 6, 2)
            layout.addWidget(self.imageLabel, 2, 0, 1, 2)
            layout.addWidget(self.infoBox, 2, 2, 4, 2)
            layout.addWidget(self.scannedCodesLabel, 3, 0)
            layout.addWidget(self.scannedCodesCounterLabel, 3, 1)
            layout.addWidget(self.mouserHitsLabel, 4, 0)
            layout.addWidget(self.foundCodesCounterLabel, 4, 1)
            layout.addWidget(self.notFoundLabel, 5, 0)
            layout.addWidget(self.notFoundCodesCounterLabel, 5, 1)
            layout.addWidget(self.settingsButton, 6, 0, 1, 2)
            layout.addWidget(self.exportButton, 6, 2, 1, 2)
            layout.addWidget(self.exitButton, 6, 4, 1, 2)
            layout.setContentsMargins(10, 10, 10, 10)
            layout.setSpacing(10)
            central_widget = QWidget()
            central_widget.setLayout(layout)
            self.setCentralWidget(central_widget)
            print("Layout arranged.")

            # Block 8: Initialize Camera Thread
            print("Initializing camera thread...")
            self.camera_thread = CameraThread()
            self.camera_thread.frame_captured.connect(self.process_frame)
            self.camera_thread.start()
            print("Camera thread initialized and started.")

            # Block 9: Finalize Setup and Display Window
            print("Finalizing setup and displaying window...")
            self.update_counters()
            self.showFullScreen()
            print("Initialization complete. Window displayed.")

        except Exception as e:
            print(f"Error during initialization: {e}")

    def update_counters(self):
        self.scannedCodesCounterLabel.setText(f"{(len(self.detected_Codes))}")
        self.foundCodesCounterLabel.setText(f"{self.found_codes}")
        self.notFoundCodesCounterLabel.setText(f"{self.not_found_codes}")
    def load_or_create_files(self):
        # Check or create uniquecodes.csv
        if not os.path.exists("uniquecodes.csv"):
            with open("uniquecodes.csv", mode="w", newline='') as file:
                writer = csv.writer(file)
                writer.writerow(["Code"])  # Add a header row

        else:
            with open("uniquecodes.csv", mode="r") as file:
                reader = csv.reader(file)
                next(reader, None)  # Skip header
                for row in reader:
                    if row:  # Avoid empty rows
                        self.detected_Codes.add(row[0])

        # Check or create components.csv
        if not os.path.exists("components.csv"):
            with open("components.csv", mode="w", newline='') as file:
                writer = csv.DictWriter(file, fieldnames=["PartNumber", "Quantity", "ImagePath", "DataSheet"])
                writer.writeheader()

        else:
            with open("components.csv", mode="r") as file:
                reader = csv.DictReader(file)
                for row in reader:
                    if row:  # Avoid empty rows
                        self.part_data_list.append(row)
    def load_pdf_from_url(self, pdf_url):
        """Load PDF from URL and display it using QWebEngineView"""
        print(f"Starting PDF load for URL: {pdf_url}")

        # Check if the PDF URL is None or empty
        if not pdf_url:
            # Use a blank webpage if no PDF URL is provided
            pdf_url = "data:text/html,<html><body></body></html>"

        if self.pdf_loader_thread:
            self.pdf_loader_thread.terminate()
        self.pdf_loader_thread = PdfLoaderThread(pdf_url)
        self.pdf_loader_thread.pdf_loaded.connect(self.display_pdf)
        self.pdf_loader_thread.start()

    @pyqtSlot(QByteArray)
    def display_pdf(self, pdf_data):
        """Handle displaying PDF after it's downloaded"""
        # Get the temporary directory in a Windows-friendly way
        temp_dir = tempfile.gettempdir()  # Standard temp directory for Windows
        temp_file_path = os.path.join(temp_dir, "temp.pdf")  # Save PDF as temp.pdf

        print(f"Saving PDF to: {temp_file_path}")

        try:
            with open(temp_file_path, "wb") as pdf_file:
                pdf_file.write(pdf_data)
            print("PDF saved successfully.")

            # Set the URL and force the viewer to update
            pdf_url = QUrl.fromLocalFile(temp_file_path)
            self.pdfViewer.setUrl(pdf_url)
            self.pdfViewer.load(pdf_url)
            self.pdfViewer.update()
            self.pdfViewer.repaint()
            print("PDF loaded into viewer successfully.")
        except Exception as e:
            print(f"Error displaying PDF: {e}")

    def load_image_from_url(self, url):
        self.image_loader.load_image(url)  # Call the load_image method
    @pyqtSlot(QImage)
    def display_image(self, q_image):
        if not q_image.isNull():
            pixmap = QPixmap.fromImage(q_image)
            scaled_pixmap = pixmap.scaled(self.imageLabel.size(),
                                          aspectRatioMode=Qt.AspectRatioMode.KeepAspectRatio,
                                          transformMode=Qt.TransformationMode.SmoothTransformation)
            self.imageLabel.setPixmap(scaled_pixmap)
            self.imageLabel.setFixedSize(scaled_pixmap.size())
        else:
            print("Received an invalid QImage for display.")
            self.imageLabel.clear()
    # Helper function to handle data retrieval
    def fetch_local_data(self, part_number):
        """Check if part exists locally and return it if found."""
        print(f"Searching for {part_number} in database")
        local_data = next((item for item in self.part_data_list if item['PartNumber'] == part_number), None)

        if local_data:
            print("Part exists in database, using locally available data:", local_data)
            return True, local_data  # Return dictionary directly

        print("Part not found in database, returning None")
        return False, None

    def fetch_data_from_api(self, part_number, qty):
        """Fetch part data from API if not found locally, and add it to the database if available."""
        state, part_data = build_part_data(part_number, qty)
        if state:
            print("Found part in Mouser... Adding to database")
            self.part_data_list.append(part_data)
            self.found_codes += 1
            return True, part_data
        else:
            print("Not found in Mouser, storing basic part number and quantity")
            self.not_found_codes += 1
            return False, part_data

    def detect_codes(self, image):
        try:
            detections = decode(image)
            current_time = time.time()
            timeout_duration = 20  # Set timeout in seconds

            if detections:
                for code in detections:
                    code_data = code.data.decode('utf-8')

                    # Check if the code was recently scanned
                    if code_data in self.code_timestamps:
                        time_since_last_scan = current_time - self.code_timestamps[code_data]
                        if time_since_last_scan < timeout_duration:
                            # Skip if detected within the timeout
                            continue


                    # Update the timestamp for this code
                    self.code_timestamps[code_data] = current_time

                    if code_data in self.detected_Codes:
                        print("Scanned code already in database")
                        if code.type == "QRCODE":
                            extracted_part_data = extract_part_data(code.data)

                            if extracted_part_data:
                                part_number = extracted_part_data.get('pm')
                                qty = extracted_part_data.get('qty')

                                # Fetch data locally since the code was previously detected
                                state, fetched_data = self.fetch_local_data(part_number)

                                if state and isinstance(fetched_data, dict):
                                    display_text = '\n'.join([f"{key}: {value}" for key, value in fetched_data.items()])
                                    self.foundCodesCounterLabel.setText(f'{self.found_codes}')
                                    self.infoBox.setText(display_text)
                                    self.load_image_from_url(fetched_data.get('ImagePath'))
                                    self.load_pdf_from_url(fetched_data.get("DataSheet"))
                                else:
                                    print("Local data not found, this shouldn't happen.")
                                    self.infoBox.setText("Data unavailable.")
                        self.update_counters()

                    else:
                        # New code detected
                        print("New Code Detected...")
                        self.detected_Codes.add(code_data)
                        self.scannedCodesCounterLabel.setText(f'{len(self.detected_Codes)}')

                        # Add new code to uniquecodes.csv
                        with open("uniquecodes.csv", mode="a", newline='') as file:
                            writer = csv.writer(file)
                            writer.writerow([code_data])

                        # Handle QR Code logic for new data
                        if code.type == 'QRCODE':
                            extracted_part_data = extract_part_data(code.data)
                            if extracted_part_data:
                                part_number = extracted_part_data.get('pm')
                                qty = extracted_part_data.get('qty')

                                # Try fetching from API if it's a new part
                                state, fetched_data = self.fetch_data_from_api(part_number, qty)

                                # Add fetched data to components.csv if available
                                with open("components.csv", mode="a", newline='') as file:
                                    writer = csv.DictWriter(file, fieldnames=fetched_data.keys())
                                    writer.writerow(fetched_data)
                                if state:
                                    # Display the fetched data
                                    display_text = '\n'.join(
                                        [f"{key}: {value}" for key, value in fetched_data.items()])
                                    self.found_codes +=1
                                    self.infoBox.setText(display_text)
                                    self.load_image_from_url(fetched_data.get('ImagePath'))
                                    self.part_data_list.append(fetched_data)
                                    self.load_pdf_from_url(fetched_data.get("DataSheet"))

                                else:
                                    # Show "Not found" message if API didn't find the part
                                    self.infoBox.setText(
                                        f"Not found on Mouser\nPart Number: {fetched_data.get('PartNumber')}\nQuantity: {fetched_data.get('Quantity')}")
                                    self.not_found_codes +=1
                                    self.imageLabel.clear()
                                    self.part_data_list.append(fetched_data)
                                    self.load_pdf_from_url(fetched_data.get("DataSheet"))
                        self.update_counters()
            return detections

        except Exception as e:
            print(f"Error in detect_codes: {e}")
            return []

    def process_frame(self, frame):
        if self.isVisible():
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
