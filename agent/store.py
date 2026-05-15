"""JSON-backed repository for Rasain entities.

Hackathon-pragmatic persistence: in-memory dicts + JSON snapshot on every write.
Data volume is tiny (~tens of records), so this is reliable, restart-survivable,
and trivially resettable for demo re-takes. V2 swaps this for a real DB behind
the same interface — agent code never touches storage details.
"""
from __future__ import annotations

import json
import threading
from pathlib import Path
from uuid import UUID

from agent.models import AgentLogEntry, Citizen, Report, Reward

_DB_PATH = Path("rasain_store.json")
_lock = threading.Lock()


class Store:
    """Single source of truth for all entities. Thread-safe writes."""

    def __init__(self, path: Path = _DB_PATH) -> None:
        self.path = path
        self.citizens: dict[str, Citizen] = {}
        self.reports: dict[str, Report] = {}
        self.rewards: dict[str, Reward] = {}
        self.logs: list[AgentLogEntry] = []
        self._load()

    # --- persistence ---
    def _load(self) -> None:
        if not self.path.exists():
            return
        raw = json.loads(self.path.read_text(encoding="utf-8"))
        self.citizens = {k: Citizen(**v) for k, v in raw.get("citizens", {}).items()}
        self.reports = {k: Report(**v) for k, v in raw.get("reports", {}).items()}
        self.rewards = {k: Reward(**v) for k, v in raw.get("rewards", {}).items()}
        self.logs = [AgentLogEntry(**v) for v in raw.get("logs", [])]

    def _save(self) -> None:
        with _lock:
            snapshot = {
                "citizens": {k: json.loads(v.model_dump_json()) for k, v in self.citizens.items()},
                "reports": {k: json.loads(v.model_dump_json()) for k, v in self.reports.items()},
                "rewards": {k: json.loads(v.model_dump_json()) for k, v in self.rewards.items()},
                "logs": [json.loads(v.model_dump_json()) for v in self.logs],
            }
            self.path.write_text(json.dumps(snapshot, indent=2, default=str), encoding="utf-8")

    # --- citizen ---
    def upsert_citizen(self, citizen: Citizen) -> Citizen:
        self.citizens[str(citizen.id)] = citizen
        self._save()
        return citizen

    def get_citizen(self, citizen_id: UUID | str) -> Citizen | None:
        return self.citizens.get(str(citizen_id))

    def get_citizen_by_wa(self, wa_number: str) -> Citizen | None:
        return next((c for c in self.citizens.values() if c.wa_number == wa_number), None)

    # --- report ---
    def upsert_report(self, report: Report) -> Report:
        self.reports[str(report.id)] = report
        self._save()
        return report

    def get_report(self, report_id: UUID | str) -> Report | None:
        return self.reports.get(str(report_id))

    def list_reports(self) -> list[Report]:
        return list(self.reports.values())

    def list_reports_by_citizen(self, citizen_id: UUID | str) -> list[Report]:
        return [r for r in self.reports.values() if str(r.citizen_id) == str(citizen_id)]

    # --- reward ---
    def upsert_reward(self, reward: Reward) -> Reward:
        self.rewards[str(reward.id)] = reward
        self._save()
        return reward

    def list_rewards_by_citizen(self, citizen_id: UUID | str) -> list[Reward]:
        return [r for r in self.rewards.values() if str(r.citizen_id) == str(citizen_id)]

    # --- agent log (reasoning trace for dashboard transparency) ---
    def add_log(self, entry: AgentLogEntry) -> AgentLogEntry:
        self.logs.append(entry)
        self._save()
        return entry

    def recent_logs(self, limit: int = 50) -> list[AgentLogEntry]:
        return self.logs[-limit:]

    # --- demo helper ---
    def reset(self) -> None:
        """Wipe all state — for demo re-takes."""
        self.citizens.clear()
        self.reports.clear()
        self.rewards.clear()
        self.logs.clear()
        self._save()


_store: Store | None = None


def get_store() -> Store:
    """Process-wide singleton."""
    global _store
    if _store is None:
        _store = Store()
    return _store
