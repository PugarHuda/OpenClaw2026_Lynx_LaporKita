"""Classifier Agent tool — Claude vision multi-modal classification of infrastructure issues.

This is the "eyes" of LaporKita. Given a citizen's photo (and optional text/GPS),
it returns a structured classification that downstream agents route on.

Design: classification taxonomy is injected from data/seed/, not hardcoded in the
prompt — so adding a category is a JSON edit, not a code change.
"""
from __future__ import annotations

import base64
import json
from pathlib import Path
from typing import Any

from anthropic import Anthropic

from agent.config import get_settings

_SEED_PATH = Path("data/seed/instansi_kategori_indonesia.json")


def _load_taxonomy() -> dict[str, Any]:
    """Load Indonesia infrastructure category taxonomy from seed data."""
    return json.loads(_SEED_PATH.read_text(encoding="utf-8"))


def _image_to_base64(image_path: str) -> tuple[str, str]:
    """Read image file → (media_type, base64_data)."""
    path = Path(image_path)
    suffix = path.suffix.lower()
    media_type = {
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".png": "image/png",
        ".webp": "image/webp",
    }.get(suffix, "image/jpeg")
    data = base64.standard_b64encode(path.read_bytes()).decode("utf-8")
    return media_type, data


# Tool schema yang dipakai Claude untuk structured output (zero parse error).
CLASSIFICATION_TOOL = {
    "name": "submit_classification",
    "description": "Submit hasil klasifikasi masalah infrastruktur publik.",
    "input_schema": {
        "type": "object",
        "properties": {
            "category": {
                "type": "string",
                "description": "Kategori utama masalah (kunci dari taxonomy)",
            },
            "subcategory": {
                "type": "string",
                "description": "Subkategori spesifik",
            },
            "severity": {
                "type": "string",
                "enum": ["low", "medium", "high", "critical"],
                "description": "Tingkat keparahan berdasarkan dampak yang TERLIHAT di foto + konteks",
            },
            "urgency": {
                "type": "integer",
                "minimum": 1,
                "maximum": 5,
                "description": "1=informasi, 3=tindakan 7 hari, 5=darurat <24 jam",
            },
            "is_valid_report": {
                "type": "boolean",
                "description": "False jika foto bukan masalah infrastruktur (selfie, spam, dll)",
            },
            "confidence": {
                "type": "number",
                "minimum": 0,
                "maximum": 1,
                "description": "Keyakinan klasifikasi 0-1",
            },
            "reasoning": {
                "type": "string",
                "description": "Penjelasan singkat: apa yang terlihat di foto, kenapa severity & urgency dipilih. Bahasa Indonesia.",
            },
            "suggested_instansi_type": {
                "type": "string",
                "description": "Tipe instansi yang berwenang (e.g. 'Dinas PUPR', 'DLH', 'PLN')",
            },
        },
        "required": [
            "category", "severity", "urgency", "is_valid_report",
            "confidence", "reasoning", "suggested_instansi_type",
        ],
    },
}


def _build_system_prompt(taxonomy: dict[str, Any]) -> str:
    """Build the classifier system prompt with injected taxonomy."""
    categories = taxonomy["kategori_masalah"]
    cat_lines = []
    for key, val in categories.items():
        subs = ", ".join(val.get("subkategori", []))
        instansi = val.get("instansi_kabkota", val.get("instansi_pusat", "-"))
        cat_lines.append(f"- {key} ({val['nama']}): subkategori=[{subs}] → {instansi}")
    taxonomy_block = "\n".join(cat_lines)

    return f"""Kamu adalah Classifier Agent untuk LaporKita — sistem pelaporan masalah \
infrastruktur publik Indonesia.

Tugasmu: lihat foto yang dikirim warga, klasifikasikan masalahnya secara akurat.

TAXONOMY KATEGORI (pilih category dari kunci ini):
{taxonomy_block}

PANDUAN PENILAIAN SEVERITY (gunakan KONTEKS VISUAL, bukan cuma jenis objek):
- low: masalah kecil, tidak mengganggu, tidak ada risiko keselamatan
- medium: mengganggu aktivitas, perlu perbaikan terjadwal
- high: kerusakan signifikan, ada risiko keselamatan, mengganggu banyak orang
- critical: bahaya fatal/segera, akses terputus, butuh respon darurat

PANDUAN URGENCY (1-5):
- 1: informasi/saran, 2: tindakan 30 hari, 3: tindakan 7 hari,
- 4: tindakan 48 jam, 5: darurat <24 jam

PRINSIP PENTING:
1. Severity ditentukan KONTEKS, bukan jenis objek. Lubang jalan di gang sepi = \
medium; lubang sama persis di tikungan tajam jalan ramai = high (risiko kecelakaan).
2. Jika foto BUKAN masalah infrastruktur publik (selfie, makanan, spam, \
foto dalam ruangan pribadi) → set is_valid_report=false.
3. confidence rendah (<0.6) jika foto blur/gelap/ambigu — downstream akan minta foto ulang.
4. reasoning HARUS sebutkan: (a) apa yang terlihat, (b) kenapa severity dipilih, \
(c) kenapa urgency dipilih. Bahasa Indonesia, ringkas tapi konkret.

Selalu panggil tool submit_classification dengan hasil analisismu."""


def classify_infrastructure_issue(
    image_path: str,
    description: str | None = None,
    kota: str | None = None,
) -> dict[str, Any]:
    """Classify an infrastructure problem photo.

    Args:
        image_path: Path ke file foto masalah.
        description: Teks deskripsi opsional dari warga.
        kota: Nama kota opsional (membantu konteks).

    Returns:
        Dict hasil klasifikasi (lihat CLASSIFICATION_TOOL schema).
    """
    settings = get_settings()
    taxonomy = _load_taxonomy()
    client = Anthropic(api_key=settings.anthropic_api_key) if settings.anthropic_api_key else Anthropic()

    media_type, image_data = _image_to_base64(image_path)

    user_content: list[dict[str, Any]] = [
        {
            "type": "image",
            "source": {"type": "base64", "media_type": media_type, "data": image_data},
        }
    ]
    context_parts = []
    if description:
        context_parts.append(f"Deskripsi warga: {description}")
    if kota:
        context_parts.append(f"Kota: {kota}")
    user_content.append({
        "type": "text",
        "text": "\n".join(context_parts) if context_parts
        else "Klasifikasikan masalah infrastruktur di foto ini.",
    })

    response = client.messages.create(
        model=settings.anthropic_vision_model,
        max_tokens=1024,
        system=_build_system_prompt(taxonomy),
        tools=[CLASSIFICATION_TOOL],
        tool_choice={"type": "tool", "name": "submit_classification"},
        messages=[{"role": "user", "content": user_content}],
    )

    for block in response.content:
        if block.type == "tool_use" and block.name == "submit_classification":
            return dict(block.input)

    raise RuntimeError("Classifier tidak mengembalikan structured output")
