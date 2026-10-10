import os
import sys

port = int(os.environ.get("PORT", "5000"))

if os.name == "nt":
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "backend"))
    from app import app

    app.run(host="0.0.0.0", port=port, debug=True)
else:
    from gunicorn.app.wsgiapp import run

    os.environ["GUNICORN_CMD_ARGS"] = (
        f"--chdir backend --bind 0.0.0.0:{port} "
        "--workers 2 --timeout 120 app:app"
    )
    run()
