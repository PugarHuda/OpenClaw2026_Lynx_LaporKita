"""Pydantic data models for Rasain core entities.

These models define the contract between agents and persist throughout the flow:
Citizen → Report → Reward, tracked end-to-end.
"""
from __future__ import annotations

from datetime import datetime
from enum import Enum
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class Severity(str, Enum):
    """Tingkat keparahan masalah infrastruktur, mapping ke SLA instansi."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ReportStatus(str, Enum):
    """Status lifecycle laporan dari submit sampai verified."""
    PENDING = "pending"           # baru masuk, belum di-process agent
    CLASSIFIED = "classified"     # sudah di-classify
    SUBMITTED = "submitted"       # sudah di-submit ke Lapor.go.id
    IN_PROGRESS = "in_progress"   # instansi terima dan kerjakan
    RESOLVED = "resolved"         # instansi nyatakan selesai
    VERIFIED = "verified"         # citizen confirm impact nyata
    REJECTED = "rejected"         # tidak valid / duplikat
    EXPIRED = "expired"           # tidak ada response > SLA + escalation


class RewardStatus(str, Enum):
    """Lifecycle reward dari earn sampai redemption."""
    EARNED = "earned"             # off-chain points accumulated
    MINTED = "minted"             # SPL token minted on Solana
    REDEEMED = "redeemed"         # burned + Doku Disbursement paid
    FAILED = "failed"             # mint atau redemption gagal


class Citizen(BaseModel):
    """Warga yang lapor masalah dan terima reward."""
    id: UUID = Field(default_factory=uuid4)
    wa_number: str
    name: str
    bank_account: str | None = None       # untuk Doku Disbursement
    bank_name: str | None = None          # BCA, Mandiri, BRI, BNI
    solana_wallet: str | None = None      # custodial address (auto-gen)
    rsn_offchain: int = 0         # accumulated pre-mint
    rsn_onchain: int = 0          # SPL token balance (cached)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class Report(BaseModel):
    """Laporan masalah infrastruktur dari citizen."""
    id: UUID = Field(default_factory=uuid4)
    citizen_id: UUID
    category: str                         # e.g., "infrastruktur_jalan"
    subcategory: str | None = None
    severity: Severity = Severity.MEDIUM
    urgency: int = Field(default=3, ge=1, le=5)
    gps_lat: float | None = None
    gps_lon: float | None = None
    kota: str
    instansi_target: str                  # e.g., "Dinas PUPR Kab. Bekasi"
    photo_url: str | None = None
    description: str
    status: ReportStatus = ReportStatus.PENDING
    lapor_ticket_id: str | None = None    # ID dari Lapor.go.id mock
    classification_reasoning: str | None = None  # transparency: agent reasoning
    submitted_at: datetime = Field(default_factory=datetime.utcnow)
    resolved_at: datetime | None = None
    verified_at: datetime | None = None


class Reward(BaseModel):
    """Reward record per laporan verified."""
    id: UUID = Field(default_factory=uuid4)
    citizen_id: UUID
    report_id: UUID
    points_earned: int = 10
    status: RewardStatus = RewardStatus.EARNED
    minted_at: datetime | None = None
    spl_mint_tx: str | None = None        # Solana transaction signature
    spl_solscan_url: str | None = None    # Solscan link untuk verify
    redeemed_at: datetime | None = None
    burn_tx: str | None = None
    doku_disbursement_id: str | None = None
    idr_amount: int | None = None         # 1 RSN = Rp 1000


class AgentLogEntry(BaseModel):
    """Reasoning trace per step untuk dashboard transparency."""
    id: UUID = Field(default_factory=uuid4)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    agent_name: str                       # "classifier", "submitter", dll
    action: str                           # "classify_image", "submit_to_lapor"
    reasoning: str                        # natural language explanation
    tool_calls: list[dict] = Field(default_factory=list)
    related_report_id: UUID | None = None
    related_citizen_id: UUID | None = None
