"""LLM service adapters."""

import json
import os
import urllib.error
import urllib.request


def get_qianwen_api_key() -> str:
    api_key = os.environ.get("QIANWEN_API_KEY", "").strip()
    if api_key:
        return api_key

    try:
        import streamlit as st

        secret_value = str(st.secrets.get("QIANWEN_API_KEY", "")).strip()
        if secret_value:
            return secret_value

        qwen_secret = st.secrets.get("qwen", {})
        if hasattr(qwen_secret, "get"):
            return str(qwen_secret.get("api_key", "")).strip()
    except Exception:
        return ""

    return ""


class QwenService:
    def __init__(self, api_key: str, model: str = "qwen-plus", temperature: float = 0.2):
        self.api_key = api_key
        self.model = model or "qwen-plus"
        self.temperature = temperature
        self.endpoint = "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions"

    def generate(self, prompt: str) -> str:
        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "You are a professional e-commerce BI analyst. "
                        "Answer with concise, data-grounded business insights. "
                        "Do not invent metrics that are not provided in the prompt."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
            "temperature": float(self.temperature),
        }
        data = json.dumps(payload).encode("utf-8")
        request = urllib.request.Request(
            self.endpoint,
            data=data,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )

        try:
            with urllib.request.urlopen(request, timeout=60) as response:
                response_data = json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            error_body = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"Qwen API HTTP {exc.code}: {error_body}") from exc
        except urllib.error.URLError as exc:
            raise RuntimeError(f"Qwen API request failed: {exc.reason}") from exc

        try:
            return response_data["choices"][0]["message"]["content"].strip()
        except (KeyError, IndexError, TypeError) as exc:
            raise RuntimeError(f"Unexpected Qwen API response: {response_data}") from exc
