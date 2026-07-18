"""
Topic service layer.

All database queries and business rules for Topics live here.
Routes call into this module instead of talking to SQLAlchemy
directly, which keeps route handlers thin and testable.
"""

from extensions import db
from models import Topic


class TopicValidationError(Exception):
    """Raised when incoming topic data fails validation."""


def get_all_topics(search=None, sort_by="updated_at", sort_dir="desc"):
    """
    Return all topics, optionally filtered by a search term and
    sorted by a given column/direction.
    """
    query = Topic.query

    if search:
        like_pattern = f"%{search.strip()}%"
        query = query.filter(Topic.name.ilike(like_pattern))

    sort_columns = {
        "name": Topic.name,
        "created_at": Topic.created_at,
        "updated_at": Topic.updated_at,
    }
    column = sort_columns.get(sort_by, Topic.updated_at)
    column = column.desc() if sort_dir == "desc" else column.asc()

    return query.order_by(column).all()


def get_topic_or_404(topic_id):
    return Topic.query.get_or_404(topic_id)


def create_topic(name, description=None):
    name = (name or "").strip()
    if not name:
        raise TopicValidationError("Topic name is required.")
    if len(name) > 150:
        raise TopicValidationError("Topic name must be 150 characters or fewer.")

    topic = Topic(name=name, description=(description or "").strip() or None)
    db.session.add(topic)
    db.session.commit()
    return topic


def update_topic(topic_id, name, description=None):
    topic = get_topic_or_404(topic_id)

    name = (name or "").strip()
    if not name:
        raise TopicValidationError("Topic name is required.")
    if len(name) > 150:
        raise TopicValidationError("Topic name must be 150 characters or fewer.")

    topic.name = name
    topic.description = (description or "").strip() or None
    db.session.commit()
    return topic


def delete_topic(topic_id):
    topic = get_topic_or_404(topic_id)
    db.session.delete(topic)
    db.session.commit()
