"""Multi-provider OAuth authentication routes."""
import time
from authlib.integrations.base_client.errors import OAuthError
from flask import Blueprint, current_app, flash, redirect, session, url_for

from auth.identity import IdentityError, get_user_identity
from auth.oauth import get_provider
from extensions import oauth
from services.user_mapping_service import get_or_create_user
from utils.token_cipher import TokenEncryptionConfigurationError, TokenCipher


auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/login/<provider_name>")
def login(provider_name):
    """Redirect a visitor to the selected provider's consent screen."""
    provider = get_provider(provider_name)
    if provider is None:
        return _redirect_to_home_with_error("That sign-in provider is not supported.")
    if not _oauth_is_configured(provider):
        return _redirect_to_home_with_error(
            f"{provider.name.title()} login is not configured on this server."
        )
    if not _token_encryption_is_configured():
        return _redirect_to_home_with_error(
            "Secure token storage is not configured on this server."
        )

    redirect_uri = url_for("auth.oauth_callback", provider_name=provider.name, _external=True)
    remote_client = getattr(oauth, provider.name)
    return remote_client.authorize_redirect(redirect_uri, **provider.authorize_params)


@auth_bp.route("/auth/<provider_name>/callback")
def oauth_callback(provider_name):
    """Complete provider sign-in and persist the local account mapping."""
    provider = get_provider(provider_name)
    if provider is None:
        return _redirect_to_home_with_error("That sign-in provider is not supported.")
    if not _oauth_is_configured(provider):
        return _redirect_to_home_with_error(
            f"{provider.name.title()} login is not configured on this server."
        )
    try:
        token_cipher = _get_token_cipher()
    except TokenEncryptionConfigurationError:
        return _redirect_to_home_with_error(
            "Secure token storage is not configured on this server."
        )

    remote_client = getattr(oauth, provider.name)
    try:
        token = remote_client.authorize_access_token()
        identity = get_user_identity(provider.name, remote_client, token)
    except OAuthError:
        return _redirect_to_home_with_error(
            f"{provider.name.title()} sign-in could not be completed. Please try again."
        )
    except IdentityError as error:
        return _redirect_to_home_with_error(str(error))

    mapping = get_or_create_user(
        provider=provider.name,
        provider_user_id=identity.user_id,
        email=identity.email,
        refresh_token=token.get("refresh_token"),
        token_cipher=token_cipher,
    )
    session["access_token"] = token.get("access_token")
    session["user_id"] = mapping.id
    session.permanent = True
    session["provider"] = mapping.provider
    session["access_token_expires_at"] = time.time() + token.get("expires_in", 3600)
    flash(f"Signed in with {provider.name.title()}.", "success")
    return redirect(url_for("topics.index"))


def _oauth_is_configured(provider):
    """Return whether both configured client credentials are available."""
    return bool(
        current_app.config[provider.client_id_config_key]
        and current_app.config[provider.client_secret_config_key]
    )


def _token_encryption_is_configured():
    """Return whether the configured key can safely encrypt persisted tokens."""
    try:
        _get_token_cipher()
    except TokenEncryptionConfigurationError:
        return False
    return True


def _get_token_cipher():
    """Create a cipher only when refresh-token persistence is needed."""
    return TokenCipher(current_app.config["TOKEN_ENCRYPTION_KEY"])


def _redirect_to_home_with_error(message):
    """Display an authentication error without exposing provider details."""
    flash(message, "danger")
    return redirect(url_for("topics.index"))
