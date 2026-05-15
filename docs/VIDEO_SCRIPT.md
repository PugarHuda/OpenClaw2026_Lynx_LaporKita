# Demo Video Script — Rasain (max 2 menit)

**Naming**: `OpenClaw2026_hayoloh_Rasain` · YouTube **Unlisted**
**Target durasi**: 110–118 detik · rekam 1920×1080 (OBS)

---

## Persiapan sebelum rekam

```bash
# 1. Backend lokal (punya scheduler otonom — WAJIB lokal, bukan Vercel)
uvicorn api.main:app --port 8000

# 2. Frontend lokal
cd web && npm run dev          # -> http://localhost:3000

# 3. Isi data demo NYATA, mode 'reports' (laporan masuk, BELUM diverifikasi)
SEED_MODE=reports python scripts/seed_demo.py
```

- Mode `reports` sengaja menyisakan 5 laporan berstatus *submitted* — supaya
  verifikasi otonom + mint RSN + redeem bisa terlihat **live** di video.
- Matikan notifikasi (Discord/WA). Tab browser rapi. Tes audio dulu.
- Buka 2 tab: (1) `localhost:3000`  (2) Telegram `@rasainAgent_bot`.
- Re-take kapan saja: `curl -X POST http://localhost:8000/demo/reset` lalu
  jalankan ulang seed.

---

## ACT 1 — Masalah & Produk (0:00 – 0:15)

**Visual**: Landing page `localhost:3000` — scroll pelan: hero → angka dampak →
deretan agent.

**Voice-over**:
> "Indonesia: 280 juta warga, ribuan masalah infrastruktur tiap hari — jalan
> rusak, lampu mati, sampah, banjir. Lapor.go.id ada, tapi lambat dan warga
> tak punya insentif. Rasain mengubahnya — sistem multi-agent AI yang otonom."

## ACT 2 — Pipeline Multi-Agent (0:15 – 0:55) ★ INTI

**Visual**: Klik **"Buka Dashboard"** → `/dashboard`. Sudah terisi 5 laporan.
1. Sorot panel **Agent Reasoning Trace** — scroll pelan: `intake → classifier →
   geolocator → submitter → memory`, tiap agent beda warna.
2. Zoom satu entri **classifier** — reasoning Claude vision yang kontekstual
   (kategori, severity, urgensi).
3. Sorot **Heatmap** — kepadatan laporan per kota + warga paling aktif.

**Voice-over**:
> "Warga kirim foto. Classifier Agent menganalisis dengan Claude vision —
> kategori, tingkat bahaya, urgensi. Geolocator merutekan ke instansi yang
> tepat. Submitter mengirim email resmi ke instansi. Memory Agent menyimpan
> riwayat warga di Mem9. Laporan sepenuhnya anonim — warga cuma dikenal lewat
> handle samaran. Tiap agent menulis jejak pikirnya — ini reasoning, bukan
> skrip."

## ACT 3 — Otonomi & Reward On-Chain (0:55 – 1:25) ★ LIVE

**Visual**: Klik **"2 · Simulasi Respon Instansi"**. Trace lanjut otomatis:
`verifier → reward`. Counter **RSN Diterbitkan** naik. Klik link **🔗 cek
on-chain** di salah satu kartu warga → tab Solscan devnet terbuka.

**Voice-over**:
> "Saat instansi merespon, Tracker Agent — yang jalan otonom tiap 20 detik
> tanpa trigger manusia — memverifikasi laporan. Reward Agent lalu me-mint
> Rasain Points sebagai token SPL di Solana. Ini transaksi on-chain sungguhan
> — kepemilikan token warga bisa diverifikasi siapa pun di Solscan."

## ACT 4 — Civic Credit & DOKU (1:25 – 1:50) ★ LIVE · Best Payment

**Visual**: Scroll ke panel **3 · Warga & Rasain Points** → klik **"Redeem
Civic Credit"** pada satu warga. Hasil muncul: RSN dipakai, potongan, sisa QRIS.

**Voice-over**:
> "Inti-nya: warga menukar Rasain Points sebagai Civic Credit. Token di-burn
> on-chain, sisa tagihan retribusi dibayar lewat DOKU QRIS. Berkontribusi
> melapor — secara harfiah membantu warga membayar kewajiban sipilnya."

## ACT 5 — Channel Real & Penutup (1:50 – 2:00)

**Visual**: Tab Telegram `@rasainAgent_bot` — tunjukkan menu tombol
(📸 Cara Lapor · 🪙 Klaim Reward · 📊 Dashboard). Tap **🪙 Klaim Reward** →
bot balas hasil klaim di chat.

**Voice-over**:
> "Warga lapor & klaim reward langsung dari Telegram — tanpa email, tanpa
> install dompet. Rasain: 8 agent otonom, DOKU, Solana, Mem9, Claude.
> Laporkan masalah, rasain perubahannya. Tim hayoloh — OpenClaw Agenthon 2026."

---

## WAJIB terlihat di video (bukti untuk juri)

- [ ] Reasoning trace streaming, agent beda warna (autonomy + multi-agent)
- [ ] Reasoning Claude vision yang kontekstual (bukan keyword)
- [ ] Status laporan berubah submitted → verified (workflow otonom)
- [ ] Counter RSN naik + link Solscan dibuka (Web3 real, verifiable)
- [ ] Redeem → burn + QRIS DOKU (Best Payment Use Case)
- [ ] Bot Telegram bisa diklik + klaim in-chat (channel real + ownership)

## Tips

- Fokus ke dashboard; jangan rekam terminal lama-lama.
- Bicara tenang, tidak terburu — 2 menit cukup untuk alur di atas.
- Upload YouTube **Unlisted**, judul `OpenClaw2026_hayoloh_Rasain`.
- Setelah upload → salin link ke `docs/DEVPOST_SUBMISSION.md` → submit Devpost.
