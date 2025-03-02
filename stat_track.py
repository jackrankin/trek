import gpxpy
import gpxpy.gpx
from geopy.distance import geodesic
class GPXAnalyzer:
    def __init__(self, gpx_file):
        # Check if gpx_file is a string (file path) or a file-like object
        if isinstance(gpx_file, str):
            # It's a file path
            with open(gpx_file, 'r') as f:
                self.gpx = gpxpy.parse(f)
        else:
            # It's already a file object
            # Make sure to reset the file pointer
            gpx_file.seek(0)
            self.gpx = gpxpy.parse(gpx_file)
    
    def calculate_total_distance(self):
        total_distance = 0.0
        for track in self.gpx.tracks:
            for segment in track.segments:
                for i in range(1, len(segment.points)):
                    prev_point = segment.points[i - 1]
                    curr_point = segment.points[i]
                    total_distance += geodesic(
                        (prev_point.latitude, prev_point.longitude),
                        (curr_point.latitude, curr_point.longitude)
                    ).meters
        return total_distance / 1000  # Convert to kilometers
    
    def calculate_average_pace(self):
        total_distance = self.calculate_total_distance()  # In km
        total_time = 0.0
        for track in self.gpx.tracks:
            for segment in track.segments:
                for i in range(1, len(segment.points)):
                    prev_point = segment.points[i - 1]
                    curr_point = segment.points[i]
                    time_diff = (curr_point.time - prev_point.time).total_seconds()
                    total_time += time_diff
        
        if total_distance > 0 and total_time > 0:
            pace_per_km = total_time / total_distance  # Seconds per km
            minutes = int(pace_per_km // 60)
            seconds = int(pace_per_km % 60)
            return f"{minutes}:{seconds:02d} min/km"
        return "N/A"

# Usage Example:
# gpx_analyzer = GPXAnalyzer('./user_data/melissa_medina/2025-02-02_Edmond Running_18171832296/activity.gpx')
# print("Total Distance:", gpx_analyzer.calculate_total_distance(), "km")
# print("Average Pace:", gpx_analyzer.calculate_average_pace(), "min/km")
