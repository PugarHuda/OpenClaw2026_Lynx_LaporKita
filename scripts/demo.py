"""End-to-end demo of the Rasain autonomous multi-agent system.

Run:  python scripts/demo.py

Exercises the FULL pipeline with three citizen reports:
  intake -> classify -> route -> submit -> (time-jump) -> track -> verify
  -> reward (mint RSN) -> redeem Civic Credit (burn RSN + DOKU QRIS)

Works WITHOUT credentials (DEMO_MODE auto-fallback for classifier/Doku/Solana),
so any validator can reproduce it. With credentials in .env it runs fully live.
"""
from __future__ import annotations

import asyncio
import sys

# Windows consoles default to cp1252 — force UTF-8 so reasoning traces print.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from agent.orchestrator import process_report, run_tracker_cycle
from agent.store import get_store
from agent.tools.intake import intake_report
from agent.tools.lapor_portal import advance_ticket_status
from agent.tools.reward import redeem_civic_credit

SCENARIOS = [
    {
        "wa_number": "6281200000001", "citizen_name": "Budi Santoso",
        "image_path": "data/images/jalan_bekasi.jpg", "kota": "Bekasi",
        "description": "Jalan berlubang parah di tikungan ramai, bahaya buat motor",
        "bank_account": "1234567801", "bank_name": "BCA",
    },
    {
        "wa_number": "6281200000002", "citizen_name": "Siti Aminah",
        "image_path": "data/images/sampah_surabaya.jpg", "kota": "Surabaya",
        "description": "Sampah menumpuk di TPS sudah seminggu, bau menyengat",
        "bank_account": "1234567802", "bank_name": "Mandiri",
    },
    {
        "wa_number": "6281200000003", "citizen_name": "Joko Widodo",
        "image_path": "data/images/lampu_jakarta.jpg", "kota": "Jakarta",
        "description": "Lampu jalan PJU mati total sepanjang gang, gelap rawan",
        "bank_account": "1234567803", "bank_name": "BRI",
    },
]


def _hr(title: str) -> None:
    print(f"\n{'=' * 64}\n  {title}\n{'=' * 64}")


async def main() -> None:
    store = get_store()
    store.reset()
    _hr("RASAIN — Autonomous Civic Reporting Agent · DEMO")

    # --- Step 1: Three citizens submit reports ---
    _hr("STEP 1 — Citizens submit reports (Intake -> Classify -> Route -> Submit)")
    results = []
    for s in SCENARIOS:
        payload = intake_report(**s, channel="demo")
        result = await process_report(payload)
        results.append(result)
        print(f"\n  [{s['citizen_name']}] {s['kota']}")
        print(f"    status        : {result['status']}")
        if result["status"] == "submitted":
            print(f"    category      : {result['category']} ({result['severity']})")
            print(f"    instansi      : {result['instansi_target']}")
            print(f"    lapor ticket  : {result['ticket_id']}")
            print(f"    reasoning     : {result['classification_reasoning'][:90]}...")

    # --- Step 2: Simulate agency resolving 2 of 3 tickets (demo time-jump) ---
    _hr("STEP 2 — Time-jump: 2 of 3 agencies resolve the reports")
    reports = store.list_reports()
    for report in reports[:2]:
        if report.lapor_ticket_id:
            advance_ticket_status(report.lapor_ticket_id, "resolved")
            print(f"  {report.lapor_ticket_id} -> resolved ({report.kota})")
    print(f"  {reports[2].lapor_ticket_id} -> still in progress ({reports[2].kota})")

    # --- Step 3: Autonomous tracker cycle verifies + rewards ---
    _hr("STEP 3 — Autonomous tracker cycle (no human trigger)")
    actions = await run_tracker_cycle()
    print(f"  polled={actions['polled']}  verified={actions['verified']}  "
          f"escalated={actions['escalated']}  rewards_minted={actions['rewards_minted']}")

    # --- Step 4: Citizen redeems RSN as Civic Credit ---
    _hr("STEP 4 — Citizen redeems Rasain Points as Civic Credit")
    citizen = next(
        (c for c in store.citizens.values() if c.solana_wallet), None
    )
    if citizen:
        print(f"  Citizen: {citizen.name}  ·  wallet: {citizen.solana_wallet[:16]}...")
        redemption = await redeem_civic_credit(str(citizen.id), "sampah", 25000)
        print(f"    retribusi      : Rp {redemption['retribusi_amount_idr']:,}")
        print(f"    RSN dipakai    : {redemption['rsn_used']} "
              f"(offset Rp {redemption['idr_offset']:,})")
        print(f"    sisa bayar     : Rp {redemption['cash_due_idr']:,} (via DOKU QRIS)")
        if redemption.get("burn_tx"):
            print(f"    burn tx        : {redemption['burn_tx'][:24]}...")
    else:
        print("  (Belum ada citizen dengan RSN — perlu laporan verified dulu.)")

    # --- Step 5: Agent reasoning trace ---
    _hr("STEP 5 — Agent reasoning trace (proof of autonomy)")
    for log in store.recent_logs(20):
        print(f"  [{log.agent_name:11}] {log.action:20} {log.reasoning[:70]}")

    _hr("DEMO COMPLETE")


if __name__ == "__main__":
    asyncio.run(main())
