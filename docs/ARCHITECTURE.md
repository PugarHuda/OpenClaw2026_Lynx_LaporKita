# Rasain Architecture

## System Overview

Rasain adalah multi-agent AI system yang menggabungkan **autonomous civic reporting** dengan **Web3 reward layer** untuk warga Indonesia.

## Multi-Agent Design (7 Agents)

```
┌──────────────────────────────────────────────────────────────────┐
│                       CITIZEN INTERFACE                          │
│  WhatsApp inbox  ·  Web dashboard  ·  Telegram bot (fallback)   │
└──────────────────────────────┬───────────────────────────────────┘
                               ↓
         ┌─────────────────────────────────────────┐
         │  1. INTAKE AGENT                        │
         │  Parse multimodal input                 │
         │  - text complaint                       │
         │  - photo (jpg/png)                      │
         │  - voice note (Whisper transcribe)     │
         │  - GPS coord                            │
         └────────────────┬────────────────────────┘
                          ↓ structured complaint
         ┌─────────────────────────────────────────┐
         │  2. CLASSIFIER AGENT                    │
         │  Claude vision multi-modal              │
         │  → category, severity, urgency, instansi│
         └────────────────┬────────────────────────┘
                          ↓ classified report
         ┌─────────────────────────────────────────┐
         │  3. GEOLOCATOR AGENT                    │
         │  GPS → kota → instansi tepat            │
         │  Routing rules: PUPR/DLH/PLN/PDAM/BPBD  │
         └────────────────┬────────────────────────┘
                          ↓ routed report
         ┌─────────────────────────────────────────┐
         │  4. SUBMITTER AGENT                     │
         │  Submit to Lapor.go.id (V1 mock portal) │
         │  → ticket_id                            │
         └────────────────┬────────────────────────┘
                          ↓ submitted ticket
         ┌─────────────────────────────────────────┐
         │  5. TRACKER AGENT (cron)                │
         │  Poll status setiap N menit             │
         │  Escalate kalau stuck >3 hari           │
         └────────────────┬────────────────────────┘
                          ↓ resolution event
         ┌─────────────────────────────────────────┐
         │  6. VERIFIER AGENT                      │
         │  Confirm resolution (photo proof)       │
         │  Cross-check official portal status     │
         └────────────────┬────────────────────────┘
                          ↓ verified impact
         ┌─────────────────────────────────────────┐
         │  7. REWARD AGENT                        │
         │  ├── Earn: +10 Rasain Points (off-chain) │
         │  ├── Threshold 10 → mint SPL token     │
         │  ├── Citizen redeem: burn RSN          │
         │  └── Doku Disbursement Rp 1k per RSN   │
         └─────────────────────────────────────────┘
```

## Autonomous Loop

Sistem berjalan otonom via 3 trigger mechanism:

### 1. Event-driven (Reactive)
- WhatsApp inbox webhook → Intake → trigger downstream agents
- User action di dashboard → API call → trigger agents

### 2. Cron-driven (Proactive)
- **Tracker Agent**: poll every 6 hours untuk semua active ticket
- **Verifier Agent**: re-verify resolved ticket every 24 hours
- **Reward Agent**: batch mint check every 1 hour

### 3. Threshold-driven (Reactive)
- Rasain Points accumulated → cross threshold → auto-mint SPL token
- N reports per kota → trigger aggregate insight generation

## Decision Branches (Reasoning)

Setiap agent membuat decision dinamis berdasarkan reasoning, bukan rule-based:

**Classifier Agent decision matrix:**
- IF image quality < 0.7 confidence → request better photo via WA
- IF severity = critical → fast-track ke BPBD parallel
- IF category ambigu → escalate ke human review (mock untuk demo)

**Submitter Agent decision matrix:**
- IF instansi response SLA < 24h → submit dengan urgency tag
- IF Lapor.go.id portal down → queue + retry
- IF duplicate report (similar GPS + category < 7 hari) → merge ke existing ticket

**Reward Agent decision matrix:**
- IF user wallet not yet created → auto-generate Solana keypair
- IF Rasain Points < threshold → save off-chain only
- IF threshold crossed → mint on-chain SPL token
- IF user redeem → burn + Doku Disbursement
- IF Doku Disbursement fails → rollback burn (refund)

## Tech Stack

| Layer | Tech |
|---|---|
| AI Orchestration | Claude Agent SDK Python |
| LLM | Claude Sonnet 4.6 (text + vision) |
| Payment | DOKU MCP Server (36 tools) |
| Memory | Mem9 (persistent agent state) |
| Blockchain | Solana Devnet + SPL Token Program |
| RPC | Helius free tier |
| Backend | FastAPI + Uvicorn |
| Database | SQLite + SQLAlchemy async |
| Frontend | Next.js 14 + shadcn/ui + Tailwind |
| Comms | Fonnte (WhatsApp Indonesia) |
| Scheduler | APScheduler |
| Hosting | Vercel (web) + Sumopod (agent) |

## Sponsor Tools Integration

**DOKU MCP** (Payment Track core):
- `create_virtual_account_payment` - retribusi/denda lokal
- `create_qris_payment` - donor crowdfund per kota
- `get_transaction_by_invoice_number` - poll status
- Disbursement via direct API call (reward redemption)

**Mem9** (Memory):
- Save: citizen profile, complaint history, classification feedback
- Recall: similar past cases, instansi response patterns

**Solana** (Web3 layer):
- SPL Token "Rasain Points" (RSN) on devnet
- Mint authority: backend agent wallet
- Citizen wallet: auto-generated per user (custodial V1)

**Sumopod**: Backend agent hosting (Python + APScheduler always-on)
**Repliz** (optional V2): cross-platform social media monitoring

## Data Model (Core Entities)

```python
class Citizen:
    id: UUID
    wa_number: str
    name: str
    bank_account: str  # untuk Doku Disbursement
    solana_wallet: str  # custodial wallet address
    rsn_offchain: int  # accumulated, pre-mint
    rsn_onchain: int  # SPL token balance

class Report:
    id: UUID
    citizen_id: UUID
    category: str  # infrastruktur_jalan/lampu_jalan/dll
    subcategory: str
    severity: str  # low/medium/high/critical
    urgency: int  # 1-5
    gps_lat: float
    gps_lon: float
    kota: str
    instansi_target: str
    photo_url: str
    description: str
    status: str  # submitted/in_progress/resolved/closed
    lapor_ticket_id: str  # ID from Lapor.go.id
    submitted_at: datetime
    resolved_at: datetime | None
    verified_at: datetime | None

class Reward:
    id: UUID
    citizen_id: UUID
    report_id: UUID
    points_earned: int
    minted_at: datetime | None  # ketika cross threshold
    spl_mint_tx: str | None  # Solana tx signature
    redeemed_at: datetime | None
    burn_tx: str | None
    doku_disbursement_id: str | None
    idr_amount: int | None
```

## Demo Flow (90 detik)

**Act 1 (15s) - Setup:**
- Dashboard idle, 3 citizen registered
- Solana mint Rasain Points (RSN) sudah ada

**Act 2 (60s) - Agent loop visible:**
- Trigger 3 paralel WA inbox messages dengan photo
- Logs streaming: Intake → Classifier (vision result visible) → Geolocator → Submitter → ticket created
- Sim time-jump: 2 dari 3 ticket resolved
- Verifier agent confirm impact
- Reward Agent: 2 citizen earn 10 Rasain Points each → threshold crossed → SPL token mint live (Solscan link visible)

**Act 3 (15s) - Reward Redemption:**
- Citizen click "Redeem 10 RSN" di dashboard
- Burn RSN (Solana tx visible)
- Doku Disbursement API call (HTTP response visible)
- Citizen BCA balance simulated +Rp 10.000

## Business Model (Slide 5 Pitch Deck)

| Tier | Customer | Price | TAM |
|---|---|---|---|
| B2G | Pemerintah daerah | Rp 50-200jt/tahun | Rp 51M+ (514 kab/kota) |
| B2B | Korporat ESG | Rp 500jt-2M/tahun (Adopt-a-City) | Rp 100M+ |
| B2C Premium | Citizen power user | Rp 10rb/bulan | Rp 50M+ |
| Data Marketplace | Insurance, Real Estate, Urban Planner | Rp 50-500jt per dataset | Rp 20M+ |

**Reward funding**: 40% B2B sponsorship + 10% B2G overhead + carbon credit upside (V3).

## Future Roadmap

- **V1 (today)**: Multi-agent flow + Doku reward + Solana SPL token devnet
- **V2 (3 months)**: Real Lapor.go.id API integration, multi-kota pilot dengan Pemda Bekasi
- **V3 (1 year)**: Carbon credit RWA tokenization untuk cleanup impact, DAO governance per kota
