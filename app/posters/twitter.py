import os
from typing import Optional

import tweepy


class TwitterPoster:
    def __init__(self, credentials: dict):
        self.credentials = credentials
        self.client_v1 = None

    def _ensure_client(self):
        if self.client_v1 is not None:
            return
        api_key = self.credentials.get("api_key")
        api_secret = self.credentials.get("api_secret")
        access_token = self.credentials.get("access_token")
        access_token_secret = self.credentials.get("access_token_secret")
        if not all([api_key, api_secret, access_token, access_token_secret]):
            raise ValueError("Twitter credentials require api_key, api_secret, access_token, access_token_secret")
        auth = tweepy.OAuth1UserHandler(api_key, api_secret, access_token, access_token_secret)
        self.client_v1 = tweepy.API(auth)

    def post(self, image_path: str, caption: str) -> str:
        self._ensure_client()
        media = self.client_v1.media_upload(filename=image_path)
        status = self.client_v1.update_status(status=caption[:280], media_ids=[media.media_id_string])
        return str(status.id)
