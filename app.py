from flask import Flask, render_template
from dotenv import load_dotenv
import os

app = Flask(__name__)
load_dotenv('.env')

@app.route('/')
def home():
    return render_template('index.html', apiKey=os.getenv('KAKAO_API_KEY'))

if __name__ == '__main__':
    app.run()
