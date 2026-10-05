import random
import string

from flask import Blueprint, jsonify, request

from config import Config
from supabase_client import db_client
from utils import admin_required

admin_bp = Blueprint("admin", __name__)


def count_rows(table, filters=None):
    query = db_client.table(table).select("id", count="exact")
    for column, value in (filters or {}).items():
        query = query.eq(column, value)
    return query.execute().count or 0


def with_user_names(items):
    for item in items:
        user_id = item.get("user_id")
        profiles = db_client.table("profiles").select("name").eq("id", user_id).execute().data if user_id else []
        item["userName"] = profiles[0]["name"] if profiles else ""
        item["userId"] = item.pop("user_id", user_id)
    return items


def records(table, status=None):
    query = db_client.table(table).select("*").order("id", desc=True)
    if status:
        query = query.eq("status", status)
    return with_user_names(query.execute().data)


@admin_bp.route("/login", methods=["POST"])
def admin_login():
    if (request.get_json() or {}).get("password") != Config.ADMIN_PASSWORD:
        return jsonify({"error": "Wrong password"}), 401
    return jsonify({"token": Config.ADMIN_SECRET})


@admin_bp.route("/stats")
@admin_required
def stats():
    count = lambda table, filters=None: count_rows(table, filters)
    return jsonify({
        "totalUsers": count("profiles"), "totalProducts": count("products"),
        "totalOrders": count("orders"), "totalWithdrawals": count("withdrawals"),
        "pendingWithdrawals": count("withdrawals", {"status": "pending"}),
        "totalDeposits": count("deposits"), "pendingDeposits": count("deposits", {"status": "pending"}),
        "openMessages": count("messages", {"status": "open"}), "totalBuybacks": count("buybacks"),
        "frozenUsers": count("profiles", {"frozen": True}),
    })


@admin_bp.route("/users")
@admin_required
def list_users():
    search = request.args.get("search", "")
    query = db_client.table("profiles").select("*").order("created_at", desc=True)
    if search:
        query = query.or_(f"name.ilike.%{search}%,email.ilike.%{search}%")
    users = query.execute().data
    for user in users:
        user["inviteCode"] = user.pop("invite_code", "")
        user["pixKey"] = user.pop("pix_key", "")
        user["pixName"] = user.pop("pix_name", "")
    return jsonify({"users": users})


@admin_bp.route("/users/<uid>/freeze", methods=["POST"])
@admin_required
def freeze_user(uid):
    frozen = bool((request.get_json() or {}).get("frozen"))
    return jsonify({"user": db_client.table("profiles").update({"frozen": frozen}).eq("id", uid).execute().data[0]})


@admin_bp.route("/users/<uid>/points", methods=["POST"])
@admin_required
def adjust_points(uid):
    delta = float((request.get_json() or {}).get("delta", 0))
    current = db_client.table("profiles").select("points").eq("id", uid).single().execute().data
    user = db_client.table("profiles").update({"points": current["points"] + delta}).eq("id", uid).execute().data[0]
    return jsonify({"user": user})


@admin_bp.route("/users/<uid>/balance", methods=["POST"])
@admin_required
def adjust_balance(uid):
    delta = float((request.get_json() or {}).get("delta", 0))
    current = db_client.table("profiles").select("balance").eq("id", uid).single().execute().data
    user = db_client.table("profiles").update({"balance": max(0, float(current["balance"]) + delta)}).eq("id", uid).execute().data[0]
    return jsonify({"user": user})


@admin_bp.route("/products")
@admin_required
def admin_products():
    query = db_client.table("products").select("*").eq("active", True).order("id")
    search = request.args.get("search", "")
    if search:
        query = query.ilike("name", f"%{search}%")
    return jsonify({"products": query.execute().data})


@admin_bp.route("/products/search-by-price")
@admin_required
def search_by_price():
    amount = float(request.args.get("amount", 0))
    if amount <= 0:
        return jsonify({"error": "Amount required"}), 400
    products = db_client.table("products").select("*").gte("price", amount - 0.01).lte("price", amount + 0.01).execute().data
    return jsonify({"products": products})


@admin_bp.route("/products", methods=["POST"])
@admin_required
def add_product():
    data = request.get_json() or {}
    if not data.get("name") or data.get("price") is None:
        return jsonify({"error": "Name and price required"}), 400
    latest = db_client.table("products").select("id").order("id", desc=True).limit(1).execute().data
    next_product_id = (int(latest[0]["id"]) + 1) if latest else 1
    product = {key: data.get(key, default) for key, default in {
        "id": next_product_id, "name": data.get("name"), "price": float(data["price"]), "category": "home",
        "image": "", "description": "", "tag": "", "icon_key": "all", "active": True,
    }.items()}
    product.update({key: data[key] for key in ["category", "image", "description", "tag", "icon_key"] if key in data})
    return jsonify({"product": db_client.table("products").insert(product).execute().data[0]})


@admin_bp.route("/products/<int:pid>/price", methods=["POST"])
@admin_required
def update_price(pid):
    delta = float((request.get_json() or {}).get("delta", 0))
    current = db_client.table("products").select("price").eq("id", pid).single().execute().data
    product = db_client.table("products").update({"price": max(0, float(current["price"]) + delta)}).eq("id", pid).execute().data[0]
    return jsonify({"product": product})


@admin_bp.route("/products/<int:pid>", methods=["PUT"])
@admin_required
def update_product(pid):
    data = request.get_json() or {}
    allowed = {key: data[key] for key in ["name", "price", "category", "image", "description", "tag", "icon_key", "active", "stock"] if key in data}
    updated = db_client.table("products").update(allowed).eq("id", pid).execute().data
    return jsonify({"product": updated[0]}) if updated else (jsonify({"error": "Not found"}), 404)


@admin_bp.route("/products/<int:pid>", methods=["DELETE"])
@admin_required
def delete_product(pid):
    db_client.table("products").update({"active": False}).eq("id", pid).execute()
    return jsonify({"ok": True})


@admin_bp.route("/withdrawals")
@admin_required
def admin_withdrawals():
    return jsonify({"withdrawals": records("withdrawals", request.args.get("status"))})


@admin_bp.route("/withdrawals/<int:wid>/status", methods=["POST"])
@admin_required
def update_withdrawal_status(wid):
    status = (request.get_json() or {}).get("status")
    if status not in ["approved", "rejected", "pending"]:
        return jsonify({"error": "Invalid status"}), 400
    row = db_client.table("withdrawals").select("*").eq("id", wid).single().execute().data
    if row["status"] == "pending" and status == "approved":
        profile = db_client.table("profiles").select("balance").eq("id", row["user_id"]).single().execute().data
        db_client.table("profiles").update({"balance": max(0, float(profile["balance"]) - float(row["amount"]))}).eq("id", row["user_id"]).execute()
    updated = db_client.table("withdrawals").update({"status": status}).eq("id", wid).execute().data[0]
    return jsonify({"withdrawal": updated})


@admin_bp.route("/deposits")
@admin_required
def admin_deposits():
    return jsonify({"deposits": records("deposits", request.args.get("status"))})


@admin_bp.route("/deposits/<int:did>/status", methods=["POST"])
@admin_required
def update_deposit_status(did):
    data = request.get_json() or {}
    row = db_client.table("deposits").select("*").eq("id", did).single().execute().data
    if row["status"] == "pending" and data.get("status") == "approved":
        profile = db_client.table("profiles").select("balance").eq("id", row["user_id"]).single().execute().data
        amount = float(data.get("amount", row["amount"]))
        db_client.table("profiles").update({"balance": float(profile["balance"]) + amount}).eq("id", row["user_id"]).execute()
    updated = db_client.table("deposits").update({"status": data.get("status")}).eq("id", did).execute().data[0]
    return jsonify({"deposit": updated})


@admin_bp.route("/messages")
@admin_required
def admin_messages():
    return jsonify({"messages": records("messages")})


@admin_bp.route("/messages/<int:mid>/reply", methods=["POST"])
@admin_required
def reply_message(mid):
    data = request.get_json() or {}
    message = db_client.table("messages").update({"reply": data.get("reply", ""), "status": "replied"}).eq("id", mid).execute().data[0]
    return jsonify({"message": message})


@admin_bp.route("/buybacks")
@admin_required
def admin_buybacks():
    return jsonify({"buybacks": records("buybacks")})


@admin_bp.route("/buybacks/<int:bid>/status", methods=["POST"])
@admin_required
def update_buyback_status(bid):
    status = (request.get_json() or {}).get("status")
    row = db_client.table("buybacks").select("*").eq("id", bid).single().execute().data
    if row["status"] == "pending" and status == "approved":
        profile = db_client.table("profiles").select("balance").eq("id", row["user_id"]).single().execute().data
        db_client.table("profiles").update({"balance": float(profile["balance"]) + float(row["price"])}).eq("id", row["user_id"]).execute()
    updated = db_client.table("buybacks").update({"status": status}).eq("id", bid).execute().data[0]
    return jsonify({"buyback": updated})


@admin_bp.route("/settings")
@admin_required
def get_settings():
    setting = db_client.table("settings").select("*").eq("id", 1).single().execute().data
    return jsonify({"pixKey": setting["pix_key"], "pixName": setting["pix_name"], "invitePrefix": setting["invite_prefix"]})


@admin_bp.route("/settings", methods=["POST"])
@admin_required
def update_settings():
    data = request.get_json() or {}
    update = {target: data[source] for source, target in [("pixKey", "pix_key"), ("pixName", "pix_name"), ("invitePrefix", "invite_prefix")] if source in data}
    if update:
        db_client.table("settings").update(update).eq("id", 1).execute()
    return get_settings()


@admin_bp.route("/invite-codes/generate", methods=["POST"])
@admin_required
def generate_invite_codes():
    count = max(1, min(int((request.get_json() or {}).get("count", 1)), 100))
    prefix = db_client.table("settings").select("invite_prefix").eq("id", 1).single().execute().data["invite_prefix"]
    codes = []
    for _ in range(count):
        code = prefix + "-" + "".join(random.choices(string.ascii_uppercase + string.digits, k=6))
        db_client.table("invite_codes").insert({"code": code}).execute()
        codes.append(code)
    return jsonify({"codes": codes})


@admin_bp.route("/invite-codes")
@admin_required
def list_invite_codes():
    return jsonify({"codes": db_client.table("invite_codes").select("*").order("created_at", desc=True).execute().data})