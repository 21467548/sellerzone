from datetime import datetime
from flask import Blueprint, request, jsonify
from models import withdrawals_col, deposits_col, users_col, next_id
from utils import auth_required

wallet_bp = Blueprint("wallet", __name__)


@wallet_bp.route("/withdrawals", methods=["POST"])
@auth_required
def request_withdrawal():
    data = request.get_json() or {}
    amount = float(data.get("amount", 0))
    if amount <= 0:
        return jsonify({"error": "Invalid amount"}), 400
    user = users_col.find_one({"id": request.user_id})
    if user.get("balance", 0) < amount:
        return jsonify({"error": "Insufficient balance"}), 400
    w = {
        "id": next_id("withdrawals"),
        "userId": request.user_id,
        "userName": user["name"],
        "amount": amount,
        "status": "pending",
        "created_at": datetime.utcnow().isoformat(),
    }
    withdrawals_col.insert_one(w)
    w.pop("_id", None)
    return jsonify({"withdrawal": w})


@wallet_bp.route("/withdrawals", methods=["GET"])
@auth_required
def list_withdrawals():
    items = list(withdrawals_col.find({"userId": request.user_id}))
    for x in items:
        x.pop("_id", None)
    return jsonify({"withdrawals": items})


@wallet_bp.route("/deposits", methods=["POST"])
@auth_required
def request_deposit():
    data = request.get_json() or {}
    amount = float(data.get("amount", 0))
    receipt = data.get("receipt", "")
    if amount <= 0:
        return jsonify({"error": "Invalid amount"}), 400
    user = users_col.find_one({"id": request.user_id})
    d = {
        "id": next_id("deposits"),
        "userId": request.user_id,
        "userName": user["name"],
        "amount": amount,
        "receipt": receipt,
        "status": "pending",
        "created_at": datetime.utcnow().isoformat(),
    }
    deposits_col.insert_one(d)
    d.pop("_id", None)
    return jsonify({"deposit": d})


@wallet_bp.route("/deposits", methods=["GET"])
@auth_required
def list_deposits():
    items = list(deposits_col.find({"userId": request.user_id}))
    for x in items:
        x.pop("_id", None)
    return jsonify({"deposits": items})


@wallet_bp.route("/me", methods=["GET"])
@auth_required
def me():
    from routes.auth import public_user
    user = users_col.find_one({"id": request.user_id})
    return jsonify({"user": public_user(user)})