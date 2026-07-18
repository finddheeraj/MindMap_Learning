""" Microsoft OneDrive storage provider using the special app folder"""

from models import UserMapping
from storage.base import StorageProvider

class OneDriveStorage(StorageProvider):
    """ Store user data as a JSON file in the users OneDrive special app folder. """
    
    _DATA_FILENAME = "learning_hub_data.json"
    
    def __init__(self, access_token: str, mapping: UserMapping) -> None:
        self._access_token = access_token
        self._mapping = mapping
        
    def load_user_data(self) -> dict:
        """Load the user's persisted data, or an empty dict if no data exists."""
        # Implementation to load user data from OneDrive using the access token and mapping
        raise NotImplementedError("load_user_data method is not implemented yet.")
    
    def save_user_data(self, data: dict) -> None:
        """Persists the user's application data to their cloud storage."""
        # Implementation to save user data to OneDrive using the access token and mapping
        raise NotImplementedError("save_user_data method is not implemented yet.")