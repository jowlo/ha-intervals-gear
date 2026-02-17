import aiohttp
from aiohttp import BasicAuth

class IntervalsICUClient:
    def __init__(self, api_key: str, athlete_id: str):
        self.api_key = api_key
        self.athlete_id = athlete_id
        self.base_url = f"https://intervals.icu/api/v1/athlete/{athlete_id}"
        self.auth = BasicAuth("API_KEY", api_key)

    async def async_get_gear(self):
        url = f"{self.base_url}/gear.json"
        async with aiohttp.ClientSession(auth=self.auth) as session:
            async with session.get(url) as resp:
                resp.raise_for_status()
                return await resp.json()

    async def async_update_bike_components(self, bike_id: str, component_ids: list):
        url = f"{self.base_url}/gear/{bike_id}"
        headers = {"Content-Type": "application/json"}
        payload = {"component_ids": component_ids}
        async with aiohttp.ClientSession(auth=self.auth) as session:
            async with session.put(url, headers=headers, json=payload) as resp:
                resp.raise_for_status()
                return await resp.json()
