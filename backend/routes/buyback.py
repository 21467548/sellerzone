from datetime import datetime
from flask import Blueprint, request, jsonify
from models import buybacks_col, products_col, users_col, next_id
from utils import auth_required

buyback_bp = Blueprint("buyback", __name__)


@buyback_bp.route("", methods=["POST"])
@auth_required
def request_buyback():
    data = request.get_json() or {}
    product_id = data.get("productId")
    qty = int(data.get("qty", 1))
    p = products_col.find_one({"id": product_id})
    if not p:
        return jsonify({"error": "Product not found"}), 404
    user = users_col.find_one({"id": request.user_id})
    price = round(p["price"] * 0.8, 2)
    b = {
        "id": next_id("buybacks"),
        "userId": request.user_id,
        "userName": user["name"],
        "productId": product_id,
        "productName": p["name"],
        "qty": qty,
        "price": price,
        "status": "pending",
        "created_at": datetime.utcnow().isoformat(),
    }
    buybacks_col.insert_one(b)
    b.pop("_id", None)
    return jsonify({"buyback": b})


@buyback_bp.route("", methods=["GET"])
@auth_required
def list_buybacks():
    items = list(buybacks_col.find({"userId": request.user_id}))
    for x in items:
        x.pop("_id", None)
    return jsonify({"buybacks": items})