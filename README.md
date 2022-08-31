[![hacs_badge](https://img.shields.io/badge/HACS-Default-orange.svg)](https://github.com/custom-components/hacs)

# ETA integration for home assistant
Integration of ETA (Heating) sensors to home assistant

Uses the ETA REST API to get sensor values.
Inspiration for getting sensor data came from: https://github.com/hubtub2/ha_custom_components


Note: You have to activate the API on your pellet heater first: see documentation http://www.holzheizer-forum.de/attachment/28434-eta-restful-v1-1-pdf/

## Installation:
Configuration for the Eta integration is performed via a config flow as opposed to yaml configuration file.

1. Go to HACS -> Integrations -> Click on the three dots in the top right corner --> Click on "userdefined repositories"
2. Insert "https://github.com/nigl/homeassistant_eta_integration" into the field "repository"
3. Choose "integration" in the dropdown field "category".
4. Click on the "Add" button.
5. Then search for the new added "ETA" integration, click on it and the click on the button "Download" on the right bottom corner 
6. Restart Home Assistant when it says to.
7. In Home Assistant, go to Configuration -> Integrations -> Click "+ Add Integration"
Search for "Eta sensors" and follow the instructions to setup.