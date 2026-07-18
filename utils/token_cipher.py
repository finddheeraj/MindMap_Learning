"""Fernet encryption for OAuth refresh tokens stored in the local database."""

from cryptography.fernet import Fernet, InvalidToken


class TokenEncryptionConfigurationError(Exception):
    """Raised when a usable Fernet key has not been configured."""


class TokenDecryptionError(Exception):
    """Raised when an encrypted token cannot be decrypted safely."""


class TokenCipher:
    """Encrypt and decrypt refresh tokens with a configured Fernet key."""

    def __init__(self, encryption_key):
        if not encryption_key:
            raise TokenEncryptionConfigurationError(
                "TOKEN_ENCRYPTION_KEY must be configured before OAuth sign-in is enabled."
            )

        try:
            self._fernet = Fernet(encryption_key.encode("utf-8"))
        except (TypeError, ValueError) as error:
            raise TokenEncryptionConfigurationError(
                "TOKEN_ENCRYPTION_KEY is not a valid Fernet key."
            ) from error

    def encrypt(self, refresh_token):
        """Return an encrypted, database-safe representation of a refresh token."""
        return self._fernet.encrypt(refresh_token.encode("utf-8")).decode("utf-8")

    def decrypt(self, encrypted_refresh_token):
        """Return plaintext only at the point a provider request requires it."""
        try:
            return self._fernet.decrypt(encrypted_refresh_token.encode("utf-8")).decode("utf-8")
        except (InvalidToken, UnicodeDecodeError) as error:
            raise TokenDecryptionError("The stored refresh token cannot be decrypted.") from error
