from flask import Flask, render_template, jsonify, send_file, request, redirect, url_for
from dotenv import load_dotenv
import os
import json
from datetime import datetime
import random
import sqlite3
from flask_cors import CORS
from parse import parser
# from natsort import natsorted

app = Flask(__name__)
CORS(app)

load_dotenv(dotenv_path='.env', override=True)

parser = parser()

cur = sqlite3.connect('./data.sqlite').cursor()

APIKEY = os.getenv('KAKAO_API_KEY')
jsonFolder = os.getenv('JSON_FOLDER_PATH')
imageFolder = os.getenv('IMAGE_FOLDER_PATH')
release = os.getenv('RELEASE_TYPE')
detectionURL = os.getenv('DETECTION_URL')

print(APIKEY, jsonFolder, imageFolder, release)

jsonData = {}
group = {}

uploadFolder = os.path.join("/tmp", "upload")

if not os.path.exists(uploadFolder):
    os.makedirs(uploadFolder)

@app.route('/')
def index():
    return render_template('directions.html', apiKey=APIKEY)

@app.route('/wang')
def wang():
    return render_template('index.html', apiKey=APIKEY)

@app.route('/drawing')
def drawing():
    return render_template('drawing.html', apiKey=APIKEY)

@app.route('/upload', methods=["get"])
def upload():
    return render_template('upload.html')

@app.route("/upload", methods=["post"])
def upload_endpoint():
    timestamp = datetime.now().timestamp()
    linename = f"{timestamp}.{random.randint(0, 1000000)}"
    filename = f"{linename}.mp4"
    savePath = os.path.join(uploadFolder, filename)

    f = request.files["file"]

    if f.filename.lower().endswith(".mp4"):
        print(f.filename, savePath)
        f.save(savePath)

        points, lineLength, congestion = parser.parse(savePath, detectionURL)

        cur.execute(
            "INSERT INTO polyline (linename, timestamp, videoname, congestion, lineLength, points) VALUES (?, ?)", \
                (linename, timestamp, filename, congestion, lineLength, points)
            )
    else:
        return "Invalid file type", 400

    return "Success", 200

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

@app.route('/api/data')
def data():
    return jsonify(jsonData)

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
