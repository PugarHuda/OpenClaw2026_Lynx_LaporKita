"""Geolocator Agent tool — route a classified report to the correct government agency.

Given a category + city (+ optional GPS), determines which Indonesian government
institution is responsible (Dinas PUPR, DLH, PLN, etc.) and the typical SLA.

Routing is reference-data driven (data/seed/), so onboarding a new city or
agency mapping is a JSON edit, not a code change.
"""
from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

_KATEGORI_PATH = Path("data/seed/instansi_kategori_indonesia.json")
_KOTA_PATH = Path("data/seed/kota_indonesia_top10.json")


def _load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Great-circle distance between two GPS points, in kilometers."""
    r = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return r * 2 * math.asin(math.sqrt(a))


def nearest_city(lat: float, lon: float) -> dict[str, Any]:
    """Find the nearest known Indonesian city to a GPS coordinate."""
    kota_data = _load(_KOTA_PATH)
    best: dict[str, Any] | None = None
    best_dist = float("inf")
    for kota in kota_data["kota"]:
        dist = _haversine_km(lat, lon, kota["lat"], kota["lon"])
        if dist < best_dist:
            best_dist, best = dist, kota
    return {**best, "distance_km": round(best_dist, 1)} if best else {}


def route_to_instansi(
    category: str,
    kota: str,
    gps_lat: float | None = None,
    gps_lon: float | None = None,
) -> dict[str, Any]:
    """Determine the responsible government agency for a report.

    Args:
        category: Category key from the taxonomy (e.g. "infrastruktur_jalan").
        kota: City name. If empty and GPS given, inferred from GPS.
        gps_lat, gps_lon: Optional GPS for city inference.

    Returns:
        Dict with instansi_target, instansi_level, expected_sla_days, kota.
    """
    taxonomy = _load(_KATEGORI_PATH)
    categories = taxonomy["kategori_masalah"]

    if category not in categories:
        return {
            "instansi_target": "Lapor.go.id (kategori umum)",
            "instansi_level": "nasional",
            "expected_sla_days": 14,
            "kota": kota,
            "routing_note": f"Kategori '{category}' tidak dikenali, route ke kanal umum.",
        }

    # Infer city from GPS if not provided.
    if not kota and gps_lat is not None and gps_lon is not None:
        nearest = nearest_city(gps_lat, gps_lon)
        kota = nearest.get("nama", "")

    cat = categories[category]
    # Prefer kabupaten/kota level agency (closest to citizen), fallback up.
    instansi_base = (
        cat.get("instansi_kabkota")
        or cat.get("instansi_provinsi")
        or cat.get("instansi_pusat")
        or "Lapor.go.id"
    )
    instansi_level = (
        "kabupaten/kota" if cat.get("instansi_kabkota")
        else "provinsi" if cat.get("instansi_provinsi")
        else "nasional"
    )
    # Compose a concrete agency name with the city appended.
    instansi_target = f"{instansi_base} {kota}".strip() if kota else instansi_base

    sla_map = taxonomy.get("instansi_response_sla_typical_days", {})
    expected_sla = next(
        (days for name, days in sla_map.items() if name.split()[0] in instansi_base),
        14,
    )

    return {
        "instansi_target": instansi_target,
        "instansi_level": instansi_level,
        "expected_sla_days": expected_sla,
        "kota": kota or "tidak diketahui",
        "category_name": cat["nama"],
    }
