from flask import Blueprint, jsonify, request
from supabase_client import db_client
from utils import auth_required

invite_bp = Blueprint("invite", __name__)


@invite_bp.route("/generate", methods=["POST"])
@auth_required
def generate_invite():
    user = db_client.table("profiles").select("invite_code").eq("id", request.user_id).single().execute().data
    return jsonify({"inviteCode": user.get("invite_code", "")})