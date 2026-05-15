"""Classifier Agent tool — multi-modal classification of infrastructure issues.

The "eyes" of Rasain. Given a citizen's photo (+ optional text/GPS), returns a
structured classification that downstream agents route on.

Vision runs through the **Sumopod AI gateway** (OpenAI-compatible) using a Claude
vision model. Falls back to a deterministic keyword classifier (DEMO_MODE) when
no Sumopod key is configured — so the pipeline always runs.

Design: the classification taxonomy is injected from data/seed/, not hardcoded
in the prompt — adding a category is a JSON edit, not a code change.
"""
from __future__ import annotations

import base64
import json
from pathlib import Path
from typing import Any

from openai import OpenAI

from agent.config import get_settings

_SEED_PATH = Path("data/seed/instansi_kategori_indonesia.json")


def _load_taxonomy() -> dict[str, Any]:
    """Load Indonesia infrastructure category taxonomy from seed data."""
    return json.loads(_SEED_PATH.read_text(encoding="utf-8"))


def _image_to_data_uri(image_path: str) -> str:
    """Read image file → data URI for OpenAI-compatible vision input."""
    path = Path(image_path)
    media_type = {
        ".jpg": "image/jpeg", ".jpeg": "image/jpeg",
        ".png": "image/png", ".webp": "image/webp",
    }.get(path.suffix.lower(), "image/jpeg")
    data = base64.standard_b64encode(path.read_bytes()).decode("utf-8")
    return f"data:{media_type};base64,{data}"


# JSON schema for the classifier's structured output (zero parse error).
_SCHEMA = {
    "type": "object",
    "properties": {
        "report_type": {
            "type": "string",
            "enum": ["civic", "product_defect"],
            "description": "civic = masalah infrastruktur publik (jalan, lampu, "
            "sampah). product_defect = barang/produk cacat atau bug yang dilaporkan "
            "ke perusahaan.",
        },
        "category": {"type": "string", "description": "Kategori utama (kunci taxonomy)"},
        "subcategory": {"type": "string", "description": "Subkategori spesifik"},
        "severity": {
            "type": "string", "enum": ["low", "medium", "high", "critical"],
            "description": "Keparahan berdasarkan dampak TERLIHAT di foto + konteks",
        },
        "urgency": {
            "type": "integer", "minimum": 1, "maximum": 5,
            "description": "1=informasi, 3=tindakan 7 hari, 5=darurat <24 jam",
        },
        "is_valid_report": {
            "type": "boolean",
            "description": "False jika foto bukan masalah infrastruktur publik",
        },
        "confidence": {"type": "number", "minimum": 0, "maximum": 1},
        "reasoning": {
            "type": "string",
            "description": "Penjelasan: apa yang terlihat, kenapa severity & urgency "
            "dipilih. Bahasa Indonesia, ringkas dan konkret.",
        },
        "suggested_instansi_type": {
            "type": "string",
            "description": "Tipe instansi berwenang (Dinas PUPR, DLH, PLN, dll)",
        },
    },
    "required": [
        "report_type", "category", "severity", "urgency", "is_valid_report",
        "confidence", "reasoning", "suggested_instansi_type",
    ],
}

def _build_tool(taxonomy: dict[str, Any]) -> dict[str, Any]:
    """Build the classification tool with `category` constrained to taxonomy keys.

    The enum forces the model to return an exact key the Geolocator can route on.
    """
    schema = json.loads(json.dumps(_SCHEMA))  # deep copy
    schema["properties"]["category"]["enum"] = list(taxonomy["kategori_masalah"].keys())
    return {
        "type": "function",
        "function": {
            "name": "submit_classification",
            "description": "Submit hasil klasifikasi masalah infrastruktur publik.",
            "parameters": schema,
        },
    }


def _build_system_prompt(taxonomy: dict[str, Any]) -> str:
    """Build the classifier system prompt with the injected taxonomy."""
    cat_lines = []
    for key, val in taxonomy["kategori_masalah"].items():
        subs = ", ".join(val.get("subkategori", []))
        instansi = val.get("instansi_kabkota", val.get("instansi_pusat", "-"))
        cat_lines.append(f"- {key} ({val['nama']}): subkategori=[{subs}] -> {instansi}")
    taxonomy_block = "\n".join(cat_lines)

    return f"""Kamu Classifier Agent untuk Rasain — sistem pelaporan masalah \
infrastruktur publik Indonesia. Lihat foto warga, klasifikasikan akurat.

TAXONOMY KATEGORI (pilih category dari kunci ini):
{taxonomy_block}

SEVERITY (pakai KONTEKS VISUAL, bukan cuma jenis objek):
- low: kecil, tidak mengganggu, tanpa risiko keselamatan
- medium: mengganggu aktivitas, perlu perbaikan terjadwal
- high: kerusakan signifikan, ada risiko keselamatan, ganggu banyak orang
- critical: bahaya fatal/segera, akses terputus, butuh respon darurat

URGENCY 1-5: 1=info, 2=30 hari, 3=7 hari, 4=48 jam, 5=darurat <24 jam

JENIS LAPORAN (report_type):
- civic: masalah infrastruktur publik (jalan, lampu, sampah, drainase) → pemerintah
- product_defect: barang/produk cacat, kemasan rusak, makanan basi, atau bug \
produk yang dilaporkan ke perusahaan/produsen

PRINSIP:
1. Severity ditentukan KONTEKS. Lubang di gang sepi = medium; lubang sama di \
tikungan ramai = high (risiko kecelakaan).
2. Foto BUKAN masalah infrastruktur publik DAN bukan produk cacat -> is_valid_report=false.
3. confidence <0.6 jika foto blur/gelap/ambigu.
4. reasoning sebut: (a) apa yang terlihat, (b) alasan severity, (c) alasan urgency.

Selalu panggil tool submit_classification."""


def _mock_classification(description: str | None) -> dict[str, Any]:
    """DEMO_MODE fallback — keyword classifier when no Sumopod key is set."""
    text = (description or "").lower()
    rules = [
        (("sampah", "tps", "kotor"), "sampah_kebersihan", "sampah_menumpuk", "DLH"),
        (("lampu", "pju", "gelap"), "lampu_jalan", "lampu_mati", "Dinas Perhubungan"),
        (("banjir", "drainase", "got"), "drainase_banjir", "drainase_mampet", "Dinas PUPR"),
        (("pohon", "tumbang"), "pohon_taman", "pohon_tumbang", "DLHK"),
        (("listrik", "tiang", "kabel"), "listrik_pln", "tiang_miring", "PLN"),
    ]
    category, subcategory, instansi = "infrastruktur_jalan", "jalan_berlubang", "Dinas PUPR"
    for keywords, cat, sub, ins in rules:
        if any(k in text for k in keywords):
            category, subcategory, instansi = cat, sub, ins
            break
    # Product-defect detection keywords.
    is_defect = any(
        k in text for k in ("cacat", "rusak produk", "barang", "kemasan",
                             "basi", "kadaluarsa", "bug", "garansi", "produk")
    )
    severe = "parah" in text or "bahaya" in text
    return {
        "report_type": "product_defect" if is_defect else "civic",
        "category": category, "subcategory": subcategory,
        "severity": "high" if severe else "medium",
        "urgency": 4 if severe else 3,
        "is_valid_report": True, "confidence": 0.82,
        "reasoning": f"Klasifikasi berbasis kata kunci dari deskripsi '{description}'. "
        f"Terdeteksi kategori {category}. (DEMO_MODE — set SUMOPOD_API_KEY untuk "
        f"analisis vision penuh.)",
        "suggested_instansi_type": instansi,
        "_demo_mode": True,
    }


def classify_infrastructure_issue(
    image_path: str,
    description: str | None = None,
    kota: str | None = None,
) -> dict[str, Any]:
    """Classify an infrastructure problem photo.

    Uses Sumopod AI (Claude vision) when SUMOPOD_API_KEY is set; otherwise falls
    back to a deterministic keyword classifier (DEMO_MODE).

    Returns a dict matching the classification schema.
    """
    settings = get_settings()
    if not settings.sumopod_api_key:
        return _mock_classification(description)

    taxonomy = _load_taxonomy()
    client = OpenAI(api_key=settings.sumopod_api_key, base_url=settings.sumopod_base_url)

    context = []
    if description:
        context.append(f"Deskripsi warga: {description}")
    if kota:
        context.append(f"Kota: {kota}")
    context_text = "\n".join(context) or "Klasifikasikan masalah infrastruktur di foto ini."

    user_content: list[dict[str, Any]] = [{"type": "text", "text": context_text}]
    # Attach the photo unless this is a text-only path.
    if image_path and Path(image_path).exists():
        user_content.append(
            {"type": "image_url", "image_url": {"url": _image_to_data_uri(image_path)}}
        )

    response = client.chat.completions.create(
        model=settings.sumopod_vision_model,
        max_tokens=1024,
        messages=[
            {"role": "system", "content": _build_system_prompt(taxonomy)},
            {"role": "user", "content": user_content},
        ],
        tools=[_build_tool(taxonomy)],
        tool_choice={"type": "function", "function": {"name": "submit_classification"}},
    )

    tool_calls = response.choices[0].message.tool_calls
    if not tool_calls:
        raise RuntimeError("Classifier tidak mengembalikan structured output")
    return json.loads(tool_calls[0].function.arguments)
