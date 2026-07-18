"""
Models package.

Import all model classes here so that `db.create_all()` in app.py
can discover every table with a single `from models import *`-style
import of this package.
"""

from .topic import Topic
from .mind_map_node import MindMapNode
from .user_mapping import UserMapping

__all__ = ["Topic", "MindMapNode", "UserMapping"]
