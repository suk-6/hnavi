import sqlite3
import json

conn = sqlite3.connect('./data.sqlite', check_same_thread=False)
cur = conn.cursor()

# Check if tables already exist
cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='marker'")
marker_exists = cur.fetchone()
cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='polyline'")
polyline_exists = cur.fetchone()

# Create tables if they don't exist
if not marker_exists:
    cur.execute('''
    CREATE TABLE marker (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        linename TEXT NOT NULL,
        x REAL NOT NULL,
        y REAL NOT NULL,
        base64Image TEXT,
        addressJson TEXT
    )
    ''')

if not polyline_exists:
    cur.execute('''
    CREATE TABLE polyline (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        linename TEXT NOT NULL,
        points TEXT NOT NULL,
        timestamp TEXT NOT NULL,
        videoname TEXT,
        congestion REAL,
        lineLength REAL,
        detection TEXT
    )
    ''')

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
        polyline.append({
            "type": "polyline",
            "lineID": lineData[0],
            "linename": lineData[1],
            "points": json.loads(lineData[2]),
            "timestamp": lineData[3],
            "videoname": lineData[4],
            "congestion": lineData[5],
            "lineLength": lineData[6],
            "detection": json.loads(lineData[7]),
            "options": {
                "strokeColor": "#808080",
                "strokeWeight": 5,
                "strokeStyle": "solid",
                "strokeOpacity": 1
            },
        })

        lineData = cur.fetchone()

    cur.execute("SELECT * FROM marker")
    markerData = cur.fetchone()

    if markerData is None:
        return None

    while markerData is not None:
        marker.append({
            "type": "marker",
            "id": markerData[0],
            "linename": markerData[1],
            "x": markerData[2],
            "y": markerData[3],
            "coordinate": "wgs84",
            "zIndex": 0,
            "content": "",
            "image": markerData[4],
            "addressJson": json.loads(markerData[5]),
        })

        markerData = cur.fetchone()

    dbData["polyline"] = polyline
    dbData["marker"] = marker

    return dbData