from flask import Blueprint, request, jsonify
from supabase_client import db_client
from utils import auth_required

buyback_bp = Blueprint("buyback", __name__)


@buyback_bp.route("", methods=["POST"])
@auth_required
def request_buyback():
    data = request.get_json() or {}
    product_id = data.get("productId")
    qty = int(data.get("qty", 1))
    products = db_client.table("products").select("*").eq("id", product_id).eq("active", True).execute().data
    if not products:
        return jsonify({"error": "Product not found"}), 404
    p = products[0]
    price = round(p["price"] * 0.8, 2)
    b = {
        "user_id": request.user_id,
        "product_id": product_id,
        "qty": qty,
        "price": price,
        "status": "pending",
    }
    b = db_client.table("buybacks").insert(b).execute().data[0]
    b["userId"] = b.pop("user_id")
    b["productId"] = b.pop("product_id")
    b["productName"] = p["name"]
    return jsonify({"buyback": b})


@buyback_bp.route("", methods=["GET"])
@auth_required
def list_buybacks():
    items = db_client.table("buybacks").select("*").eq("user_id", request.user_id).order("id", desc=True).execute().data
    for item in items:
        item["userId"] = item.pop("user_id")
        item["productId"] = item.pop("product_id")
    return jsonify({"buybacks": items})