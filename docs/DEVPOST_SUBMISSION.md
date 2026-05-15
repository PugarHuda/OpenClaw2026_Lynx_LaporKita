# Devpost Submission — Rasain (copy-paste ready)

## Project Name
`Rasain`

## Tagline
Autonomous multi-agent AI for civic infrastructure reporting — laporkan masalah, rasain perubahannya.

## Team Name
`hayoloh`

## Track / Label
☑ **Best Payment Use Case** (DOKU)

---

## Project Description (narasi)

**Inspiration**
280 juta warga Indonesia menghadapi masalah infrastruktur publik setiap hari —
jalan berlubang, lampu jalan mati, sampah menumpuk, banjir akibat drainase
mampet. Portal pemerintah Lapor.go.id ada, tapi response rate-nya rendah:
alurnya manual, lambat, dan warga tidak punya insentif apa pun untuk repot
melapor. Banyak warga juga enggan melapor karena takut identitasnya terekspos.

**What it does**
Rasain adalah sistem multi-agent AI otonom yang menutup celah itu — 8 agent
spesialis di bawah satu orchestrator:

1. Warga mengirim foto + deskripsi masalah lewat **web form** atau **bot
   Telegram**. **Intake Agent** menormalkan laporan dari channel mana pun.
   Laporan **sepenuhnya anonim**: warga hanya dikenal lewat handle samaran
   (`Warga-XXXX`) + wallet — nama asli tidak pernah disimpan (perlindungan
   pelapor).
2. **Classifier Agent** menganalisis foto dengan Claude vision — menentukan
   kategori, tingkat keparahan, dan urgensi secara kontekstual; menolak foto
   yang bukan masalah infrastruktur.
3. **Geolocator Agent** merutekan laporan ke instansi pemerintah yang tepat
   (Dinas PUPR, DLH, Dinas Perhubungan, BPBD, PLN, dll) beserta SLA-nya.
4. **Submitter Agent** mengirim **email resmi** ke instansi berikut foto bukti.
   **Tracker Agent** memantau secara otonom lewat cron loop tiap 20 detik tanpa
   trigger manusia, dan mengeskalasi laporan yang mangkrak melewati SLA.
5. **Verifier Agent** membaca inbox: balasan email dari instansi memverifikasi
   laporan selesai. **Reward Agent** lalu memberi warga **Rasain Points (RSN)**
   — token SPL di Solana, di-mint on-chain sebagai proof of impact yang
   verifiable di Solscan. **Memory Agent** menyimpan riwayat warga di Mem9.
6. Warga menukar RSN sebagai **Civic Credit**: RSN di-burn on-chain, dan sisa
   tagihan retribusi pemerintah dibayar lewat **DOKU QRIS**. Berkontribusi
   melaporkan masalah kota secara harfiah membantu warga membayar kewajiban
   sipilnya sendiri — lingkaran ekonomi yang tertutup.

Klaim reward bisa langsung dari **bot Telegram**: tanpa email, tanpa install
dompet. Telegram mengautentikasi warga, `chat_id`-nya terikat ke wallet
custodial yang dibuat otomatis — hanya pemilik akun Telegram itu yang bisa
klaim reward-nya.

**How we built it**
Orchestrator Python kustom mengkoordinasi 8 agent spesialis lewat dua
autonomous loop: event-driven (`process_report`) dan cron-driven
(`run_tracker_cycle`, jalan tiap 20 detik tanpa intervensi manusia). Setiap
langkah menulis reasoning trace natural-language yang di-stream ke dashboard —
sehingga juri melihat agent *berpikir*, bukan sekadar output. Vision & reasoning
pakai Claude Haiku 4.5 lewat Sumopod AI gateway; channel pemerintah lewat
Gmail SMTP/IMAP; pembayaran lewat DOKU MCP Server; reward layer di Solana SPL
Token; backend FastAPI + APScheduler; dashboard Next.js dengan heatmap
kepadatan laporan per kota.

**Challenges**
Menyatukan empat sistem eksternal berbeda — vision AI, blockchain Solana,
payment gateway DOKU, dan email — dalam satu pipeline yang andal. Devnet RPC
Solana flaky di bawah beban, sehingga mint pertama kerap gagal; kami selesaikan
dengan retry loop dan membuang pre-check health yang men-cache kegagalan.
Menangani race condition antara cron loop otonom dan trigger manual, serta
membuat seluruh sistem reproducible lewat DEMO_MODE yang graceful-degrade
tanpa credential.

**Accomplishments**
Pipeline end-to-end yang benar-benar berjalan: laporan anonim terklasifikasi
vision AI, diteruskan via email resmi, terverifikasi otonom, RSN ter-mint
on-chain (real Solana devnet tx), dan Civic Credit ter-redeem lewat DOKU QRIS
sungguhan — semuanya dalam 12 jam.

**What's next**
V2: integrasi API Lapor.go.id resmi + pilot dengan Pemda, dan migrasi wallet
ke self-custody (Phantom). V3: tokenisasi carbon credit RWA untuk dampak
cleanup, dan DAO tata kelola per kota.

---

## Built With
`claude-haiku-4.5` · `sumopod-ai` · `doku-mcp-server` · `solana` · `spl-token` ·
`python` · `fastapi` · `apscheduler` · `openai-sdk` · `mcp` · `mem9` ·
`telegram-bot-api` · `gmail-smtp-imap` · `nextjs` · `tailwindcss` · `typescript`

## AI Tools / Models Used
- **Claude Haiku 4.5** — multi-modal vision untuk klasifikasi foto masalah
  infrastruktur + reasoning kontekstual (severity/urgency).
- **Sumopod AI Gateway** — gateway OpenAI-compatible penyedia akses Claude;
  classifier memanggilnya via OpenAI SDK.
- **DOKU MCP Server** — Model Context Protocol server untuk pembayaran (QRIS,
  Virtual Account) — dipakai di redeem Civic Credit.
- **Mem9** — memori agen persisten lintas sesi (riwayat warga).
- **Solana SPL Token** — reward layer on-chain (Rasain Points).
- **Custom Python multi-agent orchestrator** — 8 agent spesialis + autonomous
  loop, dibangun penuh selama 12 jam (bukan framework jadi).

## Links
- **GitHub**: https://github.com/PugarHuda/OpenClaw2026_hayoloh_Rasain
- **Live Deployment**: https://rasain-web.vercel.app
- **Live API**: https://rasain-backend.vercel.app
- **Demo Video**: (YouTube Unlisted — isi setelah upload)
- **Pitch Deck**: docs/OpenClaw2026_hayoloh_Rasain.pdf (upload ke Devpost)

> Catatan untuk juri: demo otonom penuh (scheduler tracker tiap 20 detik +
> polling Telegram) berjalan saat backend di-run lokal — lihat `README.md`.
> Deployment Vercel membuktikan deployability; reproduksi cepat: jalankan
> `python scripts/seed_demo.py`.

---

## Checklist submit (sebelum 23.00 WIB)
- [ ] Project description di-paste ke Devpost
- [ ] GitHub repo link (public)
- [ ] Demo video YouTube Unlisted, judul `OpenClaw2026_hayoloh_Rasain`
- [ ] Link video diisi di bagian Links
- [ ] Pitch deck PDF di-upload
- [ ] Label "Best Payment Use Case" dicentang
- [ ] AI tools/models list diisi
- [ ] Submit paling lambat 22.50 WIB (buffer 10 menit)
- [ ] STOP commit ke GitHub setelah submit
