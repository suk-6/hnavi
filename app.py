from flask import Flask, render_template, jsonify, send_file
from dotenv import load_dotenv
import os
import json
from natsort import natsorted

app = Flask(__name__)
load_dotenv('.env')

APIKEY = os.getenv('KAKAO_API_KEY')
jsonFolder = os.getenv('JSON_FOLDER_PATH')
imageFolder = os.getenv('IMAGE_FOLDER_PATH')

jsonData = {}

@app.route('/')
def index():
    return render_template('index.html', apiKey=APIKEY)

@app.route('/drawing')
def drawing():
    return render_template('drawing.html', apiKey=APIKEY)

@app.route('/overlay/<int:index>/<int:i>')
def overlay(index, i):
    return render_template('overlay.html', index=index)

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
    jsonFiles = [f for f in os.listdir(jsonFolder) if f.endswith('.json')]
    jsonFiles.sort(key=lambda x: os.path.getmtime(os.path.join(jsonFolder, x)), reverse=True)

    if jsonFiles:
        latestJson = os.path.join(jsonFolder, jsonFiles[0])

        # JSON 파일 내용 읽어오기
        with open(latestJson, "r") as jsonFile:
            jsonData = json.load(jsonFile)

if __name__ == '__main__':
    loadJSON()
    app.run(host='0.0.0.0', port=10000)
