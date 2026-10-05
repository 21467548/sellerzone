from flask import Blueprint, request, jsonify
from supabase_client import db_client
from utils import auth_required

wallet_bp = Blueprint("wallet", __name__)


@wallet_bp.route("/withdrawals", methods=["POST"])
@auth_required
def request_withdrawal():
    data = request.get_json() or {}
    amount = float(data.get("amount", 0))
    if amount <= 0:
        return jsonify({"error": "Invalid amount"}), 400
    user = db_client.table("profiles").select("*").eq("id", request.user_id).single().execute().data
    if float(user.get("balance", 0)) < amount:
        return jsonify({"error": "Insufficient balance"}), 400
    w = {
        "user_id": request.user_id,
        "amount": amount,
        "status": "pending",
    }
    w = db_client.table("withdrawals").insert(w).execute().data[0]
    w["userId"] = w.pop("user_id")
    w["userName"] = user["name"]
    return jsonify({"withdrawal": w})


@wallet_bp.route("/withdrawals", methods=["GET"])
@auth_required
def list_withdrawals():
    items = db_client.table("withdrawals").select("*").eq("user_id", request.user_id).order("id", desc=True).execute().data
    for item in items:
        item["userId"] = item.pop("user_id")
    return jsonify({"withdrawals": items})


@wallet_bp.route("/deposits", methods=["POST"])
@auth_required
def request_deposit():
    data = request.get_json() or {}
    amount = float(data.get("amount", 0))
    receipt = data.get("receipt", "")
    if amount <= 0:
        return jsonify({"error": "Invalid amount"}), 400
    d = {
        "user_id": request.user_id,
        "amount": amount,
        "receipt": receipt,
        "status": "pending",
    }
    d = db_client.table("deposits").insert(d).execute().data[0]
    d["userId"] = d.pop("user_id")
    return jsonify({"deposit": d})


@wallet_bp.route("/deposits", methods=["GET"])
@auth_required
def list_deposits():
    items = db_client.table("deposits").select("*").eq("user_id", request.user_id).order("id", desc=True).execute().data
    for item in items:
        item["userId"] = item.pop("user_id")
    return jsonify({"deposits": items})


@wallet_bp.route("/me", methods=["GET"])
@auth_required
def me():
    from routes.auth import public_user
    user = db_client.table("profiles").select("*").eq("id", request.user_id).single().execute().data
    from routes.auth import public_user
    return jsonify({"user": public_user(user)})