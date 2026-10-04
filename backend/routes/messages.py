from datetime import datetime
from flask import Blueprint, request, jsonify
from models import messages_col, users_col, next_id
from utils import auth_required

messages_bp = Blueprint("messages", __name__)


@messages_bp.route("", methods=["POST"])
@auth_required
def send_message():
    data = request.get_json() or {}
    text = data.get("text", "").strip()
    if not text:
        return jsonify({"error": "Message required"}), 400
    user = users_col.find_one({"id": request.user_id})
    m = {
        "id": next_id("messages"),
        "userId": request.user_id,
        "userName": user["name"],
        "text": text,
        "reply": "",
        "status": "open",
        "created_at": datetime.utcnow().isoformat(),
    }
    messages_col.insert_one(m)
    m.pop("_id", None)
    return jsonify({"message": m})


@messages_bp.route("", methods=["GET"])
@auth_required
def list_messages():
    items = list(messages_col.find({"userId": request.user_id}))
    for x in items:
        x.pop("_id", None)
    return jsonify({"messages": items})