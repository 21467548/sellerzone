from flask import Flask, send_from_directory, jsonify, request, Response
from flask_cors import CORS
import os
import urllib.request
import urllib.parse

from config import Config
from supabase_client import db_client, ensure_settings
from routes.auth import auth_bp
from routes.products import products_bp
from routes.cart import cart_bp
from routes.orders import orders_bp
from routes.wallet import wallet_bp
from routes.messages import messages_bp
from routes.buyback import buyback_bp
from routes.invite import invite_bp
from routes.admin_supabase import admin_bp

FRONTEND_DIR = os.path.join(os.path.dirname(__file__), "..", "frontend")

app = Flask(__name__, static_folder=FRONTEND_DIR, static_url_path="")
CORS(app)


# Register API blueprints — SIRF EK BAAR
app.register_blueprint(auth_bp, url_prefix="/api/auth")
app.register_blueprint(products_bp, url_prefix="/api/products")
app.register_blueprint(cart_bp, url_prefix="/api/cart")
app.register_blueprint(orders_bp, url_prefix="/api/orders")
app.register_blueprint(wallet_bp, url_prefix="/api/wallet")
app.register_blueprint(messages_bp, url_prefix="/api/messages")
app.register_blueprint(buyback_bp, url_prefix="/api/buybacks")
app.register_blueprint(invite_bp, url_prefix="/api/invite")
app.register_blueprint(admin_bp, url_prefix="/api/admin")


# Run settings check safely on startup
try:
    ensure_settings()
except Exception as _e:
    pass


@app.route("/api/settings", methods=["GET"])
def public_settings():
    try:
        res = db_client.table("settings").select("*").eq("id", 1).execute()
        setting = res.data[0] if (res.data and len(res.data) > 0) else {}
    except Exception:
        setting = {}

    return jsonify({
        "pixKey": setting.get("pix_key", "bazaro@pix.com"),
        "pixName": setting.get("pix_name", "Bazaro Store"),
        "invitePrefix": setting.get("invite_prefix", "BZR"),
    })



@app.route("/api/image")
def proxy_image():
    """Proxy remote product images through the SellerZone domain.

    This avoids browser hotlink/referrer restrictions from some image hosts.
    Only http/https image responses are returned and the response is size-limited.
    """
    url = (request.args.get("url") or "").strip()
    parsed = urllib.parse.urlparse(url)
    if parsed.scheme not in ("http", "https") or not parsed.netloc:
        return jsonify({"error": "Invalid image URL"}), 400

    try:
        req = urllib.request.Request(
            url,
            headers={
                "User-Agent": "Mozilla/5.0 SellerZone/1.0",
                "Accept": "image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8",
            },
        )
        with urllib.request.urlopen(req, timeout=15) as upstream:
            content_type = upstream.headers.get("Content-Type", "")
            if not content_type.lower().startswith("image/"):
                return jsonify({"error": "URL did not return an image"}), 415

            max_bytes = 8 * 1024 * 1024
            chunks = []
            total = 0
            while True:
                chunk = upstream.read(64 * 1024)
                if not chunk:
                    break
                total += len(chunk)
                if total > max_bytes:
                    return jsonify({"error": "Image is too large"}), 413
                chunks.append(chunk)

            data = b"".join(chunks)
            return Response(
                data,
                status=200,
                content_type=content_type.split(";")[0],
                headers={"Cache-Control": "public, max-age=86400"},
            )
    except Exception as exc:
        return jsonify({"error": f"Unable to load image: {exc}"}), 502

@app.route("/api/health")
def health():
    return jsonify({"status": "ok", "service": "sellerzone"})


@app.route("/")
def index():
    return send_from_directory(FRONTEND_DIR, "index.html")


@app.route("/admin")
def admin_page():
    return send_from_directory(FRONTEND_DIR, "admin.html")


@app.route("/<path:path>")
def static_files(path):
    full = os.path.join(FRONTEND_DIR, path)
    if os.path.isfile(full):
        return send_from_directory(FRONTEND_DIR, path)
    return send_from_directory(FRONTEND_DIR, "index.html")


if __name__ == "__main__":
    ensure_settings()
    print("=" * 60)
    print("✅ SellerZone Flask backend starting")
    print("🌐 Frontend:   /")
    print("🔐 Admin:      /admin")
    print(f"🔑 Password:   {Config.ADMIN_PASSWORD}")
    print("=" * 60)
    app.run(host="0.0.0.0", port=5000, debug=True)