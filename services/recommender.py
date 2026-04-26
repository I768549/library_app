"""
AI-асистент для рекомендацій книг
Спілкується з локальним сервером Ollama (HTTP API)
Перед використанням:
    1. Встановити Ollama: https://ollama.com
    2. Запустити сервер:    ollama serve
    3. Завантажити модель:  ollama pull llama3.2
"""
from __future__ import annotations

import json
import urllib.error
import urllib.request
from typing import Callable, Iterable

from database import repository

OLLAMA_URL = "http://localhost:11434/api/chat"
DEFAULT_MODEL = "llama3.2"

SYSTEM_TEMPLATE = """
You're a professional library assistant

Rules:
- Answer the same language you're asked by a user, answer straight to the point
- If you've decided to recommend a book — choose a recommendation ONLY from the list bellow.
- You can ask for specifications (mood, genre, size).
- If there is no suitable book for a user say it 

Library's catalog:
{catalog}
"""


def _build_catalog() -> str:
    try:
        books = repository.get_all_books()
    except Exception as exc:
        return f"(не вдалося отримати каталог: {exc})"
    if not books:
        return "(каталог порожній)"
    return "\n".join(
        f'- "{b["title"]}" ({b["year"]}); автори: {b["authors"] or "—"}; '
        f'жанри: {b["genres"] or "—"}'
        for b in books
    )


def chat_stream(
    history: Iterable[dict],
    on_chunk: Callable[[str], None],
    model: str = DEFAULT_MODEL,
    url: str = OLLAMA_URL,
    timeout: int = 180,
) -> None:
    """Надсилає історію повідомлень в Ollama і викликає on_chunk для кожного
    отриманого фрагменту тексту.

    history - список {"role": "user"|"assistant", "content": str}.
    on_chunk - викликається з фонового потоку.
    """
    catalog = _build_catalog()
    messages = [
        {"role": "system", "content": SYSTEM_TEMPLATE.format(catalog=catalog)},
        *history,
    ]
    body = json.dumps(
        {"model": model, "messages": messages, "stream": True},
        ensure_ascii=False,
    ).encode("utf-8")

    req = urllib.request.Request(
        url,
        data=body,
        method="POST",
        headers={"Content-Type": "application/json"},
    )

    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            for raw in resp:
                line = raw.strip()
                if not line:
                    continue
                try:
                    data = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if "error" in data:
                    raise RuntimeError(data["error"])
                content = data.get("message", {}).get("content", "")
                if content:
                    on_chunk(content)
                if data.get("done"):
                    return
    except urllib.error.URLError as exc:
        raise RuntimeError(
            f"Не вдалося підключитись до Ollama ({url}): {exc.reason}.\n"
            f"Для роботи необхідно підняти 'ollama serve' та переконатися, що модель '{model}' "
            f"завантажена і є в ollama list, якщо ні, то 'ollama pull {model}'."
        ) from exc
