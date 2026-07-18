"""
Application entry point.

Run with:
    python app.py

Uses the Flask application factory pattern so the app can be
configured differently for testing/production later without
changing this file.
"""

import os

from flask import Flask, render_template

from config import config
from extensions import db, oauth


def create_app(config_name=None):
    config_name = config_name or os.environ.get("FLASK_ENV", "development")

    app = Flask(__name__)
    app.config.from_object(config[config_name])
    config[config_name].init_app(app)

    db.init_app(app)
    oauth.init_app(app)

    register_blueprints(app)
    register_error_handlers(app)

    with app.app_context():
        # Import models so SQLAlchemy is aware of them before create_all().
        from models import UserMapping  # noqa: F401

        db.create_all()

    return app


def register_blueprints(app):
    from auth.oauth import register_oauth_clients
    from auth.routes import auth_bp
    from routes.topics import topics_bp
    from routes.mindmap import mindmap_bp

    register_oauth_clients()
    app.register_blueprint(auth_bp)
    app.register_blueprint(topics_bp)
    app.register_blueprint(mindmap_bp)


def register_error_handlers(app):
    from flask import flash, jsonify, redirect, request, session, url_for
    from storage.base import StorageAuthError, StorageNetworkError, StorageRateLimitError, StorageServerError

    @app.errorhandler(404)
    def not_found(error):
        return render_template("errors/404.html"), 404

    @app.errorhandler(500)
    def server_error(error):
        return render_template("errors/500.html"), 500

    @app.errorhandler(StorageAuthError)
    def handle_storage_auth_error(error):
        if request.is_json:
            return jsonify({"status": "error", "message": "Cloud storage access was revoked. Please sign in again."}), 401
        flash("Your cloud storage access was revoked. Please sign in again.", "danger")
        session.clear()
        return redirect(url_for("topics.index"))

    @app.errorhandler(StorageRateLimitError)
    def handle_storage_rate_limit(error):
        if request.is_json:
            return jsonify({"status": "error", "message": "Cloud storage rate limit reached. Please try again shortly."}), 429
        flash("Cloud storage rate limit reached. Please try again shortly.", "warning")
        return redirect(url_for("topics.index"))

    @app.errorhandler(StorageServerError)
    def handle_storage_server_error(error):
        if request.is_json:
            return jsonify({"status": "error", "message": "Cloud storage returned an error. Please try again."}), 502
        flash("Cloud storage returned an error. Please try again.", "danger")
        return redirect(url_for("topics.index"))

    @app.errorhandler(StorageNetworkError)
    def handle_storage_network_error(error):
        if request.is_json:
            return jsonify({"status": "error", "message": "Could not reach cloud storage. Please check your connection."}), 503
        flash("Could not reach cloud storage. Please check your connection.", "danger")
        return redirect(url_for("topics.index"))


app = create_app()

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
