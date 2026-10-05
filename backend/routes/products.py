from flask import Blueprint, request, jsonify
from supabase_client import db_client

products_bp = Blueprint("products", __name__)


def serialize(p):
    p["icon_key"] = p.get("icon_key", "all")
    return p


@products_bp.route("", methods=["GET"])
def list_products():
    category = request.args.get("category")
    query = db_client.table("products").select("*").eq("active", True)
    if category and category.lower() != "all":
        query = query.eq("category", category)
    search = request.args.get("q", "").strip()
    if search:
        query = query.ilike("name", f"%{search}%")
    items = [serialize(p) for p in query.order("id").execute().data]
    return jsonify({"products": items})


@products_bp.route("/<int:pid>", methods=["GET"])
def get_product(pid):
    result = db_client.table("products").select("*").eq("id", pid).eq("active", True).execute().data
    if not result:
        return jsonify({"error": "Not found"}), 404
    return jsonify({"product": serialize(result[0])})