"""Einrichtung über die Oberfläche (Einstellungen → Geräte & Dienste)."""

from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigEntry, ConfigFlow, ConfigFlowResult, OptionsFlow
from homeassistant.core import callback
from homeassistant.helpers.selector import SelectOptionDict, SelectSelector, SelectSelectorConfig

from .const import DOMAIN


class TellerflammeConfigFlow(ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        if self._async_current_entries():
            return self.async_abort(reason="single_instance_allowed")
        if user_input is not None:
            return self.async_create_entry(title="Tellerflamme", data={})
        return self.async_show_form(step_id="user")

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> OptionsFlow:
        return TellerOptionsFlow()


class TellerOptionsFlow(OptionsFlow):
    """Legt fest, wem die Daten aus der Zeit vor der Trennung nach Personen gehören."""

    async def async_step_init(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        if user_input is not None:
            return self.async_create_entry(data={"main": user_input["main"]})
        data = self.hass.data.get(DOMAIN)
        people = await data.async_people() if data else []
        current = self.config_entry.options.get("main") or (data.main if data else None)
        opts = [SelectOptionDict(value=u.id, label=u.name or u.id) for u in people]
        schema = vol.Schema(
            {vol.Required("main", default=current): SelectSelector(SelectSelectorConfig(options=opts))}
        )
        return self.async_show_form(step_id="init", data_schema=schema)
