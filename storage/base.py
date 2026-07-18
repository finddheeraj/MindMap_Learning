""" Abstract interface for cloud-backed user data storage"""

from abc import ABC, abstractmethod

class StorageProvider(ABC):
    """Read and write a user's application data from their cloud storage provider."""
    
    @abstractmethod
    def load_user_data(self) -> dict:
        """Load the user's persisted data, or an empty dict if no data exists."""
        
    
    @abstractmethod
    def save_user_data(self, data: dict) -> None:
        """Persists the user's application data to their cloud storage."""