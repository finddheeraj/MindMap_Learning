"""Automatic access-token refresh using stored refresh tokens."""

import time
import requests
from flask import current_app, session

from services.user_mapping_service import get_refresh_token, update_refresh_token
from utils.token_cipher import TokenCipher

_GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
_MICROSOFT_TOKEN_URL = "https://login.microsoftonline.com/common/oauth2/v2.0/token"
_MICROSOFT_SCOPES = "openid profile email offline_access User.Read Files.ReadWrite.AppFolder"

# Refresh this many seconds before the token actually expires to avoid edge-case failures.
_EXPIRY_BUFFER_SECONDS = 60


class TokenRefreshError(Exception):
    """Raised when an access token cannot be refreshed."""


def get_valid_access_token(mapping, token_cipher: TokenCipher) -> str:
    """Return a valid access token, transparently refreshing it if expired."""
    expires_at = session.get("access_token_expires_at", 0)
    access_token = session.get("access_token")

    if access_token and time.time() < expires_at - _EXPIRY_BUFFER_SECONDS:
        return access_token

    refresh_token = get_refresh_token(mapping, token_cipher)
    if not refresh_token:
        raise TokenRefreshError("No refresh token stored for this account.")

    try:
        if mapping.provider == "google":
            new_tokens = _refresh_google(refresh_token)
        elif mapping.provider == "microsoft":
            new_tokens = _refresh_microsoft(refresh_token)
        else:
            raise TokenRefreshError(f"Unknown provider: {mapping.provider!r}")

    except requests.HTTPError as exc:
        raise TokenRefreshError(f"Provider rejected the refresh request: {exc}") from exc
    except requests.RequestException as exc:
        raise TokenRefreshError(f"Network error during token refresh: {exc}") from exc

    session["access_token"] = new_tokens["access_token"]
    session["access_token_expires_at"] = time.time() + new_tokens.get("expires_in", 3600)

    # Microsoft always rotates the refresh token; Google does so only when rotation is enabled.
    if "refresh_token" in new_tokens:
        update_refresh_token(mapping, new_tokens["refresh_token"], token_cipher)

    return new_tokens["access_token"]

def _refresh_google(refresh_token: str) -> dict:
    config = current_app.config
    response = requests.post(
        _GOOGLE_TOKEN_URL,
        data={
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
            "client_id": config["GOOGLE_CLIENT_ID"],
            "client_secret": config["GOOGLE_CLIENT_SECRET"],
        },
    )
    response.raise_for_status()
    return response.json()


def _refresh_microsoft(refresh_token: str) -> dict:
    config = current_app.config
    response = requests.post(
        _MICROSOFT_TOKEN_URL,
        data={
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
            "client_id": config["MICROSOFT_CLIENT_ID"],
            "client_secret": config["MICROSOFT_CLIENT_SECRET"],
            "scope": _MICROSOFT_SCOPES,
        },
    )
    response.raise_for_status()
    return response.json()