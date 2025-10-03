import hashlib
from typing import Dict, Optional


def build_prompt_key(
    product_description: str,
    tone: str,
    target_audience: str,
    platform: str,
    salt: Optional[str] = None,
) -> str:
    key_raw = f"{product_description}|{tone}|{target_audience}|{platform}"
    if salt:
        key_raw = key_raw + f"|{salt}"
    return hashlib.sha256(key_raw.encode()).hexdigest()
