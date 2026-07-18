"""
MindMapNode model.

Each row represents one node in a Topic's mind map. The tree
structure is stored via a self-referential `parent_id` foreign key.

`me_id` is the node id assigned by the Mind Elixir front-end library
(a client-generated string). We key upserts off (topic_id, me_id)
so that renames, drags, and additions/removals from the JS side map
cleanly onto stable database rows instead of being recreated from
scratch on every autosave.
"""

from datetime import datetime

from extensions import db


class MindMapNode(db.Model):
    __tablename__ = "mind_map_nodes"
    __table_args__ = (
        db.UniqueConstraint("topic_id", "me_id", name="uq_mind_map_node_topic_me_id"),
    )

    id = db.Column(db.Integer, primary_key=True)
    topic_id = db.Column(db.Integer, db.ForeignKey("topics.id"), nullable=False)
    parent_id = db.Column(db.Integer, db.ForeignKey("mind_map_nodes.id"), nullable=True)

    me_id = db.Column(db.String(64), nullable=False)
    title = db.Column(db.String(500), nullable=False)
    order_index = db.Column(db.Integer, default=0, nullable=False)
    expanded = db.Column(db.Boolean, default=True, nullable=False)

    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    topic = db.relationship(
        "Topic",
        backref=db.backref(
            "mind_map_nodes", cascade="all, delete-orphan", lazy="dynamic"
        ),
    )
    children = db.relationship(
        "MindMapNode",
        backref=db.backref("parent", remote_side=[id]),
        cascade="all, delete-orphan",
        order_by="MindMapNode.order_index",
    )

    def __repr__(self):
        return f"<MindMapNode id={self.id} me_id={self.me_id!r} title={self.title!r}>"
