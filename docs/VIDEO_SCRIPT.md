# Demo Video Script — Rasain (max 2 menit)

**Naming**: `OpenClaw2026_hayoloh_Rasain` · YouTube **Unlisted**
**Target durasi**: 100-110 detik
**Tools**: OBS Studio (rekam layar) + mic. Resolusi 1920x1080.

## Persiapan sebelum rekam

```bash
# 1. Reset state bersih
cd OpenClaw2026_hayoloh_Rasain
rm -f rasain_store.json lapor_portal_mock.json

# 2. Start backend (Terminal 1)
.venv\Scripts\activate
uvicorn api.main:app --port 8000

# 3. Start frontend (Terminal 2)
cd web && npm run dev

# 4. Buka http://localhost:3000 — pastikan dashboard kosong & bersih
# 5. Disable notifikasi (Discord, WhatsApp). Tutup tab lain.
```

---

## ACT 1 — Problem & Solusi (0:00 - 0:18)

**Visual**: Title card "Rasain" 3 detik → dashboard kosong di localhost:3000.

**Voice-over**:
> "Indonesia: 280 juta warga, ribuan masalah infrastruktur tiap hari — jalan
> rusak, lampu mati, sampah. Lapor.go.id ada, tapi response-nya lambat dan
> warga nggak punya insentif. Rasain mengubah itu — AI multi-agent yang
> melaporkan, melacak, dan memberi reward, otonom."

## ACT 2 — Agent Bekerja Otonom (0:18 - 1:20) ★ INTI

**Visual + aksi**:
1. Klik **"+ Kirim Laporan (Demo)"** — ulangi 3x.
   Setiap klik: panel **Agent Reasoning Trace** terisi entri baru —
   tunjukkan warna per agent: `intake → classifier → geolocator → submitter`.
2. **Zoom / sorot** panel reasoning trace saat entri muncul.
3. Panel **Laporan Warga** terisi 3 kartu dengan status `submitted`.

**Voice-over** (saat trace mengalir):
> "Warga kirim foto. Classifier Agent menganalisis pakai Claude vision —
> kategori, tingkat keparahan, urgensi. Geolocator Agent merutekan ke instansi
> yang tepat. Submitter Agent mengirim ke Lapor.go.id. Lihat — setiap agent
> menulis jejak pikirnya. Ini bukan skrip, ini reasoning."

4. Klik **"✓ Simulasi Respon Instansi"**.
   Trace lanjut: `verifier → reward`. Status laporan jadi `verified`.
   Stat **RSN Diterbitkan** naik jadi 30.

**Voice-over**:
> "Saat instansi menyelesaikan masalah, Tracker Agent — yang jalan otonom
> tanpa trigger manusia — memverifikasi, lalu Reward Agent me-mint Rasain
> Points sebagai token Solana. Reward on-chain, sungguhan."

## ACT 3 — Civic Credit & Impact (1:20 - 1:50)

**Visual + aksi**:
1. Scroll ke panel **Warga & Rasain Points** — tunjukkan 3 warga, masing-masing 10 RSN.
2. Klik **"Redeem Civic Credit"** pada satu warga.
3. Toast muncul: "Civic Credit: 10 RSN dipakai, sisa Rp 15.000".

**Voice-over**:
> "Dan inilah inti-nya: warga menukar RSN sebagai Civic Credit. Token di-burn
> di Solana, sisa tagihan retribusi dibayar lewat DOKU QRIS. Berkontribusi
> melaporkan masalah kota — secara harfiah membantu warga membayar kewajiban
> sipilnya. Lingkaran yang tertutup."

## ACT 4 — Penutup (1:50 - 2:00)

**Visual**: Dashboard penuh (stats terisi) → logo Rasain.

**Voice-over**:
> "Rasain. Tujuh agent otonom, DOKU MCP, Solana, Mem9. Laporkan masalah —
> rasain perubahannya. Tim hayoloh, OpenClaw Agenthon 2026."

---

## Catatan rekaman

- **WAJIB terlihat**: reasoning trace streaming, multiple agent, status berubah,
  RSN counter naik, redeem toast. Itu bukti otonomi + payment + Web3.
- Kalau ada `ANTHROPIC_API_KEY` di `.env`, classifier pakai Claude vision asli —
  reasoning terdengar lebih cerdas. Sangat disarankan untuk video.
- Jangan rekam terminal lama-lama. Fokus dashboard.
- Take ulang kalau ada step gagal — `rm rasain_store.json lapor_portal_mock.json`
  untuk reset.
- Upload YouTube **Unlisted**, judul `OpenClaw2026_hayoloh_Rasain`.
