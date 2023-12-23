import sqlite3
import json
import random

conn = sqlite3.connect("./data.sqlite", check_same_thread=False)
cur = conn.cursor()

# Check if tables already exist
cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='marker'")
marker_exists = cur.fetchone()
cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='polyline'")
polyline_exists = cur.fetchone()

# Create tables if they don't exist
if not marker_exists:
    cur.execute(
        """
    CREATE TABLE marker (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        videoSN TEXT NOT NULL,
        roadName TEXT NOT NULL,
        x REAL NOT NULL,
        y REAL NOT NULL,
        base64Image TEXT,
        addressJson TEXT
    )
    """
    )

if not polyline_exists:
    cur.execute(
        """
    CREATE TABLE polyline (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        videoSN TEXT NOT NULL,
        roadName TEXT NOT NULL,
        points TEXT NOT NULL,
        timestamp TEXT NOT NULL,
        videoname TEXT,
        congestion REAL,
        lineLength REAL,
        detection TEXT
    )
    """
    )

conn.commit()


def loadDB():
    dbData = {}

    cur.execute("SELECT * FROM polyline")
    lineData = cur.fetchone()

    if lineData is None:
        return None

    polyline = []
    marker = []

    while lineData is not None:
        polyline.append(
            {
                "type": "polyline",
                "lineID": lineData[0],
                "videoSN": lineData[1],
                "roadName": lineData[2],
                "points": json.loads(lineData[3]),
                "timestamp": lineData[4],
                "videoname": lineData[5],
                "congestion": lineData[6],
                "lineLength": lineData[7],
                "detection": json.loads(lineData[8]),
                "options": {
                    "strokeColor": f"#{random.randint(0, 0xFFFFFF):06x}",
                    "strokeWeight": 5,
                    "strokeStyle": "solid",
                    "strokeOpacity": 1,
                },
            }
        )

        lineData = cur.fetchone()

    cur.execute("SELECT * FROM marker")
    markerData = cur.fetchone()

    if markerData is None:
        return None

    while markerData is not None:
        marker.append(
            {
                "type": "marker",
                "id": markerData[0],
                "videoSN": markerData[1],
                "roadName": markerData[2],
                "x": markerData[3],
                "y": markerData[4],
                "coordinate": "wgs84",
                "zIndex": 0,
                "content": "",
                "image": markerData[5],
                "addressJson": json.loads(markerData[6]),
            }
        )

        markerData = cur.fetchone()

    dbData["polyline"] = polyline
    dbData["marker"] = marker

    return dbData
