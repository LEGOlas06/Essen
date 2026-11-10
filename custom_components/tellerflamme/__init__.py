"""Tellerflamme: Vorrat, Rezeptvorschläge und Geräte-Abgleich für die Tellerflamme-App.

Jede Person in Home Assistant hat ihre eigenen Daten (Tagebuch, Vorrat, Ziele …).
Welche Person es ist, ergibt sich aus dem Zugangs-Token, mit dem sich die App anmeldet.
"""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol
from aiohttp import web

from homeassistant.auth.models import User
from homeassistant.components.http import HomeAssistantView
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant, ServiceCall, callback
from homeassistant.exceptions import ServiceValidationError
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.dispatcher import async_dispatcher_send
from homeassistant.helpers.storage import Store

from .const import DOMAIN, SIGNAL_NEW_USER, SIGNAL_UPDATE, STATUSES, STORAGE_KEY, STORAGE_VERSION
from .hub import TellerHub

_LOGGER = logging.getLogger(__name__)
PLATFORMS = [Platform.TODO, Platform.SENSOR]
CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)

SET_SCHEMA = vol.Schema(
    {
        vol.Required("name"): cv.string,
        vol.Optional("status", default="da"): vol.In(STATUSES),
        vol.Optional("person"): cv.string,
    }
)
DEL_SCHEMA = vol.Schema({vol.Required("name"): cv.string, vol.Optional("person"): cv.string})


def is_person(user: User) -> bool:
    return user.is_active and not user.system_generated


class TellerData:
    """Hält pro Person einen eigenen TellerHub und speichert alles in .storage/tellerflamme."""

    def __init__(self, hass: HomeAssistant) -> None:
        self.hass = hass
        self.store: Store = Store(hass, STORAGE_VERSION, STORAGE_KEY)
        self.hubs: dict[str, TellerHub] = {}
        # Person, der die Daten aus der Zeit vor der Trennung gehören (behält die alten Entitäts-IDs)
        self.main: str | None = None

    async def async_load(self) -> None:
        raw = await self.store.async_load() or {}
        if "users" in raw:
            self.hubs = {uid: TellerHub(d) for uid, d in (raw.get("users") or {}).items()}
            self.main = raw.get("main")
        else:
            # Alte Version: ein gemeinsamer Datenbestand. Er gehört ab jetzt dem Besitzer von Home Assistant.
            self.main = await self._owner_id()
            if raw.get("records") and self.main:
                self.hubs[self.main] = TellerHub(raw)
                _LOGGER.info("Tellerflamme: bisherige Daten der Person %s zugeordnet", self.main)
        if self.main is None:
            self.main = await self._owner_id()

    async def _owner_id(self) -> str | None:
        users = [u for u in await self.hass.auth.async_get_users() if is_person(u)]
        for u in users:
            if u.is_owner:
                return u.id
        for u in users:
            if u.is_admin:
                return u.id
        return users[0].id if users else None

    async def async_people(self) -> list[User]:
        return [u for u in await self.hass.auth.async_get_users() if is_person(u)]

    def hub(self, uid: str) -> TellerHub:
        """Datenbestand einer Person (wird bei Bedarf angelegt)."""
        h = self.hubs.get(uid)
        if h is None:
            h = self.hubs[uid] = TellerHub()
            async_dispatcher_send(self.hass, SIGNAL_NEW_USER, uid)
        return h

    def as_dict(self) -> dict[str, Any]:
        return {"main": self.main, "users": {uid: h.as_dict() for uid, h in self.hubs.items()}}

    def set_main(self, uid: str) -> None:
        """Ordnet die bisherigen Daten einer anderen Person zu (tauscht die Datenbestände, nichts geht verloren)."""
        old = self.main
        if not uid or uid == old:
            return
        a, b = self.hubs.pop(old, None) if old else None, self.hubs.pop(uid, None)
        if a is not None:
            self.hubs[uid] = a
        if b is not None and old:
            self.hubs[old] = b
        self.main = uid
        # Neue Epoche erzwingen, damit alle Geräte neu abgleichen
        for h in (self.hubs.get(uid), self.hubs.get(old) if old else None):
            if h is not None:
                h.new_epoch()
        self.changed()

    @callback
    def changed(self) -> None:
        """Nach jeder Änderung: speichern (gebündelt) und Entitäten aktualisieren."""
        self.store.async_delay_save(self.as_dict, 2)
        async_dispatcher_send(self.hass, SIGNAL_UPDATE)


class TellerSyncView(HomeAssistantView):
    """POST /api/tellerflamme/sync – Abgleich mit der App (Anmeldung per Zugangs-Token)."""

    url = "/api/tellerflamme/sync"
    name = "api:tellerflamme:sync"
    requires_auth = True
    cors_allowed = True

    async def post(self, request: web.Request) -> web.Response:
        hass: HomeAssistant = request.app["hass"]
        data: TellerData | None = hass.data.get(DOMAIN)
        if data is None:
            return self.json_message("Tellerflamme ist nicht eingerichtet", 503)
        user: User | None = request.get("hass_user")
        if user is None:
            return self.json_message("Unbekannte Person", 401)
        try:
            body = await request.json()
        except ValueError:
            return self.json_message("Ungültige Daten", 400)
        if not isinstance(body, dict):
            return self.json_message("Ungültige Daten", 400)
        changes = body.get("changes") or []
        if not isinstance(changes, list):
            return self.json_message("Ungültige Daten", 400)
        hub = data.hub(user.id)
        res = hub.sync(int(body.get("cursor") or 0), changes, str(body.get("client") or "app")[:40], body.get("epoch"))
        status = body.get("status")
        if isinstance(status, dict):
            hub.status = status
            res["changed"] = True
        if res.pop("changed"):
            data.changed()
        res["person"] = user.name
        return self.json(res)


class TellerPingView(HomeAssistantView):
    """GET /api/tellerflamme/ping – prüft Adresse und Token."""

    url = "/api/tellerflamme/ping"
    name = "api:tellerflamme:ping"
    requires_auth = True
    cors_allowed = True

    async def get(self, request: web.Request) -> web.Response:
        hass: HomeAssistant = request.app["hass"]
        data: TellerData | None = hass.data.get(DOMAIN)
        user: User | None = request.get("hass_user")
        hub = data.hubs.get(user.id) if data and user else None
        return self.json(
            {"ok": data is not None, "version": 2, "person": user.name if user else None, "items": len(hub.vorrat()) if hub else 0}
        )


async def async_setup(hass: HomeAssistant, config: dict[str, Any]) -> bool:
    hass.http.register_view(TellerSyncView())
    hass.http.register_view(TellerPingView())
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    data = TellerData(hass)
    await data.async_load()
    hass.data[DOMAIN] = data
    if entry.options.get("main") and entry.options["main"] != data.main:
        data.set_main(entry.options["main"])

    async def person_id(call: ServiceCall) -> str:
        """Person aus dem Feld „person“, sonst wer die Aktion ausführt, sonst die Hauptperson."""
        name = (call.data.get("person") or "").strip().lower()
        people = await data.async_people()
        if name:
            for u in people:
                if (u.name or "").strip().lower() == name:
                    return u.id
            raise ServiceValidationError(f"Keine Person namens „{call.data['person']}“ in Home Assistant")
        uid = call.context.user_id
        if uid and any(u.id == uid for u in people):
            return uid
        if not data.main:
            raise ServiceValidationError("Keine Person gefunden")
        return data.main

    async def set_item(call: ServiceCall) -> None:
        data.hub(await person_id(call)).vorrat_set(None, call.data["name"], call.data["status"])
        data.changed()

    async def remove_item(call: ServiceCall) -> None:
        hub = data.hub(await person_id(call))
        item_id = hub.vorrat_find(call.data["name"])
        if item_id:
            hub.vorrat_delete(item_id)
            data.changed()

    hass.services.async_register(DOMAIN, "vorrat_setzen", set_item, SET_SCHEMA)
    hass.services.async_register(DOMAIN, "vorrat_entfernen", remove_item, DEL_SCHEMA)
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(_options_updated))
    return True


async def _options_updated(hass: HomeAssistant, entry: ConfigEntry) -> None:
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if ok:
        data: TellerData = hass.data.pop(DOMAIN)
        await data.store.async_save(data.as_dict())
        hass.services.async_remove(DOMAIN, "vorrat_setzen")
        hass.services.async_remove(DOMAIN, "vorrat_entfernen")
    return ok
