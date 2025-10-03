from typing import Optional
import os
import requests

from ..config import settings


def generate_caption(product_description: str, tone: str, target_audience: str) -> str:
    if settings.openai_api_key:
        try:
            return _generate_caption_openai(product_description, tone, target_audience)
        except Exception:
            pass
    # Fallback simple template
    return (
        f"Discover {product_description}! Designed for {target_audience}. "
        f"Experience the difference today. #New #MustHave"
    )


def _generate_caption_openai(product_description: str, tone: str, target_audience: str) -> str:
    # Minimal call to OpenAI chat completions API via REST to avoid SDK dependency
    url = "https://api.openai.com/v1/chat/completions"
    headers = {"Authorization": f"Bearer {settings.openai_api_key}", "Content-Type": "application/json"}
    prompt = (
        "You are an expert ad copywriter. Write a concise social media caption "
        "(max 2200 chars, 3 short sentences, 3-5 relevant hashtags) with a clear CTA. "
        f"Tone: {tone}. Target audience: {target_audience}. Product/service: {product_description}."
    )
    body = {
        "model": "gpt-4o-mini",
        "messages": [
            {"role": "system", "content": "You generate concise, catchy social captions."},
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.7,
    }
    resp = requests.post(url, headers=headers, json=body, timeout=60)
    resp.raise_for_status()
    data = resp.json()
    return data["choices"][0]["message"]["content"].strip()
