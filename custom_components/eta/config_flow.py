"""Adds config flow for Blueprint."""
import async_timeout
from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.helpers.aiohttp_client import async_get_clientsession
import voluptuous as vol
from .api import EtaAPI
import homeassistant.helpers.config_validation as cv
from homeassistant.const import (CONF_HOST, CONF_PORT)
from .const import (
    DOMAIN,
    FLOAT_DICT,
    PLATFORMS, CHOOSEN_ENTITIES
)


class EtaFlowHandler(config_entries.ConfigFlow, domain=DOMAIN):
    """Config flow for Eta."""

    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_CLOUD_POLL

    def __init__(self):
        """Initialize."""
        self._errors = {}
        session = async_get_clientsession(self.hass)

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

    async def async_step_select_entities(self, user_input = None):
        """Second step in config flow to add a repo to watch."""
        errors = {}
        if user_input is not None:

            # add choosen entities to data
            self.data[CHOOSEN_ENTITIES] = user_input

            # User is done, create the config entry.
            return self.async_create_entry(
                title=f"ETA at {user_input[CONF_HOST]}", data=self.data
            )

        return self._show_config_form_endpoint(self.data[FLOAT_DICT]
        )

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
                    vol.Required(x,msg=f"example value: {endpoint_dict[x][1]}", default=False): bool
                    for x in sorted(endpoint_dict.keys())
                }
            ),
            errors=self._errors,
        )

    async def _get_possible_endpoints(self, host, port):
        eta_client = EtaAPI(self.session, host, port)
        float_dict = await eta_client.get_float_sensors()

        return float_dict

    async def _test_url(self, host, port):
        """Return true if host port is valid."""
        eta_client = EtaAPI(self.session, host, port)

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
        return await self.async_step_user()

    async def async_step_user(self, user_input=None):
        """Handle a flow initialized by the user."""
        if user_input is not None:
            self.options.update(user_input)
            return await self._update_options()

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(x, default=self.options.get(x, True)): bool
                    for x in sorted(PLATFORMS)
                }
            ),
        )

    async def _update_options(self):
        """Update config entry options."""
        return self.async_create_entry(
            title=self.config_entry.data.get(CONF_HOST), data=self.options
        )
