from flask import Flask, render_template, jsonify, send_file, request, redirect, url_for
from dotenv import load_dotenv
import os
import json
from datetime import datetime
import random
from db import conn, cur, loadDB
from flask_cors import CORS
from parse import parser
import json
from labels import labels

app = Flask(__name__)
CORS(app)
app.config["JSON_AS_ASCII"] = False

load_dotenv(dotenv_path=".env", override=True)

parser = parser()

APIKEY = os.getenv("KAKAO_API_KEY")
detectionURL = os.getenv("DETECTION_URL")

jsonData = {}
group = {}

dbData = loadDB()
uploadFolder = os.path.join("/tmp", "upload")

if not os.path.exists(uploadFolder):
    os.makedirs(uploadFolder)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/en")
def index_en():
    return render_template("en/index.html")


@app.route("/map")
def map():
    return render_template("directions.html", apiKey=APIKEY)


@app.route("/en/map")
def map_en():
    return render_template("en/directions.html", apiKey=APIKEY)


@app.route("/db")
def dbrender():
    return render_template("db.html", apiKey=APIKEY, APIURL="/api/dbdata")


@app.route("/db-view")
def dbview():
    return render_template("db-view.html", APIURL="/api/dbdata")


@app.route("/en/db-view")
def dbview_en():
    return render_template("en/db-view.html", APIURL="/api/dbdata")


@app.route("/drawing")
def drawing():
    return render_template("drawing.html", apiKey=APIKEY)


@app.route("/upload", methods=["get"])
def upload():
    return render_template("upload.html")


@app.route("/reset", methods=["get"])
def reset():
    cur.execute("DELETE FROM marker")
    cur.execute("DELETE FROM polyline")
    conn.commit()
    loadDB()
    return redirect(url_for("upload"))


@app.route("/upload", methods=["post"])
def upload_endpoint():
    global dbData

    timestamp = datetime.now().timestamp()
    videoSN = f"{timestamp}.{random.randint(0, 1000000)}"
    basePath = os.path.join(uploadFolder, f"{videoSN}")

    f = request.files["file"]

    if f.filename.lower().endswith(".mp4"):
        print(f.filename, basePath)
        f.save(f"{basePath}.mp4")

        try:
            roads = parser.parse(basePath, detectionURL)
        except Exception as e:
            print(e)
            return "Parsing error", 400

        try:
            for file in os.listdir(uploadFolder):
                if file.startswith(f"{videoSN}"):
                    os.remove(os.path.join(uploadFolder, file))
        except:
            pass

        for road in roads:
            roadName = roads[road]["name"]
            region = roads[road]["region"]
            points = roads[road]["points"]
            lineLength = roads[road]["length"]
            congestion = roads[road]["congestion"]
            allObjects = roads[road]["allObjects"]
            midImage = roads[road]["midImage"]
            midPoint = roads[road]["midPoint"]
            imageIDs = roads[road]["imageIDs"]

            cur.execute(
                "INSERT INTO marker (videoSN, roadName, region, x, y, base64Image) VALUES (?, ?, ?, ?, ?, ?)",
                (
                    videoSN,
                    roadName,
                    region,
                    midPoint["x"],
                    midPoint["y"],
                    midImage,
                ),
            )

            cur.execute(
                "INSERT INTO polyline (videoSN, roadName, region, timestamp, videoname, congestion, lineLength, points, detection, imageIDs) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    videoSN,
                    roadName,
                    region,
                    timestamp,
                    f.filename,
                    congestion,
                    lineLength,
                    json.dumps(points),
                    json.dumps(allObjects),
                    json.dumps(imageIDs),
                ),
            )

            conn.commit()
            dbData = loadDB()
    else:
        return "Invalid file type", 400

    return "OK", 200


@app.route("/overlay-db/<int:id>")
def overlaydb(id):
    cur.execute("SELECT * FROM marker WHERE id = ?", (id,))
    markerData = cur.fetchone()

    if markerData is None:
        return "No marker found", 404

    marker = {
        "id": markerData[0],
        "videoSN": markerData[1],
        "roadName": markerData[2],
        "region": markerData[3],
        "image": markerData[6],
    }

    cur.execute("SELECT * FROM polyline WHERE id = ?", (marker["id"],))
    polylineData = cur.fetchone()

    if polylineData is None:
        return "No polyline found", 404

    marker["congestion"] = polylineData[7]
    marker["detection"] = json.loads(polylineData[9])

    detection = marker.get("detection", {})
    image = marker.get("image", {})

    dataCount = {
        "person": {
            "objectNames": ["person"],
            "count": 0,
        },
        "car": {
            "objectNames": ["car", "bus", "truck"],
            "count": 0,
        },
        "motorcycle": {
            "objectNames": ["motorcycle", "kickboard"],
            "count": 0,
        },
    }

    for object in dataCount.keys():
        for objectName in dataCount[object]["objectNames"]:
            objectClass = labels.index(objectName)
            dataCount[object]["count"] += detection.get(str(objectClass), 0)

    return render_template(
        "overlay.html",
        detailURL=f"/api/detail/{marker['id']}",
        name=marker["roadName"],
        region_depth=marker["region"],
        congestion=marker["congestion"],
        image=image,
        person=dataCount["person"]["count"],
        car=dataCount["car"]["count"],
        motorcycle=dataCount["motorcycle"]["count"],
    )


@app.route("/api/dbdata")
def dbdata():
    return jsonify(dbData)


@app.route("/api/detail/<int:id>")
def showDetail(id):
    return render_template("detail.html", IMAGEAPIURL=f"/api/image/{id}")


@app.route("/api/image/<int:id>")  # polylineID
def image(id):
    cur.execute("SELECT imageIDs FROM polyline WHERE id = ?", (id,))
    imageIDs = cur.fetchone()
    if imageIDs is None:
        return "No image found", 404

    imageIDs = json.loads(imageIDs[0])
    images = []

    for imageID in imageIDs:
        cur.execute("SELECT image FROM images WHERE id = ?", (imageID,))
        image = cur.fetchone()
        if image is None:
            continue

        images.append(image[0])

    return jsonify(images)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
