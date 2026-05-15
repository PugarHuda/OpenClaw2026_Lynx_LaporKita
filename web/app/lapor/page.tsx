"use client";

import Link from "next/link";
import { useRef, useState } from "react";
import { api } from "@/lib/api";

const KOTA = ["Bekasi", "Jakarta", "Surabaya", "Bandung", "Depok", "Tangerang", "Semarang", "Medan"];

interface Result {
  status: string;
  category?: string;
  severity?: string;
  urgency?: number;
  instansi_target?: string;
  ticket_id?: string;
  classification_reasoning?: string;
  reason?: string;
}

export default function LaporPage() {
  const [photo, setPhoto] = useState<File | null>(null);
  const [preview, setPreview] = useState<string | null>(null);
  const [description, setDescription] = useState("");
  const [email, setEmail] = useState("");
  const [kota, setKota] = useState("Bekasi");
  const [busy, setBusy] = useState(false);
  const [result, setResult] = useState<Result | null>(null);
  const [error, setError] = useState<string | null>(null);
  const fileRef = useRef<HTMLInputElement>(null);

  const pickPhoto = (file: File | null) => {
    setPhoto(file);
    setPreview(file ? URL.createObjectURL(file) : null);
  };

  const submit = async () => {
    if (!photo || !description || !email) {
      setError("Foto, deskripsi, dan email wajib diisi.");
      return;
    }
    if (!/^\S+@\S+\.\S+$/.test(email)) {
      setError("Format email tidak valid.");
      return;
    }
    setError(null);
    setBusy(true);
    setResult(null);
    try {
      const fd = new FormData();
      fd.append("photo", photo);
      fd.append("email", email.trim());
      fd.append("description", description);
      fd.append("kota", kota);
      const res = (await api.submitReportUpload(fd)) as unknown as Result;
      setResult(res);
    } catch {
      setError("Gagal mengirim. Pastikan backend aktif & coba lagi.");
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="min-h-screen bg-zinc-950 text-zinc-100">
      <nav className="border-b border-zinc-800">
        <div className="mx-auto flex max-w-3xl items-center justify-between px-6 py-4">
          <Link href="/" className="text-lg font-bold tracking-tight">
            Rasain<span className="text-amber-400">.</span>
          </Link>
          <Link href="/dashboard" className="text-sm text-zinc-400 hover:text-amber-400">
            Dashboard Agent &rarr;
          </Link>
        </div>
      </nav>

      <div className="mx-auto max-w-3xl px-6 py-10">
        <h1 className="text-2xl font-bold">Lapor Masalah Infrastruktur</h1>
        <p className="mt-1 text-sm text-zinc-500">
          Kirim foto masalah nyata. AI agent akan menganalisis, merutekan ke
          instansi, dan melacak penyelesaiannya.
        </p>

        {/* Form */}
        <div className="mt-8 space-y-5">
          {/* Photo */}
          <div>
            <label className="text-sm font-medium">Foto Masalah *</label>
            <div
              onClick={() => fileRef.current?.click()}
              className="mt-2 flex h-52 cursor-pointer items-center justify-center overflow-hidden rounded-xl border border-dashed border-zinc-700 bg-zinc-900/40 transition hover:border-amber-500"
            >
              {preview ? (
                // eslint-disable-next-line @next/next/no-img-element
                <img src={preview} alt="preview" className="h-full w-full object-cover" />
              ) : (
                <span className="text-sm text-zinc-500">Klik untuk pilih foto</span>
              )}
            </div>
            <input
              ref={fileRef}
              type="file"
              accept="image/*"
              className="hidden"
              onChange={(e) => pickPhoto(e.target.files?.[0] ?? null)}
            />
          </div>

          {/* Description */}
          <div>
            <label className="text-sm font-medium">Deskripsi Masalah *</label>
            <textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              rows={3}
              placeholder="Contoh: Jalan berlubang besar di tikungan, sudah ada motor jatuh."
              className="mt-2 w-full rounded-lg border border-zinc-700 bg-zinc-900 px-3 py-2 text-sm outline-none focus:border-amber-500"
            />
          </div>

          {/* Identity */}
          <div className="grid gap-4 sm:grid-cols-2">
            <div>
              <label className="text-sm font-medium">Email *</label>
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="kamu@email.com"
                className="mt-2 w-full rounded-lg border border-zinc-700 bg-zinc-900 px-3 py-2 text-sm outline-none focus:border-amber-500"
              />
              <p className="mt-1 text-xs text-zinc-500">
                Email = login-mu untuk melacak laporan &amp; klaim reward.
                Tidak ditampilkan publik — identitasmu tetap anonim.
              </p>
            </div>
            <div>
              <label className="text-sm font-medium">Kota</label>
              <select
                value={kota}
                onChange={(e) => setKota(e.target.value)}
                className="mt-2 w-full rounded-lg border border-zinc-700 bg-zinc-900 px-3 py-2 text-sm outline-none focus:border-amber-500"
              >
                {KOTA.map((k) => (
                  <option key={k} value={k}>{k}</option>
                ))}
              </select>
            </div>
          </div>

          {error && <p className="text-sm text-red-400">{error}</p>}

          <button
            onClick={submit}
            disabled={busy}
            className="w-full rounded-lg bg-amber-500 px-4 py-3 text-sm font-semibold text-zinc-950 transition hover:bg-amber-400 disabled:opacity-50"
          >
            {busy ? "AI agent menganalisis foto…" : "Kirim Laporan"}
          </button>
        </div>

        {/* Result */}
        {result && (
          <div className="mt-8 rounded-xl border border-zinc-800 bg-zinc-900/40 p-5">
            {result.status === "submitted" ? (
              <>
                <div className="flex items-center gap-2">
                  <span className="h-2 w-2 rounded-full bg-emerald-400" />
                  <span className="text-sm font-semibold text-emerald-300">
                    Laporan diterima &amp; diteruskan
                  </span>
                </div>
                <dl className="mt-4 grid grid-cols-2 gap-3 text-sm">
                  <div><dt className="text-zinc-500">Kategori</dt><dd>{result.category}</dd></div>
                  <div><dt className="text-zinc-500">Tingkat</dt><dd>{result.severity} · urgensi {result.urgency}/5</dd></div>
                  <div className="col-span-2"><dt className="text-zinc-500">Instansi</dt><dd>{result.instansi_target}</dd></div>
                  <div className="col-span-2"><dt className="text-zinc-500">No. Tiket</dt><dd className="font-mono">{result.ticket_id}</dd></div>
                </dl>
                <div className="mt-4 rounded-lg bg-zinc-950/60 p-3">
                  <p className="text-xs text-zinc-500">Analisis AI agent:</p>
                  <p className="mt-1 text-sm text-zinc-300">{result.classification_reasoning}</p>
                </div>
                <div className="mt-4 flex flex-col gap-1">
                  <Link
                    href={`/saya?email=${encodeURIComponent(email.trim())}`}
                    className="text-sm font-medium text-amber-400 hover:underline"
                  >
                    Lacak laporan &amp; klaim reward dengan email-mu &rarr;
                  </Link>
                  <Link
                    href="/dashboard"
                    className="text-sm text-zinc-400 hover:underline"
                  >
                    Lihat agent bekerja di Dashboard &rarr;
                  </Link>
                </div>
              </>
            ) : (
              <p className="text-sm text-amber-300">
                {result.status === "needs_better_photo"
                  ? "Foto kurang jelas — mohon kirim ulang foto yang lebih terang."
                  : result.reason ?? "Foto bukan masalah infrastruktur publik."}
              </p>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
