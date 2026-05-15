"""Rasain Orchestrator — the autonomous multi-agent loop.

Two entry points:

  process_report()    — event-driven. Triggered when a citizen submits a report.
                        Runs: classify -> route -> submit, with decision
                        branches for invalid / low-confidence / critical cases.

  run_tracker_cycle() — cron-driven. Runs WITHOUT human input. Polls every open
                        Lapor.go.id ticket, escalates stuck ones, verifies
                        resolved ones, and triggers on-chain rewards.

Every step writes an AgentLogEntry with natural-language reasoning, so the
dashboard can stream the agent's "thought process" — proof of autonomy, not
just output.
"""
from __future__ import annotations

import asyncio
from datetime import datetime
from uuid import UUID

# Serializes tracker cycles: the scheduled job and manual triggers must not
# process the same report concurrently (would double-mint rewards).
_tracker_lock = asyncio.Lock()

from agent.config import get_settings
from agent.models import AgentLogEntry, Report, ReportStatus, ReportType, Severity
from agent.store import get_store
from agent.tools.classifier import classify_infrastructure_issue
from agent.tools.email_gov import check_reply, email_configured, send_report_email
from agent.tools.geolocator import route_to_instansi
from agent.tools.lapor_portal import (
    escalate_ticket,
    get_lapor_status,
    is_ticket_stuck,
    submit_to_lapor,
)
from agent.tools.memory import recall, remember
from agent.tools.reward import earn_reward_for_report
from agent.tools.telegram import (
    download_photo,
    extract_kota,
    get_updates,
    send_message,
    telegram_configured,
)

# Telegram long-poll offset — advances past processed updates.
_tg_offset: dict[str, int] = {"value": 0}

CONFIDENCE_THRESHOLD = 0.6


def _log(
    agent_name: str,
    action: str,
    reasoning: str,
    tool_calls: list[dict] | None = None,
    report_id: UUID | None = None,
    citizen_id: UUID | None = None,
) -> AgentLogEntry:
    """Record one reasoning step for dashboard transparency."""
    entry = AgentLogEntry(
        agent_name=agent_name,
        action=action,
        reasoning=reasoning,
        tool_calls=tool_calls or [],
        related_report_id=report_id,
        related_citizen_id=citizen_id,
    )
    return get_store().add_log(entry)


async def process_report(intake_payload: dict) -> dict:
    """Process one citizen report end-to-end: classify -> route -> submit.

    Returns a dict summary including the created Report and Lapor.go.id ticket,
    or a rejection / re-photo request if the report fails a decision branch.
    """
    store = get_store()
    citizen_id = UUID(intake_payload["citizen_id"])
    kota = intake_payload["kota"]

    _log(
        "intake", "receive_report",
        f"Laporan baru dari {intake_payload['citizen_name']} via "
        f"{intake_payload['channel']} di {kota}.",
        citizen_id=citizen_id,
    )

    # --- Recall this citizen's history from Mem9 (cross-session memory) ---
    past = await asyncio.to_thread(
        recall, f"laporan warga {intake_payload['citizen_name']} {kota}", 3
    )
    if past:
        _log(
            "memory", "recall_history",
            f"Mem9: {len(past)} memori warga ini ditemukan. Konteks terbaru: "
            f"\"{past[0][:90]}\"",
            citizen_id=citizen_id,
        )

    # --- Step 1: Classify (Claude vision) ---
    classification = await asyncio.to_thread(
        classify_infrastructure_issue,
        intake_payload["image_path"],
        intake_payload.get("description"),
        kota,
    )
    _log(
        "classifier", "classify_image",
        f"Vision analysis: {classification['reasoning']}",
        tool_calls=[{"tool": "classify_infrastructure_issue", "result": classification}],
        citizen_id=citizen_id,
    )

    # --- Decision branch: invalid report ---
    if not classification.get("is_valid_report", True):
        _log(
            "classifier", "reject_invalid",
            "Foto bukan masalah infrastruktur publik — laporan ditolak.",
            citizen_id=citizen_id,
        )
        return {"status": "rejected", "reason": "Bukan masalah infrastruktur publik"}

    # --- Decision branch: low confidence -> ask for a better photo ---
    if classification.get("confidence", 1.0) < CONFIDENCE_THRESHOLD:
        _log(
            "classifier", "request_rephoto",
            f"Confidence {classification['confidence']:.2f} di bawah ambang "
            f"{CONFIDENCE_THRESHOLD} — minta warga kirim foto lebih jelas.",
            citizen_id=citizen_id,
        )
        return {
            "status": "needs_better_photo",
            "reason": "Foto kurang jelas, mohon kirim ulang",
            "confidence": classification["confidence"],
        }

    # --- Step 2: Route to the responsible agency ---
    routing = route_to_instansi(
        classification["category"],
        kota,
        intake_payload.get("gps_lat"),
        intake_payload.get("gps_lon"),
    )
    _log(
        "geolocator", "route_instansi",
        f"Kategori '{classification['category']}' di {routing['kota']} → "
        f"{routing['instansi_target']} (SLA {routing['expected_sla_days']} hari).",
        tool_calls=[{"tool": "route_to_instansi", "result": routing}],
        citizen_id=citizen_id,
    )

    # --- Persist the Report ---
    report = Report(
        citizen_id=citizen_id,
        report_type=ReportType(classification.get("report_type", "civic")),
        category=classification["category"],
        subcategory=classification.get("subcategory"),
        severity=Severity(classification["severity"]),
        urgency=classification["urgency"],
        gps_lat=intake_payload.get("gps_lat"),
        gps_lon=intake_payload.get("gps_lon"),
        kota=routing["kota"],
        instansi_target=routing["instansi_target"],
        photo_url=intake_payload["image_path"],
        description=intake_payload["description"],
        status=ReportStatus.CLASSIFIED,
        classification_reasoning=classification["reasoning"],
    )
    store.upsert_report(report)

    # --- Decision branch: critical severity -> note fast-track ---
    if report.severity == Severity.CRITICAL:
        _log(
            "orchestrator", "fast_track",
            "Severity CRITICAL — laporan di-fast-track, instansi diberi "
            "prioritas darurat.",
            report_id=report.id, citizen_id=citizen_id,
        )

    # --- Step 3: Submit to Lapor.go.id ---
    ticket = submit_to_lapor(
        report_id=str(report.id),
        category=report.category,
        instansi_target=report.instansi_target,
        kota=report.kota,
        description=report.description,
        severity=report.severity.value,
        urgency=report.urgency,
    )
    report.lapor_ticket_id = ticket["ticket_id"]
    report.status = ReportStatus.SUBMITTED
    store.upsert_report(report)
    _log(
        "submitter", "submit_lapor",
        f"Laporan tercatat di Lapor.go.id, tiket {ticket['ticket_id']}.",
        tool_calls=[{"tool": "submit_to_lapor", "result": {"ticket_id": ticket["ticket_id"]}}],
        report_id=report.id, citizen_id=citizen_id,
    )

    # --- Step 4: Email the report to the responsible agency (real channel) ---
    if email_configured():
        email_result = await asyncio.to_thread(
            send_report_email,
            ticket["ticket_id"], report.instansi_target, report.category,
            report.severity.value, report.urgency, report.kota,
            report.description, intake_payload["citizen_name"],
            f"pengaduan@{report.category.split('_')[0]}.go.id",
            report.photo_url,
        )
        if email_result.get("sent"):
            _log(
                "submitter", "send_email",
                f"Email laporan dikirim ke {email_result['recipient']}. Instansi "
                f"diminta membalas — balasan akan memverifikasi laporan otomatis.",
                tool_calls=[{"tool": "send_report_email", "result": email_result}],
                report_id=report.id, citizen_id=citizen_id,
            )
        else:
            _log(
                "submitter", "send_email_failed",
                f"Email gagal terkirim ({email_result.get('reason', 'unknown')}) — "
                f"laporan tetap dilacak via portal.",
                report_id=report.id, citizen_id=citizen_id,
            )

    return {
        "status": "submitted",
        "report_id": str(report.id),
        "ticket_id": ticket["ticket_id"],
        "category": report.category,
        "severity": report.severity.value,
        "urgency": report.urgency,
        "instansi_target": report.instansi_target,
        "classification_reasoning": report.classification_reasoning,
    }


async def process_telegram_updates() -> dict:
    """Poll Telegram for citizen reports — photo + caption — and process them.

    Cron-driven entry point: citizens report in their own words via the bot,
    the agent runs the full pipeline, and replies on Telegram.
    """
    if not telegram_configured():
        return {"processed": 0}
    updates = await asyncio.to_thread(get_updates, _tg_offset["value"], 0)
    processed = 0
    for upd in updates:
        _tg_offset["value"] = upd["update_id"] + 1
        msg = upd.get("message", {})
        chat_id = msg.get("chat", {}).get("id")
        if not chat_id:
            continue
        photos = msg.get("photo")
        if not photos:
            await asyncio.to_thread(
                send_message, chat_id,
                "Halo! Kirim <b>foto</b> masalah infrastruktur, dan tulis "
                "deskripsinya di caption foto. Contoh: \"jalan rusak parah di "
                "tikungan Bekasi\".",
            )
            continue

        caption = msg.get("caption") or "Laporan masalah infrastruktur publik"
        name = msg.get("from", {}).get("first_name", "Warga")
        image_path = await asyncio.to_thread(download_photo, photos[-1]["file_id"])
        if not image_path:
            continue

        await asyncio.to_thread(
            send_message, chat_id, "📥 Laporan diterima — AI agent menganalisis fotomu…"
        )
        payload = intake_report(
            wa_number=f"tg-{chat_id}", citizen_name=name, image_path=image_path,
            description=caption, kota=extract_kota(caption),
            channel="telegram", telegram_chat_id=str(chat_id),
        )
        result = await process_report(payload)
        processed += 1

        if result["status"] == "submitted":
            await asyncio.to_thread(
                send_message, chat_id,
                f"✅ <b>Laporanmu sudah diteruskan!</b>\n\n"
                f"Kategori  : {result['category']}\n"
                f"Tingkat   : {result['severity']} (urgensi {result['urgency']}/5)\n"
                f"Instansi  : {result['instansi_target']}\n"
                f"No. Tiket : <code>{result['ticket_id']}</code>\n\n"
                f"Agent telah mengirim email resmi ke instansi terkait. "
                f"Kamu akan dapat notifikasi di sini saat laporan terverifikasi.",
            )
        elif result["status"] == "needs_better_photo":
            await asyncio.to_thread(
                send_message, chat_id,
                "📷 Fotonya kurang jelas — mohon kirim ulang yang lebih terang ya.",
            )
        else:
            await asyncio.to_thread(
                send_message, chat_id,
                "Hmm, foto ini sepertinya bukan masalah infrastruktur publik.",
            )
    return {"processed": processed}


async def run_tracker_cycle() -> dict:
    """Autonomous loop: poll open tickets, escalate stuck, verify resolved.

    This runs on a scheduler with NO human trigger — the core of Rasain's
    autonomy. Returns a summary of actions taken this cycle.
    """
    if _tracker_lock.locked():
        return {"polled": 0, "escalated": 0, "verified": 0, "rewards_minted": 0,
                "skipped": "cycle already running"}
    async with _tracker_lock:
        return await _tracker_cycle_body()


async def _tracker_cycle_body() -> dict:
    store = get_store()
    actions = {"polled": 0, "escalated": 0, "verified": 0, "rewards_minted": 0}

    open_reports = [
        r for r in store.list_reports()
        if r.status in (ReportStatus.SUBMITTED, ReportStatus.IN_PROGRESS)
        and r.lapor_ticket_id
    ]

    use_email = email_configured()

    for report in open_reports:
        actions["polled"] += 1

        # --- Determine resolution from EITHER channel ---
        # Real email reply from the agency, OR mock-portal resolution (demo
        # trigger). Whichever fires first verifies the report.
        resolved = False
        verify_source = ""
        if use_email:
            reply = await asyncio.to_thread(check_reply, report.lapor_ticket_id)
            if reply.get("replied"):
                resolved = True
                verify_source = f"balasan email dari {reply.get('from', 'instansi')}"

        ticket = get_lapor_status(report.lapor_ticket_id)
        if not resolved and isinstance(ticket, dict) and ticket.get("status") == "resolved":
            resolved = True
            verify_source = f"portal Lapor.go.id ({report.instansi_target})"

        # --- Resolved → verify + reward ---
        if resolved:
            report.status = ReportStatus.VERIFIED
            report.resolved_at = datetime.utcnow()
            report.verified_at = datetime.utcnow()
            store.upsert_report(report)
            _log(
                "verifier", "verify_resolution",
                f"Tiket {report.lapor_ticket_id} terverifikasi via {verify_source}. "
                f"Laporan dinyatakan selesai.",
                report_id=report.id, citizen_id=report.citizen_id,
            )
            # Persist this verified impact to Mem9 — recalled on future reports.
            await asyncio.to_thread(
                remember,
                str(report.citizen_id),
                f"Warga melaporkan {report.category} ({report.severity.value}) "
                f"di {report.kota}; diteruskan ke {report.instansi_target} dan "
                f"terverifikasi selesai pada {report.verified_at:%Y-%m-%d}.",
            )
            reward = await earn_reward_for_report(report)
            actions["verified"] += 1
            if reward.spl_mint_tx:
                actions["rewards_minted"] += 1
                _log(
                    "reward", "mint_rsn",
                    f"Warga dapat {reward.points_earned} RSN. Threshold tercapai "
                    f"→ di-mint on-chain: {reward.spl_mint_tx[:16]}...",
                    tool_calls=[{"tool": "mint_rsn", "tx": reward.spl_mint_tx}],
                    report_id=report.id, citizen_id=report.citizen_id,
                )

            # --- Notify the citizen on Telegram (round-trip closed) ---
            citizen = store.get_citizen(report.citizen_id)
            if citizen and citizen.telegram_chat_id:
                await asyncio.to_thread(
                    send_message, citizen.telegram_chat_id,
                    f"🎉 <b>Laporanmu sudah selesai ditangani!</b>\n\n"
                    f"Tiket <code>{report.lapor_ticket_id}</code> ({report.category}) "
                    f"di {report.kota} telah diverifikasi selesai.\n\n"
                    f"Kamu mendapat <b>{reward.points_earned} Rasain Points (RSN)</b> "
                    f"sebagai apresiasi. Tukar jadi Civic Credit di dashboard untuk "
                    f"potongan retribusi. Terima kasih sudah menjaga kotamu! 🙏",
                )
                _log(
                    "verifier", "notify_citizen",
                    f"Notifikasi Telegram dikirim ke pelapor — laporan selesai + "
                    f"{reward.points_earned} RSN.",
                    report_id=report.id, citizen_id=report.citizen_id,
                )
            continue

        # --- In progress → just track ---
        if ticket.get("status") in ("in_progress", "forwarded", "verified_by_admin"):
            if report.status != ReportStatus.IN_PROGRESS:
                report.status = ReportStatus.IN_PROGRESS
                store.upsert_report(report)

        # --- Stuck past SLA → escalate ---
        sla = 7  # default; geolocator carries per-agency SLA in V2
        if "submitted_at" in ticket and is_ticket_stuck(ticket, sla):
            escalate_ticket(
                report.lapor_ticket_id,
                f"Tidak ada penyelesaian dalam {sla} hari (SLA terlewat).",
            )
            actions["escalated"] += 1
            _log(
                "tracker", "escalate_stuck",
                f"Tiket {report.lapor_ticket_id} melewati SLA {sla} hari tanpa "
                f"penyelesaian — dieskalasi otomatis, prioritas dinaikkan.",
                report_id=report.id, citizen_id=report.citizen_id,
            )

    return actions
