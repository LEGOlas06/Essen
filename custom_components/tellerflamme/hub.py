"""Datenhaltung: Datensätze mit Zeitstempel, Abgleich nach "letzte Änderung gewinnt".

Jeder Datensatz hat einen Schlüssel wie ``e:<id>`` (Tagebuch-Eintrag),
``v:<id>`` (Vorrat), ``f:<id>`` (eigenes Lebensmittel), ``r:<id>`` (Rezept),
``b:<datum>`` (Körperwerte eines Tages) oder ``s`` (Einstellungen).
Gelöschte Datensätze bleiben als Grabstein (``del``) erhalten, damit das
Löschen auf allen Geräten ankommt.
"""

from __future__ import annotations

import time
import uuid
from typing import Any

from .const import ST_DA, ST_LEER, ST_WENIG, STATUSES


def now_ms() -> int:
    return int(time.time() * 1000)


class TellerHub:
    """Hält alle Datensätze. Reine Logik, ohne Home-Assistant-Abhängigkeit."""

    def __init__(self, data: dict[str, Any] | None = None) -> None:
        data = data or {}
        self.records: dict[str, dict[str, Any]] = data.get("records", {})
        self.seq: int = data.get("seq", 0)
        self.epoch: str = data.get("epoch") or uuid.uuid4().hex[:12]
        self.status: dict[str, Any] = data.get("status", {})

    def new_epoch(self) -> None:
        """Zwingt alle Geräte beim nächsten Abgleich zu einem vollständigen Neuabgleich."""
        self.epoch = uuid.uuid4().hex[:12]

    def as_dict(self) -> dict[str, Any]:
        return {"records": self.records, "seq": self.seq, "epoch": self.epoch, "status": self.status}

    # ---------- Abgleich ----------
    def put(self, key: str, value: Any, ts: int | None = None, deleted: bool = False, by: str = "ha") -> bool:
        """Speichert einen Datensatz, wenn er neuer ist als der vorhandene."""
        ts = int(ts if ts is not None else now_ms())
        cur = self.records.get(key)
        if cur is not None and ts < cur["ts"]:
            return False
        if cur is not None and cur["ts"] == ts and cur.get("del") == deleted and cur.get("v") == value:
            return False
        self.seq += 1
        rec: dict[str, Any] = {"ts": ts, "seq": self.seq, "by": by}
        if deleted:
            rec["del"] = True
        else:
            rec["v"] = value
        self.records[key] = rec
        return True

    def sync(self, cursor: int, changes: list[dict[str, Any]], client: str, epoch: str | None) -> dict[str, Any]:
        """Nimmt Änderungen eines Geräts an und gibt alles zurück, was das Gerät noch nicht hat."""
        reset = bool(epoch) and epoch != self.epoch
        if reset or cursor > self.seq:
            cursor = 0
            reset = True
        changed = False
        for c in changes:
            key = c.get("k")
            if not isinstance(key, str) or not key:
                continue
            if self.put(key, c.get("v"), c.get("ts"), bool(c.get("del")), client):
                changed = True
        out = [
            {"k": k, "ts": r["ts"], **({"del": True} if r.get("del") else {"v": r.get("v")})}
            for k, r in self.records.items()
            if r["seq"] > cursor
        ]
        return {"cursor": self.seq, "epoch": self.epoch, "reset": reset, "records": out, "changed": changed}

    # ---------- Vorrat ----------
    def vorrat(self) -> list[dict[str, Any]]:
        items = []
        for k, r in self.records.items():
            if k.startswith("v:") and not r.get("del") and isinstance(r.get("v"), dict):
                v = r["v"]
                st = v.get("st") if v.get("st") in STATUSES else ST_DA
                items.append({"id": k[2:], "name": str(v.get("name") or ""), "st": st, "food": v.get("food"), "ts": r["ts"]})
        items.sort(key=lambda x: x["name"].lower())
        return items

    def vorrat_get(self, item_id: str) -> dict[str, Any] | None:
        r = self.records.get("v:" + item_id)
        if not r or r.get("del") or not isinstance(r.get("v"), dict):
            return None
        return dict(r["v"])

    def vorrat_find(self, name: str) -> str | None:
        n = name.strip().lower()
        for it in self.vorrat():
            if it["name"].strip().lower() == n:
                return it["id"]
        return None

    def vorrat_set(self, item_id: str | None, name: str | None = None, st: str | None = None) -> str:
        if item_id is None and name:
            item_id = self.vorrat_find(name)
        cur = self.vorrat_get(item_id) if item_id else None
        if cur is None:
            item_id = item_id or "ha" + uuid.uuid4().hex[:8]
            cur = {"name": (name or "").strip(), "st": ST_DA}
        if name is not None and name.strip():
            cur["name"] = name.strip()
        if st is not None:
            if st not in STATUSES:
                raise ValueError(f"Unbekannter Status: {st}")
            cur["st"] = st
        cur["t"] = now_ms()
        self.put("v:" + item_id, cur)
        return item_id

    def vorrat_delete(self, item_id: str) -> None:
        if self.vorrat_get(item_id) is not None:
            self.put("v:" + item_id, None, deleted=True)


def parse_status(text: str | None, default: str = ST_DA) -> str:
    """Erkennt einen Status aus freiem Text (z. B. aus der Beschreibung eines To-do-Eintrags)."""
    t = (text or "").strip().lower()
    if not t:
        return default
    if t in STATUSES:
        return t
    if "fast" in t or "wenig" in t or "knapp" in t or "low" in t:
        return ST_WENIG
    if "leer" in t or "aus" == t or "empty" in t:
        return ST_LEER
    return default
