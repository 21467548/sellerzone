from flask import Blueprint, request, jsonify
from datetime import datetime, timedelta
import bcrypt
import jwt
import random
import string

from models import users_col, next_id
from config import Config

auth_bp = Blueprint("auth", __name__)


def make_token(user_id):
    payload = {
        "id": user_id,
        "exp": datetime.utcnow() + timedelta(days=Config.JWT_EXP_DAYS),
    }
    return jwt.encode(payload, Config.JWT_SECRET, algorithm="HS256")


def public_user(u):
    return {
        "id": u["id"],
        "name": u["name"],
        "email": u["email"],
        "balance": u.get("balance", 0),
        "points": u.get("points", 0),
        "frozen": u.get("frozen", False),
        "inviteCode": u.get("inviteCode", ""),
        "pixKey": u.get("pixKey", ""),
        "pixName": u.get("pixName", ""),
    }


def gen_invite_code():
    return "BZR-" + "".join(random.choices(string.ascii_uppercase + string.digits, k=6))


@auth_bp.route("/register", methods=["POST"])
def register():
    data = request.get_json() or {}
    name = data.get("name")
    email = data.get("email")
    password = data.get("password")
    invited_by = data.get("inviteCode")

    if not name or not email or not password:
        return jsonify({"error": "Missing fields"}), 400

    if users_col.find_one({"email": email}):
        return jsonify({"error": "Email already used"}), 400

    password_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
    user = {
        "id": next_id("users"),
        "name": name,
        "email": email,
        "passwordHash": password_hash,
        "balance": 0,
        "points": 0,
        "frozen": False,
        "pixKey": "",
        "pixName": "",
        "inviteCode": gen_invite_code(),
        "invitedBy": invited_by,
        "created_at": datetime.utcnow().isoformat(),
    }
    users_col.insert_one(user)

    if invited_by:
        inviter = users_col.find_one({"inviteCode": invited_by})
        if inviter:
            users_col.update_one({"id": inviter["id"]}, {"$inc": {"points": 50}})

    token = make_token(user["id"])
    return jsonify({"token": token, "user": public_user(user)})


@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json() or {}
    email = data.get("email")
    password = data.get("password")

    user = users_col.find_one({"email": email})
    if not user:
        return jsonify({"error": "Invalid credentials"}), 400
    if user.get("frozen"):
        return jsonify({"error": "Account frozen. Contact support."}), 403
    if not bcrypt.checkpw(password.encode(), user["passwordHash"].encode()):
        return jsonify({"error": "Invalid credentials"}), 400

    token = make_token(user["id"])
    return jsonify({"token": token, "user": public_user(user)})