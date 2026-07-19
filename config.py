"""
Application configuration.

Centralizes all configuration values so they are not scattered
throughout the codebase. Add new environments (e.g. ProductionConfig)
here as the project grows.
"""

import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DATABASE_DIR = os.path.join(BASE_DIR, "database")

def _resolve_database_url():
    """Return the database url, fixing the postgres:// -> postgresql:// prefix that Render use but SQLAlchimy rejects."""
    database_url = os.environ.get("DATABASE_URL")
    if database_url:
        if  database_url.startswith("postgres://"):
            database_url = database_url.replace("postgres://", "postgresql://", 1)
        return database_url
    return f"sqlite:///{os.path.join(DATABASE_DIR, 'learning_hub.db')}"

class Config:
    """Base configuration shared by every application environment."""

    # Used by Flask to sign session cookies / flash messages.
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-key-change-in-production")

    # SQLite database lives inside the /database folder.
    #SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL", f"sqlite:///{os.path.join(DATABASE_DIR, 'learning_hub.db')}")
    SQLALCHEMY_DATABASE_URI = _resolve_database_url()
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Google OAuth web-client credentials. Configure these as environment
    # variables; credentials must never be committed to source control.
    GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID")
    GOOGLE_CLIENT_SECRET = os.environ.get("GOOGLE_CLIENT_SECRET")

    # Microsoft Entra application credentials for Microsoft/OneDrive login.
    MICROSOFT_CLIENT_ID = os.environ.get("MICROSOFT_CLIENT_ID")
    MICROSOFT_CLIENT_SECRET = os.environ.get("MICROSOFT_CLIENT_SECRET")

    # URL-safe base64 Fernet key used to encrypt OAuth refresh tokens at rest.
    TOKEN_ENCRYPTION_KEY = os.environ.get("TOKEN_ENCRYPTION_KEY")
    
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    PERMANENT_SESSION_LIFETIME = 60 * 60 * 24 * 7  # 7 days
    WTF_CSRF_ENABLED = True

    # Ensure the database directory exists before the app starts.
    @staticmethod
    def init_app(app):
        os.makedirs(DATABASE_DIR, exist_ok=True)


class DevelopmentConfig(Config):
    """Configuration used while developing locally."""

    DEBUG = True
    SESSION_COOKIE_SECURE = False  # Allow cookies over HTTP for local dev.


class ProductionConfig(Config):
    """Configuration used when the application is deployed."""

    DEBUG = False
    SESSION_COOKIE_SECURE = True  # Only send cookies over HTTPS in production.


config = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "default": DevelopmentConfig,
}
