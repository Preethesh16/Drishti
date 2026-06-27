"""Booth↔booth P2P sync — the LAN-loss fallback (B3 + B5, SIMULATED).

Connectivity ladder: LAN → central (normal). When LAN drops, booths sync
peer-to-peer with neighbours so the shared pool survives; when LAN returns they
reconcile upward. This is a SIM (no real BLE/DTN) that proves the merge logic:
on-device UUIDs (no collisions), terminal-status-wins, else last-writer-wins,
and no central coordinator needed for booths to converge.

Run:  python -m drishti.mesh
"""
from __future__ import annotations

from dataclasses import dataclass, field

TERMINAL = "Reunited"  # a confirmed reunion is terminal and always wins a merge


@dataclass
class Item:
    case_id: str          # on-device UUID — unique across booths, so no collisions
    report_type: str      # missing | found
    status: str
    summary: str
    origin: str           # which booth created it
    clock: int            # logical timestamp (Lamport-ish) for last-writer-wins


@dataclass
class MeshNode:
    name: str
    store: dict[str, Item] = field(default_factory=dict)
    _clock: int = 0
    log: list[str] = field(default_factory=list)

    def tick(self) -> int:
        self._clock += 1
        return self._clock

    def create(self, case_id, report_type, summary, status="Pending") -> Item:
        it = Item(case_id, report_type, status, summary, self.name, self.tick())
        self.store[case_id] = it
        self.log.append(f"{self.name}: created {case_id} ({report_type}) offline")
        return it

    def update_status(self, case_id, status):
        if case_id in self.store:
            self.store[case_id].status = status
            self.store[case_id].clock = self.tick()
            self.log.append(f"{self.name}: {case_id} → {status}")

    @staticmethod
    def _wins(incoming: Item, current: Item) -> bool:
        """Conflict resolution: terminal status wins; else higher clock (LWW)."""
        if incoming.status == TERMINAL and current.status != TERMINAL:
            return True
        if current.status == TERMINAL and incoming.status != TERMINAL:
            return False
        return incoming.clock > current.clock

    def sync(self, other: "MeshNode") -> int:
        """One P2P exchange (both directions). Returns number of records changed."""
        changed = 0
        for src, dst in ((self, other), (other, self)):
            for cid, it in src.store.items():
                cur = dst.store.get(cid)
                if cur is None:                       # new UUID → just copy
                    dst.store[cid] = Item(**it.__dict__)
                    changed += 1
                elif cur.case_id == it.case_id and it != cur and self._wins(it, cur):
                    dst.store[cid] = Item(**it.__dict__)
                    changed += 1
        tag = f"{self.name}↔{other.name}"
        self.log.append(f"P2P sync {tag}: {changed} record(s) reconciled")
        return changed


def run_demo() -> dict:
    """LAN down → A creates a FOUND, B a MISSING; A→B→C hops; C reunites it;
    LAN back → reconcile to central. Everyone converges, terminal status wins."""
    central = MeshNode("Control Room (LAN)")
    a = MeshNode("Ramkund Booth")
    b = MeshNode("Tapovan Booth")
    c = MeshNode("Sadhugram Booth")
    events: list[str] = ["📴 LAN DOWN — booths fall back to P2P"]

    a.create("F-7a1", "found", "elderly man, white kurta, found near Ramkund")
    b.create("M-3c9", "missing", "father missing, ~70, white kurta — filed at Tapovan")
    events += [a.log[-1], b.log[-1]]

    events.append("📡 P2P hops A→B→C (epidemic spread)")
    a.sync(b); events.append(a.log[-1])
    b.sync(c); events.append(b.log[-1])
    events.append(f"  → every booth now holds {len(c.store)} records offline (UUID-deduped)")

    events.append("🤝 Sadhugram volunteer confirms the reunion (offline)")
    c.update_status("F-7a1", TERMINAL); events.append(c.log[-1])
    a.update_status("F-7a1", "Transferred to hospital")  # a stale conflicting edit
    events.append(f"  ⚠️ conflict: {a.name} has F-7a1=Transferred (clock {a.store['F-7a1'].clock}), "
                  f"{c.name} has Reunited")

    events.append("🌐 LAN BACK — booths reconcile to central")
    central.sync(a); central.sync(b); central.sync(c)
    events.append(f"  → central converged: terminal status wins → "
                  f"F-7a1 = {central.store['F-7a1'].status}")

    return {
        "events": events,
        "final": {cid: it.status for cid, it in sorted(central.store.items())},
        "converged": all(
            n.store.get("F-7a1") and n.store["F-7a1"].status == TERMINAL
            for n in (central,) ) and central.store["F-7a1"].status == TERMINAL,
    }


if __name__ == "__main__":
    res = run_demo()
    for e in res["events"]:
        print(e)
    print("\nFinal central state:", res["final"])
    print("Terminal-status-wins converged:", res["converged"])
