# 카카오API를 사용하여 좌표->주소 변환 (리버스 지오코딩)
import requests, json

def get_address(lat, lng, RESTAPIKEY):
    url = f"https://dapi.kakao.com/v2/local/geo/coord2regioncode.json?x={lng}&y={lat}"
    headers = {"Authorization": f"KakaoAK {RESTAPIKEY}"}
    result = requests.get(url, headers=headers)
    resultJson = json.loads(result.text)

    return resultJson