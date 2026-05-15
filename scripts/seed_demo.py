"""Seed the RUNNING Rasain backend with real demo data over HTTP.

Unlike scripts/demo.py (which runs the pipeline in-process, in its own store),
this script drives the live API — so the dashboard the judges watch is
populated with genuine data:

  * real infrastructure photos (data/images/*.jpg) — real Claude vision calls
  * real agency routing, real Lapor.go.id tickets, real agent reasoning trace
  * real Solana SPL mints once reports are verified (RSN on-chain)
  * a real DOKU QRIS from one Civic Credit redemption

Run (with the backend up on :8000):  python scripts/seed_demo.py
Target another host:                  API_URL=https://... python scripts/seed_demo.py
"""
from __future__ import annotations

import os
import sys
import time
from pathlib import Path

import httpx

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

API_URL = os.getenv("API_URL", "http://localhost:8000").rstrip("/")
IMAGES = Path(__file__).resolve().parent.parent / "data" / "images"

# Real photos + realistic citizen reports. Warga 628110000001 reports twice —
# becomes a "top reporter" and accumulates enough RSN to redeem.
REPORTS = [
    {
        "file": "pothole-road.jpg", "wa_number": "628110000001", "kota": "Yogyakarta",
        "description": "Jalan berlubang besar di tikungan dekat SD, sudah beberapa "
                       "pemotor terjatuh terutama saat hujan",
    },
    {
        "file": "broken-streetlight.jpg", "wa_number": "628110000001", "kota": "Yogyakarta",
        "description": "Lampu PJU mati total sepanjang Jl. Diponegoro, gelap gulita "
                       "dan rawan tindak kejahatan di malam hari",
    },
    {
        "file": "garbage-pile.jpg", "wa_number": "628110000002", "kota": "Surabaya",
        "description": "Sampah menumpuk di TPS pasar lebih dari seminggu tidak diangkut, "
                       "bau menyengat sampai ke rumah warga",
    },
    {
        "file": "fallen-tree.jpg", "wa_number": "628110000003", "kota": "Bandung",
        "description": "Pohon besar tumbang menutup separuh badan jalan setelah angin "
                       "kencang, lalu lintas tersendat",
    },
    {
        "file": "flood-street.jpg", "wa_number": "628110000004", "kota": "Jakarta",
        "description": "Banjir merendam jalan di depan pertokoan, kendaraan sulit lewat, "
                       "drainase meluap setiap hujan deras",
    },
]


def _hr(title: str) -> None:
    print(f"\n{'=' * 64}\n  {title}\n{'=' * 64}")


def _wait_verified(client: httpx.Client, expected: int, timeout: int = 70) -> int:
    """Poll until the autonomous tracker has verified all resolved reports."""
    deadline = time.time() + timeout
    resolved = 0
    while time.time() < deadline:
        resolved = client.get("/stats").json().get("resolved", 0)
        if resolved >= expected:
            return resolved
        time.sleep(5)
    return resolved


def main() -> None:
    client = httpx.Client(base_url=API_URL, timeout=90)

    try:
        client.get("/health").raise_for_status()
    except Exception as e:
        sys.exit(f"Backend tidak merespon di {API_URL} — jalankan dulu uvicorn. ({e})")

    _hr(f"SEED RASAIN — data demo nyata · target {API_URL}")
    client.post("/demo/reset").raise_for_status()
    print("  store di-reset — mulai dari nol")

    # --- Submit real photo reports through the real pipeline ---
    _hr("Mengirim laporan warga (foto nyata → AI vision → routing → submit)")
    submitted = 0
    for r in REPORTS:
        img = IMAGES / r["file"]
        if not img.exists():
            print(f"  ! lewati {r['file']} — file tidak ditemukan")
            continue
        with img.open("rb") as fh:
            resp = client.post(
                "/report/upload",
                files={"photo": (r["file"], fh, "image/jpeg")},
                data={
                    "wa_number": r["wa_number"],
                    "citizen_name": "warga",  # diabaikan — laporan anonim
                    "description": r["description"],
                    "kota": r["kota"],
                },
            )
        if resp.status_code >= 300:
            print(f"  ! {r['file']} gagal: {resp.status_code} {resp.text[:120]}")
            continue
        d = resp.json()
        if d.get("status") == "submitted":
            submitted += 1
            print(f"  ✓ {r['kota']:11} {d['category']:22} "
                  f"{d['severity']:8} → {d['instansi_target']}")
        else:
            print(f"  · {r['kota']:11} status={d.get('status')}")
        time.sleep(1)  # ramah ke rate limit gateway AI

    # --- Agencies resolve the tickets → autonomous tracker verifies + mints RSN ---
    _hr("Instansi merespon → tracker otonom verifikasi & mint RSN on-chain")
    res = client.post("/portal/resolve-all", timeout=120).json()
    print(f"  tiket di-resolve : {res.get('resolved_tickets', 0)}")
    print("  menunggu tracker otonom memverifikasi & mint RSN…")
    verified = _wait_verified(client, submitted)
    print(f"  terverifikasi    : {verified}/{submitted}")

    # --- Richest citizen redeems RSN as Civic Credit (burn + DOKU QRIS) ---
    _hr("Warga menukar RSN jadi Civic Credit (burn on-chain + QRIS DOKU)")
    citizens = client.get("/citizens").json()
    holder = max(citizens, key=lambda c: c.get("rsn_onchain", 0), default=None)
    if holder and holder.get("rsn_onchain", 0) > 0:
        print(f"  warga    : {holder['name']}  ·  wallet {holder['solana_wallet'][:20]}…")
        print(f"  RSN saldo: {holder['rsn_onchain']}")
        rd = client.post("/redeem", json={
            "citizen_id": holder["id"],
            "retribusi_type": "sampah",
            "retribusi_amount_idr": 25000,
        }, timeout=120)
        if rd.status_code < 300:
            d = rd.json()
            print(f"  retribusi: Rp {d['retribusi_amount_idr']:,}")
            print(f"  RSN pakai: {d['rsn_used']} (potongan Rp {d['idr_offset']:,})")
            print(f"  sisa     : Rp {d['cash_due_idr']:,} → QRIS DOKU")
            if d.get("burn_tx"):
                print(f"  burn tx  : {d['burn_tx'][:32]}…")
        else:
            print(f"  ! redeem gagal: {rd.status_code} {rd.text[:120]}")
    else:
        print("  (belum ada warga dengan RSN on-chain — tracker belum selesai)")

    # --- Summary ---
    stats = client.get("/stats").json()
    logs = client.get("/logs?limit=200").json()
    _hr("SELESAI — backend siap untuk demo")
    print(f"  laporan        : {stats['total_reports']}")
    print(f"  terselesaikan  : {stats['resolved']}")
    print(f"  warga          : {stats['citizens']}")
    print(f"  RSN diterbitkan: {stats['rsn_minted']}")
    print(f"  jejak reasoning agent: {len(logs)} langkah tercatat")
    client.close()


if __name__ == "__main__":
    main()
