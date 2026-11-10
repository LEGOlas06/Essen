"""Sensoren pro Person: Vorrat, Rezeptvorschlag, Kalorien, Streak und Vitaminlücken (die App liefert die Werte)."""

from __future__ import annotations

from typing import Any

from homeassistant.components.sensor import SensorEntity, SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import ST_DA, ST_LEER, ST_WENIG
from .entity import PersonEntity, setup_per_person


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, add: AddEntitiesCallback) -> None:
    await setup_per_person(hass, entry, add, (VorratSensor, VorschlagSensor, KalorienSensor, StreakSensor, LueckenSensor))


class _Base(PersonEntity, SensorEntity):
    _platform = "sensor"

    @property
    def status(self) -> dict[str, Any]:
        return self.hub.status or {}

    @property
    def _stamp(self) -> dict[str, Any]:
        s = self.status
        return {"aktualisiert": s.get("updated"), "geraet": s.get("device")}


class VorratSensor(_Base):
    _key = "vorrat_anzahl"
    _attr_icon = "mdi:fridge-outline"
    _attr_native_unit_of_measurement = "Sachen"
    _attr_state_class = SensorStateClass.MEASUREMENT

    @property
    def native_value(self) -> int:
        return sum(1 for i in self.hub.vorrat() if i["st"] != ST_LEER)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        items = self.hub.vorrat()
        return {
            "da": [i["name"] for i in items if i["st"] == ST_DA],
            "fast_leer": [i["name"] for i in items if i["st"] == ST_WENIG],
            "leer": [i["name"] for i in items if i["st"] == ST_LEER],
        }


class VorschlagSensor(_Base):
    _key = "rezeptvorschlag"
    _attr_icon = "mdi:chef-hat"

    @property
    def native_value(self) -> str | None:
        sug = self.status.get("suggestions") or []
        return str(sug[0].get("name"))[:250] if sug else None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        return {"vorschlaege": self.status.get("suggestions") or [], "lebensmittel": self.status.get("foods") or [], **self._stamp}


class KalorienSensor(_Base):
    _key = "kalorien_heute"
    _attr_icon = "mdi:fire"
    _attr_native_unit_of_measurement = "kcal"
    _attr_state_class = SensorStateClass.MEASUREMENT

    @property
    def native_value(self) -> int | None:
        return self.status.get("kcal")

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        s = self.status
        return {"ziel": s.get("kcalGoal"), "eiweiss": s.get("prot"), "datum": s.get("date"), **self._stamp}


class StreakSensor(_Base):
    _key = "streak"
    _attr_icon = "mdi:fire-circle"
    _attr_native_unit_of_measurement = "Tage"

    @property
    def native_value(self) -> int | None:
        return self.status.get("streak")


class LueckenSensor(_Base):
    _key = "vitaminluecken"
    _attr_icon = "mdi:pill"

    @property
    def native_value(self) -> str | None:
        gaps = self.status.get("gaps") or []
        return ", ".join(str(g.get("name")) for g in gaps[:3])[:250] or None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        return {"naehrstoffe": self.status.get("gaps") or [], "zeitraum": self.status.get("gapDays"), **self._stamp}
