import os
import requests
from dotenv import load_dotenv
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
    # Decode bytes to string if necessary
    if isinstance(code_data, bytes):
        code_data = code_data.decode('utf-8')

    # Remove the curly braces and split the string into key-value pairs
    print(code_data)
    key_value_pairs = code_data.strip('{}').split(',')
    part_data = {}

    # Iterate through the pairs and extract values for 'pm' and 'qty'
    for pair in key_value_pairs:
        # Split only if there is a key and a value
        if ':' in pair:
            key, value = pair.split(':', 1)
            part_data[key.strip()] = value.strip()
        else:
            print(f"Warning: Skipping malformed pair '{pair}'")

    return part_data  # Return the dictionary containing part data


def build_part_data(mpn, qty):
    load_dotenv()
    #get name, datasheet info ,etc
    #the dict would look something like: {'mp':'xxxx','qty':xxx,'name':"xxx",'description': "xxxx" 'type':"xxxx", 'datasheet':"xxxx"}
    api_key = os.getenv("MOUSER_API_KEY")  # Fetch the API key from environment variables
    url = f"https://api.mouser.com/api/v1/search/partnumber?apiKey={api_key}"
    headers = {
        "Content-Type": "application/json"
    }
    request_body = {
        "SearchByPartRequest": {
            "mouserPartNumber": mpn  # Use the provided mpn variable
        }
    }
    try:
        response = requests.post(url, json=request_body, headers=headers)
        response.raise_for_status()  # Raise an error for bad responses
        data = response.json()

        # Check for errors in the response
        if data["Errors"]:
            print(f"Errors in response: {data['Errors']}")
            return False, None

        # Ensure there is at least one result
        if data["SearchResults"]["NumberOfResult"] > 0:
            mouserPart = {
                'PartNumber': mpn,
                'Quantity': qty,
                'Description': data["SearchResults"]["Parts"][0]["Description"],
                'DataSheet' : data["SearchResults"]["Parts"][0]["DataSheetUrl"],
                'ImagePath' : data["SearchResults"]["Parts"][0]["ImagePath"]
            }
            #print(mouserPart)
            return True, mouserPart
        else:
            print("No results found for the provided MPN.")
            genericPart = {
                'PartNumber': mpn,
                'Quantity': qty,
                'Description': None,
                'DataSheet': None,
                'ImagePath': None
            }
            return False, genericPart
    except requests.exceptions.RequestException as e:
        print(f"HTTP request failed: {e}")
        return None
