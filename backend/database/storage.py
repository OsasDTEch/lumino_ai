from dotenv import load_dotenv
from supabase import create_client
import os
load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_APIKEY")
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

def save_to_supabase(file_bytes: bytes, path: str) -> str:
    bucket = "resume"  # create this bucket in Supabase
    supabase.storage.from_(bucket).upload(path, file_bytes, {"content-type": "application/pdf"})
    return supabase.storage.from_(bucket).get_public_url(path)
