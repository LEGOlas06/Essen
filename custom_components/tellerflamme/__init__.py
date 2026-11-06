"""Tellerflamme: Vorrat, Rezeptvorschläge und Geräte-Abgleich für die Tellerflamme-App."""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol
from aiohttp import web

from homeassistant.components.http import HomeAssistantView
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant, ServiceCall, callback
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.dispatcher import async_dispatcher_send
from homeassistant.helpers.storage import Store

from .const import DOMAIN, SIGNAL_UPDATE, STATUSES, STORAGE_KEY, STORAGE_VERSION
from .hub import TellerHub

_LOGGER = logging.getLogger(__name__)
PLATFORMS = [Platform.TODO, Platform.SENSOR]
CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)

SET_SCHEMA = vol.Schema({vol.Required("name"): cv.string, vol.Optional("status", default="da"): vol.In(STATUSES)})
DEL_SCHEMA = vol.Schema({vol.Required("name"): cv.string})


class TellerData:
    """Verbindet die reine Logik mit dem Speicher von Home Assistant."""

    def __init__(self, hass: HomeAssistant) -> None:
        self.hass = hass
        self.store: Store = Store(hass, STORAGE_VERSION, STORAGE_KEY)
        self.hub = TellerHub()

    async def async_load(self) -> None:
        self.hub = TellerHub(await self.store.async_load())

    @callback
    def changed(self) -> None:
        """Nach jeder Änderung: speichern (gebündelt) und Entitäten aktualisieren."""
        self.store.async_delay_save(self.hub.as_dict, 2)
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
        try:
            body = await request.json()
        except ValueError:
            return self.json_message("Ungültige Daten", 400)
        if not isinstance(body, dict):
            return self.json_message("Ungültige Daten", 400)
        changes = body.get("changes") or []
        if not isinstance(changes, list):
            return self.json_message("Ungültige Daten", 400)
        res = data.hub.sync(int(body.get("cursor") or 0), changes, str(body.get("client") or "app")[:40], body.get("epoch"))
        status = body.get("status")
        if isinstance(status, dict):
            data.hub.status = status
            res["changed"] = True
        if res.pop("changed"):
            data.changed()
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
        return self.json({"ok": data is not None, "version": 1, "items": len(data.hub.vorrat()) if data else 0})


async def async_setup(hass: HomeAssistant, config: dict[str, Any]) -> bool:
    hass.http.register_view(TellerSyncView())
    hass.http.register_view(TellerPingView())
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    data = TellerData(hass)
    await data.async_load()
    hass.data[DOMAIN] = data

    async def set_item(call: ServiceCall) -> None:
        data.hub.vorrat_set(None, call.data["name"], call.data["status"])
        data.changed()

    async def remove_item(call: ServiceCall) -> None:
        item_id = data.hub.vorrat_find(call.data["name"])
        if item_id:
            data.hub.vorrat_delete(item_id)
            data.changed()

    hass.services.async_register(DOMAIN, "vorrat_setzen", set_item, SET_SCHEMA)
    hass.services.async_register(DOMAIN, "vorrat_entfernen", remove_item, DEL_SCHEMA)
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if ok:
        data: TellerData = hass.data.pop(DOMAIN)
        await data.store.async_save(data.hub.as_dict())
        hass.services.async_remove(DOMAIN, "vorrat_setzen")
        hass.services.async_remove(DOMAIN, "vorrat_entfernen")
    return ok
