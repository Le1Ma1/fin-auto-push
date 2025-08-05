from supabase import create_client
import os
from dotenv import load_dotenv
load_dotenv()
supabase = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_KEY'))

test_row = {"date": "2024-08-01", "score": 50, "level": "Neutral"}
resp = supabase.table("fear_greed_index").insert([test_row]).execute()
print(resp)
