"""Gemeinsame Basis: pro Person ein eigenes Gerät „Tellerflamme <Name>“ mit eigenen Entitäten."""

from __future__ import annotations

from homeassistant.auth.models import User
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.util import slugify

from .const import DOMAIN, SIGNAL_NEW_USER, SIGNAL_UPDATE
from .hub import TellerHub


async def setup_per_person(hass: HomeAssistant, entry: ConfigEntry, add: AddEntitiesCallback, classes: tuple) -> None:
    """Legt die Entitäten für jede Person an und später für jede neue Person, die sich verbindet."""
    data = hass.data[DOMAIN]
    done: set[str] = set()

    def make(user: User) -> list[Entity]:
        done.add(user.id)
        return [cls(hass, entry, user, user.id == data.main) for cls in classes]

    ents: list[Entity] = []
    for u in await data.async_people():
        ents += make(u)
    add(ents)

    async def new_user(uid: str) -> None:
        if uid in done:
            return
        user = await hass.auth.async_get_user(uid)
        if user is not None:
            add(make(user))

    @callback
    def on_new_user(uid: str) -> None:
        hass.async_create_task(new_user(uid))

    entry.async_on_unload(async_dispatcher_connect(hass, SIGNAL_NEW_USER, on_new_user))


class PersonEntity(Entity):
    """Entität, die zu den Daten einer Person gehört."""

    _attr_has_entity_name = True
    _attr_should_poll = False
    _key = ""
    _platform = ""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry, user: User, main: bool) -> None:
        self._data = hass.data[DOMAIN]
        self._uid = user.id
        self._attr_translation_key = self._key
        name = user.name or "Person"
        if main:
            # Hauptperson behält die bisherigen IDs, damit Dashboards und Automationen weiter funktionieren
            self._attr_unique_id = f"{entry.entry_id}_{self._key}"
            self.entity_id = f"{self._platform}.tellerflamme_{self._key}"
            dev_id = entry.entry_id
        else:
            self._attr_unique_id = f"{entry.entry_id}_{self._key}_{user.id}"
            self.entity_id = f"{self._platform}.tellerflamme_{self._key}_{slugify(name)}"
            dev_id = f"{entry.entry_id}_{user.id}"
        self._attr_device_info = {"identifiers": {(DOMAIN, dev_id)}, "name": f"Tellerflamme {name}", "manufacturer": "Tellerflamme"}

    async def async_added_to_hass(self) -> None:
        self.async_on_remove(async_dispatcher_connect(self.hass, SIGNAL_UPDATE, self._refresh))

    @callback
    def _refresh(self) -> None:
        self.async_write_ha_state()

    @property
    def hub(self) -> TellerHub:
        return self._data.hub(self._uid)
