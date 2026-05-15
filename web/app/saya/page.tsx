"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { api, type Me } from "@/lib/api";

const solscan = (addr: string) =>
  `https://solscan.io/account/${addr}?cluster=devnet`;

const STATUS_STYLE: Record<string, string> = {
  verified: "border-emerald-700/60 bg-emerald-900/30 text-emerald-300",
  resolved: "border-emerald-700/60 bg-emerald-900/30 text-emerald-300",
  submitted: "border-sky-700/60 bg-sky-900/30 text-sky-300",
  in_progress: "border-amber-700/60 bg-amber-900/30 text-amber-300",
  rejected: "border-red-800/60 bg-red-950/40 text-red-300",
};

const rupiah = (n: number) => `Rp ${n.toLocaleString("id-ID")}`;

export default function SayaPage() {
  const [email, setEmail] = useState("");
  const [data, setData] = useState<Me | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [claim, setClaim] = useState<string | null>(null);

  const load = async (value: string) => {
    const e = value.trim();
    if (!e) return;
    setBusy(true);
    setError(null);
    setClaim(null);
    try {
      setData(await api.me(e));
    } catch {
      setError("Email belum terdaftar — kirim laporan pertamamu dulu di /lapor.");
      setData(null);
    } finally {
      setBusy(false);
    }
  };

  useEffect(() => {
    const q = new URLSearchParams(window.location.search).get("email");
    if (q) {
      setEmail(q);
      load(q);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const redeem = async () => {
    if (!data) return;
    setBusy(true);
    setError(null);
    try {
      const r = (await api.redeem({
        citizen_id: data.citizen.id,
        retribusi_type: "sampah",
        retribusi_amount_idr: 25000,
      })) as Record<string, number>;
      setClaim(
        `Berhasil! ${r.rsn_used} RSN dipakai (potongan ${rupiah(r.idr_offset)}), ` +
          `sisa ${rupiah(r.cash_due_idr)} dibayar via QRIS DOKU.`,
      );
      await load(email);
    } catch {
      setError("Klaim gagal — pastikan kamu punya RSN on-chain.");
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
          <Link href="/lapor" className="text-sm text-zinc-400 hover:text-amber-400">
            Buat Laporan &rarr;
          </Link>
        </div>
      </nav>

      <div className="mx-auto max-w-3xl px-6 py-10">
        <h1 className="text-2xl font-bold">Laporan &amp; Reward Saya</h1>
        <p className="mt-1 text-sm text-zinc-500">
          Masuk dengan email yang kamu pakai saat melapor — lacak status
          laporan dan klaim reward RSN-mu.
        </p>

        {/* Email login */}
        <div className="mt-6 flex flex-col gap-3 sm:flex-row">
          <input
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && load(email)}
            placeholder="kamu@email.com"
            className="flex-1 rounded-lg border border-zinc-700 bg-zinc-900 px-3 py-2 text-sm outline-none focus:border-amber-500"
          />
          <button
            onClick={() => load(email)}
            disabled={busy}
            className="rounded-lg bg-amber-500 px-5 py-2 text-sm font-semibold text-zinc-950 transition hover:bg-amber-400 disabled:opacity-50"
          >
            {busy ? "Memuat…" : "Masuk"}
          </button>
        </div>

        {error && <p className="mt-4 text-sm text-red-400">{error}</p>}
        {claim && (
          <p className="mt-4 rounded-lg border border-emerald-800/60 bg-emerald-950/40 px-3 py-2 text-sm text-emerald-300">
            {claim}
          </p>
        )}

        {data && (
          <>
            {/* Wallet + RSN */}
            <section className="mt-6 rounded-xl border border-zinc-800 bg-zinc-900/40 p-5">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-zinc-500">Identitas anonim</p>
                  <p className="text-lg font-semibold">{data.citizen.name}</p>
                </div>
                <div className="text-right">
                  <p className="text-sm text-zinc-500">RSN on-chain</p>
                  <p className="text-2xl font-bold text-pink-400">
                    {data.citizen.rsn_onchain}
                  </p>
                </div>
              </div>
              {data.citizen.solana_wallet && (
                <a
                  href={solscan(data.citizen.solana_wallet)}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="mt-2 block break-all font-mono text-xs text-sky-500 hover:text-sky-400"
                >
                  🔗 {data.citizen.solana_wallet} · cek kepemilikan on-chain
                </a>
              )}
              <button
                onClick={redeem}
                disabled={busy || data.citizen.rsn_onchain <= 0}
                className="mt-4 w-full rounded-lg border border-pink-500/40 bg-pink-500/10 px-4 py-2 text-sm font-semibold text-pink-300 transition hover:bg-pink-500/20 disabled:opacity-40"
              >
                {data.citizen.rsn_onchain > 0
                  ? "Klaim Reward — Tukar jadi Civic Credit"
                  : "Belum ada RSN — laporan harus terverifikasi dulu"}
              </button>
            </section>

            {/* Reports */}
            <section className="mt-6">
              <p className="mb-2 text-sm font-semibold">
                Laporan Saya ({data.reports.length})
              </p>
              {data.reports.length === 0 ? (
                <p className="text-sm text-zinc-600">Belum ada laporan.</p>
              ) : (
                <div className="space-y-2">
                  {data.reports.map((r) => (
                    <div
                      key={r.id}
                      className="rounded-lg border border-zinc-800 bg-zinc-900/40 p-3"
                    >
                      <div className="flex items-center justify-between">
                        <span className="text-sm font-medium">{r.category}</span>
                        <span
                          className={`rounded border px-2 py-0.5 text-xs ${
                            STATUS_STYLE[r.status] ?? STATUS_STYLE.submitted
                          }`}
                        >
                          {r.status}
                        </span>
                      </div>
                      <p className="mt-1 text-xs text-zinc-500">
                        {r.kota} · {r.instansi_target}
                      </p>
                      {r.lapor_ticket_id && (
                        <p className="mt-1 font-mono text-xs text-zinc-600">
                          {r.lapor_ticket_id}
                        </p>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </section>
          </>
        )}
      </div>
    </div>
  );
}
