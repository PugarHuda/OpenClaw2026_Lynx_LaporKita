"""Rasain FastAPI backend — HTTP bridge between the agent and the dashboard.

Exposes the orchestrator's capabilities as REST endpoints, plus a live
reasoning-trace feed (the demo centerpiece). An APScheduler job runs the
autonomous tracker loop on an interval — no human trigger.
"""
from __future__ import annotations

from contextlib import asynccontextmanager

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from agent.config import get_settings
from agent.orchestrator import process_report, run_tracker_cycle
from agent.store import get_store
from agent.tools.intake import intake_report
from agent.tools.reward import redeem_civic_credit

# Tracker cycle interval. Short for demo; in production this would be minutes.
TRACKER_INTERVAL_SECONDS = 20

scheduler = AsyncIOScheduler()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Start the autonomous tracker loop on boot, stop it on shutdown."""
    scheduler.add_job(
        run_tracker_cycle,
        "interval",
        seconds=TRACKER_INTERVAL_SECONDS,
        id="tracker_cycle",
        max_instances=1,
    )
    scheduler.start()
    yield
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
