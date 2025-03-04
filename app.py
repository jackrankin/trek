import os
import json
import requests
from flask import Flask, jsonify, request
from flask_cors import CORS, cross_origin
from math import radians, sin, cos, sqrt, atan2

app = Flask(__name__)
CORS(app)

PINATA_URL = 'https://api.pinata.cloud'
PINATA_API_KEY = os.getenv("PINATA_API_KEY")
PINATA_SECRET_KEY = os.getenv("PINATA_SECRET_KEY")

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



def parse_gpx(file_path, username):
    try:
        import xml.etree.ElementTree as ET
        tree = ET.parse(file_path)
        root = tree.getroot()
        namespace = {'gpx': 'http://www.topografix.com/GPX/1/1'}


        track_points = root.findall('.//gpx:trkpt', namespace)
        coordinates = []
        dist = 0 
        pace = 0

        def haversine(lat1, lon1, lat2, lon2):
            
            R = 6371
            lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
            
            dlat = lat2 - lat1
            dlon = lon2 - lon1
            
            a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
            c = 2 * atan2(sqrt(a), sqrt(1 - a))
            
            return R * c
        
        for point in track_points:
            lat = float(point.attrib['lat'])
            lon = float(point.attrib['lon'])
            coordinates.append([lat, lon])
        


        for i in range(1, len(coordinates)):
            dist += haversine(*coordinates[i - 1], *coordinates[i])
        
        dist = dist / 1.6

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

        js = jsonify(info)

        return js, 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/get_constellations', methods=['GET'])
def get_constellations():
    try:
        filename_filter = 'trekstarwebapp.json'

        url = f"{PINATA_URL}/data/pinList?status=pinned&nameContains={filename_filter}"

        headers = {
            'pinata_api_key': PINATA_API_KEY,
            'pinata_secret_api_key': PINATA_SECRET_KEY
        }

        response = requests.get(url, headers=headers)

        if response.status_code == 200:
            pinned_files = response.json()['rows']
         
            all_constellations = []
            for file in pinned_files:
                ipfs_hash = file['ipfs_pin_hash']
                ipfs_url = f"https://chocolate-occasional-woodpecker-122.mypinata.cloud/ipfs/{ipfs_hash}"
                file_response = requests.get(ipfs_url)

                if file_response.status_code == 200:
                    constellation_data = file_response.json()
                    if "coordinates" in constellation_data:
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
