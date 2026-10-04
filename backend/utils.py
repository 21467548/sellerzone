from functools import wraps
from flask import request, jsonify
import jwt
from config import Config


def auth_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        header = request.headers.get("Authorization", "")
        token = header.replace("Bearer ", "")
        if not token:
            return jsonify({"error": "Not authenticated"}), 401
        try:
            payload = jwt.decode(token, Config.JWT_SECRET, algorithms=["HS256"])
            request.user_id = payload["id"]
        except Exception:
            return jsonify({"error": "Invalid token"}), 401
        return f(*args, **kwargs)
    return wrapper


def admin_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        header = request.headers.get("Authorization", "")
        token = header.replace("Bearer ", "")
        if token != Config.ADMIN_SECRET:
            return jsonify({"error": "Admin only"}), 401
        return f(*args, **kwargs)
    return wrapper