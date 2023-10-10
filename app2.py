from flask import Flask, render_template, request, redirect, url_for
from dotenv import load_dotenv
import os

app = Flask(__name__)
load_dotenv('.env')

APIKEY = os.getenv('KAKAO_API_KEY')

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        keyword = request.form.get('keyword')
        if keyword == '왕십리역':
            return redirect('https://hnavi.wsuk.dev/')
        else:
            # Handle other keywords or display an error message
            pass
    return render_template('directions.html', apiKey=APIKEY)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)