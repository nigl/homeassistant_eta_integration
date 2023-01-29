import pytest
from unittest.mock import patch
from custom_components.eta.api import EtaAPI
from pathlib import Path
import asyncio
import os
import xmltodict

TESTDATA_FILENAME = os.path.join(os.path.dirname(__file__), "res", "menu.xml")
menu_txt = Path(TESTDATA_FILENAME).read_text()


class TestResponse:
    status = 200

    def text(self):
        value_text = """<?xml version="1.0" encoding="utf-8"?>
<eta version="1.0" xmlns="http://www.eta.co.at/rest/v1">
  <value uri="/user/var//40/10211/0/0/12015" strValue="6539" unit="kg" decPlaces="0" scaleFactor="10" advTextOffset="0">65391</value>
</eta>"""
        future = asyncio.Future()
        future.set_result(value_text)
        return future


class TestResponseMenu:
    def text(self):
        future = asyncio.Future()
        future.set_result(menu_txt)
        return future


def mock_get_request(*args, **kwargs):
    future = asyncio.Future()
    future.set_result(TestResponse())
    return future


def mock_get_request_menu(*args, **kwargs):
    future = asyncio.Future()
    future.set_result(TestResponseMenu())
    return future


@pytest.mark.asyncio
async def test_get_request(monkeypatch):
    monkeypatch.setattr(EtaAPI, "get_request", mock_get_request)
    eta = EtaAPI("session", "host", "port")

    resp = await eta.get_request("")
    assert resp.status == 200


@pytest.mark.asyncio
async def test_does_endpoint_exists(monkeypatch):
    monkeypatch.setattr(EtaAPI, "get_request", mock_get_request)
    eta = EtaAPI("session", "host", "port")

    resp = await eta.does_endpoint_exists()
    assert resp == True


@pytest.mark.asyncio
async def test_get_data(monkeypatch):
    monkeypatch.setattr(EtaAPI, "get_request", mock_get_request)
    eta = EtaAPI("session", "host", "port")

    value, unit = await eta.get_data("blub")
    assert value == 6539
    assert unit == "kg"


@pytest.mark.asyncio
async def test_get_raw_sensor_dict(monkeypatch):
    monkeypatch.setattr(EtaAPI, "get_request", mock_get_request_menu)
    eta = EtaAPI("session", "host", "port")

    value = await eta.get_raw_sensor_dict()
    assert type(value) == list  # even if it is called dict it is a list


@pytest.mark.asyncio
async def test_get_menu(monkeypatch):
    monkeypatch.setattr(EtaAPI, "get_request", mock_get_request_menu)
    eta = EtaAPI("session", "host", "port")

    value = await eta.get_sensors_dict()
    assert type(value) == dict


def test_get_all_childs():
    eta = EtaAPI("session", "host", "port")
    uri_dict = {}
    eta.evaluate_xml_dict(xmltodict.parse(menu_txt)["eta"]["menu"]["fub"], uri_dict)
    assert type(uri_dict) == dict
    assert len(uri_dict) == 97


def test_build_uri():
    eta = EtaAPI("session", "host", "port")
    assert eta.build_uri("/suffix") == "http://host:port/suffix"


@pytest.mark.asyncio
async def test_get_float_sensors(monkeypatch):
    def mock_sensors_dict(*args, **kwargs):
        future = asyncio.Future()
        future.set_result({"sensor_xy": "test_uri"})
        return future

    monkeypatch.setattr(EtaAPI, "get_request", mock_get_request)
    monkeypatch.setattr(EtaAPI, "get_sensors_dict", mock_sensors_dict)
    eta = EtaAPI("session", "host", "port")

    float_dict = await eta.get_float_sensors()
    assert float_dict == {"sensor_xy": ("test_uri", 6539.0, "kg")}
