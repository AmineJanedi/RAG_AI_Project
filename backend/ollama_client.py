# backend/ollama_client.py
"""
Simple Ollama HTTP client wrapper.
Supports streaming (iterating response lines) and non-streaming.
Assumes Ollama server runs at http://localhost:11434/api/generate
"""

import os
import requests
from dotenv import load_dotenv

load_dotenv()

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434/api/generate")
DEFAULT_MODEL = os.getenv("OLLAMA_MODEL", "llama3")  # or "cad-assistant" if you built one

def query_ollama(prompt: str, model: str = None, stream=False, timeout=120):
    """
    If stream=False -> returns full string response.
    If stream=True -> returns a generator yielding partial strings.
    """
    payload = {"model": model or DEFAULT_MODEL, "prompt": prompt, "stream": stream}
    resp = requests.post(OLLAMA_URL, json=payload, stream=stream, timeout=timeout)
    resp.raise_for_status()

    if not stream:
        # Some Ollama versions return {"response": "..."} or {"message": {"content": "..."}}
        data = resp.json()
        if "response" in data:
            return data["response"]
        if "message" in data and isinstance(data["message"], dict) and "content" in data["message"]:
            return data["message"]["content"]
        # fallback
        return str(data)

    # stream mode: yield decoded lines as they arrive
    def generator():
        # Ollama streaming returns NDJSON or line-delimited JSON; we decode safe
        for line in resp.iter_lines(decode_unicode=True):
            if not line:
                continue
            # line may be JSON or plain text. Try parse.
            try:
                import json
                obj = json.loads(line)
                # main content might be in 'response' or 'message'...
                if isinstance(obj, dict) and "response" in obj:
                    yield obj["response"]
                elif isinstance(obj, dict) and "message" in obj and "content" in obj["message"]:
                    yield obj["message"]["content"]
                else:
                    # fallback: yield raw line
                    yield line
            except Exception:
                yield line
    return generator()
