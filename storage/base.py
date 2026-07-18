""" Abstract interface for cloud-backed user data storage"""

from abc import ABC, abstractmethod

class StorageError(Exception):
    """Base exception for all cloud storage failures."""


class StorageAuthError(StorageError):
    """Provider rejected the access token (401/403) – user must re-authenticate."""


class StorageRateLimitError(StorageError):
    """Provider rate limit hit (429) – back off and retry later."""


class StorageServerError(StorageError):
    """Provider returned a 5xx response or unreadable data."""


class StorageNetworkError(StorageError):
    """Network connectivity failure reaching the provider."""

class StorageProvider(ABC):
    """Read and write a user's application data from their cloud storage provider."""
    
    @abstractmethod
    def load_user_data(self) -> dict:
        """Load the user's persisted data, or an empty dict if no data exists."""
        
    
    @abstractmethod
    def save_user_data(self, data: dict) -> None:
        """Persists the user's application data to their cloud storage."""