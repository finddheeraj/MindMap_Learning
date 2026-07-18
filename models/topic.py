"""
Topic model.

A Topic is the top-level learning subject shown on the landing page
table. In later phases, a Topic will own a tree of MindMapNode rows
(the root node of its mind map).
"""

from datetime import datetime

from extensions import db


class Topic(db.Model):
    __tablename__ = "topics"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    description = db.Column(db.String(500), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    def __repr__(self):
        return f"<Topic id={self.id} name={self.name!r}>"

    def to_dict(self):
        """Serialize the topic for JSON responses (AJAX calls)."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "created_at": self.created_at.strftime("%Y-%m-%d %H:%M"),
            "updated_at": self.updated_at.strftime("%Y-%m-%d %H:%M"),
        }
