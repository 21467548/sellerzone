import os
from pathlib import Path
from dotenv import load_dotenv

for env_path in [
    Path(__file__).with_name(".env"),
    Path(__file__).parent.parent / ".env",
    Path("/etc/secrets/.env"),
]:
    if env_path.exists():
        load_dotenv(env_path)


class Config:
    SUPABASE_URL = os.getenv("SUPABASE_URL", "")
    SUPABASE_PUBLISHABLE_KEY = os.getenv("SUPABASE_PUBLISHABLE_KEY", "")
    SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")
    SUPABASE_STORAGE_BUCKET = os.getenv("SUPABASE_STORAGE_BUCKET", "product-images")
    ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin123")
    ADMIN_SECRET = os.getenv("ADMIN_SECRET", "bazaro-admin-secret-change-me")
