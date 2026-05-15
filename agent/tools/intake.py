"""Intake Agent tool — the entry point for citizen reports.

Accepts a report from any channel (web upload, WhatsApp webhook, Telegram) and
normalizes it into a Citizen + raw report payload the pipeline can process.

Channel-agnostic by design: the orchestrator never knows or cares whether a
report arrived via WhatsApp or a web form.
"""
from __future__ import annotations

import hashlib
from typing import Any

from agent.models import Citizen
from agent.store import get_store


def _anonymous_handle(seed: str) -> str:
    """Derive a stable pseudonymous handle from a seed (wa number / chat id).

    Citizens are anonymous — identified by a pseudonym + their Solana wallet,
    never their real name. This protects reporters (whistleblower safety).
    """
    short = hashlib.sha1(seed.encode()).hexdigest()[:4].upper()
    return f"Warga-{short}"


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
    email: str | None = None,
) -> dict[str, Any]:
    """Normalize an incoming citizen report.

    Looks up or creates the Citizen, then returns a raw report payload
    (not yet classified) for the orchestrator to process.

    Identity: web reporters are keyed by `email` (their login + ownership
    anchor); Telegram/WhatsApp reporters are keyed by `wa_number`.
    """
    store = get_store()
    citizen = store.get_citizen_by_email(email) if email else None
    if citizen is None:
        citizen = store.get_citizen_by_wa(wa_number)
    if citizen is None:
        # The public-facing identity stays a pseudonymous handle; the email is
        # a private login key, never shown on the dashboard.
        citizen = Citizen(
            wa_number=wa_number,
            email=email,
            name=_anonymous_handle(email or wa_number),
            bank_account=bank_account,
            bank_name=bank_name,
            telegram_chat_id=telegram_chat_id,
        )
        store.upsert_citizen(citizen)
    else:
        # Keep identity + contact details fresh if newly provided.
        changed = False
        if email and not citizen.email:
            citizen.email = email
            changed = True
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
