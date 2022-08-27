import urllib
from urllib.request import urlopen
import xml.etree.ElementTree as etree


class EtaAPI:

    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.url = self.build_url(self.host, self.port)

    @staticmethod
    def build_url(host, port):
        return f"http://{host}:{port}"

    def get_xml_data(self, url_suffix):
        response = urllib.request.urlopen(self.url + url_suffix)
        tree = etree.parse(response)
        root = tree.getroot()
        return root
