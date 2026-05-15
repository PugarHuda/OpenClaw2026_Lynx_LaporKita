"""Government email channel — the Submitter agent's real-world output.

Instead of a mock portal, the Submitter agent autonomously emails the report to
the responsible government agency. The Verifier later polls the inbox via IMAP:
a reply from the agency = the report is verified.

This makes the agent's action genuinely real — a real email leaves the system,
and verification depends on a real response. Uses stdlib smtplib + imaplib
(Gmail SMTP/IMAP), so no extra dependencies.
"""
from __future__ import annotations

import email
import imaplib
import smtplib
from email.message import EmailMessage
from email.utils import parsedate_to_datetime
from typing import Any

from agent.config import get_settings

_SMTP_HOST, _SMTP_PORT = "smtp.gmail.com", 587
_IMAP_HOST = "imap.gmail.com"


def email_configured() -> bool:
    """True when the agent's Gmail credentials are present."""
    s = get_settings()
    return bool(s.gov_email_address and s.gov_email_app_password)


def send_report_email(
    ticket_id: str,
    instansi_target: str,
    category: str,
    severity: str,
    urgency: int,
    kota: str,
    description: str,
    citizen_name: str,
    agency_email: str,
    image_path: str | None = None,
) -> dict[str, Any]:
    """Email a citizen report to a government agency. Returns send status.

    The ticket_id is embedded in the subject so a reply can be matched back to
    the report during verification. The citizen's photo is attached when given.
    """
    settings = get_settings()
    if not email_configured():
        return {"sent": False, "reason": "email not configured (DEMO_MODE)", "ticket_id": ticket_id}

    # Demo override: route every report to the test inbox playing the agency.
    recipient = settings.gov_email_demo_recipient or agency_email

    msg = EmailMessage()
    msg["Subject"] = f"[Rasain] Laporan Infrastruktur {ticket_id} - {category} ({kota})"
    msg["From"] = settings.gov_email_address
    msg["To"] = recipient
    msg.set_content(
        f"""Kepada Yth. {instansi_target},

Sistem Rasain meneruskan laporan masalah infrastruktur publik dari warga:

  Nomor Tiket   : {ticket_id}
  Kategori      : {category}
  Tingkat       : {severity} (urgensi {urgency}/5)
  Lokasi        : {kota}
  Pelapor       : {citizen_name}

Deskripsi:
{description}

Mohon laporan ini dapat ditindaklanjuti. Balas email ini untuk konfirmasi
penerimaan atau penyelesaian — sistem akan memverifikasi laporan secara otomatis.

Hormat kami,
Rasain — Autonomous Civic Reporting Agent
"""
    )

    # Attach the citizen's photo as evidence, if available.
    if image_path:
        try:
            from pathlib import Path

            p = Path(image_path)
            if p.exists():
                subtype = p.suffix.lstrip(".").lower() or "jpeg"
                msg.add_attachment(
                    p.read_bytes(), maintype="image",
                    subtype="jpeg" if subtype == "jpg" else subtype,
                    filename=f"bukti-{ticket_id}{p.suffix}",
                )
        except Exception:
            pass  # attachment is best-effort; the report email still sends

    try:
        with smtplib.SMTP(_SMTP_HOST, _SMTP_PORT, timeout=20) as server:
            server.starttls()
            server.login(settings.gov_email_address, settings.gov_email_app_password)
            server.send_message(msg)
        return {"sent": True, "recipient": recipient, "ticket_id": ticket_id}
    except Exception as e:
        return {"sent": False, "reason": str(e)[:160], "ticket_id": ticket_id}


def check_reply(ticket_id: str) -> dict[str, Any]:
    """Poll the agent's inbox via IMAP for a reply to a given ticket.

    A reply is matched when an email subject contains the ticket_id. Returns
    {"replied": bool, ...}. Best-effort — failures degrade gracefully.
    """
    settings = get_settings()
    if not email_configured():
        return {"replied": False, "reason": "email not configured"}

    try:
        imap = imaplib.IMAP4_SSL(_IMAP_HOST)
        imap.login(settings.gov_email_address, settings.gov_email_app_password)
        imap.select("INBOX")
        # Search messages whose subject carries the ticket id.
        status, data = imap.search(None, "SUBJECT", f'"{ticket_id}"')
        if status != "OK" or not data or not data[0]:
            imap.logout()
            return {"replied": False}

        for num in data[0].split():
            status, msg_data = imap.fetch(num, "(RFC822)")
            if status != "OK" or not msg_data or not msg_data[0]:
                continue
            raw = msg_data[0][1]
            if not isinstance(raw, (bytes, bytearray)):
                continue
            parsed = email.message_from_bytes(raw)
            subject = str(parsed.get("Subject", ""))
            sender = str(parsed.get("From", ""))
            # A reply carries the "Re:" prefix; the original report email does
            # not — so this distinguishes a reply even in a send-to-self demo.
            if subject.lower().startswith("re:"):
                received = parsed.get("Date")
                imap.logout()
                return {
                    "replied": True,
                    "ticket_id": ticket_id,
                    "from": sender,
                    "at": parsedate_to_datetime(received).isoformat() if received else None,
                }
        imap.logout()
        return {"replied": False}
    except Exception as e:
        return {"replied": False, "reason": str(e)[:160]}
