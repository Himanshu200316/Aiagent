from typing import Optional
import io
import requests
from PIL import Image, ImageDraw, ImageFont

from ..config import settings


def generate_image(product_description: str, tone: str, target_audience: str) -> bytes:
    # Prefer OpenAI images if available; fallback to Stability; then to placeholder
    if settings.openai_api_key:
        try:
            img = _generate_openai_image(product_description, tone, target_audience)
            if img:
                return img
        except Exception:
            pass
    if settings.stability_api_key:
        try:
            img = _generate_stability_image(product_description, tone, target_audience)
            if img:
                return img
        except Exception:
            pass
    return _generate_placeholder_image(product_description)


def _generate_openai_image(product_description: str, tone: str, target_audience: str) -> Optional[bytes]:
    url = "https://api.openai.com/v1/images/generations"
    headers = {"Authorization": f"Bearer {settings.openai_api_key}", "Content-Type": "application/json"}
    prompt = f"An eye-catching ad image for {product_description}, tone {tone}, targeting {target_audience}."
    body = {"model": "gpt-image-1", "prompt": prompt, "size": "1024x1024"}
    resp = requests.post(url, headers=headers, json=body, timeout=120)
    resp.raise_for_status()
    data = resp.json()
    b64 = data["data"][0]["b64_json"]
    import base64
    return base64.b64decode(b64)


def _generate_stability_image(product_description: str, tone: str, target_audience: str) -> Optional[bytes]:
    # Stability REST example (text-to-image) using SDXL
    url = "https://api.stability.ai/v1/generation/stable-diffusion-xl-1024-v1-0/text-to-image"
    headers = {"Authorization": f"Bearer {settings.stability_api_key}"}
    prompt = f"An eye-catching ad image for {product_description}, tone {tone}, targeting {target_audience}."
    form = {"text_prompts[0][text]": prompt, "cfg_scale": 7, "height": 1024, "width": 1024, "samples": 1}
    resp = requests.post(url, headers=headers, files={}, data=form, timeout=120)
    if resp.status_code != 200:
        resp.raise_for_status()
    # Stability returns an artifacts list with base64 values in JSON for some endpoints; for others it's multipart
    try:
        data = resp.json()
        import base64
        return base64.b64decode(data["artifacts"][0]["base64"])  # type: ignore[index]
    except Exception:
        return None


def _generate_placeholder_image(title: str) -> bytes:
    img = Image.new("RGB", (1024, 1024), color=(245, 245, 245))
    draw = ImageDraw.Draw(img)
    text = f"AD: {title[:60]}" if title else "AD"
    # Load default font
    try:
        font = ImageFont.load_default()
    except Exception:
        font = None
    draw.rectangle([(40, 40), (984, 984)], outline=(0, 0, 0), width=6)
    draw.text((80, 480), text, fill=(0, 0, 0), font=font)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()
