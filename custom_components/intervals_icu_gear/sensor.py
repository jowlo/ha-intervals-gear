from homeassistant.helpers.entity import Entity
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, CoordinatorEntity
from homeassistant.helpers.device_registry import DeviceEntryType
from homeassistant.const import CONF_API_KEY
from .const import DOMAIN, CONF_ATHLETE_ID
from .api import IntervalsICUClient
import logging

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass, entry, async_add_entities):
    api_key = entry.data[CONF_API_KEY]
    athlete_id = entry.data[CONF_ATHLETE_ID]
    client = IntervalsICUClient(api_key, athlete_id)

    async def async_update_data():
        return await client.async_get_gear()

    coordinator = DataUpdateCoordinator(
        hass,
        _LOGGER,
        name="intervals_icu_gear",
        update_method=async_update_data,
        update_interval=hass.config.time_zone or 3600,
    )
    await coordinator.async_config_entry_first_refresh()

    entities = []
    gear_by_id = {g["id"]: g for g in coordinator.data}
    for gear in coordinator.data:
        if gear.get("type") == "Bike" and not gear.get("component", False):
            entities.append(IntervalsICUBikeSensor(coordinator, gear, gear_by_id))
            for comp_id in gear.get("component_ids", []):
                comp = gear_by_id.get(comp_id)
                if comp:
                    entities.append(IntervalsICUComponentSensor(coordinator, comp, gear))
    async_add_entities(entities)

class IntervalsICUBikeSensor(CoordinatorEntity, Entity):
    def __init__(self, coordinator, gear, gear_by_id):
        super().__init__(coordinator)
        self.gear = gear
        self.gear_by_id = gear_by_id
        self._attr_name = f"{gear['name']} Mileage"
        self._attr_unique_id = f"intervals_icu_bike_{gear['id']}"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, gear["id"] )},
            "name": gear["name"],
            "manufacturer": "Intervals.icu",
            "model": gear.get("type", "Bike"),
            "entry_type": DeviceEntryType.SERVICE,
        }

    @property
    def state(self):
        return self.gear.get("distance")

    @property
    def unit_of_measurement(self):
        return "km"

class IntervalsICUComponentSensor(CoordinatorEntity, Entity):
    def __init__(self, coordinator, comp, bike):
        super().__init__(coordinator)
        self.comp = comp
        self.bike = bike
        self._attr_name = f"{bike['name']} - {comp['name']} Mileage"
        self._attr_unique_id = f"intervals_icu_component_{comp['id']}"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, bike["id"] )},
            "name": bike["name"],
            "manufacturer": "Intervals.icu",
            "model": bike.get("type", "Bike"),
            "entry_type": DeviceEntryType.SERVICE,
        }

    @property
    def state(self):
        return self.comp.get("distance")

    @property
    def unit_of_measurement(self):
        return "km"
import aiohttp

class IntervalsICUClient:
    def __init__(self, api_key: str, athlete_id: str):
        self.api_key = api_key
        self.athlete_id = athlete_id
        self.base_url = "https://intervals.icu/api/v1/athlete/{}/gear.json".format(athlete_id)

    async def async_get_gear(self):
        headers = {"Authorization": f"Bearer {self.api_key}"}
        async with aiohttp.ClientSession() as session:
            async with session.get(self.base_url, headers=headers) as resp:
                resp.raise_for_status()
                return await resp.json()

