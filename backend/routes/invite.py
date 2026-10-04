from flask import Blueprint, jsonify
from models import users_col
from utils import auth_required

invite_bp = Blueprint("invite", __name__)


@invite_bp.route("/generate", methods=["POST"])
@auth_required
def generate_invite():
    user = users_col.find_one({"id": request.user_id})
    return jsonify({"inviteCode": user.get("inviteCode", "")})