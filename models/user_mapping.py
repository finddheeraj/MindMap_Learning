"""Local mapping between an application user and an OAuth provider account."""

from datetime import datetime

from extensions import db


class UserMapping(db.Model):
    """Store provider identity metadata without storing application data."""

    __tablename__ = "user_mappings"
    __table_args__ = (
        db.UniqueConstraint("provider", "user_id", name="uq_user_mapping_provider_user"),
    )

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(320), nullable=False)
    provider = db.Column(db.String(32), nullable=False)
    refresh_token = db.Column(db.Text, nullable=True)
    drive_file_id = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    def __repr__(self):
        return f"<UserMapping id={self.id} provider={self.provider!r} user_id={self.user_id!r}>"
