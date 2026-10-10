import os
from pathlib import Path

from dotenv import load_dotenv
from supabase import Client, create_client

for env_path in [
    Path(__file__).with_name(".env"),
    Path(__file__).parent.parent / ".env",
    Path("/etc/secrets/.env"),
]:
    if env_path.exists():
        load_dotenv(env_path)

SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
SUPABASE_PUBLISHABLE_KEY = os.environ.get("SUPABASE_PUBLISHABLE_KEY", "")
SUPABASE_SERVICE_ROLE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY", "")


SERVER_KEY = SUPABASE_SERVICE_ROLE_KEY or SUPABASE_PUBLISHABLE_KEY

auth_client: Client = create_client(SUPABASE_URL, SERVER_KEY)
db_client: Client = create_client(
    SUPABASE_URL,
    SERVER_KEY,
)


def ensure_settings():
    try:
        existing = db_client.table("settings").select("id").eq("id", 1).execute().data
        if not existing:
            db_client.table("settings").insert({
                "id": 1,
                "pix_key": "bazaro@pix.com",
                "pix_name": "Bazaro Store",
                "invite_prefix": "BZR",
            }).execute()
    except Exception as exc:
        print(f"[Warning] ensure_settings failed: {exc}")