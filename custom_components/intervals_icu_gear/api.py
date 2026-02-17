import aiohttp

class IntervalsICUClient:
    def __init__(self, api_key: str, athlete_id: str):
        self.api_key = api_key
        self.athlete_id = athlete_id

    async def async_update_bike_components(self, bike_id: str, component_ids: list):
        url = f"https://intervals.icu/api/v1/athlete/{self.athlete_id}/gear/{bike_id}"
        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
        payload = {"component_ids": component_ids}
        async with aiohttp.ClientSession() as session:
            async with session.put(url, headers=headers, json=payload) as resp:
                resp.raise_for_status()
                return await resp.json()
