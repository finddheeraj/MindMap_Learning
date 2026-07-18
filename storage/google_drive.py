""" Google Drive storage provider using the Drive appDataFolder"""
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


_FILES_API = "https://www.googleapis.com/drive/v3/files"
_UPLOAD_API = "https://www.googleapis.com/upload/drive/v3/files"

class GoogleDriveStorage(StorageProvider):
    """Store user data as a JSON file in Drive's hidden appDataFolder."""

    _DATA_FILENAME = "learning_hub_data.json"

    def __init__(self, access_token: str, mapping: UserMapping) -> None:
        self.access_token = access_token
        self.mapping = mapping

    def load_user_data(self) -> dict:
        file_id = self.mapping.drive_file_id
        if not file_id:
            file_id = self._find_data_file()
            if not file_id:
                return {}
            save_drive_file_id(self.mapping, file_id)

        result = self._download_file(file_id)
        if result is None:
            # File was deleted externally – clear stale ID and start fresh.
            save_drive_file_id(self.mapping, None)
            return {}

        return result

    def save_user_data(self, data: dict) -> None:
        content = json.dumps(data).encode("utf-8")
        file_id = self.mapping.drive_file_id
        if file_id:
            self._update_file(file_id, content)
        else:
            file_id = self._create_file(content)
            save_drive_file_id(self.mapping, file_id)

    # --------------------------------------------------
    # Private Drive API helpers
    # --------------------------------------------------

    def _auth_headers(self) -> dict:
        return {"Authorization": f"Bearer {self.access_token}"}

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

    def _find_data_file(self) -> str | None:
        """Return the Drive file ID of the data file, or None if it doesn't exist yet."""
        try:
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
        except requests.HTTPError as exc:
            raise self._map_http_error(exc) from exc
        except requests.RequestException as exc:
            raise StorageNetworkError(str(exc)) from exc

        files = response.json().get("files", [])
        return files[0]["id"] if files else None

    def _download_file(self, file_id: str) -> dict | None:
        """Fetch file content as a dict, or None if the file no longer exists."""
        try:
            response = requests.get(
                f"{_FILES_API}/{file_id}",
                headers=self._auth_headers(),
                params={"alt": "media"},
            )
            if response.status_code == 404:
                return None
            response.raise_for_status()
        except requests.HTTPError as exc:
            raise self._map_http_error(exc) from exc
        except requests.RequestException as exc:
            raise StorageNetworkError(str(exc)) from exc

        try:
            return response.json()
        except ValueError as exc:
            raise StorageServerError("Drive returned unreadable data.") from exc

    def _create_file(self, content: bytes) -> str:
        """Upload a new file to appDataFolder and return its Drive file ID."""
        metadata = json.dumps({
            "name": self._DATA_FILENAME,
            "parents": ["appDataFolder"]
        }).encode("utf-8")

        try:
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
        except requests.HTTPError as exc:
            raise self._map_http_error(exc) from exc
        except requests.RequestException as exc:
            raise StorageNetworkError(str(exc)) from exc

        return response.json()["id"]

    def _update_file(self, file_id: str, content: bytes) -> None:
        """Overwrite the existing file's content in place."""
        try:
            response = requests.patch(
                f"{_UPLOAD_API}/{file_id}",
                headers={**self._auth_headers(), "Content-Type": "application/json"},
                params={"uploadType": "media"},
                data=content,
            )
            response.raise_for_status()
        except requests.HTTPError as exc:
            raise self._map_http_error(exc) from exc
        except requests.RequestException as exc:
            raise StorageNetworkError(str(exc)) from exc