import xmltodict


class EtaAPI:
    def __init__(self, session, host, port):
        self._session = session
        self._host = host
        self._port = port

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

    async def get_data(self, uri):
        data = await self.get_request("/user/var/" + str(uri))
        text = await data.text()
        data = xmltodict.parse(text)
        return data["eta"]["value"]["@strValue"], data["eta"]["value"]["@unit"]

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
                raw_value, unit = await self.get_data(sensor_dict[key])
                value = float(raw_value)
                cleaned_key = key.lower().replace(" ", "_")
                float_dict[cleaned_key] = (sensor_dict[key], value, unit)
            except:
                pass
        return float_dict
