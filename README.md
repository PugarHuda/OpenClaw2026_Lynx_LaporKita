# Rasain

> **Autonomous multi-agent system for civic infrastructure reporting in Indonesia.**
> *Laporkan masalah, rasain perubahannya.*

**OpenClaw Agenthon Indonesia 2026** · Tim **hayoloh** · Track: Juara Umum + **Best Payment Use Case (DOKU)**

---

## What is Rasain?

280 juta warga Indonesia menghadapi masalah infrastruktur publik setiap hari — jalan
berlubang, lampu jalan mati, sampah menumpuk, drainase mampet. Portal pemerintah
**Lapor.go.id** ada, tapi *response rate* rendah dan warga tidak punya insentif untuk
melapor.

**Rasain** adalah sistem **multi-agent AI otonom** yang menyelesaikan ini:

1. **Warga lapor** lewat foto + deskripsi (web / WhatsApp / Telegram)
2. **AI agent mengklasifikasi** masalah pakai Claude vision (kategori, severity, urgensi)
3. **AI agent merutekan** ke instansi pemerintah yang tepat (Dinas PUPR, DLH, PLN, dll)
4. **AI agent submit** ke Lapor.go.id dan **melacak** status secara otonom
5. Saat masalah **terverifikasi selesai**, warga dapat **Rasain Points (RSN)** —
   token SPL di Solana sebagai *proof of impact*
6. Warga **menukar RSN sebagai Civic Credit**: RSN di-*burn* on-chain, sisa tagihan
   retribusi pemerintah dibayar via **DOKU QRIS**

> **Civic engagement → civic credit.** Berkontribusi melaporkan masalah kota
> secara harfiah membantu warga membayar kewajiban sipilnya.

## Autonomous Multi-Agent Architecture

7 agent spesialis, dikoordinasi oleh orchestrator dengan **autonomous loop**:

```
Citizen → Intake → Classifier (vision) → Geolocator → Submitter (Lapor.go.id)
                                                            |
            Reward <- Verifier <- Tracker (cron loop, no human trigger)
              |
   +----------+----------+
   Solana SPL mint     DOKU QRIS (Civic Credit redemption)
```

| Agent | Tugas | Tools |
|---|---|---|
| **Intake** | Normalisasi laporan dari channel apapun | — |
| **Classifier** | Klasifikasi foto via Claude vision | Sumopod AI (Claude Haiku 4.5) |
| **Geolocator** | Routing ke instansi + SLA | reference data |
| **Submitter** | Submit ke Lapor.go.id | portal API |
| **Tracker** | Poll status + eskalasi (autonomous cron) | portal API |
| **Verifier** | Verifikasi resolusi → trigger reward | — |
| **Reward** | Mint/burn RSN + DOKU Civic Credit | Solana SPL, DOKU MCP |

**Dua entry point autonomous loop:**
- `process_report()` — event-driven (laporan masuk)
- `run_tracker_cycle()` — **cron-driven, zero human input** (tiap 20 detik)

Setiap langkah menulis *reasoning trace* — dashboard menampilkan "jejak pikir" agent
secara live. Detail lengkap: [`docs/ARCHITECTURE.md`](./docs/ARCHITECTURE.md).

## Quick Start

### Prasyarat
- Python 3.11+
- Node.js 20+

### 1. Backend (agent + API)

```bash
git clone https://github.com/PugarHuda/OpenClaw2026_hayoloh_Rasain.git
cd OpenClaw2026_hayoloh_Rasain

python -m venv .venv
# Windows:        .venv\Scripts\activate
# macOS / Linux:  source .venv/bin/activate
pip install -e .

cp .env.example .env          # opsional — lihat "DEMO_MODE" di bawah
uvicorn api.main:app --port 8000
```

### 2. Frontend (dashboard)

```bash
cd web
npm install
npm run dev                   # http://localhost:3000
```

### 3. Jalankan demo end-to-end (cara tercepat memverifikasi)

```bash
python scripts/demo.py
```

Ini menjalankan SELURUH pipeline: 3 warga melapor → klasifikasi → routing →
submit → verifikasi otonom → mint RSN → redeem Civic Credit — dan mencetak
*reasoning trace* tiap agent.

## DEMO_MODE — Berjalan Tanpa Credentials

**`python scripts/demo.py` dan seluruh sistem berjalan penuh tanpa credential apapun.**

Setiap tool eksternal *graceful-degrade* ke mock yang realistis bila credential
tidak ada:

| Tool | Dengan credential | Tanpa credential (DEMO_MODE) |
|---|---|---|
| Classifier | Claude vision sungguhan | Klasifikasi berbasis kata kunci |
| DOKU | QRIS/VA live via DOKU MCP | Mock QRIS (struktur respons sama) |
| Solana | Mint/burn SPL on-chain | Mock signature tx |

Untuk menjalankan **mode live penuh**, isi `.env` (lihat `.env.example`):
- `ANTHROPIC_API_KEY` — Claude vision
- `DOKU_CLIENT_ID` + `DOKU_AUTHORIZATION_BASE64` — DOKU MCP sandbox
- `SOLANA_MINT_AUTHORITY_KEYPAIR_PATH` + `RSN_MINT_ADDRESS` — Solana devnet
  (jalankan `python scripts/setup_solana.py` untuk membuat mint)

## API Endpoints

| Method | Path | Fungsi |
|---|---|---|
| POST | `/report` | Submit laporan (jalankan pipeline) |
| POST | `/redeem` | Tukar RSN jadi Civic Credit |
| POST | `/tracker/run` | Trigger satu siklus tracker |
| POST | `/portal/resolve-all` | Simulasi instansi menyelesaikan laporan (demo) |
| GET | `/reports` `/citizens` `/logs` `/stats` | Data untuk dashboard |

## Tech Stack & AI Tools

- **AI Orchestration**: custom Python multi-agent orchestrator — 7 specialist
  agents + event-driven & cron-driven autonomous loops (`agent/orchestrator.py`)
- **LLM / Vision**: **Claude Haiku 4.5** via the **Sumopod AI gateway**
  (OpenAI-compatible) — multi-modal classification + reasoning
- **Payment**: **DOKU MCP Server** (QRIS, Virtual Account) — *Best Payment Track*
- **Web3**: **Solana** devnet + SPL Token Program (Rasain Points)
- **Backend**: FastAPI + APScheduler (autonomous loop)
- **Frontend**: Next.js 16 + Tailwind
- **Hosting**: Vercel

## Project Structure

```
agent/
  orchestrator.py      # autonomous multi-agent loop
  models.py            # Citizen / Report / Reward / AgentLog
  store.py             # JSON-backed repository
  config.py            # env settings
  tools/
    classifier.py      # Claude vision classification
    geolocator.py      # agency routing
    lapor_portal.py    # Lapor.go.id submitter + tracker
    doku.py            # DOKU MCP payment client
    solana_token.py    # Solana SPL token (mint/burn)
    reward.py          # earn + redeem Civic Credit
    intake.py          # channel-agnostic entry
api/main.py            # FastAPI backend
web/                   # Next.js dashboard
scripts/demo.py        # end-to-end demo
docs/ARCHITECTURE.md   # full design
```

## Demo & Links

- **Live Dashboard**: https://rasain-web.vercel.app
- **Live API**: https://rasain-backend.vercel.app (`/health`, `/stats`, `/logs`)
- **Demo Video**: *(YouTube Unlisted — lihat Devpost)*
- **Pitch Deck**: [`docs/OpenClaw2026_hayoloh_Rasain.pdf`](./docs/)

> Catatan: live backend di Vercel berjalan serverless — state in-memory
> (reset saat cold start). Untuk demo penuh dengan autonomous scheduler +
> persistensi, jalankan lokal (lihat Quick Start).

## Author

**Tim hayoloh** — Pugar Huda Mantoro · OpenClaw Agenthon Indonesia 2026

## License

MIT — lihat [LICENSE](./LICENSE)
