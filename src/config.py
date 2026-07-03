import os

from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_SECRET_KEY = os.environ["SUPABASE_SECRET_KEY"]

BANDUNG_API_BASE_URL = "https://opendata.bandung.go.id/api/bigdata/dinas_pendidikan"
