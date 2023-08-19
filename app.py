from flask import Flask, render_template, url_for
from dotenv import load_dotenv
import os
import requests

app = Flask(__name__)
load_dotenv('.env')

APIKEY = os.getenv('KAKAO_API_KEY')

@app.route('/')
def index():
    return render_template('index.html', apiKey=APIKEY)

@app.route('/drawing')
def drawing():
    return render_template('drawing.html', apiKey=APIKEY)

@app.route('/overlay/<int:index>')
def overlay(index):
    return render_template('overlay.html', index=index)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
