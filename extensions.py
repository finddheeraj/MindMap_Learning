"""
Shared Flask extension instances.

Kept in their own module (separate from app.py) so that models,
routes, and services can import `db` without causing circular imports.
"""

from authlib.integrations.flask_client import OAuth
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()
oauth = OAuth()
