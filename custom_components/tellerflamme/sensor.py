"""Sensoren: Vorrat, Rezeptvorschlag, Kalorien, Streak und Vitaminlücken (die App liefert die Werte)."""

from __future__ import annotations

from typing import Any

from homeassistant.components.sensor import SensorEntity, SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, SIGNAL_UPDATE, ST_DA, ST_LEER, ST_WENIG


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, add: AddEntitiesCallback) -> None:
    add([cls(hass, entry) for cls in (VorratSensor, VorschlagSensor, KalorienSensor, StreakSensor, LueckenSensor)])


class _Base(SensorEntity):
    _attr_has_entity_name = True
    _attr_should_poll = False
    _key = ""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        self._data = hass.data[DOMAIN]
        self._attr_unique_id = f"{entry.entry_id}_{self._key}"
        self._attr_translation_key = self._key
        self.entity_id = f"sensor.tellerflamme_{self._key}"
        self._attr_device_info = {"identifiers": {(DOMAIN, entry.entry_id)}, "name": "Tellerflamme", "manufacturer": "Tellerflamme"}

    async def async_added_to_hass(self) -> None:
        self.async_on_remove(async_dispatcher_connect(self.hass, SIGNAL_UPDATE, self._refresh))

    @callback
    def _refresh(self) -> None:
        self.async_write_ha_state()

    @property
    def status(self) -> dict[str, Any]:
        return self._data.hub.status or {}

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
        return sum(1 for i in self._data.hub.vorrat() if i["st"] != ST_LEER)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        items = self._data.hub.vorrat()
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
