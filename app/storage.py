import base64
import json
import os
import threading
from pathlib import Path
from typing import Any, Dict, List, Optional

from cryptography.fernet import Fernet

from .config import settings


_lock = threading.Lock()


def _ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def _get_fernet() -> Optional[Fernet]:
    key = settings.encryption_key
    if not key:
        return None
    try:
        # The key must be in base64 urlsafe format. Accept raw 32 bytes hex too.
        if len(key) == 44 and key.endswith("="):
            f_key = key.encode()
        else:
            # try to interpret as hex and convert to urlsafe base64
            raw = bytes.fromhex(key)
            f_key = base64.urlsafe_b64encode(raw)
        return Fernet(f_key)
    except Exception:
        return None


def _encrypt(data: bytes) -> bytes:
    f = _get_fernet()
    if f is None:
        return data
    return f.encrypt(data)


def _decrypt(data: bytes) -> bytes:
    f = _get_fernet()
    if f is None:
        return data
    return f.decrypt(data)


class Storage:
    def __init__(self, root: Optional[str] = None) -> None:
        self.root = Path(root or settings.data_dir)
        _ensure_dir(self.root)

    def _user_dir(self, user_id: str) -> Path:
        path = self.root / "users" / user_id
        _ensure_dir(path)
        return path

    def save_credentials(self, user_id: str, platform: str, data: Dict[str, Any]) -> None:
        user_dir = self._user_dir(user_id)
        cred_dir = user_dir / "credentials"
        _ensure_dir(cred_dir)
        file = cred_dir / f"{platform}.json.enc"
        payload = json.dumps(data, indent=2).encode()
        enc = _encrypt(payload)
        with _lock:
            file.write_bytes(enc)

    def load_credentials(self, user_id: str, platform: str) -> Optional[Dict[str, Any]]:
        file = self._user_dir(user_id) / "credentials" / f"{platform}.json.enc"
        if not file.exists():
            return None
        with _lock:
            data = _decrypt(file.read_bytes())
        return json.loads(data.decode())

    def save_prompt(self, user_id: str, prompt_key: str, record: Dict[str, Any]) -> None:
        file = self._user_dir(user_id) / "prompts.json"
        prompts: Dict[str, Any] = {}
        if file.exists():
            prompts = json.loads(file.read_text())
        prompts[prompt_key] = record
        with _lock:
            file.write_text(json.dumps(prompts, indent=2))

    def prompt_exists(self, user_id: str, prompt_key: str) -> bool:
        file = self._user_dir(user_id) / "prompts.json"
        if not file.exists():
            return False
        prompts = json.loads(file.read_text())
        return prompt_key in prompts

    def append_history(self, user_id: str, entry: Dict[str, Any]) -> None:
        file = self._user_dir(user_id) / "history.json"
        history: List[Dict[str, Any]] = []
        if file.exists():
            history = json.loads(file.read_text())
        history.append(entry)
        with _lock:
            file.write_text(json.dumps(history, indent=2))

    def list_history(self, user_id: str) -> List[Dict[str, Any]]:
        file = self._user_dir(user_id) / "history.json"
        if not file.exists():
            return []
        return json.loads(file.read_text())

    def save_image(self, user_id: str, image_bytes: bytes, suffix: str = ".png") -> str:
        img_dir = self._user_dir(user_id) / "images"
        _ensure_dir(img_dir)
        # Simple deterministic-ish name to avoid duplicates
        import hashlib
        digest = hashlib.sha256(image_bytes).hexdigest()[:16]
        path = img_dir / f"{digest}{suffix}"
        with _lock:
            path.write_bytes(image_bytes)
        return str(path)

    def get_uploaded_image_path(self, user_id: str, image_id: str) -> Optional[str]:
        img_path = self._user_dir(user_id) / "images" / image_id
        if img_path.exists():
            return str(img_path)
        return None

    def save_schedule(self, user_id: str, hour: int, minute: int, timezone: str) -> None:
        file = self._user_dir(user_id) / "schedule.json"
        with _lock:
            file.write_text(json.dumps({"hour": hour, "minute": minute, "timezone": timezone}, indent=2))

    def get_schedule(self, user_id: str) -> Dict[str, Any]:
        file = self._user_dir(user_id) / "schedule.json"
        if not file.exists():
            return {"hour": settings.default_post_hour, "minute": settings.default_post_minute, "timezone": settings.default_timezone}
        return json.loads(file.read_text())

    def list_users(self) -> List[str]:
        users_root = self.root / "users"
        if not users_root.exists():
            return []
        return [p.name for p in users_root.iterdir() if p.is_dir()]
