"""
Mind map routes.

`GET /topic/<id>` renders the interactive mind map page for a topic.
`POST /topic/<id>/mindmap/save` accepts the full current tree (as
produced by Mind Elixir's `getData().nodeData`) and persists it.
"""

from flask import Blueprint, render_template, request, jsonify

from services import topic_service, mindmap_service
from services.mindmap_service import MindMapValidationError

mindmap_bp = Blueprint("mindmap", __name__)


@mindmap_bp.route("/topic/<int:topic_id>")
def view(topic_id):
    topic = topic_service.get_topic_or_404(topic_id)
    tree = mindmap_service.build_tree(topic)
    return render_template("mindmap.html", topic=topic, initial_tree=tree)


@mindmap_bp.route("/topic/<int:topic_id>/mindmap/save", methods=["POST"])
def save(topic_id):
    payload = request.get_json(silent=True)
    if not payload or "nodeData" not in payload:
        return jsonify({"status": "error", "message": "Missing 'nodeData' in request body."}), 400

    try:
        topic = mindmap_service.save_tree(topic_id, payload["nodeData"])
    except MindMapValidationError as e:
        return jsonify({"status": "error", "message": str(e)}), 400

    return jsonify(
        {
            "status": "ok",
            "updated_at": topic.updated_at.strftime("%d %b %Y, %H:%M"),
        }
    )
