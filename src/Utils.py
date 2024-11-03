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
    # Remove the curly braces and split the string into key-value pairs
    key_value_pairs = code_data.strip('{}').split(',')
    part_data = {}
    # Iterate through the pairs and extract values for 'pm' and 'qty'
    for pair in key_value_pairs:
        key, value = pair.split(':', 1)  # Split only on the first colon
        part_data[key.strip()] = value.strip()  # Add to part_data dictionary
    print(part_data)
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
            return None

        # Ensure there is at least one result
        if data["SearchResults"]["NumberOfResult"] > 0:
            mouserPart = {
                'PartNumber': mpn,
                'Quantity': qty,
                'Description': data["SearchResults"]["Parts"][0]["Description"],
                'Datasheet' : data["SearchResults"]["Parts"][0]["DataSheetUrl"],
                'ImagePath' : data["SearchResults"]["Parts"][0]["ImagePath"]
            }
            print(mouserPart)
            return mouserPart
        else:
            print("No results found for the provided MPN.")
            return None
    except requests.exceptions.RequestException as e:
        print(f"HTTP request failed: {e}")
        return None
