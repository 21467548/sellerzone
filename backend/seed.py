from models import products_col, ensure_settings, next_id

PRODUCTS = [
    {
        "name": "Logitech Webcam Brio 101 Full HD 1080p Auto Focus",
        "price": 34.99,
        "category": "electronics",
        "icon_key": "webcam",
        "tag": "Hot",
        "image": "/images/products/webcam.svg",
        "description": "Full HD 1080p webcam with auto-light correction, dual mics and privacy shutter."
    },
    {
        "name": "TOMI Ring, Inde Yellow Gold K55 (B324952)",
        "price": 1620.00,
        "category": "jewelry",
        "icon_key": "ring",
        "tag": "New",
        "image": "/images/products/ring.svg",
        "description": "18K yellow gold ring with natural accent stones."
    },
    {
        "name": "L'ORÉAL Youth Password Serum",
        "price": 89.90,
        "category": "cosmetics",
        "icon_key": "cosmetic_serum",
        "tag": "New",
        "image": "/images/products/cosmetic_serum.svg",
        "description": "Anti-aging serum with hyaluronic acid and vitamin C."
    },
    {
        "name": "Smart Watch Series 8 Pro",
        "price": 399.00,
        "category": "watches",
        "icon_key": "watch_smart",
        "tag": "Hot",
        "image": "/images/products/watch_smart.svg",
        "description": "AMOLED display, heart-rate monitor, GPS and 7-day battery life."
    },
    {
        "name": "Classic Leather Watch Brown",
        "price": 249.00,
        "category": "watches",
        "icon_key": "watch_leather",
        "tag": "Sale",
        "image": "/images/products/watch_leather.svg",
        "description": "Timeless brown leather strap watch."
    },
    {
        "name": "Cadeira de rodas de transporte leve e dobrável",
        "price": 1220.00,
        "category": "home",
        "icon_key": "travelbed",
        "image": "/images/products/travelbed.svg",
        "description": "Lightweight foldable transport wheelchair."
    },
    {
        "name": "Android 13.0 Radio for Toyota Etios 2010-2019",
        "price": 3280.00,
        "category": "electronics",
        "icon_key": "device_cat",
        "image": "/images/products/device_cat.svg",
        "description": "13.0 inch IPS Touch Screen Stereo with Bluetooth 5.0, Carplay, Android Auto GPS."
    },
    {
        "name": "Oura Ring 5 Smart Ring Monitor",
        "price": 3300.00,
        "category": "jewelry",
        "icon_key": "ring",
        "image": "/images/products/ring.svg",
        "description": "Smart ring monitor with sleep tracking and health insights."
    },
    {
        "name": "Brown Tweezers BT Skin Powder Matte Loose",
        "price": 137.00,
        "category": "cosmetics",
        "icon_key": "cosmetic_cream",
        "image": "/images/products/cosmetic_cream.svg",
        "description": "Matte loose powder for oily and combination skin."
    },
    {
        "name": "La Mer The Concentrate (50ml)",
        "price": 25.00,
        "category": "cosmetics",
        "icon_key": "cosmetic_serum",
        "image": "/images/products/cosmetic_serum.svg",
        "description": "Soothing concentrate for sensitive skin."
    },
    {
        "name": "Hiccapop Inflatable Toddler Travel Bed",
        "price": 60.00,
        "category": "home",
        "icon_key": "travelbed",
        "tag": "Hot",
        "image": "/images/products/travelbed.svg",
        "description": "Portable toddler bed for travel, camping and vacation."
    },
]


def seed():
    ensure_settings()
    if products_col.count_documents({}) > 0:
        print(f"⚠️  Products already exist ({products_col.count_documents({})}). Skipping seed.")
        return
    for p in PRODUCTS:
        p["id"] = next_id("products")
        products_col.insert_one(p)
        print(f"✅ Inserted: {p['name'][:50]}")
    print(f"\n🎉 Seeded {len(PRODUCTS)} products into MongoDB.")


if __name__ == "__main__":
    seed()