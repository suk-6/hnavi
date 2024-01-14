import cv2
import base64
import requests

imagePath = "/tmp/temp.jpg"
detectionURL = "http://prediction.prediction.orb.local:10001/detect"

image = cv2.imread(imagePath)

base64Image = str(base64.b64encode(cv2.imencode(".jpg", image)[1].tobytes()), "utf-8")

response = requests.post(detectionURL, data={"frame": base64Image})

detection = response.json()

print(detection)
