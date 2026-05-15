"""Mem9 memory tool — persistent agent memory for Rasain.

The agent remembers each citizen's reporting history across sessions. When a
new report arrives, the orchestrator recalls that citizen's past cases from
Mem9 so classification and routing are informed by context (e.g. a repeat
reporter, or a recurring problem at the same location).

Mem9 is an external hosted service (api.mem9.ai); calls are best-effort — if
Mem9 is unreachable the agent degrades gracefully and keeps running.
"""
from __future__ import annotations

import httpx

from agent.config import get_settings

_AGENT_ID = "rasain"


def _headers() -> dict[str, str]:
    settings = get_settings()
    return {
        "X-API-Key": settings.mem9_api_key,
        "X-Mnemo-Agent-Id": _AGENT_ID,
        "Content-Type": "application/json",
    }


def remember(citizen_id: str, text: str) -> bool:
    """Persist a fact about a citizen to Mem9. Best-effort.

    Args:
        citizen_id: Used as the Mem9 session id so memories group per citizen.
        text: Natural-language fact to remember.

    Returns:
        True if Mem9 accepted the write, False on any failure (non-fatal).
    """
    settings = get_settings()
    if not settings.mem9_api_key:
        return False
    try:
        resp = httpx.post(
            f"{settings.mem9_base_url}/v1alpha2/mem9s/memories",
            headers=_headers(),
            json={
                "session_id": f"citizen-{citizen_id}",
                "agent_id": _AGENT_ID,
                "mode": "smart",
                "messages": [{"role": "user", "content": text}],
            },
            timeout=8.0,
        )
        return resp.status_code < 300
    except Exception:
        return False  # memory is an enhancement, never a hard dependency


def recall(query: str, limit: int = 5) -> list[str]:
    """Recall relevant memories from Mem9 for a query. Best-effort.

    Returns a list of memory content strings (empty on any failure).
    """
    settings = get_settings()
    if not settings.mem9_api_key:
        return []
    try:
        resp = httpx.get(
            f"{settings.mem9_base_url}/v1alpha2/mem9s/memories",
            headers=_headers(),
            params={"q": query, "limit": limit},
            timeout=8.0,
        )
        if resp.status_code >= 300:
            return []
        memories = resp.json().get("memories", [])
        return [m["content"] for m in memories if m.get("content")]
    except Exception:
        return []
