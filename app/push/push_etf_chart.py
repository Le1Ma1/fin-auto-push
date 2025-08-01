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
    上傳本地圖片到 Cloudflare R2，回傳 CDN 圖片網址
    """
    # 環境參數
    bucket = os.getenv('CF_R2_BUCKET_NAME')
    endpoint = os.getenv('CF_R2_ENDPOINT')
    access_key = os.getenv('CF_R2_ACCESS_KEY')
    secret_key = os.getenv('CF_R2_SECRET_KEY')
    cdn_domain = os.getenv('CF_R2_CDN_DOMAIN')  # 若沒設定就用 endpoint

    # 檔案唯一命名（避免 cache 問題）
    if object_name is None:
        ext = local_path.split('.')[-1]
        object_name = f"{int(time.time())}_{uuid.uuid4().hex}.{ext}"

    # 建立 S3/R2 客戶端
    s3 = boto3.client(
        's3',
        endpoint_url=endpoint,
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key,
        config=Config(signature_version='s3v4')
    )

    # 上傳
    s3.upload_file(local_path, bucket, object_name, ExtraArgs={'ACL': 'public-read', 'ContentType': 'image/png'})

    # 圖片網址：推薦使用你的 CDN 子網域，如沒有就用原生 R2 endpoint
    if cdn_domain:
        img_url = f"{cdn_domain}/{object_name}"
    else:
        img_url = f"{endpoint}/{bucket}/{object_name}"

    # 預熱 CDN，避免 Flex 首次推播延遲
    try:
        import requests
        requests.get(img_url, timeout=5)
    except Exception:
        pass

    return img_url
