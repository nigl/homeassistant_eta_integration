"""Sample API Client."""
import logging
import asyncio
import socket
import xmltodict
from typing import Optional
from urllib import request
import aiohttp
import async_timeout

TIMEOUT = 10

_LOGGER: logging.Logger = logging.getLogger(__package__)

HEADERS = {"Content-type": "application/json; charset=UTF-8"}


class EtaSensorAPIClient:
    """Config flow for Eta."""

    def __init__(
            self, host: str, port: str, session: aiohttp.ClientSession
    ) -> None:
        """Sample API Client."""
        self._host = host
        self._port = port
        self._session = session
        self._url = self.build_url(self._host, self._port)

    @staticmethod
    def build_url(host, port):
        return f"http://{host}:{port}"

    async def async_get_data(self, suffix) -> dict:
        """Get data from the API."""
        return await self.api_wrapper(self._url+suffix)

    @staticmethod
    def get_float_from_dict(data) -> float:
        return data['eta']['value']['@strValue']

    async def api_wrapper(self, url: str) -> dict:
        """Get information from the API."""
        try:
            async with async_timeout.timeout(TIMEOUT):
                data = await request.get(url)
                data = xmltodict.parse(data.text)
            return data

        except asyncio.TimeoutError as exception:
            _LOGGER.error(
                "Timeout error fetching information from %s - %s",
                url,
                exception,
            )

        except (KeyError, TypeError) as exception:
            _LOGGER.error(
                "Error parsing information from %s - %s",
                url,
                exception,
            )
        except Exception as exception:  # pylint: disable=broad-except
            _LOGGER.error("Something really wrong happened! - %s", exception)
