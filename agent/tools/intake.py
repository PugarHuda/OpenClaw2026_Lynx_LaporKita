"""Intake Agent tool — the entry point for citizen reports.

Accepts a report from any channel (web upload, WhatsApp webhook, Telegram) and
normalizes it into a Citizen + raw report payload the pipeline can process.

Channel-agnostic by design: the orchestrator never knows or cares whether a
report arrived via WhatsApp or a web form.
"""
from __future__ import annotations

from typing import Any

from agent.models import Citizen
from agent.store import get_store


def intake_report(
    wa_number: str,
    citizen_name: str,
    image_path: str,
    description: str,
    kota: str,
    gps_lat: float | None = None,
    gps_lon: float | None = None,
    bank_account: str | None = None,
    bank_name: str | None = None,
    channel: str = "web",
    telegram_chat_id: str | None = None,
) -> dict[str, Any]:
    """Normalize an incoming citizen report.

    Looks up or creates the Citizen, then returns a raw report payload
    (not yet classified) for the orchestrator to process.
    """
    store = get_store()
    citizen = store.get_citizen_by_wa(wa_number)
    if citizen is None:
        citizen = Citizen(
            wa_number=wa_number,
            name=citizen_name,
            bank_account=bank_account,
            bank_name=bank_name,
            telegram_chat_id=telegram_chat_id,
        )
        store.upsert_citizen(citizen)
    else:
        # Keep contact details fresh if newly provided.
        changed = False
        if bank_account and not citizen.bank_account:
            citizen.bank_account, citizen.bank_name = bank_account, bank_name
            changed = True
        if telegram_chat_id and citizen.telegram_chat_id != telegram_chat_id:
            citizen.telegram_chat_id = telegram_chat_id
            changed = True
        if changed:
            store.upsert_citizen(citizen)

    return {
        "citizen_id": str(citizen.id),
        "citizen_name": citizen.name,
        "image_path": image_path,
        "description": description,
        "kota": kota,
        "gps_lat": gps_lat,
        "gps_lon": gps_lon,
        "channel": channel,
    }
