"""Submitter + Tracker tools — interface to the Lapor.go.id government portal.

V1 uses a stateful mock of Lapor.go.id (the real portal has no public API).
The mock is deliberately faithful: tickets have realistic IDs, a status
lifecycle, timestamps, and an agency response log — so the agent's submit /
poll / escalate logic is exactly what V2 (real API) will run.

The mock persists to JSON so demo state survives restarts and supports the
"time-jump" demo trick (advance_ticket_status).
"""
from __future__ import annotations

import json
import random
import string
import threading
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

_PORTAL_PATH = Path("lapor_portal_mock.json")
_lock = threading.Lock()

# Status lifecycle of a Lapor.go.id ticket.
LAPOR_STATUSES = ["submitted", "verified_by_admin", "forwarded", "in_progress", "resolved"]


def _load() -> dict[str, Any]:
    if _PORTAL_PATH.exists():
        return json.loads(_PORTAL_PATH.read_text(encoding="utf-8"))
    return {"tickets": {}}


def _save(data: dict[str, Any]) -> None:
    with _lock:
        _PORTAL_PATH.write_text(json.dumps(data, indent=2, default=str), encoding="utf-8")


def _gen_ticket_id() -> str:
    """Lapor.go.id-style tracking ID, e.g. 'LAPOR-7K3M9X2A'."""
    suffix = "".join(random.choices(string.ascii_uppercase + string.digits, k=8))
    return f"LAPOR-{suffix}"


def submit_to_lapor(
    report_id: str,
    category: str,
    instansi_target: str,
    kota: str,
    description: str,
    severity: str,
    urgency: int,
) -> dict[str, Any]:
    """Submit a classified report to Lapor.go.id. Returns the created ticket.

    Critical-urgency reports are fast-tracked: they skip straight to
    'forwarded' so the responsible agency sees them immediately.
    """
    data = _load()
    ticket_id = _gen_ticket_id()
    now = datetime.utcnow()
    initial_status = "forwarded" if urgency >= 5 else "submitted"

    ticket = {
        "ticket_id": ticket_id,
        "report_id": report_id,
        "category": category,
        "instansi_target": instansi_target,
        "kota": kota,
        "description": description,
        "severity": severity,
        "urgency": urgency,
        "status": initial_status,
        "submitted_at": now.isoformat(),
        "last_update_at": now.isoformat(),
        "resolved_at": None,
        "agency_log": [
            {"at": now.isoformat(), "event": f"Laporan diterima Lapor.go.id ({initial_status})"}
        ],
        "escalation_count": 0,
    }
    data["tickets"][ticket_id] = ticket
    _save(data)
    return ticket


def get_lapor_status(ticket_id: str) -> dict[str, Any]:
    """Poll the current status of a Lapor.go.id ticket."""
    data = _load()
    ticket = data["tickets"].get(ticket_id)
    if ticket is None:
        return {"error": f"Ticket {ticket_id} tidak ditemukan"}
    return ticket


def escalate_ticket(ticket_id: str, reason: str) -> dict[str, Any]:
    """Escalate a stuck ticket — bumps priority and logs the escalation."""
    data = _load()
    ticket = data["tickets"].get(ticket_id)
    if ticket is None:
        return {"error": f"Ticket {ticket_id} tidak ditemukan"}
    ticket["escalation_count"] += 1
    ticket["urgency"] = min(5, ticket["urgency"] + 1)
    now = datetime.utcnow().isoformat()
    ticket["last_update_at"] = now
    ticket["agency_log"].append(
        {"at": now, "event": f"ESKALASI #{ticket['escalation_count']}: {reason}"}
    )
    _save(data)
    return ticket


def advance_ticket_status(ticket_id: str, to_status: str | None = None) -> dict[str, Any]:
    """Advance a ticket along its lifecycle.

    Used by the demo "time-jump" to simulate agency response. With no
    `to_status`, advances exactly one step; otherwise jumps to the given status.
    """
    data = _load()
    ticket = data["tickets"].get(ticket_id)
    if ticket is None:
        return {"error": f"Ticket {ticket_id} tidak ditemukan"}

    if to_status is None:
        idx = LAPOR_STATUSES.index(ticket["status"])
        to_status = LAPOR_STATUSES[min(idx + 1, len(LAPOR_STATUSES) - 1)]

    now = datetime.utcnow()
    ticket["status"] = to_status
    ticket["last_update_at"] = now.isoformat()
    ticket["agency_log"].append(
        {"at": now.isoformat(), "event": f"Status berubah → {to_status}"}
    )
    if to_status == "resolved":
        ticket["resolved_at"] = now.isoformat()
    _save(data)
    return ticket


def is_ticket_stuck(ticket: dict[str, Any], sla_days: int) -> bool:
    """A ticket is 'stuck' if unresolved past its SLA window."""
    if ticket["status"] == "resolved":
        return False
    submitted = datetime.fromisoformat(ticket["submitted_at"])
    return datetime.utcnow() - submitted > timedelta(days=sla_days)
