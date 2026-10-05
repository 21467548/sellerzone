import os
from pathlib import Path

from dotenv import load_dotenv
from supabase import Client, create_client

load_dotenv(Path(__file__).with_name(".env"))

SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_PUBLISHABLE_KEY = os.environ["SUPABASE_PUBLISHABLE_KEY"]
SUPABASE_SERVICE_ROLE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")

SERVER_KEY = SUPABASE_SERVICE_ROLE_KEY or SUPABASE_PUBLISHABLE_KEY

auth_client: Client = create_client(SUPABASE_URL, SERVER_KEY)
db_client: Client = create_client(
    SUPABASE_URL,
    SERVER_KEY,
)


def ensure_settings():
    existing = db_client.table("settings").select("id").eq("id", 1).execute().data
    if not existing:
        db_client.table("settings").insert({
            "id": 1,
            "pix_key": "bazaro@pix.com",
            "pix_name": "Bazaro Store",
            "invite_prefix": "BZR",
        }).execute()