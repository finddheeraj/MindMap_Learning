"""OAuth client registration shared by authentication routes."""

from dataclasses import dataclass

from extensions import oauth


@dataclass(frozen=True)
class OAuthProvider:
    """Configuration shared by one OAuth provider's login flow."""

    name: str
    server_metadata_url: str
    scopes: str
    authorize_params: dict[str, str]

    @property
    def client_id_config_key(self):
        return f"{self.name.upper()}_CLIENT_ID"

    @property
    def client_secret_config_key(self):
        return f"{self.name.upper()}_CLIENT_SECRET"


GOOGLE_PROVIDER = "google"
MICROSOFT_PROVIDER = "microsoft"

OAUTH_PROVIDERS = {
    GOOGLE_PROVIDER: OAuthProvider(
        name=GOOGLE_PROVIDER,
        server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
        scopes="openid email profile https://www.googleapis.com/auth/drive.appdata",
        authorize_params={"access_type": "offline", "prompt": "consent"},
    ),
    MICROSOFT_PROVIDER: OAuthProvider(
        name=MICROSOFT_PROVIDER,
        server_metadata_url=(
            "https://login.microsoftonline.com/common/v2.0/.well-known/openid-configuration"
        ),
        scopes=(
            "openid profile email offline_access User.Read Files.ReadWrite.AppFolder"
        ),
        authorize_params={"prompt": "select_account"},
    ),
}


def get_provider(provider_name):
    """Return a supported provider configuration or ``None``."""
    return OAUTH_PROVIDERS.get(provider_name)


def register_oauth_clients():
    """Register every supported OAuth client with Authlib."""
    for provider in OAUTH_PROVIDERS.values():
        oauth.register(
            name=provider.name,
            server_metadata_url=provider.server_metadata_url,
            client_kwargs={"scope": provider.scopes},
        )
