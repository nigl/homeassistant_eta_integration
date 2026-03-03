"""Adds config flow for ETA Heating."""
import voluptuous as vol
import logging
from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.helpers import selector
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.const import CONF_HOST, CONF_PORT

from .api import EtaAPI
from .const import (
    DOMAIN,
    FLOAT_DICT,
    CHOOSEN_ENTITIES
)

_LOGGER = logging.getLogger(__name__)

class EtaFlowHandler(config_entries.ConfigFlow, domain=DOMAIN):
    """Config flow for Eta."""

    VERSION = 1

    def __init__(self):
        """Initialize."""
        self._errors = {}
        self.data = {}

    async def async_step_user(self, user_input=None):
        """Handle a flow initialized by the user."""
        self._errors = {}

        if user_input is not None:
            valid = await self._test_url(
                user_input[CONF_HOST],
                user_input[CONF_PORT]
            )
            if valid:
                self.data = user_input
                try:
                    # Abrufen der verfügbaren Sensoren von der API
                    self.data[FLOAT_DICT] = await self._get_possible_endpoints(
                        user_input[CONF_HOST],
                        user_input[CONF_PORT])
                except Exception:
                    self._errors["base"] = "cannot_connect"
                    return await self.async_step_user()

                return await self.async_step_select_entities()
            else:
                self._errors["base"] = "cannot_connect"

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_HOST, default="0.0.0.0"): str,
                    vol.Required(CONF_PORT, default=8080): cv.port,
                }
            ),
            errors=self._errors,
        )

    async def async_step_select_entities(self, user_input=None):
        """Second step in config flow to add sensors."""
        if user_input is not None:
            self.data[CHOOSEN_ENTITIES] = user_input[CHOOSEN_ENTITIES]

            return self.async_create_entry(
                title=f"ETA at {self.data[CONF_HOST]}", data=self.data
            )

        # Liste der Sensoren für das Dropdown-Menü
        options = [key for key in self.data.get(FLOAT_DICT, {}).keys()]

        return self.async_show_form(
            step_id="select_entities",
            data_schema=vol.Schema(
                {
                    vol.Optional(CHOOSEN_ENTITIES):
                        selector.SelectSelector(
                            selector.SelectSelectorConfig(
                                options=options,
                                mode=selector.SelectSelectorMode.DROPDOWN,
                                multiple=True
                            ))
                }
            ),
            errors=self._errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return EtaOptionsFlowHandler(config_entry)

    async def _get_possible_endpoints(self, host, port):
        session = async_get_clientsession(self.hass)
        eta_client = EtaAPI(session, host, port)
        return await eta_client.get_float_sensors()

    async def _test_url(self, host, port):
        """Return true if host port is valid."""
        try:
            session = async_get_clientsession(self.hass)
            eta_client = EtaAPI(session, host, port)
            return await eta_client.does_endpoint_exists()
        except Exception:
            return False


class EtaOptionsFlowHandler(config_entries.OptionsFlow):
    """Handle options flow for ETA."""

    def __init__(self, config_entry):
        """Initialize options flow."""
        super().__init__()
        # Wir speichern den Eintrag in einem privaten Attribut, um Konflikte zu vermeiden
        self._config_entry = config_entry

    async def async_step_init(self, user_input=None):
        """Manage the options."""
        return await self.async_step_user(user_input)

    async def async_step_user(self, user_input=None):
        """Handle the options step."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        endpoint_dict = self._config_entry.data.get(FLOAT_DICT, {})
        current_chosen = self._config_entry.data.get(CHOOSEN_ENTITIES, [])

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Optional(CHOOSEN_ENTITIES, default=current_chosen):
                        selector.SelectSelector(
                            selector.SelectSelectorConfig(
                                options=[key for key in endpoint_dict.keys()],
                                mode=selector.SelectSelectorMode.DROPDOWN,
                                multiple=True
                            ))
                }
            )
        )
