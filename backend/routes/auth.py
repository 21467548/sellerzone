from flask import Blueprint, request, jsonify
import random
import string

from supabase_client import auth_client, db_client

auth_bp = Blueprint("auth", __name__)


def public_user(u):
    return {
        "id": str(u["id"]),
        "name": u["name"],
        "email": u["email"],
        "balance": float(u.get("balance", 0)),
        "points": u.get("points", 0),
        "frozen": u.get("frozen", False),
        "inviteCode": u.get("invite_code", ""),
        "pixKey": u.get("pix_key", ""),
        "pixName": u.get("pix_name", ""),
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

    try:
        response = auth_client.auth.sign_up({"email": email, "password": password})
        if not response.user:
            return jsonify({"error": "Unable to create account"}), 400

        profile = {
            "id": response.user.id,
            "name": name,
            "email": email,
            "invite_code": gen_invite_code(),
            "invited_by": invited_by,
        }
        db_client.table("profiles").upsert(profile).execute()
        saved = db_client.table("profiles").select("*").eq("id", response.user.id).single().execute().data
        if not response.session:
            return jsonify({
                "message": "Check your email to confirm your account, then log in.",
                "requiresConfirmation": True,
                "user": public_user(saved),
            }), 201
        return jsonify({"token": response.session.access_token, "user": public_user(saved)})
    except Exception as error:
        return jsonify({"error": str(error)}), 400


@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json() or {}
    email = data.get("email")
    password = data.get("password")

    try:
        response = auth_client.auth.sign_in_with_password({"email": email, "password": password})
        profile = db_client.table("profiles").select("*").eq("id", response.user.id).single().execute().data
        if profile.get("frozen"):
            return jsonify({"error": "Account frozen. Contact support."}), 403
        return jsonify({"token": response.session.access_token, "user": public_user(profile)})
    except Exception as error:
        if "confirm" in str(error).lower() or "not confirmed" in str(error).lower():
            return jsonify({"error": "Please confirm your email before signing in."}), 403
        return jsonify({"error": "Invalid credentials"}), 400