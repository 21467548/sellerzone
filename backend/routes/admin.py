from datetime import datetime
from flask import Blueprint, request, jsonify
import bcrypt
import random
import string

from models import (
    users_col, products_col, orders_col, withdrawals_col, deposits_col,
    messages_col, buybacks_col, invite_codes_col, settings_col, next_id
)
from config import Config
from utils import admin_required

admin_bp = Blueprint("admin", __name__)


@admin_bp.route("/login", methods=["POST"])
def admin_login():
    data = request.get_json() or {}
    if data.get("password") != Config.ADMIN_PASSWORD:
        return jsonify({"error": "Wrong password"}), 401
    return jsonify({"token": Config.ADMIN_SECRET})


@admin_bp.route("/stats", methods=["GET"])
@admin_required
def stats():
    return jsonify({
        "totalUsers": users_col.count_documents({}),
        "totalProducts": products_col.count_documents({}),
        "totalOrders": orders_col.count_documents({}),
        "totalWithdrawals": withdrawals_col.count_documents({}),
        "pendingWithdrawals": withdrawals_col.count_documents({"status": "pending"}),
        "totalDeposits": deposits_col.count_documents({}),
        "pendingDeposits": deposits_col.count_documents({"status": "pending"}),
        "openMessages": messages_col.count_documents({"status": "open"}),
        "totalBuybacks": buybacks_col.count_documents({}),
        "frozenUsers": users_col.count_documents({"frozen": True}),
    })


# ---------- USERS ----------
@admin_bp.route("/users", methods=["GET"])
@admin_required
def list_users():
    search = request.args.get("search", "").lower()
    query = {}
    if search:
        query = {"$or": [
            {"name": {"$regex": search, "$options": "i"}},
            {"email": {"$regex": search, "$options": "i"}},
        ]}
    users = []
    for u in users_col.find(query):
        u.pop("_id", None); u.pop("passwordHash", None)
        users.append(u)
    return jsonify({"users": users})


@admin_bp.route("/users/<int:uid>/freeze", methods=["POST"])
@admin_required
def freeze_user(uid):
    data = request.get_json() or {}
    users_col.update_one({"id": uid}, {"$set": {"frozen": bool(data.get("frozen"))}})
    u = users_col.find_one({"id": uid})
    u.pop("_id", None); u.pop("passwordHash", None)
    return jsonify({"user": u})


@admin_bp.route("/users/<int:uid>/reset-password", methods=["POST"])
@admin_required
def reset_password(uid):
    data = request.get_json() or {}
    new_password = data.get("newPassword") or "sellerzone123"
    h = bcrypt.hashpw(new_password.encode(), bcrypt.gensalt()).decode()
    users_col.update_one({"id": uid}, {"$set": {"passwordHash": h}})
    return jsonify({"ok": True, "newPassword": new_password})


@admin_bp.route("/users/<int:uid>/points", methods=["POST"])
@admin_required
def adjust_points(uid):
    data = request.get_json() or {}
    delta = float(data.get("delta", 0))
    users_col.update_one({"id": uid}, {"$inc": {"points": delta}})
    u = users_col.find_one({"id": uid})
    u.pop("_id", None); u.pop("passwordHash", None)
    return jsonify({"user": u})


@admin_bp.route("/users/<int:uid>/balance", methods=["POST"])
@admin_required
def adjust_balance(uid):
    data = request.get_json() or {}
    delta = float(data.get("delta", 0))
    users_col.update_one({"id": uid}, {"$inc": {"balance": delta}})
    u = users_col.find_one({"id": uid})
    if u.get("balance", 0) < 0:
        users_col.update_one({"id": uid}, {"$set": {"balance": 0}})
    u = users_col.find_one({"id": uid})
    u.pop("_id", None); u.pop("passwordHash", None)
    return jsonify({"user": u})


# ---------- PRODUCTS ----------
@admin_bp.route("/products", methods=["GET"])
@admin_required
def admin_products():
    search = request.args.get("search", "")
    query = {}
    if search:
        query["name"] = {"$regex": search, "$options": "i"}
    items = []
    for p in products_col.find(query):
        p.pop("_id", None)
        items.append(p)
    return jsonify({"products": items})


@admin_bp.route("/products/search-by-price", methods=["GET"])
@admin_required
def search_by_price():
    amount = float(request.args.get("amount", 0))
    if amount <= 0:
        return jsonify({"error": "Amount required"}), 400
    items = []
    for p in products_col.find({"price": {"$gte": amount - 0.01, "$lte": amount + 0.01}}):
        p.pop("_id", None)
        items.append(p)
    return jsonify({"products": items})


@admin_bp.route("/products", methods=["POST"])
@admin_required
def add_product():
    data = request.get_json() or {}
    if not data.get("name") or data.get("price") is None:
        return jsonify({"error": "Name and price required"}), 400
    p = {
        "id": next_id("products"),
        "name": data["name"],
        "price": float(data["price"]),
        "category": data.get("category", "home"),
        "image": data.get("image", ""),
        "description": data.get("description", ""),
        "tag": data.get("tag", ""),
        "icon_key": data.get("icon_key", "all"),
    }
    products_col.insert_one(p)
    p.pop("_id", None)
    return jsonify({"product": p})


@admin_bp.route("/products/<int:pid>/price", methods=["POST"])
@admin_required
def update_price(pid):
    data = request.get_json() or {}
    delta = float(data.get("delta", 0))
    p = products_col.find_one({"id": pid})
    if not p:
        return jsonify({"error": "Not found"}), 404
    new_price = max(0, p["price"] + delta)
    products_col.update_one({"id": pid}, {"$set": {"price": new_price}})
    p = products_col.find_one({"id": pid})
    p.pop("_id", None)
    return jsonify({"product": p})


@admin_bp.route("/products/<int:pid>", methods=["PUT"])
@admin_required
def update_product(pid):
    data = request.get_json() or {}
    data.pop("_id", None); data.pop("id", None)
    products_col.update_one({"id": pid}, {"$set": data})
    p = products_col.find_one({"id": pid})
    if not p:
        return jsonify({"error": "Not found"}), 404
    p.pop("_id", None)
    return jsonify({"product": p})


@admin_bp.route("/products/<int:pid>", methods=["DELETE"])
@admin_required
def delete_product(pid):
    products_col.delete_one({"id": pid})
    return jsonify({"ok": True})


# ---------- WITHDRAWALS ----------
@admin_bp.route("/withdrawals", methods=["GET"])
@admin_required
def admin_withdrawals():
    status = request.args.get("status")
    query = {"status": status} if status else {}
    items = list(withdrawals_col.find(query).sort("id", -1))
    for x in items:
        x.pop("_id", None)
    return jsonify({"withdrawals": items})


@admin_bp.route("/withdrawals/<int:wid>/status", methods=["POST"])
@admin_required
def update_withdrawal_status(wid):
    data = request.get_json() or {}
    status = data.get("status")
    if status not in ["approved", "rejected", "pending"]:
        return jsonify({"error": "Invalid status"}), 400
    w = withdrawals_col.find_one({"id": wid})
    if not w:
        return jsonify({"error": "Not found"}), 404
    if w["status"] == "pending" and status == "approved":
        users_col.update_one({"id": w["userId"]}, {"$inc": {"balance": -w["amount"]}})
    withdrawals_col.update_one({"id": wid}, {"$set": {"status": status}})
    w = withdrawals_col.find_one({"id": wid})
    w.pop("_id", None)
    return jsonify({"withdrawal": w})


# ---------- DEPOSITS ----------
@admin_bp.route("/deposits", methods=["GET"])
@admin_required
def admin_deposits():
    status = request.args.get("status")
    query = {"status": status} if status else {}
    items = list(deposits_col.find(query).sort("id", -1))
    for x in items:
        x.pop("_id", None)
    return jsonify({"deposits": items})


@admin_bp.route("/deposits/<int:did>/status", methods=["POST"])
@admin_required
def update_deposit_status(did):
    data = request.get_json() or {}
    status = data.get("status")
    amount = data.get("amount")
    d = deposits_col.find_one({"id": did})
    if not d:
        return jsonify({"error": "Not found"}), 404
    if d["status"] == "pending" and status == "approved":
        add_amount = float(amount) if amount is not None else d["amount"]
        users_col.update_one({"id": d["userId"]}, {"$inc": {"balance": add_amount}})
    deposits_col.update_one({"id": did}, {"$set": {"status": status}})
    d = deposits_col.find_one({"id": did})
    d.pop("_id", None)
    return jsonify({"deposit": d})


# ---------- MESSAGES ----------
@admin_bp.route("/messages", methods=["GET"])
@admin_required
def admin_messages():
    items = list(messages_col.find().sort("id", -1))
    for x in items:
        x.pop("_id", None)
    return jsonify({"messages": items})


@admin_bp.route("/messages/<int:mid>/reply", methods=["POST"])
@admin_required
def reply_message(mid):
    data = request.get_json() or {}
    messages_col.update_one({"id": mid}, {"$set": {"reply": data.get("reply", ""), "status": "replied"}})
    m = messages_col.find_one({"id": mid})
    m.pop("_id", None)
    return jsonify({"message": m})


# ---------- BUYBACKS ----------
@admin_bp.route("/buybacks", methods=["GET"])
@admin_required
def admin_buybacks():
    items = list(buybacks_col.find().sort("id", -1))
    for x in items:
        x.pop("_id", None)
    return jsonify({"buybacks": items})


@admin_bp.route("/buybacks/<int:bid>/status", methods=["POST"])
@admin_required
def update_buyback_status(bid):
    data = request.get_json() or {}
    status = data.get("status")
    b = buybacks_col.find_one({"id": bid})
    if not b:
        return jsonify({"error": "Not found"}), 404
    if b["status"] == "pending" and status == "approved":
        users_col.update_one({"id": b["userId"]}, {"$inc": {"balance": b["price"]}})
    buybacks_col.update_one({"id": bid}, {"$set": {"status": status}})
    b = buybacks_col.find_one({"id": bid})
    b.pop("_id", None)
    return jsonify({"buyback": b})


# ---------- SETTINGS ----------
@admin_bp.route("/settings", methods=["GET"])
@admin_required
def get_settings():
    s = settings_col.find_one({"_id": "global"}) or {}
    s.pop("_id", None)
    return jsonify(s)


@admin_bp.route("/settings", methods=["POST"])
@admin_required
def update_settings():
    data = request.get_json() or {}
    update = {}
    for k in ["pixKey", "pixName", "invitePrefix"]:
        if k in data:
            update[k] = data[k]
    if update:
        settings_col.update_one({"_id": "global"}, {"$set": update}, upsert=True)
    s = settings_col.find_one({"_id": "global"})
    s.pop("_id", None)
    return jsonify(s)


# ---------- INVITE CODES ----------
@admin_bp.route("/invite-codes/generate", methods=["POST"])
@admin_required
def generate_invite_codes():
    data = request.get_json() or {}
    count = int(data.get("count", 1))
    s = settings_col.find_one({"_id": "global"}) or {"invitePrefix": "BZR"}
    prefix = s.get("invitePrefix", "BZR")
    codes = []
    for _ in range(count):
        code = prefix + "-" + "".join(random.choices(string.ascii_uppercase + string.digits, k=6))
        invite_codes_col.insert_one({
            "code": code,
            "created_at": datetime.utcnow().isoformat(),
            "usedBy": None,
        })
        codes.append(code)
    return jsonify({"codes": codes})


@admin_bp.route("/invite-codes", methods=["GET"])
@admin_required
def list_invite_codes():
    items = list(invite_codes_col.find().sort("created_at", -1))
    for x in items:
        x.pop("_id", None)
    return jsonify({"codes": items})