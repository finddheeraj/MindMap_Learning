"""Provider-specific identity normalization for the shared OAuth flow."""

from dataclasses import dataclass

from auth.oauth import GOOGLE_PROVIDER, MICROSOFT_PROVIDER


MICROSOFT_GRAPH_ME_URL = "https://graph.microsoft.com/v1.0/me?$select=id,mail,userPrincipalName"


class IdentityError(Exception):
    """Raised when an OAuth provider does not return a usable identity."""


@dataclass(frozen=True)
class UserIdentity:
    """The normalized identity stored in a provider mapping."""

    user_id: str
    email: str


def get_user_identity(provider_name, remote_client, token):
    """Return a normalized, verified identity for a supported provider."""
    if provider_name == GOOGLE_PROVIDER:
        return _get_google_identity(token)
    if provider_name == MICROSOFT_PROVIDER:
        return _get_microsoft_identity(remote_client)
    raise IdentityError("That sign-in provider is not supported.")


def _get_google_identity(token):
    userinfo = token.get("userinfo")
    if not userinfo or not userinfo.get("sub") or not userinfo.get("email"):
        raise IdentityError("Google did not provide the account information required to sign in.")
    if userinfo.get("email_verified") is not True:
        raise IdentityError("Google did not verify the email address for this account.")

    return UserIdentity(user_id=userinfo["sub"], email=userinfo["email"])


def _get_microsoft_identity(remote_client):
    response = remote_client.get(MICROSOFT_GRAPH_ME_URL)
    if not response.ok:
        raise IdentityError("Microsoft account information could not be retrieved. Please try again.")

    profile = response.json()
    email = profile.get("mail") or profile.get("userPrincipalName")
    if not profile.get("id") or not email:
        raise IdentityError("Microsoft did not provide the account information required to sign in.")

    return UserIdentity(user_id=profile["id"], email=email)
