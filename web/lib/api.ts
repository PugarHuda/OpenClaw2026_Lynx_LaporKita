// API client for the Rasain agent backend.

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

async function get<T>(path: string): Promise<T> {
  const res = await fetch(`${API_URL}${path}`, { cache: "no-store" });
  if (!res.ok) throw new Error(`GET ${path} failed: ${res.status}`);
  return res.json();
}

async function post<T>(path: string, body: unknown): Promise<T> {
  const res = await fetch(`${API_URL}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) throw new Error(`POST ${path} failed: ${res.status}`);
  return res.json();
}

export interface Stats {
  total_reports: number;
  resolved: number;
  citizens: number;
  rsn_minted: number;
}

export interface AgentLog {
  id: string;
  timestamp: string;
  agent_name: string;
  action: string;
  reasoning: string;
  tool_calls: Record<string, unknown>[];
}

export interface Report {
  id: string;
  citizen_id: string;
  category: string;
  severity: string;
  urgency: number;
  kota: string;
  instansi_target: string;
  description: string;
  status: string;
  lapor_ticket_id: string | null;
  classification_reasoning: string | null;
  submitted_at: string;
}

export interface Citizen {
  id: string;
  name: string;
  wa_number: string;
  solana_wallet: string | null;
  rsn_offchain: number;
  rsn_onchain: number;
}

export interface CityHeat {
  kota: string;
  total: number;
  resolved: number;
  categories: Record<string, number>;
}

export interface Heatmap {
  cities: CityHeat[];
  top_reporters: { name: string; reports: number }[];
}

export const api = {
  stats: () => get<Stats>("/stats"),
  heatmap: () => get<Heatmap>("/heatmap"),
  logs: (limit = 40) => get<AgentLog[]>(`/logs?limit=${limit}`),
  reports: () => get<Report[]>("/reports"),
  citizens: () => get<Citizen[]>("/citizens"),
  submitReport: (body: Record<string, unknown>) => post<Record<string, unknown>>("/report", body),
  submitReportUpload: async (formData: FormData): Promise<Record<string, unknown>> => {
    const res = await fetch(`${API_URL}/report/upload`, { method: "POST", body: formData });
    if (!res.ok) throw new Error(`upload failed: ${res.status}`);
    return res.json();
  },
  runTracker: () => post<Record<string, number>>("/tracker/run", {}),
  resolveAll: () => post<Record<string, unknown>>("/portal/resolve-all", {}),
  redeem: (body: Record<string, unknown>) => post<Record<string, unknown>>("/redeem", body),
};
