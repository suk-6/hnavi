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
from rgeo import get_address

app = Flask(__name__)
CORS(app)
app.config['JSON_AS_ASCII'] = False

load_dotenv(dotenv_path='.env', override=True)

parser = parser()

APIKEY = os.getenv('KAKAO_API_KEY')
RESTAPIKEY = os.getenv('KAKAO_REST_API_KEY')
jsonFolder = os.getenv('JSON_FOLDER_PATH')
imageFolder = os.getenv('IMAGE_FOLDER_PATH')
release = os.getenv('RELEASE_TYPE')
detectionURL = os.getenv('DETECTION_URL')

print(APIKEY, jsonFolder, imageFolder, release)

jsonData = {}
group = {}

dbData = loadDB()
uploadFolder = os.path.join("/tmp", "upload")

if not os.path.exists(uploadFolder):
    os.makedirs(uploadFolder)

@app.route('/')
def index():
    return render_template('directions.html', apiKey=APIKEY)

@app.route('/wang')
def wang():
    return render_template('index.html', apiKey=APIKEY, APIURL="/api/data")

@app.route('/db')
def dbrender():
    return render_template('db.html', apiKey=APIKEY, APIURL="/api/dbdata")

@app.route('/drawing')
def drawing():
    return render_template('drawing.html', apiKey=APIKEY)

@app.route('/upload', methods=["get"])
def upload():
    return render_template('upload.html')

@app.route("/upload", methods=["post"])
def upload_endpoint():
    global dbData

    timestamp = datetime.now().timestamp()
    linename = f"{timestamp}.{random.randint(0, 1000000)}"
    basePath = os.path.join(uploadFolder, f"{linename}")

    f = request.files["file"]

    if f.filename.lower().endswith(".mp4"):
        print(f.filename, basePath)
        f.save(f"{basePath}.mp4")
        
        # try:
        points, lineLength, congestion, midpoint, allObjects, midImage = parser.parse(basePath, detectionURL)
        # except:
        #     return "Parsing error", 400

        try:
            for file in os.listdir(uploadFolder):
                if file.startswith(f"{linename}"):
                    os.remove(os.path.join(uploadFolder, file))
        except:
            pass
        
        addressJson = json.dumps(get_address(midpoint["y"], midpoint["x"], RESTAPIKEY))

        cur.execute(
            "INSERT INTO marker (linename, x, y, base64Image, addressJson) VALUES (?, ?, ?, ?, ?)", \
                (linename, midpoint["x"], midpoint["y"], midImage, addressJson)
            )

        cur.execute(
            "INSERT INTO polyline (linename, timestamp, videoname, congestion, lineLength, points, detection) VALUES (?, ?, ?, ?, ?, ?, ?)", \
                (linename, timestamp, f.filename, congestion, lineLength, json.dumps(points), json.dumps(allObjects))
            )
        
        conn.commit()
        dbData = loadDB()
    else:
        return "Invalid file type", 400

    return "OK", 200

@app.route('/overlay/<int:index>/<int:i>')
def overlay(index, i):
    marker = group[index]

    detection = marker.get("detection", {})

    person = detection.get("0", 0)
    car = detection.get("2", 0)
    motorcycle = detection.get("3", 0) + detection.get("88", 0) + detection.get("1", 0)
    
    return render_template(
        'overlay.html', 
        index=marker["index"], 
        congestion=marker["congestion"],
        person=person,
        car=car,
        motorcycle=motorcycle,
        )

@app.route('/overlay-db/<int:id>')
def overlaydb(id):
    cur.execute("SELECT * FROM marker WHERE id = ?", (id,))
    markerData = cur.fetchone()

    if markerData is None:
        return "No marker found", 404
    
    marker = {
        "id": markerData[0],
        "linename": markerData[1],
        "image": markerData[4],
        "addressJson": json.loads(markerData[5]),
    }

    cur.execute("SELECT * FROM polyline WHERE linename = ?", (marker["linename"],))
    polylineData = cur.fetchone()

    if polylineData is None:
        return "No polyline found", 404
    
    marker["congestion"] = polylineData[5]
    marker["detection"] = json.loads(polylineData[7])

    detection = marker.get("detection", {})

    person = detection.get("0", 0)
    car = detection.get("2", 0)
    motorcycle = detection.get("3", 0) + detection.get("88", 0) + detection.get("1", 0)
    
    return render_template(
        'overlay.html', 
        index=marker["id"], 
        region_depth=marker["addressJson"]["documents"][0]["address_name"],
        congestion=marker["congestion"],
        person=person,
        car=car,
        motorcycle=motorcycle,
        )

@app.route('/api/data')
def data():
    return jsonify(jsonData)

@app.route('/api/dbdata')
def dbdata():
    return jsonify(dbData)

@app.route('/api/detect/<int:index>')
def detect(index):
    for data in jsonData["marker"]:
        if data["index"] == index:
            return jsonify(data["detection"])
    
    return jsonify({})

@app.route('/api/image/<int:index>')
def image(index):
    try:
        image = os.path.join(imageFolder, f"{index}.jpg")
        return send_file(image, mimetype='image/jpeg')
    except:
        return "No image found"

def loadJSON():
    global jsonData
    if release == "prod":
        with open(os.path.join(jsonFolder, "data.json"), "r") as jsonFile:
            jsonData = json.load(jsonFile)

    else:
        jsonFiles = [f for f in os.listdir(jsonFolder) if f.endswith('.json')]
        jsonFiles.sort(key=lambda x: os.path.getmtime(os.path.join(jsonFolder, x)), reverse=True)

        if jsonFiles:
            latestJson = os.path.join(jsonFolder, jsonFiles[0])

            # JSON 파일 내용 읽어오기
            with open(latestJson, "r") as jsonFile:
                jsonData = json.load(jsonFile)

    for marker in jsonData["marker"]:
        group[marker["index"]] = marker

if __name__ == '__main__':
    loadJSON()
    app.run(host='0.0.0.0', port=10000)
