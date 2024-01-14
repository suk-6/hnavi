import cv2
import torch
from torchvision import transforms
import base64
from PIL import Image
import numpy as np
import os
from flask import Flask, request

app = Flask(__name__)

# YOLO 모델과 가중치 로드
model = torch.hub.load(
    "./", "custom", path="./models/best.pt", source="local", force_reload=True
)


@app.route("/detect", methods=["POST"])
def detect():
    frameBase64 = request.form["frame"]

    frameData = base64.b64decode(frameBase64)
    frameNp = cv2.imdecode(np.frombuffer(frameData, np.uint8), cv2.IMREAD_COLOR)
    framePil = Image.fromarray(frameNp)

    results = model(framePil)

    annos = []

    for bbox in zip(results.xyxy[0]):
        xmin, ymin, xmax, ymax, conf, label = bbox[0].tolist()

        if conf > 0.2:
            annos.append(
                {
                    "xmin": int(xmin),
                    "ymin": int(ymin),
                    "xmax": int(xmax),
                    "ymax": int(ymax),
                    "label": int(label),
                    "confidence": float(conf),
                }
            )

    print(annos)

    return annos


if __name__ == "__main__":
    app.run(host="0.0.0.0", port="10001")
