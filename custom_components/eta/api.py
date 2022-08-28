import requests
import xmltodict


class EtaAPI:
    def __init__(self, host, port):
        self._host = host
        self._port = port

    def build_uri(self, suffix):
        return "http://" + self.host + ":" + str(self.port) + suffix

    @staticmethod
    def evaluate_xml_dict(self, xml_dict, uri_dict, prefix=""):
        if type(xml_dict) == list:
            for child in xml_dict:
                self.evaluate_xml_dict(child, uri_dict, prefix)
        else:
            if 'object' in xml_dict:
                child = xml_dict['object']
                new_prefix = f"{prefix}_{xml_dict['@name']}"
                self.evaluate_xml_dict(child, uri_dict, new_prefix)
            else:
                uri_dict[f"{prefix}_{xml_dict['@name']}"] = xml_dict["@uri"]

    def get_data(self, uri):
        data = requests.get(self.build_uri("/user/var/" + str(uri)))
        data = xmltodict.parse(data.text)
        return data['eta']['value']['@strValue']

    def get_raw_sensor_dict(self):
        data = requests.get(self.build_uri("/user/menu/"))
        data = xmltodict.parse(data.text)
        raw_dict = data["eta"]["menu"]["fub"]
        return raw_dict

    def get_sensors_dict(self):
        raw_dict = self.get_raw_sensor_dict()
        uri_dict = {}
        self.evaluate_xml_dict(raw_dict, uri_dict)
        return uri_dict

    def get_float_sensors(self):
        sensor_dict = self.get_sensors_dict()
        float_dict = {}
        for key in sensor_dict:
            try:
                value = float(self.get_data(sensor_dict[key]))
                float_dict[key] = value
            except:
                pass
        return float_dict