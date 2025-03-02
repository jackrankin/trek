import os
import json
import uuid
import requests
from flask import Flask, jsonify, request
from flask_cors import CORS, cross_origin
from stat_track import GPXAnalyzer

app = Flask(__name__)
CORS(app)

# Set your Pinata API credentials here
PINATA_API_KEY = '845041f604a7899f6c26'
PINATA_SECRET_KEY = 'ab5fbe3e36f6ac6a92a42058656c3f7bda9f651ef148ab3650f59b8a8215c848'
PINATA_URL = 'https://api.pinata.cloud'

def upload_to_pinata(info):
    try:
        json_data = json.dumps(info)

        url = f"{PINATA_URL}/pinning/pinFileToIPFS"
        
        headers = {
            'pinata_api_key': PINATA_API_KEY,
            'pinata_secret_api_key': PINATA_SECRET_KEY
        }
        
        files = {
            'file': ('trekstarwebapp.json', json_data, 'application/json')
        }

        response = requests.post(url, headers=headers, files=files)

        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"Error uploading to Pinata: {response.text}")
    
    except Exception as e:
        raise Exception(f"Error uploading to Pinata: {str(e)}")



# Replace the GPX parsing function (optional)
def parse_gpx(file_path, username):
    try:
        import xml.etree.ElementTree as ET
        tree = ET.parse(file_path)
        root = tree.getroot()
        namespace = {'gpx': 'http://www.topografix.com/GPX/1/1'}


        dist = 0
        pace = 0
        try:
            tracker = GPXAnalyzer(file_path)
            dist = tracker.calculate_total_distance()
            pace = tracker.calculate_average_pace()
        except Exception as e:
            print(e)

        track_points = root.findall('.//gpx:trkpt', namespace)
        coordinates = []
        for point in track_points:
            lat = float(point.attrib['lat'])
            lon = float(point.attrib['lon'])
            coordinates.append([lat, lon])


        info = {
            "name" : username,
            "distance" : dist,
            "pace": pace,
            "coordinates" : coordinates,
        }

        return info 

    except Exception as e:
        return []

@app.route('/upload_gpx', methods=['POST'])
def upload_gps():
    try:
        username = request.form.get("username")
        if not username:
            return jsonify({"error": "Username is required"}), 400

        file = request.files.get("file")
        if not file:
            return jsonify({"error": "No file uploaded"}), 400

        info = parse_gpx(file, username)

        ipfs_hash = upload_to_pinata(info)

        js = jsonify(info)

        return js, 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/get_constellations', methods=['GET'])
def get_constellations():
    try:
        # Define the filename filter to get all files named "trekstarwebapp"
        filename_filter = 'trekstarwebapp.json'

        # Pinata API endpoint to list pinned files
        url = f"{PINATA_URL}/data/pinList?status=pinned&nameContains={filename_filter}"

        headers = {
            'pinata_api_key': PINATA_API_KEY,
            'pinata_secret_api_key': PINATA_SECRET_KEY
        }

        # Make the request to get pinned files from Pinata
        response = requests.get(url, headers=headers)

        if response.status_code == 200:
            pinned_files = response.json()['rows']
         
            all_constellations = []
            for file in pinned_files:
                ipfs_hash = file['ipfs_pin_hash']
                # Construct the IPFS gateway URL for each file
                ipfs_url = f"https://gateway.pinata.cloud/ipfs/{ipfs_hash}"
                file_response = requests.get(ipfs_url)

                if file_response.status_code == 200:
                    # Assuming the file contains JSON data
                    constellation_data = file_response.json()
                    all_constellations.append(constellation_data)

            return jsonify({
                "message": "Successfully retrieved constellation data",
                "count": len(all_constellations),
                "constellations": all_constellations
            }), 200
        else:
            raise Exception(f"Error retrieving constellations: {response.text}")

    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    app.run(debug=True)
