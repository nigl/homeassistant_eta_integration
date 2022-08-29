NAME = "eta"
DOMAIN = "eta"
ISSUE_URL = "https://github.com/nigl/homeassistant_eta_integration/issues"
# Configuration and options
CONF_ENABLED = "enabled"




FLOAT_DICT = "FLOAT_DICT"
CHOOSEN_ENTITIES = "choosen_entities"


BINARY_SENSOR = "binary_sensor"
SENSOR = "sensor"

PLATFORMS = [BINARY_SENSOR, SENSOR]
# URLS
USER_MENU_SUFFIX = "/user/menu"

# Defaults
DEFAULT_NAME = DOMAIN
REQUEST_TIMEOUT = 60

STARTUP_MESSAGE = f"""
-------------------------------------------------------------------
{NAME}
This is a custom integration!
If you have any issues with this you need to open an issue here:
{ISSUE_URL}
-------------------------------------------------------------------
"""