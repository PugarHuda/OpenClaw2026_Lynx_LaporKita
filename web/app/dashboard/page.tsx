"use client";

import Link from "next/link";
import { useCallback, useEffect, useRef, useState } from "react";
import { api, type AgentLog, type Citizen, type Report, type Stats } from "@/lib/api";

const AGENT_COLORS: Record<string, string> = {
  intake: "text-sky-400",
  classifier: "text-violet-400",
  geolocator: "text-amber-400",
  submitter: "text-emerald-400",
  tracker: "text-orange-400",
  verifier: "text-teal-400",
  reward: "text-pink-400",
  memory: "text-cyan-400",
  orchestrator: "text-zinc-300",
};

const STATUS_STYLES: Record<string, string> = {
  submitted: "bg-sky-500/15 text-sky-300 border-sky-500/30",
  in_progress: "bg-amber-500/15 text-amber-300 border-amber-500/30",
  resolved: "bg-emerald-500/15 text-emerald-300 border-emerald-500/30",
  verified: "bg-emerald-500/15 text-emerald-300 border-emerald-500/30",
  classified: "bg-violet-500/15 text-violet-300 border-violet-500/30",
  pending: "bg-zinc-500/15 text-zinc-300 border-zinc-500/30",
};

const DEMO_SCENARIOS = [
  {
    wa_number: "6281200000001", citizen_name: "Budi Santoso", kota: "Bekasi",
    image_path: "data/images/jalan.jpg", bank_account: "1234567801", bank_name: "BCA",
    description: "Jalan berlubang parah di tikungan ramai, bahaya buat pemotor",
  },
  {
    wa_number: "6281200000002", citizen_name: "Siti Aminah", kota: "Surabaya",
    image_path: "data/images/sampah.jpg", bank_account: "1234567802", bank_name: "Mandiri",
    description: "Sampah menumpuk di TPS sudah seminggu, bau menyengat sekali",
  },
  {
    wa_number: "6281200000003", citizen_name: "Joko Prasetyo", kota: "Jakarta",
    image_path: "data/images/lampu.jpg", bank_account: "1234567803", bank_name: "BRI",
    description: "Lampu jalan PJU mati total sepanjang gang, gelap dan rawan",
  },
];

const STEPS = [
  { n: 1, label: "Kirim laporan demo", desc: "Warga melapor — agent klasifikasi, rute, submit" },
  { n: 2, label: "Simulasi respon instansi", desc: "Instansi menyelesaikan — agent verifikasi & beri reward" },
  { n: 3, label: "Redeem Civic Credit", desc: "Warga tukar RSN — burn on-chain + QRIS Doku" },
];

function StatCard({ label, value, accent }: { label: string; value: number; accent: string }) {
  return (
    <div className="rounded-xl border border-zinc-800 bg-zinc-900/60 p-4">
      <div className={`text-3xl font-bold ${accent}`}>{value}</div>
      <div className="mt-1 text-xs uppercase tracking-wide text-zinc-500">{label}</div>
    </div>
  );
}

export default function Dashboard() {
  const [stats, setStats] = useState<Stats | null>(null);
  const [logs, setLogs] = useState<AgentLog[]>([]);
  const [reports, setReports] = useState<Report[]>([]);
  const [citizens, setCitizens] = useState<Citizen[]>([]);
  const [busy, setBusy] = useState<string | null>(null);
  const [toast, setToast] = useState<string | null>(null);
  const traceRef = useRef<HTMLDivElement>(null);

  const refresh = useCallback(async () => {
    try {
      const [s, l, r, c] = await Promise.all([
        api.stats(), api.logs(), api.reports(), api.citizens(),
      ]);
      // Never regress to an empty view: a serverless cold instance may briefly
      // report no data — keep the last-known populated state instead of blinking.
      setStats((prev) =>
        prev && s.total_reports === 0 && prev.total_reports > 0 ? prev : s,
      );
      setLogs((prev) => (l.length === 0 && prev.length > 0 ? prev : l));
      setReports((prev) => (r.length === 0 && prev.length > 0 ? prev : r));
      setCitizens((prev) => (c.length === 0 && prev.length > 0 ? prev : c));
    } catch {
      /* backend not reachable — keep last-known state, keep polling */
    }
  }, []);

  useEffect(() => {
    refresh();
    const t = setInterval(refresh, 2500);
    return () => clearInterval(t);
  }, [refresh]);

  const flash = (msg: string) => {
    setToast(msg);
    setTimeout(() => setToast(null), 4000);
  };

  const submitDemoReport = async () => {
    const scenario = DEMO_SCENARIOS[reports.length % DEMO_SCENARIOS.length];
    setBusy("report");
    try {
      const res = await api.submitReport({ ...scenario, channel: "dashboard" });
      flash(`Laporan diproses: ${String(res.status)}`);
      await refresh();
    } catch {
      flash("Gagal — pastikan backend berjalan");
    } finally {
      setBusy(null);
    }
  };

  const resolveAll = async () => {
    setBusy("resolve");
    try {
      await api.resolveAll();
      flash("Instansi menyelesaikan laporan — agent memverifikasi & mint reward");
      await refresh();
    } catch {
      flash("Gagal mensimulasikan respon instansi");
    } finally {
      setBusy(null);
    }
  };

  const redeem = async (citizen: Citizen) => {
    setBusy(`redeem-${citizen.id}`);
    try {
      const res = await api.redeem({
        citizen_id: citizen.id, retribusi_type: "sampah", retribusi_amount_idr: 25000,
      });
      flash(`Civic Credit: ${res.rsn_used} RSN dipakai, sisa Rp ${res.cash_due_idr}`);
      await refresh();
    } catch {
      flash("Redeem gagal — warga belum punya RSN");
    } finally {
      setBusy(null);
    }
  };

  // Which guided step is the user on?
  const activeStep = reports.length === 0 ? 1 : (stats?.resolved ?? 0) === 0 ? 2 : 3;

  return (
    <div className="min-h-screen bg-zinc-950 text-zinc-100">
      <div className="mx-auto max-w-7xl px-6 py-8">
        {/* Header */}
        <header className="flex items-center justify-between border-b border-zinc-800 pb-6">
          <div>
            <Link href="/" className="text-xs text-zinc-500 hover:text-amber-400">
              &larr; Beranda
            </Link>
            <h1 className="mt-1 text-2xl font-bold tracking-tight">
              Dashboard Agent<span className="text-amber-400">.</span>
            </h1>
            <p className="text-sm text-zinc-500">
              Pantau 7 agent Rasain bekerja secara otonom
            </p>
          </div>
          <div className="flex items-center gap-2 text-xs text-emerald-400">
            <span className="h-2 w-2 animate-pulse rounded-full bg-emerald-400" />
            agent loop aktif
          </div>
        </header>

        {/* Guided steps */}
        <section className="mt-6 grid grid-cols-1 gap-3 md:grid-cols-3">
          {STEPS.map((s) => (
            <div
              key={s.n}
              className={`rounded-xl border p-4 transition ${
                activeStep === s.n
                  ? "border-amber-500/60 bg-amber-500/5"
                  : "border-zinc-800 bg-zinc-900/40"
              }`}
            >
              <div className="flex items-center gap-2">
                <span
                  className={`flex h-6 w-6 items-center justify-center rounded-full text-xs font-bold ${
                    activeStep === s.n ? "bg-amber-500 text-zinc-950" : "bg-zinc-800 text-zinc-400"
                  }`}
                >
                  {s.n}
                </span>
                <span className="text-sm font-semibold">{s.label}</span>
              </div>
              <p className="mt-1 text-xs text-zinc-500">{s.desc}</p>
            </div>
          ))}
        </section>

        {/* Stats */}
        <section className="mt-6 grid grid-cols-2 gap-4 md:grid-cols-4">
          <StatCard label="Total Laporan" value={stats?.total_reports ?? 0} accent="text-sky-400" />
          <StatCard label="Terselesaikan" value={stats?.resolved ?? 0} accent="text-emerald-400" />
          <StatCard label="Warga Aktif" value={stats?.citizens ?? 0} accent="text-amber-400" />
          <StatCard label="RSN Diterbitkan" value={stats?.rsn_minted ?? 0} accent="text-pink-400" />
        </section>

        {/* Actions */}
        <section className="mt-6 flex flex-wrap gap-3">
          <button
            onClick={submitDemoReport}
            disabled={busy !== null}
            className="rounded-lg bg-amber-500 px-4 py-2 text-sm font-semibold text-zinc-950 transition hover:bg-amber-400 disabled:opacity-50"
          >
            {busy === "report" ? "Memproses…" : "1 · Kirim Laporan (Demo)"}
          </button>
          <button
            onClick={resolveAll}
            disabled={busy !== null}
            className="rounded-lg border border-emerald-700/60 bg-emerald-900/20 px-4 py-2 text-sm font-semibold text-emerald-300 transition hover:border-emerald-500 disabled:opacity-50"
          >
            {busy === "resolve" ? "Memproses…" : "2 · Simulasi Respon Instansi"}
          </button>
        </section>

        {/* Main grid */}
        <div className="mt-6 grid grid-cols-1 gap-6 lg:grid-cols-2">
          {/* Reasoning trace */}
          <section className="rounded-xl border border-zinc-800 bg-zinc-900/40">
            <div className="border-b border-zinc-800 px-4 py-3 text-sm font-semibold">
              Agent Reasoning Trace
              <span className="ml-2 text-xs font-normal text-zinc-500">
                jejak pikir agent — live
              </span>
            </div>
            <div ref={traceRef} className="max-h-[460px] space-y-2 overflow-y-auto p-4">
              {logs.length === 0 && (
                <p className="text-sm text-zinc-600">
                  Belum ada aktivitas. Klik &quot;1 · Kirim Laporan&quot; untuk mulai.
                </p>
              )}
              {logs.map((log) => (
                <div key={log.id} className="rounded-lg border border-zinc-800/80 bg-zinc-950/60 p-3">
                  <div className="flex items-center gap-2 text-xs">
                    <span className={`font-mono font-semibold ${AGENT_COLORS[log.agent_name] ?? "text-zinc-400"}`}>
                      {log.agent_name}
                    </span>
                    <span className="text-zinc-600">·</span>
                    <span className="text-zinc-500">{log.action}</span>
                  </div>
                  <p className="mt-1 text-sm leading-snug text-zinc-300">{log.reasoning}</p>
                </div>
              ))}
            </div>
          </section>

          {/* Reports */}
          <section className="rounded-xl border border-zinc-800 bg-zinc-900/40">
            <div className="border-b border-zinc-800 px-4 py-3 text-sm font-semibold">
              Laporan Warga
            </div>
            <div className="max-h-[460px] space-y-2 overflow-y-auto p-4">
              {reports.length === 0 && (
                <p className="text-sm text-zinc-600">Belum ada laporan.</p>
              )}
              {reports.map((r) => (
                <div key={r.id} className="rounded-lg border border-zinc-800/80 bg-zinc-950/60 p-3">
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-medium">{r.category}</span>
                    <span className={`rounded border px-2 py-0.5 text-xs ${STATUS_STYLES[r.status] ?? STATUS_STYLES.pending}`}>
                      {r.status}
                    </span>
                  </div>
                  <p className="mt-1 text-xs text-zinc-500">
                    {r.kota} · {r.instansi_target} · urgensi {r.urgency}/5
                  </p>
                  {r.lapor_ticket_id && (
                    <p className="mt-1 font-mono text-xs text-zinc-600">{r.lapor_ticket_id}</p>
                  )}
                </div>
              ))}
            </div>
          </section>
        </div>

        {/* Citizens / rewards */}
        <section className="mt-6 rounded-xl border border-zinc-800 bg-zinc-900/40">
          <div className="border-b border-zinc-800 px-4 py-3 text-sm font-semibold">
            3 · Warga &amp; Rasain Points (RSN)
            <span className="ml-2 text-xs font-normal text-zinc-500">
              reward on-chain · redeem jadi Civic Credit
            </span>
          </div>
          <div className="grid grid-cols-1 gap-3 p-4 md:grid-cols-3">
            {citizens.length === 0 && (
              <p className="text-sm text-zinc-600">Belum ada warga terdaftar.</p>
            )}
            {citizens.map((c) => (
              <div key={c.id} className="rounded-lg border border-zinc-800/80 bg-zinc-950/60 p-3">
                <div className="font-medium">{c.name}</div>
                <div className="mt-1 text-xs text-zinc-500">
                  RSN on-chain: <span className="text-pink-400">{c.rsn_onchain}</span>
                  {c.rsn_offchain > 0 && (
                    <span className="text-zinc-600"> (+{c.rsn_offchain} pending)</span>
                  )}
                </div>
                {c.solana_wallet && (
                  <div className="mt-1 font-mono text-[10px] text-zinc-600">
                    {c.solana_wallet.slice(0, 24)}…
                  </div>
                )}
                <button
                  onClick={() => redeem(c)}
                  disabled={busy !== null || c.rsn_onchain === 0}
                  className="mt-2 w-full rounded border border-pink-500/40 bg-pink-500/10 px-2 py-1 text-xs text-pink-300 transition hover:bg-pink-500/20 disabled:opacity-40"
                >
                  {busy === `redeem-${c.id}` ? "Memproses…" : "Redeem Civic Credit"}
                </button>
              </div>
            ))}
          </div>
        </section>

        <footer className="mt-8 border-t border-zinc-800 pt-4 text-xs text-zinc-600">
          Rasain · Tim hayoloh · OpenClaw Agenthon Indonesia 2026 ·
          Claude Haiku 4.5 + DOKU MCP + Mem9 + Solana SPL
        </footer>
      </div>

      {toast && (
        <div className="fixed bottom-6 right-6 rounded-lg border border-zinc-700 bg-zinc-900 px-4 py-3 text-sm shadow-xl">
          {toast}
        </div>
      )}
    </div>
  );
}
