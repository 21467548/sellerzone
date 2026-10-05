from flask import Blueprint, request, jsonify
from supabase_client import db_client
from utils import auth_required

cart_bp = Blueprint("cart", __name__)


def cart_with_details(user_id):
    items = []
    cart_items = db_client.table("cart_items").select("*").eq("user_id", user_id).order("id").execute().data
    for cart_item in cart_items:
        products = db_client.table("products").select("*").eq("id", cart_item["product_id"]).execute().data
        if products:
            p = products[0]
            items.append({
                "productId": p["id"],
                "name": p["name"],
                "price": p["price"],
                "qty": cart_item["qty"],
                "iconKey": p.get("icon_key", "all"),
                "image": p.get("image", ""),
            })
    return {"items": items}


@cart_bp.route("", methods=["GET"])
@auth_required
def get_cart():
    return jsonify(cart_with_details(request.user_id))


@cart_bp.route("", methods=["POST"])
@auth_required
def add_to_cart():
    data = request.get_json() or {}
    product_id = data.get("productId", data.get("product_id"))
    qty = int(data.get("qty", 1))
    if not product_id or qty <= 0:
        return jsonify({"error": "Product and quantity required"}), 400

    if not db_client.table("products").select("id").eq("id", product_id).eq("active", True).execute().data:
        return jsonify({"error": "Product not found"}), 404

    existing = db_client.table("cart_items").select("id, qty").eq("user_id", request.user_id).eq("product_id", product_id).execute().data
    if existing:
        db_client.table("cart_items").update({"qty": existing[0]["qty"] + qty}).eq("id", existing[0]["id"]).execute()
    else:
        db_client.table("cart_items").insert({"user_id": request.user_id, "product_id": product_id, "qty": qty}).execute()

    return jsonify(cart_with_details(request.user_id))


@cart_bp.route("/<int:pid>", methods=["DELETE"])
@auth_required
def remove_from_cart(pid):
    db_client.table("cart_items").delete().eq("user_id", request.user_id).eq("product_id", pid).execute()
    return jsonify(cart_with_details(request.user_id))