"""
Topic service layer.

All database queries and business rules for Topics live here.
Routes call into this module instead of talking to SQLAlchemy
directly, which keeps route handlers thin and testable.
"""
from dataclasses import dataclass
from datetime import datetime, timezone
from extensions import db
from models import Topic


class TopicValidationError(Exception):
    """Raised when incoming topic data fails validation."""



@dataclass
class TopicData:
    id: int
    name: str
    description: str
    created_at: datetime
    updated_at: datetime
    
def _now() -> datetime:
    """Return the current UTC time."""
    return datetime.now(timezone.utc)

def _topic_from_dict(d: dict) -> TopicData:
    """Convert a dictionary to a TopicData object."""
    return TopicData(
        id=d["id"],
        name=d["name"],
        description=d.get("description", ""),
        created_at=datetime.fromisoformat(d["created_at"]),
        updated_at=datetime.fromisoformat(d["updated_at"]),
    )
    
def _topic_to_dict(topic: TopicData) -> dict:
    """Convert a TopicData object to a dictionary."""
    return {
        "id": topic.id,
        "name": topic.name,
        "description": topic.description,
        "created_at": topic.created_at.isoformat(),
        "updated_at": topic.updated_at.isoformat(),
    }
    
def _validate_name(name: str) -> str:
    """Validate the topic name and return the cleaned name."""
    name = (name or "").strip()
    if not name:
        raise TopicValidationError("Topic name is required.")
    if len(name) > 150:
        raise TopicValidationError("Topic name must be 150 characters or fewer.")
    return name


def get_all_topics(storage, *, search="", sort_by="updated_at", sort_dir="desc") -> list[TopicData]:
    """
    Return all topics, optionally filtered by a search term and
    sorted by a given column/direction.
    """
    topics = storage.load_user_data().get("topics", [])
    if search:
        search_lower = search.lower()
        topics = [t for t in topics if search_lower in t["name"].lower()]
    reverse = sort_dir == "desc"
    topics = sorted(topics, key=lambda t:t.get(sort_by, ""), reverse=reverse)
    return [_topic_from_dict(t) for t in topics]

def get_topic_or_404(storage, topic_id: int) -> TopicData:
    from flask import abort
    for t in storage.load_user_data().get("topics", []):
        if t["id"] == topic_id:
            return _topic_from_dict(t)
    abort(404)


def create_topic(storage, name: str, description: str = "") -> TopicData:
    """
    Create a new topic with the given name and optional description.
    Raises TopicValidationError if the name is invalid.
    """
    name = _validate_name(name)
    description = (description or "").strip()
    
    # Shadow-write to SQLite so MindMapNode FK and mindmap_service still work
    shadow = Topic(name=name, description=description)
    db.session.add(shadow)
    db.session.flush()
    topic_id = shadow.id
    db.session.commit()
    
    now = _now()
    topic = TopicData(
        id=topic_id,
        name=name,
        description=description,
        created_at=now,
        updated_at=now
    )
    data = storage.load_user_data()
    data.setdefault("topics", []).append(_topic_to_dict(topic))
    storage.save_user_data(data)
    return topic

def update_topic(storage, topic_id: int, name: str, description: str = "") -> TopicData:
    """
    Update an existing topic with the given name and optional description.
    Raises TopicValidationError if the name is invalid.
    Raises 404 if the topic does not exist.
    """
    name = _validate_name(name)
    description = (description or "").strip()
    
    data = storage.load_user_data()
    for t in data.get("topics", []):
        if t["id"] == topic_id:
            t["name"] = name
            t["description"] = description
            t["updated_at"] = _now().isoformat()
            storage.save_user_data(data)
            # Shadow-Update
            shadow = Topic.query.get(topic_id)
            if shadow:
                shadow.name = name
                db.session.commit()
            return _topic_from_dict(t)
    from flask import abort
    abort(404)
    
def delete_topic(storage, topic_id: int) -> None:
    """
    Delete an existing topic by ID.
    Raises 404 if the topic does not exist.
    """
    data = storage.load_user_data()
    data["topics"] = [t for t in data.get("topics", []) if t["id"] != topic_id]
    storage.save_user_data(data)
    # Shadow-Delete
    shadow = Topic.query.get(topic_id)
    if shadow:
        db.session.delete(shadow)
        db.session.commit()
    
