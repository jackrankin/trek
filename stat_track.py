import xml.etree.ElementTree as ET
import os
from datetime import datetime
from math import radians, sin, cos, sqrt, atan2

class StatTrack:
  def __init__(self, file):
    tree = ET.parse(file)  
    self.contents = tree.getroot()  
    self.namespace = {"ns": self.contents.tag.split("}")[0].strip("{")}  
    self.data = self.extract()
    self.dist = 0 #meters
    self.speed = 0 #meters per seconds
    self.time = 0 #seconds
    self.calcDist()
    self.getSpeed()

  """
  extracts gpx file stores in data list
  """
  def extract(self):
    data = []
    trkpts = self.contents.findall(".//ns:trkpt", self.namespace)

    if not trkpts:
      return []

    times = []
    for trkpt in trkpts:
      lat = float(trkpt.get('lat'))
      lon = float(trkpt.get('lon'))
      time_elem = trkpt.find('ns:time', self.namespace)

      if time_elem is None or not time_elem.text:
        continue

      time_obj = datetime.strptime(time_elem.text, "%Y-%m-%dT%H:%M:%SZ")
      times.append(time_obj)
      data.append((lat, lon, time_obj))
    if len(data) < 1:
      return []

    # Compute incremental time (seconds since first point)
    start_time = times[0]
    return [(lat, lon, (time_obj - start_time).total_seconds()) for lat, lon, time_obj in data]
  
  """
  Calculates distance in meters
  """
  def calcDist(self):
    if len(self.data) <= 1:
      return
    self.dist = sum(
        self.haversine(self.data[i][0], self.data[i][1], self.data[i+1][0], self.data[i+1][1])
        for i in range(len(self.data) - 1)
    )
  
  """
  Getter for distance in meters
  """
  def getDist(self):
    return self.dist
  
  """
  Getter for speed in meters per second
  """
  def getSpeed(self):
    if len(self.data) == 0:
      return 0
    self.time = self.data[-1][2] - self.data[0][2]
    if self.time == 0:
      return 0
    return self.dist/self.time
  
  """
  Getter for distance in miles
  """
  def getMileDist(self):
    return self.dist / 1609.34
  
  """
  Getter for speed in minutes/mile
  """
  def getMinMile(self):
    min = self.time / 60
    if self.getMileDist() == 0:
      return 0
    return min /self.getMileDist()
  
  """
  Calculates distance between two points
  """
  def haversine(self, lat1, lon1, lat2, lon2):
    R = 6371000  
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])

    dlat = lat2 - lat1
    dlon = lon2 - lon1

    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))

    return R * c

# # Run parsing
# path = "lukebs/Lunch_jog.gpx"
# tracker = StatTrack(path)
# points = tracker.extract()

# print("Meters :: ", tracker.getDist())
# print("AVG meters per second ::", tracker.getSpeed())
# print("Miles :: ", tracker.getMileDist())
# print("Min/Mile :: ", tracker.getMinMile())
