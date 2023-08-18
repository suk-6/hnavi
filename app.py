from flask import Flask, render_template, url_for
from dotenv import load_dotenv
import os

app = Flask(__name__)
load_dotenv('.env')

@app.route('/')
def index():
    jsonURL = url_for('static', filename='data.json')
    return render_template('index.html', apiKey=os.getenv('KAKAO_API_KEY'), jsonURL=jsonURL)

@app.route('/drawing')
def drawing():
    return render_template('drawing.html', apiKey=os.getenv('KAKAO_API_KEY'))

@app.route('/overlay/<int:index>')
def overlay(index):
    return render_template('overlay.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000, debug=True)
