from flask import Blueprint, request, jsonify
from supabase_client import db_client
from utils import auth_required

orders_bp = Blueprint("orders", __name__)


@orders_bp.route("", methods=["GET"])
@auth_required
def list_orders():
    items = db_client.table("orders").select("*").eq("user_id", request.user_id).order("id", desc=True).execute().data
    for order in items:
        order["userId"] = order.pop("user_id")
        order["created_at"] = order.get("created_at")
    return jsonify({"orders": items})


@orders_bp.route("", methods=["POST"])
@auth_required
def create_order():
    cart_items = db_client.table("cart_items").select("*").eq("user_id", request.user_id).execute().data
    if not cart_items:
        return jsonify({"error": "Cart is empty"}), 400

    order_items = []
    total = 0
    for cart_item in cart_items:
        products = db_client.table("products").select("*").eq("id", cart_item["product_id"]).execute().data
        if not products:
            continue
        p = products[0]
        order_items.append({
            "product_id": p["id"],
            "name": p["name"],
            "price": p["price"],
            "qty": cart_item["quantity"],
        })
        total += p["price"] * cart_item["quantity"]

    profile_result = db_client.table("profiles").select("*").eq("id", request.user_id).single().execute()
    user = profile_result.data
    if float(user.get("balance", 0)) < total:
        return jsonify({"error": "Insufficient balance"}), 400

    body = request.get_json() or {}
    order = {
        "user_id": request.user_id,
        "items": order_items,
        "total": total,
        "status": "placed",
        "address": body.get("address", ""),
    }
    db_client.table("profiles").update({"balance": float(user["balance"]) - total}).eq("id", request.user_id).execute()
    saved = db_client.table("orders").insert(order).execute().data[0]
    db_client.table("cart_items").delete().eq("user_id", request.user_id).execute()
    saved["userId"] = saved.pop("user_id")
    from routes.auth import public_user
    updated_user = db_client.table("profiles").select("*").eq("id", request.user_id).single().execute().data
    return jsonify({"order": saved, "user": public_user(updated_user)})