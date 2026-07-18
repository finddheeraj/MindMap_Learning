""" Google Drive storage provider using the Drive appDataFolder"""
import json
import requests
from models import UserMapping
from storage.base import StorageProvider
from services.user_mapping_service import save_drive_file_id


_FILES_API = "https://www.googleapis.com/drive/v3/files"
_UPLOAD_API = "https://www.googleapis.com/upload/drive/v3/files"

class GoogleDriveStorage(StorageProvider):
    """ Store user data as a JSON file in the users Google Drive hiddenappDataFolder. """
    
    _DATA_FILENAME = "learning_hub_data.json"
    
    def __init__(self, access_token: str, mapping: UserMapping) -> None:
        self._access_token = access_token
        self._mapping = mapping
        
    def load_user_data(self) -> dict:
        """Load the user's persisted data, or an empty dict if no data exists."""
        file_id = self._mapping.drive_file_id
        if not file_id:
            file_id = self._find_data_file_id()
            if not file_id:
                return {}
            save_drive_file_id(self._mapping, file_id)
        return self._download_file(file_id)
    
    def save_user_data(self, data: dict) -> None:
        """Persists the user's application data to their cloud storage."""
        content = json.dumps(data).encode("utf-8")
        file_id = self._mapping.drive_file_id
        if file_id:
            self._update_file(file_id, content)
        else:
            file_id = self._create_file(content)
            save_drive_file_id(self._mapping, file_id)
            
#----------------------------------------------------------------------------
# Private Drive API helpers
#----------------------------------------------------------------------------

def _auth_headers(self) -> dict:
    return {"Authorization": f"Bearer {self._access_token}"}

def _find_data_file(self) -> str | None:
    """Return the Drive file ID of the data file, or None if it doesn't exist yet."""
    response = requests.get(
        _FILES_API,
        headers=self._auth_headers(),
        params={
            "spaces": "appDataFolder",
            "q": f"name='{self._DATA_FILENAME}'",
            "fields": "files(id)",
        },
    )
    response.raise_for_status()
    files = response.json().get("files", [])
    return files[0]["id"] if files else None

def _download_file(self, file_id: str) -> dict:
    """Fetch the file's contents and parse it as JSON."""
    response = requests.get(
        f"{_FILES_API}/{file_id}",
        headers=self._auth_headers(),
        params={"alt": "media"},
    )
    response.raise_for_status()
    return response.json()

def _create_file(self, content: bytes) -> str:
    """Create and upload a new file in the appDataFolder and return its file ID."""
    metadata = json.dumps(
        {"name": self._DATA_FILENAME, "parents": ["appDataFolder"]}
    ).encode("utf-8")
    response = requests.post(
        _UPLOAD_API,
        headers=self._auth_headers(),
        params={"uploadType": "multipart"},
        files={
            "metadata": ("metadata", metadata, "application/json; charset=UTF-8"),
            "media": ("media", content, "application/json"),
        },
    )
    response.raise_for_status()
    return response.json()["id"]

def _update_file(self, file_id: str, content: bytes) -> None:
    """Update an existing file in the appDataFolder with new content."""
    response = requests.patch(
        f"{_UPLOAD_API}/{file_id}",
        headers={**self._auth_headers(), "Content-Type": "application/json"},
        params={"uploadType": "media"},
        data=content,
    )
    response.raise_for_status()

