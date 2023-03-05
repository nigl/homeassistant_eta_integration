"""
Platform for ETA sensor integration in Home Assistant

Help Links:
 Entity Source: https://github.com/home-assistant/core/blob/dev/homeassistant/helpers/entity.py
 SensorEntity derives from Entity https://github.com/home-assistant/core/blob/dev/homeassistant/components/sensor/__init__.py


author nigl

"""

from __future__ import annotations

import logging
from datetime import timedelta

_LOGGER = logging.getLogger(__name__)
from .api import EtaAPI

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
    ENTITY_ID_FORMAT,
)

from homeassistant.core import HomeAssistant
from homeassistant import config_entries
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.entity import generate_entity_id
from homeassistant.const import CONF_HOST, CONF_PORT
from .const import DOMAIN, CHOOSEN_ENTITIES, FLOAT_DICT

SCAN_INTERVAL = timedelta(minutes=1)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: config_entries.ConfigEntry,
    async_add_entities,
):
    """Setup sensors from a config entry created in the integrations UI."""
    config = hass.data[DOMAIN][config_entry.entry_id]
    # Update our config to include new repos and remove those that have been removed.
    if config_entry.options:
        config.update(config_entry.options)

    choosen_entities = config[CHOOSEN_ENTITIES]
    sensors = [
        EtaSensor(
            config,
            hass,
            entity,
            config[FLOAT_DICT][entity][0],
            config[FLOAT_DICT][entity][2],
        )
        for entity in choosen_entities
    ]
    async_add_entities(sensors, update_before_add=True)


class EtaSensor(SensorEntity):
    """Representation of a Sensor."""

    def __init__(
        self, config, hass, name, uri, unit, state_class=SensorStateClass.MEASUREMENT
    ):
        """
        Initialize sensor.

        To show all values: http://192.168.178.75:8080/user/menu

        There are:
          - entity_id - used to reference id, english, e.g. "eta_outside_temperature"
          - name - Friendly name, e.g "Außentemperatur" in local language

        """
        _LOGGER.warning("ETA Integration - init sensor")

        self._attr_device_class = self.determine_device_class(unit)

        if unit == "":
            unit = None

        if self._attr_device_class == SensorDeviceClass.ENERGY:
            self._attr_state_class = SensorStateClass.TOTAL_INCREASING
        else:
            self._attr_state_class = state_class

        self._attr_native_unit_of_measurement = unit
        self._attr_native_value = float
        id = name.lower().replace(" ", "_")
        self._attr_name = name  # friendly name - local language
        self.entity_id = generate_entity_id(ENTITY_ID_FORMAT, "eta_" + id, hass=hass)
        self.session = async_get_clientsession(hass)

        self.uri = uri
        self.host = config.get(CONF_HOST)
        self.port = config.get(CONF_PORT)

        # This must be a unique value within this domain. This is done using host
        self._attr_unique_id = "eta" + "_" + self.host + "." + name.replace(" ", "_")

    async def async_update(self):
        """Fetch new state data for the sensor.
        This is the only method that should fetch new data for Home Assistant.
        readme: activate first: http://www.holzheizer-forum.de/attachment/28434-eta-restful-v1-1-pdf/
        """
        eta_client = EtaAPI(self.session, self.host, self.port)
        value, _ = await eta_client.get_data(self.uri)
        self._attr_native_value = float(value)

    @staticmethod
    def determine_device_class(unit):
        unit_dict_eta = {
            "°C": SensorDeviceClass.TEMPERATURE,
            "W": SensorDeviceClass.POWER,
            "A": SensorDeviceClass.CURRENT,
            "Hz": SensorDeviceClass.FREQUENCY,
            "Pa": SensorDeviceClass.PRESSURE,
            "V": SensorDeviceClass.VOLTAGE,
            "W/m²": SensorDeviceClass.IRRADIANCE,
            "bar": SensorDeviceClass.PRESSURE,
            "kW": SensorDeviceClass.POWER,
            "kWh": SensorDeviceClass.ENERGY,
            "kg": SensorDeviceClass.WEIGHT,
            "mV": SensorDeviceClass.VOLTAGE,
            "s": SensorDeviceClass.DURATION,
        }

        if unit in unit_dict_eta:
            return unit_dict_eta[unit]
        else:
            return None
