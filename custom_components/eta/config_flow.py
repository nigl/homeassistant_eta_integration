"""Adds config flow for Blueprint."""
import voluptuous as vol
from copy import deepcopy
from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.helpers import selector
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.const import (CONF_HOST, CONF_PORT)
from homeassistant.helpers.entity_registry import (
    async_entries_for_config_entry,
    async_get_registry,
)
from .api import EtaAPI
from .const import (
    DOMAIN,
    FLOAT_DICT,
    CHOOSEN_ENTITIES
)


class EtaFlowHandler(config_entries.ConfigFlow, domain=DOMAIN):
    """Config flow for Eta."""

    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_CLOUD_POLL

    def __init__(self):
        """Initialize."""
        self._errors = {}

    async def async_step_user(self, user_input=None):
        """Handle a flow initialized by the user."""
        self._errors = {}

        # Uncomment the next 2 lines if only a single instance of the integration is allowed:
        # if self._async_current_entries():
        #     return self.async_abort(reason="single_instance_allowed")

        if user_input is not None:
            valid = await self._test_url(
                user_input[CONF_HOST],
                user_input[CONF_PORT]
            )
            if valid:
                self.data = user_input
                self.data[FLOAT_DICT] = await self._get_possible_endpoints(
                    user_input[CONF_HOST],
                    user_input[CONF_PORT])

                return await self.async_step_select_entities()
            else:
                self._errors["base"] = "url_broken"

            return await self._show_config_form_user(user_input)

        user_input = {}
        # Provide defaults for form
        user_input[CONF_HOST] = "0.0.0.0"
        user_input[CONF_PORT] = "8080"

        return await self._show_config_form_user(user_input)

    async def async_step_select_entities(self, user_input=None):
        """Second step in config flow to add a repo to watch."""
        if user_input is not None:
            # add choosen entities to data
            self.data[CHOOSEN_ENTITIES] = user_input[CHOOSEN_ENTITIES]

            # User is done, create the config entry.
            return self.async_create_entry(
                title=f"ETA at {self.data[CONF_HOST]}", data=self.data
            )

        return await self._show_config_form_endpoint(self.data[FLOAT_DICT])

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return EtaOptionsFlowHandler(config_entry)

    async def _show_config_form_user(self, user_input):  # pylint: disable=unused-argument
        """Show the configuration form to edit host and port data."""
        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_HOST, default=user_input[CONF_HOST]): str,
                    vol.Required(CONF_PORT, default=user_input[CONF_PORT]): str,
                }
            ),
            errors=self._errors,
        )

    async def _show_config_form_endpoint(self, endpoint_dict):  # pylint: disable=unused-argument
        """Show the configuration form to select which endpoints should become entities."""
        return self.async_show_form(
            step_id="select_entities",
            data_schema=vol.Schema(
                {
                    vol.Optional(CHOOSEN_ENTITIES):
                        selector.SelectSelector(
                            selector.SelectSelectorConfig(
                                options=[key for key in endpoint_dict.keys()],
                                mode=selector.SelectSelectorMode.DROPDOWN,
                                multiple=True
                            ))
                }
            ),
            errors=self._errors,
        )

    async def _get_possible_endpoints(self, host, port):
        session = async_get_clientsession(self.hass)
        eta_client = EtaAPI(session, host, port)
        float_dict = await eta_client.get_float_sensors()

        return float_dict

    async def _test_url(self, host, port):
        """Return true if host port is valid."""
        session = async_get_clientsession(self.hass)
        eta_client = EtaAPI(session, host, port)

        does_endpoint_exist = await eta_client.does_endpoint_exists()
        return does_endpoint_exist


class EtaOptionsFlowHandler(config_entries.OptionsFlow):
    """Blueprint config flow options handler."""

    def __init__(self, config_entry):
        """Initialize HACS options flow."""
        self.config_entry = config_entry
        self.options = dict(config_entry.options)

    async def async_step_init(self, user_input=None):  # pylint: disable=unused-argument
        """Manage the options."""
        errors = {}

        entity_registry = await async_get_registry(self.hass)
        entries = async_entries_for_config_entry(
            entity_registry, self.config_entry.entry_id
        )
        entity_map = {e.entity_id: e for e in entries}

        if user_input is not None:
            updated_entities = deepcopy(self.config_entry.data[CHOOSEN_ENTITIES])
            # Remove any unchecked repos.
            removed_entities = [
                entity_id
                for entity_id in entity_map.keys()
                if entity_id not in user_input[CHOOSEN_ENTITIES]
            ]
            for entity_id in removed_entities:
                # Unregister from HA
                entity_registry.async_remove(entity_id)
                # Remove from our configured repos.
                entry = entity_map[entity_id]
                updated_repos = [e for e in updated_entities if e != entry]

            return self.async_create_entry(
                title="", data=self.config_entry.data
            )

        return self._show_config_form_endpoint(self.options[FLOAT_DICT], self.options[CHOOSEN_ENTITIES])

    async def _show_config_form_endpoint(self, endpoint_dict, current_chosen):  # pylint: disable=unused-argument
        """Show the configuration form to select which endpoints should become entities."""
        return self.async_show_form(
            step_id="select_entities",
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
            ),
            errors=self._errors,
        )

    async def _update_options(self):
        """Update config entry options."""
        return self.async_create_entry(
            title=self.config_entry.data.get(CONF_HOST), data=self.options
        )
