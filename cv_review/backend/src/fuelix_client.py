"""Fuelix API client - OpenAI-compatible chat completions."""
import os
from typing import Iterator, List, Optional

import requests

DEFAULT_BASE_URL = "https://api.fuelix.ai/v1"


def _message_to_role_content(msg: dict) -> tuple:
    role = (msg.get("role") or "user").strip().lower()
    if role not in ("system", "user", "assistant"):
        role = "user"
    content = msg.get("content") or ""
    return role, str(content)


def chat_completion(
    messages: List[dict],
    *,
    model: str,
    api_key: Optional[str] = None,
    base_url: Optional[str] = None,
    timeout: int = 120,
    temperature: Optional[float] = None,
) -> dict:
    """
    Call Fuelix chat completions API.
    messages: list of {"role": "user"|"assistant"|"system", "content": "..."}
    temperature: lower (e.g. 0.1–0.2) for more consistent, accurate evaluation.
    """
    api_key = api_key or os.getenv("FUELIX_API_KEY") or os.getenv("FUELIX_SECRET_TOKEN")
    base_url = (base_url or os.getenv("FUELIX_BASE_URL") or DEFAULT_BASE_URL).rstrip("/")
    if not api_key:
        raise ValueError("FUELIX_API_KEY or FUELIX_SECRET_TOKEN must be set")

    url = f"{base_url}/chat/completions"
    payload = {
        "model": model,
        "messages": [{"role": m.get("role", "user"), "content": m.get("content", "")} for m in messages],
    }
    if temperature is not None:
        payload["temperature"] = max(0.0, min(2.0, float(temperature)))
    resp = requests.post(
        url,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        },
        json=payload,
        timeout=timeout,
    )
    resp.raise_for_status()
    return resp.json()


def chat_completion_stream(
    messages: List[dict],
    *,
    model: str,
    api_key: Optional[str] = None,
    base_url: Optional[str] = None,
    timeout: int = 120,
) -> Iterator[str]:
    """Stream chat completion chunks (SSE)."""
    api_key = api_key or os.getenv("FUELIX_API_KEY") or os.getenv("FUELIX_SECRET_TOKEN")
    base_url = (base_url or os.getenv("FUELIX_BASE_URL") or DEFAULT_BASE_URL).rstrip("/")
    if not api_key:
        raise ValueError("FUELIX_API_KEY or FUELIX_SECRET_TOKEN must be set")

    url = f"{base_url}/chat/completions"
    payload = {
        "model": model,
        "messages": [{"role": m.get("role", "user"), "content": m.get("content", "")} for m in messages],
        "stream": True,
    }
    with requests.post(
        url,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        },
        json=payload,
        stream=True,
        timeout=timeout,
    ) as r:
        r.raise_for_status()
        for line in r.iter_lines(decode_unicode=True):
            if line and line.strip().startswith("data:"):
                data = line.strip()[5:].strip()
                if data == "[DONE]":
                    break
                try:
                    import json
                    obj = json.loads(data)
                    delta = (obj.get("choices") or [{}])[0].get("delta", {})
                    content = delta.get("content")
                    if content:
                        yield content
                except Exception:
                    pass


