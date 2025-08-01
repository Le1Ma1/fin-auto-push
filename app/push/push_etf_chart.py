import os
import uuid
import time
import boto3
from botocore.client import Config
from dotenv import load_dotenv

# 自動載入 .env
load_dotenv()

def upload_to_r2(local_path, object_name=None):
    """
    上傳本地圖片到 Cloudflare R2，回傳 CDN 圖片公開開發網址
    """
    # 1. 讀取環境變數
    bucket = os.getenv('CF_R2_BUCKET_NAME')
    endpoint = os.getenv('CF_R2_ENDPOINT')
    access_key = os.getenv('CF_R2_ACCESS_KEY')
    secret_key = os.getenv('CF_R2_SECRET_KEY')
    # 你必須填自己的公開開發 URL，例如：
    # CF_R2_CDN_DOMAIN=https://pub-fa63e55cc28d46829201c2420a86a4a4.r2.dev
    cdn_domain = os.getenv('CF_R2_CDN_DOMAIN')  

    # 2. 檔案唯一命名（避免 cache 問題）
    if object_name is None:
        ext = local_path.split('.')[-1]
        object_name = f"{int(time.time())}_{uuid.uuid4().hex}.{ext}"

    # 3. 建立 S3/R2 客戶端
    s3 = boto3.client(
        's3',
        endpoint_url=endpoint,
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key,
        config=Config(signature_version='s3v4')
    )

    # 4. 上傳
    s3.upload_file(local_path, bucket, object_name, ExtraArgs={'ACL': 'public-read', 'ContentType': 'image/png'})

    # 5. 強制使用公開開發 URL
    if cdn_domain:
        img_url = f"{cdn_domain}/{object_name}"
    else:
        # 萬一沒設，仍用原 endpoint，但建議強制用公開 URL
        img_url = f"{endpoint}/{bucket}/{object_name}"

    # 6. 等待圖片可用（最多重試10次，每0.5秒）
    import requests
    for _ in range(10):
        try:
            resp = requests.get(img_url, timeout=5)
            if resp.status_code == 200:
                break
        except Exception:
            pass
        time.sleep(0.5)

    # 7. debug log
    print(f"[DEBUG] 已上傳至 R2，圖片公開網址：{img_url}")

    return img_url
