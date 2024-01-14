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
cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='images'")
images_exists = cur.fetchone()

# Create tables if they don't exist
if not marker_exists:
    cur.execute(
        """
    CREATE TABLE marker (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        videoSN TEXT NOT NULL,
        roadName TEXT NOT NULL,
        region TEXT NOT NULL,
        x REAL NOT NULL,
        y REAL NOT NULL,
        base64Image TEXT
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
        region TEXT NOT NULL,
        points TEXT NOT NULL,
        timestamp TEXT NOT NULL,
        videoname TEXT,
        congestion REAL,
        lineLength REAL,
        detection TEXT,
        imageIDs TEXT
    )
    """
    )

if not images_exists:
    cur.execute(
        """
    CREATE TABLE images (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        image TEXT NOT NULL
    )
    """
    )

conn.commit()


def saveImage(image):
    cur.execute("INSERT INTO images (image) VALUES (?)", (image,))
    conn.commit()

    return cur.lastrowid


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
                "region": lineData[3],
                "points": json.loads(lineData[4]),
                "timestamp": lineData[5],
                "videoname": lineData[6],
                "congestion": lineData[7],
                "lineLength": lineData[8],
                "detection": json.loads(lineData[9]),
                "imageIDs": json.loads(lineData[10]),
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
                "region": markerData[3],
                "x": markerData[4],
                "y": markerData[5],
                "coordinate": "wgs84",
                "zIndex": 0,
                "content": "",
                "image": markerData[6],
            }
        )

        markerData = cur.fetchone()

    dbData["polyline"] = polyline
    dbData["marker"] = marker

    return dbData
