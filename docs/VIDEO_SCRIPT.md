# Demo Video Script — Rasain (max 2 menit)

**Naming**: `OpenClaw2026_hayoloh_Rasain` · YouTube **Unlisted**
**Target**: 100-115 detik · rekam 1920x1080 (OBS)

## Persiapan sebelum rekam

```
Backend  : sudah jalan di localhost:8000  (atau restart: uvicorn api.main:app --port 8000)
Frontend : sudah jalan di localhost:3000  (atau: cd web && npm run dev)
Reset    : curl -X POST http://localhost:8000/demo/reset
```
- Disable notifikasi (Discord/WA). Browser tab rapi. Audio test dulu.
- Buka 2 tab: (1) http://localhost:3000  (2) Telegram @rasainAgent_bot (opsional shot)

---

## ACT 1 — Problem & Produk (0:00 - 0:18)

**Visual**: Landing page `localhost:3000` — scroll pelan: hero → "Rp 327 T" → 7 agent.

**Voice-over**:
> "Indonesia: 280 juta warga, ribuan masalah infrastruktur tiap hari — jalan
> rusak, lampu mati, sampah. Lapor.go.id ada tapi lambat, dan warga nggak punya
> insentif. Rasain mengubah itu — sistem multi-agent AI yang otonom."

## ACT 2 — Agent Bekerja Otonom (0:18 - 1:05) ★ INTI

**Visual**: Klik **"Buka Dashboard Agent"** → di `/dashboard`:
1. Klik **"1 · Kirim Laporan (Demo)"** 3×. Panel **Agent Reasoning Trace**
   terisi — sorot/zoom: `intake → classifier → geolocator → submitter → memory`.
2. Tunjuk satu entri classifier — reasoning Claude vision yang kontekstual.

**Voice-over**:
> "Warga kirim foto. Classifier Agent menganalisis pakai Claude vision —
> kategori, tingkat bahaya, urgensi. Geolocator merutekan ke instansi yang
> tepat. Submitter mengirim email resmi ke instansi. Memory Agent menyimpan
> riwayat warga di Mem9. Setiap agent menulis jejak pikirnya — ini reasoning,
> bukan skrip."

3. Klik **"2 · Simulasi Respon Instansi"**. Trace lanjut: `verifier → reward`.
   Stat **RSN Diterbitkan** naik.

**Voice-over**:
> "Saat instansi merespon, Tracker Agent — yang jalan otonom tiap 20 detik
> tanpa trigger manusia — memverifikasi, lalu Reward Agent me-mint Rasain
> Points sebagai token Solana. Reward on-chain, transaksi sungguhan."

## ACT 3 — Civic Credit & Sponsor (1:05 - 1:35)

**Visual**: Scroll ke panel **Warga & RSN** → klik **"Redeem Civic Credit"**.
Toast muncul: "10 RSN dipakai, sisa Rp 15.000".

**Voice-over**:
> "Inti-nya: warga tukar Rasain Points sebagai Civic Credit. Token di-burn di
> Solana, sisa tagihan retribusi dibayar lewat DOKU QRIS. Berkontribusi melapor
> — harfiah membantu warga bayar kewajiban sipilnya."

## ACT 4 — Real Channel & Penutup (1:35 - 2:00)

**Visual**: Quick shot Telegram `@rasainAgent_bot` — chat: foto terkirim, bot
balas klasifikasi. (Opsional: glimpse email di inbox.)

**Voice-over**:
> "Warga bisa lapor langsung dari Telegram pakai bahasa sendiri — agent ubah
> jadi email resmi + foto, dan kirim notifikasi balik saat selesai. Rasain:
> 8 agent otonom, DOKU, Solana, Mem9, Claude. Laporkan masalah, rasain
> perubahannya. Tim hayoloh — OpenClaw Agenthon 2026."

---

## WAJIB terlihat di video (bukti untuk juri)
- [ ] Reasoning trace streaming (autonomy + reasoning)
- [ ] Multiple agent berbeda warna (multi-agent)
- [ ] Status laporan berubah submitted → verified (workflow)
- [ ] RSN counter naik / mint (Web3 real)
- [ ] Redeem → QRIS Doku (Best Payment Track)
- [ ] Telegram bot (real intake channel) — minimal sekilas

## Tips
- Re-take: `curl -X POST http://localhost:8000/demo/reset` lalu refresh.
- Jangan rekam terminal lama-lama. Fokus dashboard.
- Upload YouTube **Unlisted**, judul `OpenClaw2026_hayoloh_Rasain`.
- Setelah upload → submit Devpost (teks siap di `docs/DEVPOST_SUBMISSION.md`).
