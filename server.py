import os
import json
import psycopg2
from flask import Flask, jsonify, request
from flask_cors import CORS
from math import radians, sin, cos, sqrt, atan2

app = Flask(__name__)
CORS(app)

DB_URL = os.getenv("DATABASE_URL")
conn = psycopg2.connect(DB_URL)
cursor = conn.cursor()

cursor.execute('''
    CREATE TABLE IF NOT EXISTS gpx_data (
        id SERIAL PRIMARY KEY,
        name TEXT NOT NULL,
        distance FLOAT NOT NULL,
        coordinates JSONB NOT NULL
    );
''')

conn.commit()

def parse_gpx(file, name):
    import xml.etree.ElementTree as ET
    tree = ET.parse(file)
    root = tree.getroot()
    namespace = {'gpx': 'http://www.topografix.com/GPX/1/1'}

    track_points = root.findall('.//gpx:trkpt', namespace)
    coordinates = []
    dist = 0

    def haversine(lat1, lon1, lat2, lon2):
        R = 6371
        lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
        c = 2 * atan2(sqrt(a), sqrt(1 - a))
        return R * c

    prev_lat, prev_lon = float(track_points[0].attrib['lat']), float(track_points[0].attrib['lon'])

    for i in range(1, len(track_points)):
        point = track_points[i]
        lat = float(point.attrib['lat'])
        lon = float(point.attrib['lon'])
        dist += haversine(prev_lat, prev_lon, lat, lon)
        prev_lat, prev_lon = lat, lon
        if i%10 == 0:
            coordinates.append([lat, lon])
        
    filtered_points = []
    removed = set()

    for i in range(len(coordinates)):
        if i in removed:
            continue

        for j in range(i + 1, len(coordinates)):
            if j not in removed and haversine(*coordinates[i], *coordinates[j]) < 0.1:
                removed.add(j)

        filtered_points.append(coordinates[i])

    dist = dist / 1.6

    return {
        "name": name,
        "distance": dist,
        "coordinates": filtered_points,
    }

@app.route('/upload_gpx', methods=['POST'])
def upload_gpx():
    try:
        name = request.form.get("name")
        if not name:
            return jsonify({"error": "'name' is required"}), 400
        
        file = request.files.get("file")
        if not file:
            return jsonify({"error": "No file uploaded"}), 400

        info = parse_gpx(file, name)

        cursor.execute(
            "INSERT INTO gpx_data (name, distance, coordinates) VALUES (%s, %s, %s) RETURNING id",
            (info["name"], info["distance"], json.dumps(info["coordinates"]))
        )
        conn.commit()

        return jsonify(info), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/get_constellations', methods=['GET'])
def get_constellations():
    try:
        cursor.execute("SELECT name, distance, coordinates FROM gpx_data")
        rows = cursor.fetchall()

        all_constellations = [
            {"name": row[0], "distance": row[1], "coordinates": row[2]} for row in rows
        ]

        return jsonify({
            "message": "Successfully retrieved constellation data",
            "count": len(all_constellations),
            "constellations": all_constellations
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
