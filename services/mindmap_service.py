"""
Mind map service layer.

Converts between our relational MindMapNode rows and the JSON tree
shape the Mind Elixir front-end library expects/produces, e.g.:

    {
        "id": "me-root",
        "topic": "Machine Learning",
        "root": True,
        "expanded": True,
        "children": [
            {"id": "abc123", "topic": "Supervised Learning", "expanded": True, "children": []}
        ]
    }
"""

from datetime import datetime, timezone
from services.topic_service import TopicData

_ROOT_ME_ID = "me-root"


class MindMapValidationError(Exception):
    """Raised when an incoming mind map payload is malformed."""


def build_tree(storage, topic: TopicData) -> dict:
    """Return the Mind Elixir nodeData for a topic, creating a default if none exists yet."""
    data = storage.load_user_data()
    tree = data.get("mind_maps", {}).get(str(topic.id))
    if tree is not None:
        return tree

    tree = {
        "id": _ROOT_ME_ID,
        "topic": topic.name,
        "root": True,
        "expanded": True,
        "children": [],
    }

    data.setdefault("mind_maps", {})[str(topic.id)] = tree
    storage.save_user_data(data)
    return tree


def save_tree(storage, topic_id: int, root_node_json: dict) -> TopicData:
    """Persist the full mind map tree and return the updated TopicData."""
    if not isinstance(root_node_json, dict) or not root_node_json.get("id"):
        raise MindMapValidationError("Root node must be an object with an 'id'.")

    data = storage.load_user_data()

    topic_dict = next((t for t in data.get("topics", []) if t["id"] == topic_id), None)
    if topic_dict is None:
        from flask import abort
        abort(404)

    root_title = (root_node_json.get("topic") or "").strip()
    if root_title and root_title != topic_dict["name"]:
        topic_dict["name"] = root_title

    now = datetime.now(timezone.utc).isoformat()
    topic_dict["updated_at"] = now

    data.setdefault("mind_maps", {})[str(topic_id)] = root_node_json
    storage.save_user_data(data)

    return TopicData(
        id=topic_dict["id"],
        name=topic_dict["name"],
        description=topic_dict.get("description", ""),
        created_at=datetime.fromisoformat(topic_dict["created_at"]),
        updated_at=datetime.fromisoformat(topic_dict["updated_at"]),
    )