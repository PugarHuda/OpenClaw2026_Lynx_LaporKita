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
jalan berlubang, lampu jalan mati, sampah menumpuk, drainase mampet. Portal
pemerintah Lapor.go.id ada, tapi response rate-nya di bawah 30%: alurnya manual,
lambat, dan warga tidak punya insentif apapun untuk repot-repot melapor. Akibatnya
potensi nilai infrastruktur publik yang mangkrak menyentuh ratusan triliun rupiah
per tahun.

**What it does**
Rasain adalah sistem multi-agent AI otonom yang menutup celah itu:

1. Warga mengirim foto + deskripsi masalah (web / WhatsApp / Telegram).
2. **Classifier Agent** menganalisis foto dengan Claude vision — menentukan
   kategori, tingkat keparahan, dan urgensi secara kontekstual.
3. **Geolocator Agent** merutekan laporan ke instansi pemerintah yang tepat
   (Dinas PUPR, DLH, PLN, BPBD, dll) beserta SLA-nya.
4. **Submitter Agent** mengirim ke Lapor.go.id; **Tracker Agent** memantau status
   secara otonom lewat cron loop tanpa trigger manusia, dan mengeskalasi laporan
   yang mangkrak melewati SLA.
5. Saat **Verifier Agent** mengonfirmasi masalah selesai, **Reward Agent** memberi
   warga **Rasain Points (RSN)** — token SPL di Solana sebagai proof of impact
   yang verifiable di Solscan.
6. Warga menukar RSN sebagai **Civic Credit**: RSN di-burn on-chain, dan sisa
   tagihan retribusi pemerintah dibayar lewat **DOKU QRIS**. Berkontribusi
   melaporkan masalah kota secara harfiah membantu warga membayar kewajiban
   sipilnya sendiri — sebuah lingkaran ekonomi yang tertutup.

**How we built it**
Orchestrator Python kustom mengkoordinasi 7 agent spesialis lewat dua autonomous
loop: event-driven (`process_report`) dan cron-driven (`run_tracker_cycle`, jalan
tiap 20 detik tanpa intervensi manusia). Setiap langkah menulis reasoning trace
natural-language yang di-stream ke dashboard — sehingga juri melihat agent
*berpikir*, bukan sekadar output. Reasoning & vision pakai Claude Haiku 4.5 lewat
Sumopod AI gateway, integrasi pembayaran lewat DOKU MCP Server, reward layer di
Solana SPL Token, backend FastAPI + APScheduler, dan dashboard Next.js.

**Challenges**
Menyatukan tiga sistem eksternal yang berbeda — vision AI, blockchain Solana,
dan payment gateway DOKU — dalam satu transaksi atomik (redeem Civic Credit:
burn RSN lalu generate QRIS). Menangani race condition antara cron loop otonom
dan trigger manual, serta membuat seluruh sistem tetap reproducible untuk juri
lewat DEMO_MODE yang graceful-degrade tanpa credential.

**Accomplishments**
Pipeline end-to-end yang benar-benar berjalan: laporan terklasifikasi,
terverifikasi otonom, RSN ter-mint on-chain (real Solana devnet tx), dan Civic
Credit ter-redeem lewat DOKU QRIS sungguhan — semuanya dalam 12 jam.

**What's next**
V2: integrasi API Lapor.go.id resmi + pilot dengan Pemda. V3: tokenisasi carbon
credit RWA untuk dampak cleanup, dan DAO tata kelola per kota.

---

## Built With
`claude-haiku-4.5` · `sumopod-ai` · `doku-mcp-server` · `solana` · `spl-token` ·
`python` · `fastapi` · `apscheduler` · `openai-sdk` · `mcp` · `nextjs` ·
`tailwindcss` · `typescript`

## AI Tools / Models Used
- **Claude Haiku 4.5** — multi-modal vision untuk klasifikasi foto masalah
  infrastruktur + reasoning kontekstual (severity/urgency).
- **Sumopod AI Gateway** — gateway OpenAI-compatible yang menyediakan akses
  Claude; classifier memanggilnya via OpenAI SDK.
- **DOKU MCP Server** — Model Context Protocol server untuk pembayaran (QRIS,
  Virtual Account) — dipakai di reward Civic Credit.
- **Solana SPL Token** — reward layer on-chain (Rasain Points).
- **Custom Python multi-agent orchestrator** — 7 agent spesialis + autonomous
  loop (bukan framework jadi — dibangun penuh selama 12 jam).

## Links
- **GitHub**: https://github.com/PugarHuda/OpenClaw2026_hayoloh_Rasain
- **Live Deployment**: https://rasain-web.vercel.app
- **Live API**: https://rasain-backend.vercel.app
- **Demo Video**: (YouTube Unlisted — isi setelah upload)
- **Pitch Deck**: docs/OpenClaw2026_hayoloh_Rasain.pdf (upload ke Devpost)

---

## Checklist submit (sebelum 23.00 WIB)
- [ ] Project description di-paste ke Devpost
- [ ] GitHub repo link (public — sudah)
- [ ] Demo video YouTube Unlisted, judul `OpenClaw2026_hayoloh_Rasain`
- [ ] Pitch deck PDF di-upload
- [ ] Label "Best Payment Use Case" dicentang
- [ ] AI tools/models list diisi
- [ ] Submit paling lambat 22.50 WIB (buffer 10 menit)
- [ ] STOP commit ke GitHub setelah submit
