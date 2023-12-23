FROM python:3.10

WORKDIR /app
COPY . /app

RUN git clone https://github.com/juanmcasillas/gopro2gpx && cd gopro2gpx && python3 setup.py install

RUN pip install -r requirements.txt

EXPOSE 20004

CMD ["python", "/app/app.py"]