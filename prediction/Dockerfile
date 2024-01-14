FROM ultralytics/yolov5:latest 
# FROM ultralytics/yolov5:latest-cpu
# FROM ultralytics/yolov5:latest-arm64

ENV TZ Asia/Seoul
ENV PYTHONIOENCODING UTF-8
ENV LC_CTYPE C.UTF-8

LABEL maintainer="https://suk.kr"

RUN python3 -m pip install flask

COPY . .

CMD [ "python3", "./app.py" ]