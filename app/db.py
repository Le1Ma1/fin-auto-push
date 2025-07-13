from supabase import create_client
from app.config import SUPABASE_URL, SUPABASE_KEY

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

def insert_row(table, data):
    return supabase.table(table).insert(data).execute()

def upsert_row(table, data, on_conflict):
    return supabase.table(table).upsert(data, on_conflict=on_conflict).execute()

def fetch_rows(table, filters=None, limit=100):
    query = supabase.table(table).select("*")
    if filters:
        for k, v in filters.items():
            query = query.eq(k, v)
    return query.limit(limit).execute().data

# ...可擴充查詢、更新、刪除等
