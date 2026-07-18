""" Microsoft OneDrive storage provider using the special app folder"""
import json
import requests
from models import UserMapping
from storage.base import StorageProvider
from services.user_mapping_service import save_drive_file_id

_GRAPH_API = "https://graph.microsoft.com/v1.0"

class OneDriveStorage(StorageProvider):
    """ Store user data as a JSON file in the users OneDrive special app folder. """
    
    _DATA_FILENAME = "learning_hub_data.json"
    
    def __init__(self, access_token: str, mapping: UserMapping) -> None:
        self._access_token = access_token
        self._mapping = mapping
        
    def load_user_data(self) -> dict:
        """Load the user's persisted data, or an empty dict if no data exists."""
        response = requests.get(
            f"{_GRAPH_API}/me/drive/special/approot:/{self._DATA_FILENAME}:/content",
            headers=self._auth_headers(),
        )
        if response.status_code == 404:
            return {}
        response.raise_for_status()
        return response.json()
    
    def save_user_data(self, data: dict) -> None:
        """Persists the user's application data to their cloud storage."""
        content = json.dumps(data).encode("utf-8")
        response = requests.put(
            f"{_GRAPH_API}/me/drive/special/approot:/{self._DATA_FILENAME}:/content",
            headers={**self._auth_headers(), "Content-Type": "application/json"},
            data=content,
        )
        response.raise_for_status()
        if not self._mapping.drive_file_id:
            save_drive_file_id(self._mapping, response.json()["id"])
            
    def _auth_headers(self) -> dict:
        return {"Authorization": f"Bearer {self._access_token}"}
        