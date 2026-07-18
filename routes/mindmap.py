"""Mind map routes."""

from flask import Blueprint, flash, jsonify, redirect, render_template, request, session, url_for
from models import UserMapping
from services import mindmap_service, topic_service
from services.mindmap_service import MindMapValidationError
from storage import get_storage

mindmap_bp = Blueprint("mindmap", __name__)


def _current_user_and_storage():
    """Return (mapping, storage) for the logged-in user, or (None, None) if not authenticated."""
    user_id = session.get("user_id")
    if not user_id:
        return None, None
    mapping = UserMapping.query.get(user_id)
    if not mapping:
        session.clear()
        return None, None
    access_token = session.get("access_token")
    if not access_token:
        return None, None
    return mapping, get_storage(mapping, access_token)


@mindmap_bp.route("/topic/<int:topic_id>")
def view(topic_id):
    mapping, storage = _current_user_and_storage()
    if storage is None:
        flash("Please sign in to continue.", "warning")
        return redirect(url_for("topics.index"))

    topic = topic_service.get_topic_or_404(storage, topic_id)
    tree = mindmap_service.build_tree(topic)
    return render_template(
        "mindmap.html",
        topic=topic,
        initial_tree=tree
    )
    
@mindmap_bp.route("/topic/<int:topic_id>/mindmap/save", methods=["POST"])
def save(topic_id):
    mapping, storage = _current_user_and_storage()
    if storage is None:
        return jsonify({"status": "error", "message": "Not authenticated."}), 401

    payload = request.get_json(silent=True)
    if not payload or "nodeData" not in payload:
        return jsonify({"status": "error", "message": "Missing 'nodeData' in request body."}), 400

    try:
        topic = mindmap_service.save_tree(topic_id, payload["nodeData"])
    except MindMapValidationError as e:
        return jsonify({"status": "error", "message": str(e)}), 400

    return jsonify({
        "status": "ok",
        "updated_at": topic.updated_at.strftime("%d %b %Y, %H:%M")
    })