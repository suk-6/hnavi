import os
import re
import math
import xml.etree.ElementTree as ET
from datetime import datetime
import cv2
import base64
import requests

class parser:
    def __init__(self) -> None:
        pass

    def parse(self, path: str, detectionURL: str):
        basePath = path[:-4]

        try:
            os.system(f"gopro2gpx -s {path} {basePath}")
        except:
            raise Exception("Is not a GoPro video file")
        
        points = self.points(basePath)
        lineLength = self.lineLength(points)
        congestion = self.congestion(basePath, points, detectionURL)

        return points, lineLength, congestion

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
        for index, point in enumerate(points):
            if index % 10 == 0:
                frame = self.frame(point, basePath)
                detection = self.detectObjects(frame, detectionURL)

                if detection is not None:
                    raise Exception("Failed to detect objects")
                
                # TODO: Calculate congestion

    def detectObjects(self, frame, detectionURL):
        _, buffer = cv2.imencode(".jpg", frame)
        textImage = buffer.tobytes()
        base64Image = str(base64.b64encode(textImage), "utf-8")

        response = requests.post(detectionURL, data={"frame": base64Image})
        detection = response.json()

        return detection

    def frame(self, point, basePath):
        GPXPath = basePath + ".gpx"

        root = ET.parse(os.path.join(GPXPath)).getroot()

        metaTime_str = (
            root.find(".//{http://www.topografix.com/GPX/1/1}metadata")
            .find("{http://www.topografix.com/GPX/1/1}time")
            .text
        )
        metaTime = datetime.strptime(metaTime_str, "%Y-%m-%dT%H:%M:%S.%fZ")

        videoPath = basePath + ".mp4"

        # 영상 읽기
        cap = cv2.VideoCapture(videoPath)

        # trkseg 내의 모든 trkpt 태그 처리
        for trkpt in root.findall(".//{http://www.topografix.com/GPX/1/1}trkpt"):
            lat = float(trkpt.attrib["lat"])
            lon = float(trkpt.attrib["lon"])

            try:
                if lat == point["y"] and lon == point["x"]:
                    print(f"Found point: {lat}, {lon} - {point['y']}, {point['x']}")
                    trkptTime_str = trkpt.find("{http://www.topografix.com/GPX/1/1}time").text
                    trkptTime = datetime.strptime(trkptTime_str, "%Y-%m-%dT%H:%M:%S.%fZ")

                    timeDifference = trkptTime - metaTime
                    secondsDifference = timeDifference.total_seconds()

                    cap.set(cv2.CAP_PROP_POS_MSEC, secondsDifference * 1000)

                    ret, frame = cap.read()

                    if ret:
                        return frame
                    else:
                        raise Exception("Not a valid frame")
            except:
                raise Exception("Failed to read frame")

        # 영상 읽기 종료
        cap.release()