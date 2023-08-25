from flask import Flask, render_template, jsonify
from dotenv import load_dotenv
import os
import json

app = Flask(__name__)
load_dotenv('.env')

APIKEY = os.getenv('KAKAO_API_KEY')
jsonFolder = os.getenv('JSON_FOLDER_PATH')

@app.route('/')
def index():
    return render_template('index.html', apiKey=APIKEY)

@app.route('/drawing')
def drawing():
    return render_template('drawing.html', apiKey=APIKEY)

@app.route('/overlay/<int:index>')
def overlay(index):
    return render_template('overlay.html', index=index)

@app.route('/api/data')
def data():
    # JSON 파일들의 타임스탬프를 기준으로 정렬
    jsonFiles = [f for f in os.listdir(jsonFolder) if f.endswith('.json')]
    jsonFiles.sort(key=lambda x: os.path.getmtime(os.path.join(jsonFolder, x)), reverse=True)

    if jsonFiles:
        latestJson = os.path.join(jsonFolder, jsonFiles[0])

        # JSON 파일 내용 읽어오기
        with open(latestJson, "r") as jsonFile:
            jsonData = json.load(jsonFile)

        return jsonify(jsonData)
    else:
        return "No JSON files found"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
