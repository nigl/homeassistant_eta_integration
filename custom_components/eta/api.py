import xmltodict


class EtaAPI:
    def __init__(self, session, host, port):
        self._session = session
        self._host = host
        self._port = port

        self._float_sensor_units = [
            "%",
            "A",
            "Hz",
            "Ohm",
            "Pa",
            "U/min",
            "V",
            "W",
            "W/m²",
            "bar",
            "kW",
            "kWh",
            "kg",
            "l",
            "l/min",
            "mV",
            "m²",
            "s",
            "°C",
        ]

    def build_uri(self, suffix):
        return "http://" + self._host + ":" + str(self._port) + suffix

    def evaluate_xml_dict(self, xml_dict, uri_dict, prefix=""):
        if type(xml_dict) == list:
            for child in xml_dict:
                self.evaluate_xml_dict(child, uri_dict, prefix)
        else:
            if "object" in xml_dict:
                child = xml_dict["object"]
                new_prefix = f"{prefix}_{xml_dict['@name']}"
                self.evaluate_xml_dict(child, uri_dict, new_prefix)
            else:
                uri_dict[f"{prefix}_{xml_dict['@name']}"] = xml_dict["@uri"]

    async def get_request(self, suffix):
        data = await self._session.get(self.build_uri(suffix))
        return data

    async def does_endpoint_exists(self):
        resp = await self.get_request("/user/menu")
        return resp.status == 200

    async def _parse_data(self, data):
        unit = data["@unit"]
        if unit in self._float_sensor_units:
            scale_factor = int(data["@scaleFactor"])
            decimal_places = int(data["@decPlaces"])
            raw_value = float(data["#text"])
            value = raw_value / scale_factor
            value = round(value, decimal_places)
        else:
            # use default text string representation for values that cannot be parsed properly
            value = data["@strValue"]
        return value, unit

    async def get_data(self, uri):
        data = await self.get_request("/user/var/" + str(uri))
        text = await data.text()
        data = xmltodict.parse(text)["eta"]["value"]
        return await self._parse_data(data)

    async def get_raw_sensor_dict(self):
        data = await self.get_request("/user/menu/")
        text = await data.text()
        data = xmltodict.parse(text)
        raw_dict = data["eta"]["menu"]["fub"]
        return raw_dict

    async def get_sensors_dict(self):
        raw_dict = await self.get_raw_sensor_dict()
        uri_dict = {}
        self.evaluate_xml_dict(raw_dict, uri_dict)
        return uri_dict

    async def get_float_sensors(self):
        sensor_dict = await self.get_sensors_dict()
        float_dict = {}
        for key in sensor_dict:
            try:
                value, unit = await self.get_data(sensor_dict[key])
                if unit not in self._float_sensor_units:
                    continue
                cleaned_key = key.lower().replace(" ", "_")
                float_dict[cleaned_key] = (sensor_dict[key], value, unit)
            except:
                pass
        return float_dict
