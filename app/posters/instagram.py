from typing import Optional
from pathlib import Path

from ..config import settings


class InstagramPoster:
    def __init__(self, credentials: dict):
        self.credentials = credentials
        self.mode = settings.instagram_api_mode
        self._client = None

    def _ensure_client(self):
        if self._client is not None:
            return
        if self.mode == "instagrapi":
            from instagrapi import Client
            self._client = Client()
            username = self.credentials.get("username")
            password = self.credentials.get("password")
            if not username or not password:
                raise ValueError("Instagram instagrapi requires username/password")
            self._client.login(username, password)
        else:
            raise NotImplementedError("Graph API mode not implemented in this scaffold")

    def post_feed(self, image_path: str, caption: str) -> str:
        if self.mode != "instagrapi":
            raise NotImplementedError("Graph API feed posting not implemented here")
        self._ensure_client()
        media = self._client.photo_upload(path=image_path, caption=caption)
        return str(media.pk)

    def post_story(self, image_path: str) -> str:
        if self.mode != "instagrapi":
            raise NotImplementedError("Graph API story posting not implemented here")
        self._ensure_client()
        media = self._client.photo_upload_to_story(path=image_path)
        return str(media.pk)
