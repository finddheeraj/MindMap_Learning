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

from datetime import datetime

from extensions import db
from models import MindMapNode, Topic

ROOT_ME_ID = "me-root"


class MindMapValidationError(Exception):
    """Raised when an incoming mind map payload is malformed."""


def _node_to_json(node, is_root=False):
    payload = {
        "id": node.me_id,
        "topic": node.title,
        "expanded": node.expanded,
        "children": [_node_to_json(child) for child in node.children],
    }
    if is_root:
        payload["root"] = True
    return payload


def get_or_create_root(topic):
    """Return the topic's root MindMapNode, creating one if this is a brand new mind map."""
    root = MindMapNode.query.filter_by(topic_id=topic.id, parent_id=None).first()
    if root is None:
        root = MindMapNode(
            topic_id=topic.id,
            me_id=ROOT_ME_ID,
            title=topic.name,
            parent_id=None,
            order_index=0,
            expanded=True,
        )
        db.session.add(root)
        db.session.commit()
    return root


def build_tree(topic):
    """Return the full mind map for a topic as a Mind Elixir nodeData dict."""
    root = get_or_create_root(topic)
    return _node_to_json(root, is_root=True)


def _upsert_node(topic_id, node_json, parent_db_id, order_index, seen_me_ids):
    if not isinstance(node_json, dict):
        raise MindMapValidationError("Each node must be an object.")

    me_id = node_json.get("id")
    if not me_id or not isinstance(me_id, str):
        raise MindMapValidationError("Every node requires a string 'id'.")

    title = (node_json.get("topic") or "").strip() or "Untitled"
    expanded = bool(node_json.get("expanded", True))

    seen_me_ids.add(me_id)

    node = MindMapNode.query.filter_by(topic_id=topic_id, me_id=me_id).first()
    if node is None:
        node = MindMapNode(topic_id=topic_id, me_id=me_id)
        db.session.add(node)

    node.title = title[:500]
    node.expanded = expanded
    node.parent_id = parent_db_id
    node.order_index = order_index
    db.session.flush()  # assign node.id so children can reference it as parent_db_id

    children = node_json.get("children") or []
    if not isinstance(children, list):
        raise MindMapValidationError("A node's 'children' must be a list.")

    for index, child_json in enumerate(children):
        _upsert_node(topic_id, child_json, node.id, index, seen_me_ids)


def save_tree(topic_id, root_node_json):
    """
    Persist a full mind map tree for a topic.

    Upserts every node present in the incoming tree (matched by the
    Mind Elixir `me_id`), then deletes any existing rows for the
    topic that were not present (i.e. nodes removed on the client).
    """
    topic = Topic.query.get_or_404(topic_id)

    seen_me_ids = set()
    _upsert_node(topic_id, root_node_json, None, 0, seen_me_ids)

    stale_nodes = MindMapNode.query.filter(
        MindMapNode.topic_id == topic_id,
        ~MindMapNode.me_id.in_(seen_me_ids),
    ).all()
    for node in stale_nodes:
        db.session.delete(node)

    # The root node's topic text IS the topic name - keep them in sync if
    # the user renamed the root node directly inside the mind map.
    root = MindMapNode.query.filter_by(topic_id=topic_id, parent_id=None).first()
    if root and root.title != topic.name:
        topic.name = root.title

    # Keep the topic's "Last Updated" column in sync with mind map edits.
    topic.updated_at = datetime.utcnow()

    db.session.commit()
    return topic
