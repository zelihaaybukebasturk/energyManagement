"""
LLM-based Turkish translation helper.

Goal:
- Use a *second* model call (typically Ollama) to translate generated outputs to Turkish.
- Keep formatting (Markdown headings, lists) intact.
"""

from __future__ import annotations

import os
from typing import List


def _chunk_text(text: str, max_chars: int) -> List[str]:
    if len(text) <= max_chars:
        return [text]

    # Chunk by paragraphs to preserve structure.
    paras = text.split("\n\n")
    chunks: List[str] = []
    current: List[str] = []
    current_len = 0

    for p in paras:
        p_len = len(p) + 2
        if current and current_len + p_len > max_chars:
            chunks.append("\n\n".join(current))
            current = [p]
            current_len = p_len
        else:
            current.append(p)
            current_len += p_len

    if current:
        chunks.append("\n\n".join(current))
    return chunks


def translate_to_turkish_llm(text: str) -> str:
    """
    Translate text to Turkish using an LLM (Ollama by default).

    Environment:
    - TRANSLATION_OLLAMA_BASE_URL (default: http://localhost:11434)
    - TRANSLATION_OLLAMA_MODEL (default: llama3.2)
    - TRANSLATION_MAX_CHARS (default: 6000) chunk size
    """
    if not text or len(text.strip()) < 3:
        return text

    base_url = os.getenv("TRANSLATION_OLLAMA_BASE_URL", os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"))
    model = os.getenv("TRANSLATION_OLLAMA_MODEL", os.getenv("OLLAMA_MODEL", "llama3.2"))
    max_chars = int(os.getenv("TRANSLATION_MAX_CHARS", "6000"))

    try:
        import requests
    except ImportError as e:
        raise ImportError("requests package not installed. Install with: pip install requests") from e

    system_prompt = (
        "You are a professional translation engine.\n"
        "Translate the user's text to Turkish.\n"
        "Rules:\n"
        "- Preserve Markdown structure (## headings, lists, bold text).\n"
        "- Keep numbers and units unchanged.\n"
        "- Do NOT add extra commentary.\n"
        "- Return ONLY the Turkish translation.\n"
    )

    chunks = _chunk_text(text, max_chars=max_chars)
    out_chunks: List[str] = []

    for chunk in chunks:
        prompt = f"{system_prompt}\nTEXT:\n{chunk}"
        resp = requests.post(
            f"{base_url}/api/generate",
            json={
                "model": model,
                "prompt": prompt,
                "stream": False,
                "options": {"temperature": 0.0, "num_predict": 1800},
            },
            timeout=60,
        )
        resp.raise_for_status()
        out_chunks.append((resp.json().get("response") or "").strip())

    return "\n\n".join(out_chunks).strip() or text

