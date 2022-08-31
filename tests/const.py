"""Constants for integration_blueprint tests."""
from homeassistant.const import (CONF_HOST, CONF_PORT)
# Mock config data to be used across multiple tests
MOCK_CONFIG = {CONF_HOST: "192.168.178.68", CONF_PORT: "8080"}
FLOAT_DICT_CONFIG = {"sensor1": ("uri1", 0.0, "kg"),
                     "2": ("uri2", 0.0, "°C"),
                     "sensor3": ("uri3", 1.0, "°C")}
