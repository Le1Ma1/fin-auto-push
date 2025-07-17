import requests
import os

def upload_imgbb(image_path):
    api_key = os.getenv("IMGBB_API_KEY")
    with open(image_path, "rb") as f:
        files = {"image": f.read()}
    payload = {"key": api_key}
    res = requests.post("https://api.imgbb.com/1/upload", files=files, data=payload)
    print("imgbb response:", res.text)   # 加這行
    if res.status_code == 200:
        return res.json()['data']['url']
    else:
        raise Exception(f"imgbb 上傳失敗: {res.text}")

