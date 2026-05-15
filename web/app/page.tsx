import Link from "next/link";

const AGENTS = [
  { name: "Intake", desc: "Terima laporan dari WhatsApp / web", color: "text-sky-400" },
  { name: "Classifier", desc: "Klasifikasi foto via Claude vision", color: "text-violet-400" },
  { name: "Geolocator", desc: "Rute ke instansi pemerintah tepat", color: "text-amber-400" },
  { name: "Submitter", desc: "Submit ke Lapor.go.id", color: "text-emerald-400" },
  { name: "Tracker", desc: "Pantau status otonom + eskalasi", color: "text-orange-400" },
  { name: "Verifier", desc: "Verifikasi penyelesaian masalah", color: "text-teal-400" },
  { name: "Reward", desc: "Mint RSN + Civic Credit via Doku", color: "text-pink-400" },
];

const STEPS = [
  {
    n: "1", title: "Warga Lapor",
    desc: "Kirim foto masalah infrastruktur — jalan rusak, lampu mati, sampah — lewat WhatsApp atau web.",
  },
  {
    n: "2", title: "AI Agent Proses",
    desc: "7 agent otonom mengklasifikasi, merutekan ke instansi, submit ke Lapor.go.id, dan melacak status.",
  },
  {
    n: "3", title: "Warga Dapat Reward",
    desc: "Masalah beres → warga dapat Rasain Points on-chain, ditukar jadi Civic Credit bayar retribusi.",
  },
];

export default function Landing() {
  return (
    <div className="min-h-screen bg-zinc-950 text-zinc-100">
      {/* Nav */}
      <nav className="sticky top-0 z-10 border-b border-zinc-800 bg-zinc-950/80 backdrop-blur">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-6 py-4">
          <span className="text-lg font-bold tracking-tight">
            Rasain<span className="text-amber-400">.</span>
          </span>
          <div className="flex items-center gap-3">
            <Link href="/dashboard" className="text-sm text-zinc-400 transition hover:text-amber-400">
              Dashboard
            </Link>
            <Link
              href="/lapor"
              className="rounded-lg bg-amber-500 px-4 py-2 text-sm font-semibold text-zinc-950 transition hover:bg-amber-400"
            >
              Lapor Masalah
            </Link>
          </div>
        </div>
      </nav>

      {/* Hero */}
      <section className="mx-auto max-w-6xl px-6 pt-20 pb-16 text-center">
        <div className="inline-block rounded-full border border-zinc-800 bg-zinc-900 px-4 py-1 text-xs text-zinc-400">
          OpenClaw Agenthon Indonesia 2026 · Tim hayoloh
        </div>
        <h1 className="mx-auto mt-6 max-w-3xl text-5xl font-extrabold leading-tight tracking-tight md:text-6xl">
          Laporkan masalah,<br />
          <span className="text-amber-400">rasain</span> perubahannya.
        </h1>
        <p className="mx-auto mt-6 max-w-2xl text-lg text-zinc-400">
          Rasain adalah sistem multi-agent AI otonom yang membantu 280 juta warga
          Indonesia melaporkan masalah infrastruktur publik — dengan reward yang
          bisa dicairkan, transparan di blockchain.
        </p>
        <div className="mt-8 flex flex-wrap justify-center gap-3">
          <Link
            href="/lapor"
            className="rounded-lg bg-amber-500 px-6 py-3 text-sm font-semibold text-zinc-950 transition hover:bg-amber-400"
          >
            Lapor Masalah Sekarang →
          </Link>
          <Link
            href="/dashboard"
            className="rounded-lg border border-zinc-700 px-6 py-3 text-sm font-semibold transition hover:border-zinc-500"
          >
            Lihat Agent Bekerja
          </Link>
        </div>
      </section>

      {/* Problem */}
      <section className="border-y border-zinc-800 bg-zinc-900/30">
        <div className="mx-auto grid max-w-6xl gap-8 px-6 py-16 md:grid-cols-[1fr_2fr]">
          <div>
            <div className="text-5xl font-extrabold text-amber-400">Rp 327 T</div>
            <p className="mt-2 text-sm text-zinc-500">
              potensi nilai infrastruktur publik mangkrak tiap tahun karena
              pelaporan yang patah.
            </p>
          </div>
          <div className="grid gap-4 sm:grid-cols-3">
            {[
              ["280 juta", "warga menghadapi masalah infrastruktur tiap hari"],
              ["< 30%", "response rate Lapor.go.id — alur manual & lambat"],
              ["0 insentif", "warga tak punya alasan ekonomi untuk melapor"],
            ].map(([stat, desc]) => (
              <div key={stat} className="rounded-xl border border-zinc-800 bg-zinc-950 p-4">
                <div className="text-xl font-bold text-zinc-100">{stat}</div>
                <p className="mt-1 text-xs text-zinc-500">{desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* How it works */}
      <section id="cara-kerja" className="mx-auto max-w-6xl px-6 py-16">
        <h2 className="text-center text-3xl font-bold">Cara Kerja</h2>
        <p className="mt-2 text-center text-sm text-zinc-500">
          Tiga langkah — sisanya agent yang urus, otonom.
        </p>
        <div className="mt-10 grid gap-5 md:grid-cols-3">
          {STEPS.map((s) => (
            <div key={s.n} className="rounded-2xl border border-zinc-800 bg-zinc-900/40 p-6">
              <div className="flex h-10 w-10 items-center justify-center rounded-full bg-amber-500 text-lg font-bold text-zinc-950">
                {s.n}
              </div>
              <h3 className="mt-4 text-lg font-semibold">{s.title}</h3>
              <p className="mt-2 text-sm text-zinc-400">{s.desc}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Agents */}
      <section className="border-t border-zinc-800 bg-zinc-900/30">
        <div className="mx-auto max-w-6xl px-6 py-16">
          <h2 className="text-center text-3xl font-bold">7 Agent Spesialis</h2>
          <p className="mt-2 text-center text-sm text-zinc-500">
            Dikoordinasi orchestrator dengan autonomous loop — tanpa intervensi manusia.
          </p>
          <div className="mt-10 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
            {AGENTS.map((a) => (
              <div key={a.name} className="rounded-xl border border-zinc-800 bg-zinc-950 p-4">
                <div className={`font-mono text-sm font-bold ${a.color}`}>{a.name}</div>
                <p className="mt-1 text-xs text-zinc-500">{a.desc}</p>
              </div>
            ))}
            <div className="rounded-xl border border-amber-500/30 bg-amber-500/5 p-4">
              <div className="font-mono text-sm font-bold text-amber-400">Orchestrator</div>
              <p className="mt-1 text-xs text-zinc-500">
                Autonomous loop — event &amp; cron-driven
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* Civic Credit highlight */}
      <section className="mx-auto max-w-6xl px-6 py-16">
        <div className="rounded-2xl border border-zinc-800 bg-gradient-to-br from-zinc-900 to-zinc-950 p-8 text-center">
          <h2 className="text-2xl font-bold">
            Civic engagement → <span className="text-amber-400">civic credit</span>
          </h2>
          <p className="mx-auto mt-3 max-w-2xl text-sm text-zinc-400">
            Saat masalah terverifikasi selesai, warga dapat Rasain Points (RSN) —
            token SPL di Solana. RSN di-burn on-chain dan menjadi diskon tagihan
            retribusi pemerintah, dibayar lewat DOKU QRIS. Berkontribusi melapor
            secara harfiah membantu warga membayar kewajiban sipilnya.
          </p>
        </div>
      </section>

      {/* Tech */}
      <section className="border-t border-zinc-800">
        <div className="mx-auto max-w-6xl px-6 py-12 text-center">
          <p className="text-xs uppercase tracking-widest text-zinc-600">Dibangun dengan</p>
          <div className="mt-4 flex flex-wrap justify-center gap-2">
            {[
              "Claude Haiku 4.5", "Sumopod AI", "DOKU MCP Server", "Mem9",
              "Solana SPL Token", "FastAPI", "Next.js",
            ].map((t) => (
              <span
                key={t}
                className="rounded-full border border-zinc-800 bg-zinc-900 px-3 py-1 text-xs text-zinc-400"
              >
                {t}
              </span>
            ))}
          </div>
          <div className="mt-8">
            <Link
              href="/dashboard"
              className="rounded-lg bg-amber-500 px-6 py-3 text-sm font-semibold text-zinc-950 transition hover:bg-amber-400"
            >
              Buka Dashboard Agent →
            </Link>
          </div>
        </div>
      </section>

      <footer className="border-t border-zinc-800 py-6 text-center text-xs text-zinc-600">
        Rasain · Tim hayoloh · OpenClaw Agenthon Indonesia 2026
      </footer>
    </div>
  );
}
