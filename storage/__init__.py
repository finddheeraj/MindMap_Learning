"""Cloud-data serialization and storage abstractions."""

from models.user_mapping import UserMapping
from storage.base import StorageProvider
from storage.google_drive import GoogleDriveStorage
from storage.onedrive import OneDriveStorage

_PROVIDERS = {
    "google": GoogleDriveStorage,
    "microsoft": OneDriveStorage,
}

def get_storage(mapping: "UserMapping", access_token: str) -> StorageProvider:
    """Return the correct StorageProvider for a user's OAUTH Provider."""
    cls = _PROVIDERS.get(mapping.provider)
    if cls is None:
        raise ValueError(f"Unsupported provider: {mapping.provider}")
    return cls(access_token=access_token, mapping=mapping)