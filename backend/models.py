from pymongo import MongoClient
from config import Config

client = MongoClient(Config.MONGO_URI)
db = client[Config.DB_NAME]

users_col = db["users"]
products_col = db["products"]
carts_col = db["carts"]
wishlists_col = db["wishlists"]
orders_col = db["orders"]
addresses_col = db["addresses"]
withdrawals_col = db["withdrawals"]
deposits_col = db["deposits"]
messages_col = db["messages"]
buybacks_col = db["buybacks"]
invite_codes_col = db["invite_codes"]
settings_col = db["settings"]
counters_col = db["counters"]


def next_id(name):
    doc = counters_col.find_one_and_update(
        {"_id": name},
        {"$inc": {"seq": 1}},
        upsert=True,
        return_document=True,
    )
    return doc["seq"]


def ensure_settings():
    if not settings_col.find_one({"_id": "global"}):
        settings_col.insert_one({
            "_id": "global",
            "pixKey": "sellerzone@pix.com",
            "pixName": "SellerZone Store",
            "invitePrefix": "SZ",
        })