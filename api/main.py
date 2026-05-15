"""Rasain FastAPI backend — HTTP bridge between the agent and the dashboard.

Exposes the orchestrator's capabilities as REST endpoints, plus a live
reasoning-trace feed (the demo centerpiece). An APScheduler job runs the
autonomous tracker loop on an interval — no human trigger.
"""
from __future__ import annotations

import os
import tempfile
from contextlib import asynccontextmanager

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from agent.config import get_settings
from agent.orchestrator import (
    process_report,
    process_telegram_updates,
    run_tracker_cycle,
)
from agent.store import get_store
from agent.tools.intake import intake_report
from agent.tools.reward import redeem_civic_credit

# Tracker cycle interval. Short for demo; in production this would be minutes.
TRACKER_INTERVAL_SECONDS = 20
# Telegram poll interval — citizens report via the bot.
TELEGRAM_POLL_SECONDS = 6

# Serverless (Vercel) has no long-lived process for a scheduler — there the
# autonomous loop is driven by the dashboard's manual trigger instead.
_SERVERLESS = bool(os.getenv("VERCEL"))
scheduler = AsyncIOScheduler()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Start the autonomous tracker loop on boot, stop it on shutdown."""
    if not _SERVERLESS:
        scheduler.add_job(
            run_tracker_cycle,
            "interval",
            seconds=TRACKER_INTERVAL_SECONDS,
            id="tracker_cycle",
            max_instances=1,
        )
        scheduler.add_job(
            process_telegram_updates,
            "interval",
            seconds=TELEGRAM_POLL_SECONDS,
            id="telegram_poll",
            max_instances=1,
        )
        scheduler.start()
    yield
    if not _SERVERLESS and scheduler.running:
        scheduler.shutdown(wait=False)


app = FastAPI(title="Rasain API", version="0.1.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- Request models ---
class ReportRequest(BaseModel):
    wa_number: str
    citizen_name: str
    image_path: str
    description: str
    kota: str
    gps_lat: float | None = None
    gps_lon: float | None = None
    bank_account: str | None = None
    bank_name: str | None = None
    channel: str = "web"


class RedeemRequest(BaseModel):
    citizen_id: str
    retribusi_type: str
    retribusi_amount_idr: int


# --- Endpoints ---
@app.get("/health")
async def health() -> dict:
    return {"status": "ok", "service": "rasain-api"}


@app.post("/report")
async def submit_report(req: ReportRequest) -> dict:
    """Submit a citizen report — runs the full classify→route→submit pipeline."""
    intake_payload = intake_report(
        wa_number=req.wa_number,
        citizen_name=req.citizen_name,
        image_path=req.image_path,
        description=req.description,
        kota=req.kota,
        gps_lat=req.gps_lat,
        gps_lon=req.gps_lon,
        bank_account=req.bank_account,
        bank_name=req.bank_name,
        channel=req.channel,
    )
    return await process_report(intake_payload)


@app.post("/report/upload")
async def submit_report_upload(
    photo: UploadFile = File(...),
    wa_number: str = Form(...),
    citizen_name: str = Form(...),
    description: str = Form(...),
    kota: str = Form(...),
    bank_account: str = Form(""),
    bank_name: str = Form(""),
) -> dict:
    """Submit a REAL citizen report with an uploaded photo.

    The photo is saved to a temp file and analysed by the vision Classifier —
    a genuine end-to-end flow: real person, real photo, real AI classification.
    """
    suffix = os.path.splitext(photo.filename or "photo.jpg")[1] or ".jpg"
    tmp_dir = "/tmp" if os.getenv("VERCEL") else None
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix, dir=tmp_dir) as tmp:
        tmp.write(await photo.read())
        image_path = tmp.name

    intake_payload = intake_report(
        wa_number=wa_number,
        citizen_name=citizen_name,
        image_path=image_path,
        description=description,
        kota=kota,
        bank_account=bank_account or None,
        bank_name=bank_name or None,
        channel="web-upload",
    )
    return await process_report(intake_payload)


@app.post("/redeem")
async def redeem(req: RedeemRequest) -> dict:
    """Redeem RSN as Civic Credit against a retribusi bill."""
    try:
        return await redeem_civic_credit(
            req.citizen_id, req.retribusi_type, req.retribusi_amount_idr
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@app.post("/tracker/run")
async def trigger_tracker() -> dict:
    """Manually trigger one tracker cycle (demo time-jump helper)."""
    return await run_tracker_cycle()


@app.post("/portal/resolve-all")
async def portal_resolve_all() -> dict:
    """Force all open Lapor.go.id tickets to resolved (demo control)."""
    from agent.tools.lapor_portal import resolve_all_open_tickets

    count = resolve_all_open_tickets()
    actions = await run_tracker_cycle()
    return {"resolved_tickets": count, "tracker": actions}


@app.post("/demo/reset")
async def demo_reset() -> dict:
    """Wipe all demo state — for clean demo runs and video re-takes."""
    import os

    get_store().reset()
    for f in ("lapor_portal_mock.json",):
        if os.path.exists(f):
            os.remove(f)
    return {"status": "reset"}


@app.get("/reports")
async def list_reports() -> list[dict]:
    """All reports, newest first — feeds the admin dashboard."""
    reports = get_store().list_reports()
    return [r.model_dump(mode="json") for r in reports]


@app.get("/citizens")
async def list_citizens() -> list[dict]:
    return [c.model_dump(mode="json") for c in get_store().citizens.values()]


@app.get("/citizen/{citizen_id}")
async def get_citizen(citizen_id: str) -> dict:
    citizen = get_store().get_citizen(citizen_id)
    if citizen is None:
        raise HTTPException(status_code=404, detail="Citizen tidak ditemukan")
    rewards = get_store().list_rewards_by_citizen(citizen_id)
    reports = get_store().list_reports_by_citizen(citizen_id)
    return {
        "citizen": citizen.model_dump(mode="json"),
        "reports": [r.model_dump(mode="json") for r in reports],
        "rewards": [r.model_dump(mode="json") for r in rewards],
    }


@app.get("/logs")
async def agent_logs(limit: int = 50) -> list[dict]:
    """Live reasoning trace — the demo centerpiece. Newest agent steps."""
    logs = get_store().recent_logs(limit)
    return [log.model_dump(mode="json") for log in reversed(logs)]


@app.get("/heatmap")
async def heatmap() -> dict:
    """Geographic report density per city + most active citizen reporters."""
    store = get_store()
    reports = store.list_reports()

    by_city: dict[str, dict] = {}
    for r in reports:
        city = by_city.setdefault(
            r.kota, {"kota": r.kota, "total": 0, "resolved": 0, "categories": {}}
        )
        city["total"] += 1
        if r.status.value in ("resolved", "verified"):
            city["resolved"] += 1
        city["categories"][r.category] = city["categories"].get(r.category, 0) + 1

    reporter_counts: dict[str, int] = {}
    for r in reports:
        citizen = store.get_citizen(r.citizen_id)
        name = citizen.name if citizen else "Anonim"
        reporter_counts[name] = reporter_counts.get(name, 0) + 1

    return {
        "cities": sorted(by_city.values(), key=lambda c: -c["total"]),
        "top_reporters": sorted(
            ({"name": n, "reports": c} for n, c in reporter_counts.items()),
            key=lambda x: -x["reports"],
        )[:5],
    }


@app.get("/stats")
async def stats() -> dict:
    """Aggregate metrics for the dashboard hero numbers."""
    store = get_store()
    reports = store.list_reports()
    resolved = [r for r in reports if r.status.value in ("resolved", "verified")]
    return {
        "total_reports": len(reports),
        "resolved": len(resolved),
        "citizens": len(store.citizens),
        "rsn_minted": sum(
            r.points_earned for r in store.rewards.values() if r.spl_mint_tx
        ),
    }
