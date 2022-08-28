"""
Platform for ETA sensor integration in Home Assistant

Help Links:
 Entity Source: https://github.com/home-assistant/core/blob/dev/homeassistant/helpers/entity.py
 SensorEntity derives from Entity https://github.com/home-assistant/core/blob/dev/homeassistant/components/sensor/__init__.py


author hubtub2

"""

from __future__ import annotations
import requests
from datetime import timedelta
import xmltodict
import logging
import voluptuous as vol

_LOGGER = logging.getLogger(__name__)

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
    PLATFORM_SCHEMA,
    ENTITY_ID_FORMAT
)

from homeassistant.core import HomeAssistant
from homeassistant import config_entries
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType
import homeassistant.helpers.config_validation as cv

from homeassistant.helpers.entity import generate_entity_id

# See https://github.com/home-assistant/core/blob/dev/homeassistant/const.py
from homeassistant.const import (CONF_HOST, CONF_PORT, TEMP_CELSIUS, ENERGY_KILO_WATT_HOUR, POWER_KILO_WATT,
                                 MASS_KILOGRAMS)
from .const import DOMAIN

SCAN_INTERVAL = timedelta(minutes=1)

# See https://community.home-assistant.io/t/problem-with-scan-interval/139031
PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_HOST): cv.string,
    vol.Required(CONF_PORT): cv.positive_int,
    # vol.Optional(DEFAULT_NAME): cv.string,
    # vol.Optional(CONF_TYPE): cv.string,
    # vol.Optional(CONF_SCAN_INTERVAL): cv.time_period,
})


async def async_setup_entry(
        hass: HomeAssistant,
        config_entry: config_entries.ConfigEntry,
        async_add_entities,
):
    """Setup sensors from a config entry created in the integrations UI."""
    config = hass.data[DOMAIN][config_entry.entry_id]
    sensors = [EtaSensor(config, hass, "Außentemperatur", "/user/var/120/10601/0/0/12197", TEMP_CELSIUS)]
    async_add_entities(sensors, update_before_add=True)


def setup_platform(
        hass: HomeAssistant,
        config: ConfigType,
        add_entities: AddEntitiesCallback,
        discovery_info: DiscoveryInfoType | None = None
) -> None:
    """Set up the sensor platform."""

    _LOGGER.warning("ETA Integration - setup platform")

    # TODO: read http://192.168.178.75:8080/user/menu and get friendly name in original language
    entities = [
        EtaSensor(config, hass, "Außentemperatur", "/user/var/120/10601/0/0/12197", TEMP_CELSIUS)
        # EtaSensor(config, hass, "Requested Power", "/user/var/40/10021/0/0/12077", POWER_KILO_WATT),
        # EtaSensor(config, hass, "Requested Temp", "/user/var///40/10021/0/0/12006", TEMP_CELSIUS),
        # EtaSensor(config, hass, "Kesseltemperatur", "/user/var///40/10021/0/11109/0", TEMP_CELSIUS),
        # EtaSensor(config, hass, "Abgastemperatur", "/user/var//40/10021/0/11110/0", TEMP_CELSIUS),
        # EtaSensor(config, hass, "Vorlauftemperatur", "/user/var///120/10101/0/11125/2121", TEMP_CELSIUS),
        # EtaSensor(config, hass, "Silo", "/user/var//40/10201/0/0/12015", MASS_KILOGRAMS),
        # EtaSensor(config, hass, "Pellets Gesamtverbrauch", "/user/var//40/10021/0/0/12016", MASS_KILOGRAMS),
        # EtaSensor(config, hass, "Pellets Gesamtenergie", "/user/var//40/10021/0/0/12016", ENERGY_KILO_WATT_HOUR,
        #           device_class=SensorDeviceClass.ENERGY, state_class=SensorStateClass.TOTAL_INCREASING, factor=4.8)

    ]

    add_entities(entities, update_before_add=True)


class EtaSensor(SensorEntity):
    """Representation of a Sensor."""

    # _attr_device_class = SensorDeviceClass.TEMPERATURE
    # _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, config, hass, name, uri, unit, state_class=SensorStateClass.MEASUREMENT,
                 device_class=SensorDeviceClass.TEMPERATURE, factor=1.0):
        """
        Initialize sensor.

        To show all values: http://192.168.178.75:8080/user/menu

        There are:
          - entity_id - used to reference id, english, e.g. "eta_outside_temperature"
          - name - Friendly name, e.g "Außentemperatur" in local language
          - unique_id - globally unique id of sensor, e.g. "eta_11.123488_outside_temp", based on serial number

        """
        _LOGGER.warning("ETA Integration - init sensor")

        self._attr_state_class = state_class
        self._attr_device_class = device_class

        id = name.lower().replace(' ', '_')
        self._attr_name = name  # friendly name - local language
        self.entity_id = generate_entity_id(ENTITY_ID_FORMAT, "eta_" + id, hass=hass)
        # self.entity_description = description
        self._attr_native_unit_of_measurement = unit
        self.uri = uri
        self.factor = 1.0
        self.host = config.get(CONF_HOST)
        self.port = config.get(CONF_PORT)

        # This must be a unique value within this domain. This is done use host
        self._attr_unique_id = "eta" + "_" + self.host + "." + name.replace(" ", "_")

    def update(self) -> None:
        """Fetch new state data for the sensor.
        This is the only method that should fetch new data for Home Assistant.
        TODO: readme: activate first: http://www.holzheizer-forum.de/attachment/28434-eta-restful-v1-1-pdf/
        """

        # REST GET
        data = requests.get("http://" + self.host + ":" + str(self.port) + self.uri)
        data = xmltodict.parse(data.text)
        value = data['eta']['value']['@strValue']
        value = float(value.replace(',', '.')) * self.factor

        self._attr_native_value = value
