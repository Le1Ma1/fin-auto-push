import os
from dotenv import load_dotenv

load_dotenv()  # 讀取 .env

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET")
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
PUSH_GROUP_IDS = os.getenv("PUSH_GROUP_IDS", "").split(",")
IMGBB_API_KEY = os.getenv("IMGBB_API_KEY")
TZ = os.getenv("TZ", "Asia/Taipei")
