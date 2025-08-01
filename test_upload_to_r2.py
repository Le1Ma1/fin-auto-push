from app.push.push_etf_chart import upload_to_r2

img_path = 'test.png'   # 請換成你本地的一張圖片檔案
url = upload_to_r2(img_path)
print("圖片已上傳，R2 CDN 網址：", url)
