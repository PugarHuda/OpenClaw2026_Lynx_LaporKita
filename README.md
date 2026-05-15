# Rasain

> **AI Civic Reporting Agent for Indonesia with Web3 Reward Layer**

Rasain adalah AI agent yang membantu 280 juta warga Indonesia melapor masalah infrastruktur publik (jalan rusak, lampu mati, sampah, banjir, dll) ke Lapor.go.id secara otomatis — dengan reward yang bisa dicairkan ke rekening bank, dibangun di atas transparansi blockchain.

**Submission untuk**: [OpenClaw Agenthon Indonesia 2026](https://luma.com/openclaw-agenthon-id) - RISTEK × Build Club

**Track**: Juara Umum + Best Payment Use Case (Doku)

---

## Inti Sistem (3-Liner)

1. Warga foto masalah via WhatsApp → AI agent klasifikasi pakai vision multi-modal → submit otomatis ke Lapor.go.id dengan tag instansi tepat
2. Setelah masalah resolved oleh pemerintah daerah → citizen dapat **Rasain Points**, di-mint otomatis sebagai SPL token di Solana sebagai proof of impact
3. Citizen redeem token → **Doku Disbursement** transfer langsung ke rekening BCA/Mandiri/dll

## Mengapa Penting

- **280 juta warga Indonesia** dengan ribuan masalah infrastruktur tiap hari
- **Lapor.go.id resmi pemerintah** tapi response rate <30% karena underused
- **Tidak ada insentif untuk warga lapor** → engagement rendah
- **Pemda tidak punya data terstruktur** untuk prioritas perbaikan

Rasain memecahkan ini dengan: **automasi laporan + insentif ekonomi nyata + akuntabilitas on-chain**.

## Multi-Agent Architecture (Detail di [docs/ARCHITECTURE.md](./docs/ARCHITECTURE.md))

```
Citizen → Intake Agent → Classifier Agent → Geolocator Agent
                                                ↓
                                          Submitter Agent (Lapor.go.id)
                                                ↓
                                          Tracker Agent (poll status)
                                                ↓
                                          Verifier Agent (impact verified)
                                                ↓
                                          Reward Agent
                                          ├── SPL Token mint (Solana)
                                          └── Doku Disbursement (IDR off-ramp)
```

## Quick Start

### Prerequisites
- Python 3.11+
- Node.js 20+
- Anthropic API key
- Doku Sandbox account (Brand ID + API Key)
- Mem9 API key (auto-provisioned via Claude Code plugin)

### Setup (< 10 menit)

```bash
# 1. Clone
git clone https://github.com/PugarHuda/OpenClaw2026_hayoloh_Rasain.git
cd OpenClaw2026_hayoloh_Rasain

# 2. Setup Python env
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -e .

# 3. Setup environment
cp .env.example .env
# Edit .env dengan credentials

# 4. Setup frontend
cd web && npm install && cd ..

# 5. Generate Solana devnet wallet (untuk SPL token)
python scripts/setup_solana.py

# 6. Run
# Terminal 1: Backend agent + API
uvicorn api.main:app --reload --port 8000

# Terminal 2: Frontend dashboard
cd web && npm run dev
```

## Demo

- **Live**: TBD (will deploy to Vercel + Sumopod)
- **Video**: TBD (YouTube Unlisted, max 2 menit)
- **Pitch Deck**: [docs/PitchDeck.pdf](./docs/PitchDeck.pdf)

## Tech Stack

- **AI Agent**: [Claude Agent SDK](https://github.com/anthropics/claude-agent-sdk-python) + [Anthropic Claude](https://www.anthropic.com)
- **Payment**: [DOKU MCP Server](https://docs.doku.com/accept-payments/integration-tools/doku-mcp-server) (QRIS, VA, Disbursement)
- **Memory**: [Mem9](https://mem9.ai/) (persistent agent memory)
- **Web3**: Solana devnet + SPL Token Program
- **Frontend**: Next.js 14 + shadcn/ui + Tailwind
- **Backend**: FastAPI + uvicorn
- **Hosting**: Vercel (web) + Sumopod (agent backend)

## Authors

- **hayoloh (Pugar Huda Mantoro)** — Solo builder with Claude Code as pair programmer

## License

MIT — see [LICENSE](./LICENSE)

---

*Built in 12 hours for OpenClaw Agenthon Indonesia 2026 - 15 Mei 2026.*
