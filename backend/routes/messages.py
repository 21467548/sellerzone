from flask import Blueprint, request, jsonify
from supabase_client import db_client
from utils import auth_required

messages_bp = Blueprint("messages", __name__)


@messages_bp.route("", methods=["POST"])
@auth_required
def send_message():
    data = request.get_json() or {}
    text = data.get("text", "").strip()
    if not text:
        return jsonify({"error": "Message required"}), 400
    m = {
        "user_id": request.user_id,
        "text": text,
        "reply": "",
        "status": "open",
    }
    m = db_client.table("messages").insert(m).execute().data[0]
    m["userId"] = m.pop("user_id")
    return jsonify({"message": m})


@messages_bp.route("", methods=["GET"])
@auth_required
def list_messages():
    items = db_client.table("messages").select("*").eq("user_id", request.user_id).order("id", desc=True).execute().data
    for item in items:
        item["userId"] = item.pop("user_id")
    return jsonify({"messages": items})