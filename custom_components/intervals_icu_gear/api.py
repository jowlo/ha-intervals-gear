import aiohttp
from aiohttp import BasicAuth
import logging

_LOGGER = logging.getLogger(__name__)

class IntervalsICUClient:
    def __init__(self, api_key: str, athlete_id: str):
        self.api_key = api_key
        self.athlete_id = athlete_id
        self.base_url = f"https://intervals.icu/api/v1/athlete/{athlete_id}"
        self.auth = BasicAuth("API_KEY", api_key)

    async def async_get_gear(self):
        url = f"{self.base_url}/gear"
        _LOGGER.debug("Fetching gear from: %s", url)
        async with aiohttp.ClientSession(auth=self.auth) as session:
            async with session.get(url) as resp:
                _LOGGER.debug("API response status: %s", resp.status)
                if resp.status == 401:
                    _LOGGER.error("Authentication failed - check your API key and athlete ID")
                resp.raise_for_status()
                data = await resp.json()
                _LOGGER.debug("API returned %d gear items", len(data) if data else 0)
                return data

    async def async_update_bike_components(self, bike_id: str, component_ids: list):
        url = f"{self.base_url}/gear/{bike_id}"
        headers = {"Content-Type": "application/json"}
        payload = {"component_ids": component_ids}
        async with aiohttp.ClientSession(auth=self.auth) as session:
            async with session.put(url, headers=headers, json=payload) as resp:
                resp.raise_for_status()
                return await resp.json()
