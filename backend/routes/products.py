from flask import Blueprint, request, jsonify
from models import products_col

products_bp = Blueprint("products", __name__)


def serialize(p):
    p.pop("_id", None)
    return p


@products_bp.route("", methods=["GET"])
def list_products():
    category = request.args.get("category")
    query = {}
    if category and category != "all":
        query["category"] = category
    items = [serialize(p) for p in products_col.find(query)]
    return jsonify({"products": items})


@products_bp.route("/<int:pid>", methods=["GET"])
def get_product(pid):
    p = products_col.find_one({"id": pid})
    if not p:
        return jsonify({"error": "Not found"}), 404
    return jsonify({"product": serialize(p)})