"""
Shared Flask extension instances.

Kept in their own module (separate from app.py) so that models,
routes, and services can import `db` without causing circular imports.
"""

from authlib.integrations.flask_client import OAuth
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFProtect

db = SQLAlchemy()
oauth = OAuth()
csrf = CSRFProtect()
