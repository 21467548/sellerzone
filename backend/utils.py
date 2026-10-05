from functools import wraps
from flask import request, jsonify
from config import Config
from supabase_client import auth_client


def auth_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        header = request.headers.get("Authorization", "")
        token = header.replace("Bearer ", "")
        if not token:
            return jsonify({"error": "Not authenticated"}), 401
        try:
            response = auth_client.auth.get_user(token)
            if not response.user:
                raise ValueError("Missing user")
            request.user_id = str(response.user.id)
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