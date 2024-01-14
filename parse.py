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
from mapdb import db


class parser:
    def __init__(self) -> None:
        self.mapdb = db("seoul")
        self.positions = self.mapdb.getPositions()
        self.nearbyPositions = None
        self.nearbyPositionsRenew = True
        self.lastNearbyPosition = None

    def parse(self, basePath: str, detectionURL: str):
        try:
            os.system(f"gopro2gpx -s {f'{basePath}.mp4'} {basePath} > /dev/null")
        except:
            raise Exception("Is not a GoPro video file")

        points = self.points(basePath)
        roads = self.classificationByMapBase(points)
        for road in roads.keys():
            (
                roads[road]["congestion"],
                roads[road]["allObjects"],
                roads[road]["midImage"],
                roads[road]["imageIDs"],
            ) = self.congestion(
                basePath, roads[road]["points"], detectionURL, roads[road]["midPoint"]
            )

        return roads

    def findNearby(self, lat, lon):
        if self.nearbyPositions is not None:
            positions = self.nearbyPositions
        else:
            positions = self.positions

        minDist = self.haversine(
            lat, lon, float(positions[0][2]), float(positions[0][1])
        )
        minID = positions[0][0]

        for position in positions:
            dist = self.haversine(lat, lon, float(position[2]), float(position[1]))
            if dist < minDist:
                minDist = dist
                minID = position[0]

        self.lastNearbyPosition = minID
        return minID

    def saveNearbyPositions(self, lat, lon):
        if self.nearbyPositionsRenew:
            self.nearbyPositions = []
            for position in self.positions:
                dist = self.haversine(lat, lon, float(position[2]), float(position[1]))
                if dist < 1:
                    self.nearbyPositions.append(position)

            self.nearbyPositions.sort(
                key=lambda x: self.haversine(lat, lon, float(x[2]), float(x[1]))
            )

            tenPercent = int(len(self.nearbyPositions) / 10)
            self.longDistances = self.nearbyPositions[-tenPercent:]

            self.nearbyPositionsRenew = False

        if self.nearbyPositions is not None:
            if self.lastNearbyPosition in [
                position[0] for position in self.longDistances
            ]:
                self.nearbyPositionsRenew = True

    def classificationByMapBase(self, points):
        result = {}
        for point in tqdm(points[::2], desc="Calculating Road Segments"):
            rid = self.findNearby(point["y"], point["x"])
            self.saveNearbyPositions(point["y"], point["x"])
            rdata = self.mapdb.getDataOfID(rid)

            roadcd = rdata[10]
            if roadcd not in result.keys():
                result[roadcd] = {
                    "name": rdata[11],
                    "region": f"{rdata[6]} {rdata[7]} {rdata[9]}",
                    "congestion": -1,
                    "length": -1,
                    "midPoint": -1,
                    "points": [],
                }

            result[roadcd]["points"].append(point)

        for roadcd in result.keys():
            result[roadcd]["length"] = self.lineLength(result[roadcd]["points"])
            result[roadcd]["midPoint"] = self.calcMidPoint(result[roadcd]["points"])

        return result

    def calcMidPoint(self, points):
        return points[int(len(points) / 2)]

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

    def congestion(self, basePath, points, detectionURL, midPoint):
        congestion = 0
        allObjects = {key: 0 for key in range(len(labels))}
        imageIDs = []

        # Video Capture and GPX Parsing
        cap = cv2.VideoCapture(basePath + ".mp4")
        width = cap.get(cv2.CAP_PROP_FRAME_WIDTH)
        height = cap.get(cv2.CAP_PROP_FRAME_HEIGHT)

        root = ET.parse(os.path.join(basePath + ".gpx")).getroot()

        metaTime = (
            root.find(".//{http://www.topografix.com/GPX/1/1}metadata")
            .find("{http://www.topografix.com/GPX/1/1}time")
            .text
        )

        metaTime = datetime.strptime(metaTime, "%Y-%m-%dT%H:%M:%S.%fZ")

        for index, point in enumerate(tqdm(points)):
            if index % (int(len(points) / 15)) == 0:
                frame = self.frame(point, cap, root, metaTime)
                if frame is None:
                    continue

                try:
                    detection, imageID = self.detectObjects(frame, detectionURL)
                    imageIDs.append(imageID)
                except:
                    detection = []
                objects = self.sumObjects(detection)
                allObjects = self.sumAllObjects(detection, allObjects)
                congestion += self.calcCongestion(objects)

        # Save Mid Point Frame with base64
        frame = self.frame(midPoint, cap, root, metaTime)
        frame = cv2.resize(frame, (int(width / 5), int(height / 5)))
        midImage = self.frameToBase64(frame)

        cap.release()
        return congestion, allObjects, midImage, imageIDs

    def calcCongestion(self, objects):
        congestion = 0

        for object in objects.keys():
            try:
                weight = weightofObject[labels[int(object)]]
            except:
                weight = 0.1

            congestion += objects[object] * weight

        # return round(((congestion**2) / 10e2), 1)
        return congestion

    def sumObjects(self, detection):
        objects = {key: 0 for key in range(len(labels))}

        for object in detection:
            objects[object["label"]] += 1

        return objects

    def sumAllObjects(self, detection, objects):
        for object in detection:
            objects[object["label"]] += 1

        return objects

    def frameToBase64(self, frame):
        _, buffer = cv2.imencode(".jpg", frame)
        textImage = buffer.tobytes()
        return str(base64.b64encode(textImage), "utf-8")

    def detectObjects(self, frame, detectionURL):
        base64Image = self.frameToBase64(frame)

        response = requests.post(detectionURL, data={"frame": base64Image})
        detection = response.json()

        if detection != []:
            return detection, self.saveDetectedFrame(frame, detection)

        return None

    def frame(self, point, cap, root, metaTime):
        for trkpt in root.findall(".//{http://www.topografix.com/GPX/1/1}trkpt"):
            lat = float(trkpt.attrib["lat"])
            lon = float(trkpt.attrib["lon"])

            if lat == point["y"] and lon == point["x"]:
                trkptTime_str = trkpt.find(
                    "{http://www.topografix.com/GPX/1/1}time"
                ).text
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

    def saveDetectedFrame(self, frame, detection):
        return ""

        # TODO: Save Detected Frame
