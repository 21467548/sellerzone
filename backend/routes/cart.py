from flask import Blueprint, request, jsonify
from models import carts_col, products_col
from utils import auth_required

cart_bp = Blueprint("cart", __name__)


def cart_with_details(user_id):
    cart = carts_col.find_one({"userId": user_id}) or {"userId": user_id, "items": []}
    items = []
    for ci in cart.get("items", []):
        p = products_col.find_one({"id": ci["productId"]})
        if p:
            items.append({
                "productId": p["id"],
                "name": p["name"],
                "price": p["price"],
                "qty": ci["qty"],
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
    product_id = data.get("productId")
    qty = int(data.get("qty", 1))

    p = products_col.find_one({"id": product_id})
    if not p:
        return jsonify({"error": "Product not found"}), 404

    cart = carts_col.find_one({"userId": request.user_id})
    if not cart:
        carts_col.insert_one({"userId": request.user_id, "items": [{"productId": product_id, "qty": qty}]})
    else:
        items = cart.get("items", [])
        found = False
        for it in items:
            if it["productId"] == product_id:
                it["qty"] += qty
                found = True
                break
        if not found:
            items.append({"productId": product_id, "qty": qty})
        carts_col.update_one({"userId": request.user_id}, {"$set": {"items": items}})

    return jsonify(cart_with_details(request.user_id))


@cart_bp.route("/<int:pid>", methods=["DELETE"])
@auth_required
def remove_from_cart(pid):
    cart = carts_col.find_one({"userId": request.user_id})
    if cart:
        items = [i for i in cart.get("items", []) if i["productId"] != pid]
        carts_col.update_one({"userId": request.user_id}, {"$set": {"items": items}})
    return jsonify(cart_with_details(request.user_id))