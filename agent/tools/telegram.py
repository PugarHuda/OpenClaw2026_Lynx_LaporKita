"""Telegram bot channel — citizen intake + reply notifications.

Citizens report in their own casual words: they send a photo (with a caption
describing the problem) to the Telegram bot. The agent processes it and, once
the agency responds, notifies the citizen back on Telegram.

Telegram Bot API is plain HTTP — uses httpx, no SDK. Polling (getUpdates),
so no public webhook is required.
"""
from __future__ import annotations

import tempfile
from typing import Any

import httpx

from agent.config import get_settings

# Known cities for lightweight kota extraction from a free-text caption.
_KNOWN_KOTA = [
    "Jakarta", "Bekasi", "Surabaya", "Bandung", "Depok", "Tangerang",
    "Semarang", "Medan", "Makassar", "Palembang", "Bogor", "Yogyakarta",
]


def telegram_configured() -> bool:
    """True when a Telegram bot token is set."""
    return bool(get_settings().telegram_bot_token)


def _api(method: str) -> str:
    return f"https://api.telegram.org/bot{get_settings().telegram_bot_token}/{method}"


def get_updates(offset: int = 0, timeout: int = 0) -> list[dict[str, Any]]:
    """Poll Telegram for new messages and button taps since `offset`."""
    if not telegram_configured():
        return []
    try:
        resp = httpx.get(
            _api("getUpdates"),
            params={
                "offset": offset,
                "timeout": timeout,
                "allowed_updates": '["message","callback_query"]',
            },
            timeout=timeout + 10,
        )
        return resp.json().get("result", []) if resp.status_code < 300 else []
    except Exception:
        return []


def download_photo(file_id: str) -> str | None:
    """Resolve a Telegram photo file_id and download it to a temp file.

    Returns the local path, or None on failure.
    """
    if not telegram_configured():
        return None
    settings = get_settings()
    try:
        meta = httpx.get(_api("getFile"), params={"file_id": file_id}, timeout=15)
        file_path = meta.json()["result"]["file_path"]
        url = f"https://api.telegram.org/file/bot{settings.telegram_bot_token}/{file_path}"
        data = httpx.get(url, timeout=20).content
        suffix = "." + file_path.rsplit(".", 1)[-1] if "." in file_path else ".jpg"
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            tmp.write(data)
            return tmp.name
    except Exception:
        return None


def send_message(
    chat_id: int | str,
    text: str,
    buttons: list[list[dict[str, str]]] | None = None,
) -> bool:
    """Send a Telegram message, optionally with a clickable inline keyboard.

    `buttons` is a list of rows; each button is a dict with "text" plus either
    "url" (opens a link) or "callback_data" (taps back into the bot).
    """
    if not telegram_configured():
        return False
    payload: dict[str, Any] = {"chat_id": chat_id, "text": text, "parse_mode": "HTML"}
    if buttons:
        payload["reply_markup"] = {"inline_keyboard": buttons}
    try:
        resp = httpx.post(_api("sendMessage"), json=payload, timeout=15)
        return resp.status_code < 300
    except Exception:
        return False


def answer_callback(callback_query_id: str, text: str = "") -> bool:
    """Acknowledge a button tap so Telegram stops its loading spinner."""
    if not telegram_configured():
        return False
    try:
        resp = httpx.post(
            _api("answerCallbackQuery"),
            json={"callback_query_id": callback_query_id, "text": text},
            timeout=15,
        )
        return resp.status_code < 300
    except Exception:
        return False


def extract_kota(text: str) -> str:
    """Best-effort city extraction from a free-text caption."""
    lowered = (text or "").lower()
    for kota in _KNOWN_KOTA:
        if kota.lower() in lowered:
            return kota
    return "Jakarta"
