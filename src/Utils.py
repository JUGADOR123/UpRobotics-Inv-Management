
from PyQt5.QtGui import QImage, QPixmap

def set_feed(frame, label):
    try:
        h, w, ch = frame.shape
        bytes_per_line = ch * w
        qt_image = QImage(frame.data, w, h, bytes_per_line, QImage.Format_RGB888)
        label.setPixmap(QPixmap.fromImage(qt_image))
    except Exception as e:
        print(f"Error in set_feed: {e}")

def extract_part_data(code_data):
    # Remove the curly braces and split the string into key-value pairs
    key_value_pairs = code_data.strip('{}').split(',')
    part_data = {}
    # Iterate through the pairs and extract values for 'pm' and 'qty'
    for pair in key_value_pairs:
        key, value = pair.split(':', 1)  # Split only on the first colon
        part_data[key.strip()] = value.strip()  # Add to part_data dictionary
    return part_data  # Return the dictionary containing part data
