"""Business logic for OAuth-provider user mappings."""

from extensions import db
from models import UserMapping


def get_or_create_user(*, provider, provider_user_id, email, refresh_token=None, token_cipher=None):
    """Return a mapping for an OAuth account, creating it if needed."""
    mapping = UserMapping.query.filter_by(
        provider=provider,
        user_id=provider_user_id,
    ).one_or_none()

    if mapping is None:
        mapping = UserMapping(
            provider=provider,
            user_id=provider_user_id,
            email=email,
        )
        db.session.add(mapping)
    elif mapping.email != email:
        mapping.email = email

    if refresh_token:
        if token_cipher is None:
            raise ValueError("A token cipher is required to persist a refresh token.")
        mapping.refresh_token = token_cipher.encrypt(refresh_token)

    db.session.commit()
    return mapping


def get_refresh_token(mapping, token_cipher):
    """Decrypt a mapping's refresh token only when a provider call needs it."""
    if not mapping.refresh_token:
        return None
    return token_cipher.decrypt(mapping.refresh_token)
