import base64
import json
import mimetypes
import re
from pathlib import Path

from supabase_client import db_client, SUPABASE_SERVICE_ROLE_KEY
from config import Config


PRODUCT_FILE = Path(__file__).with_name("bazaro.products.json")
BUCKET = Config.SUPABASE_STORAGE_BUCKET


def upload_data_url(data_url, product_id):
    match = re.match(r"data:(image/[^;]+);base64,(.+)", data_url, re.DOTALL)
    if not match or not SUPABASE_SERVICE_ROLE_KEY:
        return data_url

    content_type, encoded = match.groups()
    extension = mimetypes.guess_extension(content_type) or ".bin"
    path = f"catalog/{product_id}{extension}"
    try:
        db_client.storage.from_(BUCKET).upload(
            path,
            base64.b64decode(encoded),
            {"content-type": content_type, "upsert": "true"},
        )
        return db_client.storage.from_(BUCKET).get_public_url(path)
    except Exception as error:
        print(f"Storage upload skipped for product {product_id}: {error}")
        return data_url


def seed():
    products = json.loads(PRODUCT_FILE.read_text(encoding="utf-8"))
    rows = []
    for source in products:
        product_id = int(source["id"])
        rows.append({
            "id": product_id,
            "name": source["name"],
            "price": float(source["price"]),
            "old_price": source.get("old_price"),
            "category": source.get("category", "home"),
            "icon_key": source.get("icon_key", "all"),
            "tag": source.get("tag", ""),
            "image": upload_data_url(source.get("image", ""), product_id),
            "description": source.get("description", ""),
            "active": True,
        })

    db_client.table("products").upsert(rows, on_conflict="id").execute()
    print(f"Seeded {len(rows)} products into Supabase.")


if __name__ == "__main__":
    seed()