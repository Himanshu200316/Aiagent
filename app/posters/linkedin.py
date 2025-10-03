import requests
from typing import Optional


class LinkedInPoster:
    def __init__(self, credentials: dict):
        self.credentials = credentials
        self._author_urn = None

    def _ensure_author(self):
        if self._author_urn:
            return
        token = self.credentials.get("access_token")
        if not token:
            raise ValueError("LinkedIn requires access_token")
        headers = {"Authorization": f"Bearer {token}"}
        me = requests.get("https://api.linkedin.com/v2/me", headers=headers, timeout=30)
        me.raise_for_status()
        data = me.json()
        self._author_urn = data.get("id")
        if self._author_urn and not self._author_urn.startswith("urn:"):
            self._author_urn = f"urn:li:person:{self._author_urn}"

    def post(self, image_url: str, caption: str) -> str:
        # Minimal UGC post without media upload handshake (using external image URL)
        # For production you should use the media upload API to upload the image and attach the asset.
        self._ensure_author()
        token = self.credentials.get("access_token")
        headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
        body = {
            "author": self._author_urn,
            "lifecycleState": "PUBLISHED",
            "specificContent": {
                "com.linkedin.ugc.ShareContent": {
                    "shareCommentary": {"text": caption[:1300]},
                    "shareMediaCategory": "IMAGE",
                    "media": [
                        {
                            "status": "READY",
                            "originalUrl": image_url,
                            "title": {"text": "Ad"}
                        }
                    ]
                }
            },
            "visibility": {"com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"}
        }
        resp = requests.post("https://api.linkedin.com/v2/ugcPosts", headers=headers, json=body, timeout=60)
        resp.raise_for_status()
        return resp.headers.get("x-restli-id", "")
