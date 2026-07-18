"""
Models package.

Import all model classes here so that `db.create_all()` in app.py
can discover every table with a single `from models import *`-style
import of this package.
"""

from .user_mapping import UserMapping

__all__ = ["UserMapping"]
