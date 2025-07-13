import requests
import base64
from app.config import IMGBB_API_KEY

def upload_image_to_imgbb(image_buffer):
    """
    將 BytesIO 的圖像上傳至 IMGBB，回傳公開圖片網址
    """
    url = "https://api.imgbb.com/1/upload"
    image_base64 = base64.b64encode(image_buffer.getvalue()).decode()
    payload = {
        "key": IMGBB_API_KEY,
        "image": image_base64,
    }
    resp = requests.post(url, data=payload)
    if resp.status_code == 200 and resp.json().get("success"):
        return resp.json()["data"]["url"]
    else:
        raise Exception(f"IMGBB upload failed: {resp.text}")
