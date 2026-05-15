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
from agent.models import AgentLogEntry, Report, ReportStatus, Severity
from agent.store import get_store
from agent.tools.classifier import classify_infrastructure_issue
from agent.tools.geolocator import route_to_instansi
from agent.tools.lapor_portal import (
    escalate_ticket,
    get_lapor_status,
    is_ticket_stuck,
    submit_to_lapor,
)
from agent.tools.reward import earn_reward_for_report

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
        f"Laporan dikirim ke Lapor.go.id, tiket {ticket['ticket_id']}, "
        f"status awal '{ticket['status']}'.",
        tool_calls=[{"tool": "submit_to_lapor", "result": {"ticket_id": ticket["ticket_id"]}}],
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

    for report in open_reports:
        actions["polled"] += 1
        ticket = get_lapor_status(report.lapor_ticket_id)
        if "error" in ticket:
            continue

        # --- Resolved → verify + reward ---
        if ticket["status"] == "resolved":
            report.status = ReportStatus.VERIFIED
            report.resolved_at = datetime.utcnow()
            report.verified_at = datetime.utcnow()
            store.upsert_report(report)
            _log(
                "verifier", "verify_resolution",
                f"Tiket {report.lapor_ticket_id} dinyatakan resolved oleh "
                f"{report.instansi_target}. Laporan terverifikasi.",
                report_id=report.id, citizen_id=report.citizen_id,
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
            continue

        # --- In progress → just track ---
        if ticket["status"] in ("in_progress", "forwarded", "verified_by_admin"):
            if report.status != ReportStatus.IN_PROGRESS:
                report.status = ReportStatus.IN_PROGRESS
                store.upsert_report(report)

        # --- Stuck past SLA → escalate ---
        sla = 7  # default; geolocator carries per-agency SLA in V2
        if is_ticket_stuck(ticket, sla):
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
