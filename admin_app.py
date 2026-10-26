from flask import Flask, redirect, url_for
from admin_backend import register_admin_routes

app = Flask(__name__)
register_admin_routes(app)

@app.route("/")
def admin_home():
    return redirect(url_for("admin_page"))

if __name__ == "__main__":
    import os
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", "10000")))
