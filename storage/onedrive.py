""" Microsoft OneDrive storage provider using the special app folder"""
import json
import requests
from models import UserMapping
from storage.base import (
    StorageAuthError,
    StorageNetworkError,
    StorageRateLimitError,
    StorageServerError,
    StorageProvider,
)
from services.user_mapping_service import save_drive_file_id

_GRAPH_API = "https://graph.microsoft.com/v1.0"

class OneDriveStorage(StorageProvider):
    """ Store user data as a JSON file in the users OneDrive special app folder. """
    
    _DATA_FILENAME = "learning_hub_data.json"
    
    def __init__(self, access_token: str, mapping: UserMapping) -> None:
        self._access_token = access_token
        self._mapping = mapping
        
    def load_user_data(self) -> dict:
        try:
            response = requests.get(
                f"{_GRAPH_API}/me/drive/special/approot:/{self._DATA_FILENAME}:/content",
                headers=self._auth_headers(),
            )
            if response.status_code == 404:
                return {}
            response.raise_for_status()
        except requests.HTTPError as exc:
            raise self._map_http_error(exc) from exc
        except requests.RequestException as exc:
            raise StorageNetworkError(str(exc)) from exc

        try:
            return response.json()
        except ValueError as exc:
            raise StorageServerError("OneDrive returned unreadable data.") from exc
    
    def save_user_data(self, data: dict) -> None:
        content = json.dumps(data).encode("utf-8")
        try:
            response = requests.put(
                f"{_GRAPH_API}/me/drive/special/approot:/{self._DATA_FILENAME}:/content",
                headers={**self._auth_headers(), "Content-Type": "application/json"},
                data=content,
            )
            response.raise_for_status()
        except requests.HTTPError as exc:
            raise self._map_http_error(exc) from exc
        except requests.RequestException as exc:
            raise StorageNetworkError(str(exc)) from exc

        if not self.mapping.drive_file_id:
            save_drive_file_id(self.mapping, response.json()["id"])
            
    def _auth_headers(self) -> dict:
        return {"Authorization": f"Bearer {self._access_token}"}
    
    @staticmethod
    def _map_http_error(exc: requests.HTTPError) -> Exception:
        status = exc.response.status_code if exc.response is not None else 0
        if status in (401, 403):
            return StorageAuthError(str(exc))
        if status == 429:
            return StorageRateLimitError(str(exc))
        if status >= 500:
            return StorageServerError(str(exc))
        return StorageServerError(str(exc))
        