import os
import re
import math
import xml.etree.ElementTree as ET
from datetime import datetime
import cv2
import base64
import requests
from labels import labels, weightofObject
from tqdm import tqdm

class parser:
    def __init__(self):
        self.midpoint = {}

    def parse(self, basePath: str, detectionURL: str):
        try:
            os.system(f"gopro2gpx -s {f'{basePath}.mp4'} {basePath} > /dev/null")
        except:
            raise Exception("Is not a GoPro video file")
        
        points = self.points(basePath)
        lineLength = self.lineLength(points)
        congestion, allObjects, midImage = self.congestion(basePath, points, detectionURL)

        return points, lineLength, congestion, self.midpoint, allObjects, midImage

    def points(self, basePath: str):
        try:
            kmlPath = basePath + ".kml"

            with open(kmlPath, "r") as kmlFile:
                kmlData = kmlFile.read()

            coordinatesData = re.findall(
                r"<coordinates>(.*?)</coordinates>", kmlData, re.DOTALL
            )

            points = []

            for coordinates in coordinatesData:
                lines = coordinates.strip().split("\n")  # 각 줄을 분리
                for i, line in enumerate(lines):
                    longitude, latitude, _ = line.split(",")  # 세 번째 값은 무시
                    result = {"x": float(longitude), "y": float(latitude)}
                    points.append(result)

            self.midpoint = points[len(points) // 2]

            return points
        except:
            raise Exception("Failed to parse KML file")
        
    def haversine(self, lat1, lon1, lat2, lon2):
        radius = 6371.0

        lat1 = math.radians(lat1)
        lon1 = math.radians(lon1)
        lat2 = math.radians(lat2)
        lon2 = math.radians(lon2)

        dlon = lon2 - lon1
        dlat = lat2 - lat1

        a = (
            math.sin(dlat / 2) ** 2
            + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
        )
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        distance = radius * c

        return distance
    
    def lineLength(self, points):
        lineLength = 0

        for point in enumerate(points):
            if point[0] == len(points) - 1:
                break
            lineLength += self.haversine(
                point[1]["y"],
                point[1]["x"],
                points[point[0] + 1]["y"],
                points[point[0] + 1]["x"],
            )

        return lineLength

    def congestion(self, basePath, points, detectionURL):
        congestion = 0
        allObjects = {key: 0 for key in range(len(labels))}

        # Video Capture and GPX Parsing
        cap = cv2.VideoCapture(basePath + ".mp4")
        root = ET.parse(os.path.join(basePath + ".gpx")).getroot()

        metaTime = (
            root.find(".//{http://www.topografix.com/GPX/1/1}metadata")
            .find("{http://www.topografix.com/GPX/1/1}time")
            .text
        )

        metaTime = datetime.strptime(metaTime, "%Y-%m-%dT%H:%M:%S.%fZ")

        for index, point in enumerate(tqdm(points)):
            if index % 100 == 0:
                frame = self.frame(point, cap, root, metaTime)

                if frame is None:
                    continue

                detection = self.detectObjects(frame, detectionURL)

                if detection is not None:
                    pass
                
                objects = self.sumObjects(detection)
                allObjects = self.sumAllObjects(detection, allObjects)
                congestion += self.calcCongestion(objects)

            # Save Mid Point Frame with base64
            if index == len(points) // 2:
                _, buffer = cv2.imencode(".jpg", frame)
                textImage = buffer.tobytes()
                midImage = str(base64.b64encode(textImage), "utf-8")

        cap.release()
        return congestion, allObjects, midImage

    def calcCongestion(self, objects):
        congestion = 0

        for object in objects.keys():
            try:
                weight = weightofObject[labels[int(object)]]
            except:
                weight = 0.1

            congestion += objects[object] * weight

        # return round(((congestion**2) / 10e2), 1)
        return round(congestion, 5)

    def sumObjects(self, detection):
        objects = {key: 0 for key in range(len(labels))}

        for object in detection:
            objects[object["label"]] += 1

        return objects

    def sumAllObjects(self, detection, objects):
        for object in detection:
            objects[object["label"]] += 1

        return objects
    
    def detectObjects(self, frame, detectionURL):
        _, buffer = cv2.imencode(".jpg", frame)
        textImage = buffer.tobytes()
        base64Image = str(base64.b64encode(textImage), "utf-8")

        response = requests.post(detectionURL, data={"frame": base64Image})
        detection = response.json()

        return detection

    def frame(self, point, cap, root, metaTime):
        for trkpt in root.findall(".//{http://www.topografix.com/GPX/1/1}trkpt"):
            lat = float(trkpt.attrib["lat"])
            lon = float(trkpt.attrib["lon"])

            if lat == point["y"] and lon == point["x"]:
                trkptTime_str = trkpt.find("{http://www.topografix.com/GPX/1/1}time").text
                trkptTime = datetime.strptime(trkptTime_str, "%Y-%m-%dT%H:%M:%S.%fZ")

                timeDifference = trkptTime - metaTime
                secondsDifference = timeDifference.total_seconds()

                cap.set(cv2.CAP_PROP_POS_MSEC, secondsDifference * 1000)

                try:
                    ret, frame = cap.read()
                except:
                    raise Exception("Failed to read frame")

                if ret:
                    return frame
                else:
                    return None
                
        return None