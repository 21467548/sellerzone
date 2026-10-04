from datetime import datetime
from flask import Blueprint, request, jsonify
from models import orders_col, carts_col, products_col, users_col, next_id
from utils import auth_required

orders_bp = Blueprint("orders", __name__)


@orders_bp.route("", methods=["GET"])
@auth_required
def list_orders():
    items = list(orders_col.find({"userId": request.user_id}).sort("id", -1))
    for o in items:
        o.pop("_id", None)
    return jsonify({"orders": items})


@orders_bp.route("", methods=["POST"])
@auth_required
def create_order():
    cart = carts_col.find_one({"userId": request.user_id}) or {"items": []}
    if not cart.get("items"):
        return jsonify({"error": "Cart is empty"}), 400

    order_items = []
    total = 0
    for ci in cart["items"]:
        p = products_col.find_one({"id": ci["productId"]})
        if not p:
            continue
        order_items.append({
            "product_id": p["id"],
            "name": p["name"],
            "price": p["price"],
            "qty": ci["qty"],
        })
        total += p["price"] * ci["qty"]

    user = users_col.find_one({"id": request.user_id})
    if user.get("balance", 0) < total:
        return jsonify({"error": "Insufficient balance"}), 400

    users_col.update_one({"id": request.user_id}, {"$inc": {"balance": -total}})

    body = request.get_json() or {}
    order = {
        "id": next_id("orders"),
        "userId": request.user_id,
        "items": order_items,
        "total": total,
        "status": "placed",
        "created_at": datetime.utcnow().isoformat(),
        "name": body.get("name", ""),
        "email": body.get("email", ""),
        "address": body.get("address", ""),
        "city": body.get("city", ""),
        "postal": body.get("postal", ""),
    }
    orders_col.insert_one(order)
    carts_col.update_one({"userId": request.user_id}, {"$set": {"items": []}})

    order.pop("_id", None)
    from routes.auth import public_user
    user = users_col.find_one({"id": request.user_id})
    return jsonify({"order": order, "user": public_user(user)})