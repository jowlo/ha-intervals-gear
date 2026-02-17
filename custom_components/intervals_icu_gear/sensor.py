from datetime import timedelta
from homeassistant.components.sensor import SensorEntity, SensorDeviceClass, SensorStateClass
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, CoordinatorEntity
from homeassistant.helpers.device_registry import DeviceEntryType
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.const import UnitOfLength
from .const import DOMAIN, CONF_API_KEY, CONF_ATHLETE_ID
from .api import IntervalsICUClient
import logging

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass, entry, async_add_entities):
    api_key = entry.data[CONF_API_KEY]
    athlete_id = entry.data[CONF_ATHLETE_ID]
    client = IntervalsICUClient(api_key, athlete_id)

    async def async_update_data():
        try:
            data = await client.async_get_gear()
            _LOGGER.debug("Intervals.icu API returned %d items", len(data) if data else 0)
            return data if data else []
        except Exception as err:
            _LOGGER.error("Error fetching Intervals.icu gear data: %s", err)
            raise

    coordinator = DataUpdateCoordinator(
        hass,
        _LOGGER,
        name="intervals_icu_gear",
        update_method=async_update_data,
        update_interval=timedelta(hours=1),
    )

    await coordinator.async_config_entry_first_refresh()

    if coordinator.data is None:
        _LOGGER.error("Failed to fetch gear data from Intervals.icu API")
        raise ConfigEntryNotReady("Could not fetch gear data from Intervals.icu")

    entities = []
    gear_by_id = {g["id"]: g for g in coordinator.data}

    # Track which components are attached to which gear
    component_to_parent = {}
    for gear in coordinator.data:
        if not gear.get("component", False):
            for comp_id in gear.get("component_ids") or []:
                component_to_parent[comp_id] = gear

    for gear in coordinator.data:
        is_component = gear.get("component", False)

        _LOGGER.debug("Processing gear: %s, type: %s, is_component: %s",
                      gear.get("name"), gear.get("type"), is_component)

        if not is_component:
            # Create entity for main gear (bikes, shoes, etc.)
            entities.append(IntervalsICUGearSensor(coordinator, gear, gear_by_id))
        else:
            # Create entity for components (chains, tyres, cassettes, etc.)
            parent_gear = component_to_parent.get(gear["id"])
            entities.append(IntervalsICUComponentSensor(coordinator, gear, parent_gear))

    _LOGGER.info("Created %d Intervals.icu gear entities", len(entities))
    async_add_entities(entities)


class IntervalsICUGearSensor(CoordinatorEntity, SensorEntity):
    """Sensor for main gear (bikes, shoes, etc.)."""

    _attr_device_class = SensorDeviceClass.DISTANCE
    _attr_state_class = SensorStateClass.TOTAL
    _attr_native_unit_of_measurement = UnitOfLength.KILOMETERS

    def __init__(self, coordinator, gear, gear_by_id):
        super().__init__(coordinator)
        self._gear_id = gear["id"]
        self._attr_name = f"{gear['name']} Mileage"
        self._attr_unique_id = f"intervals_icu_gear_{gear['id']}"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, gear["id"])},
            "name": gear["name"],
            "manufacturer": "Intervals.icu",
            "model": gear.get("type", "Gear"),
            "entry_type": DeviceEntryType.SERVICE,
        }

    @property
    def _gear(self):
        """Get current gear data from coordinator."""
        for g in self.coordinator.data or []:
            if g["id"] == self._gear_id:
                return g
        return {}

    @property
    def extra_state_attributes(self):
        gear = self._gear
        return {
            "gear_id": gear.get("id"),
            "gear_type": gear.get("type"),
            "activities": gear.get("activities"),
            "time_seconds": gear.get("time"),
        }

    @property
    def native_value(self):
        """Return distance in km (API returns meters)."""
        distance = self._gear.get("distance")
        if distance is not None:
            return round(distance / 1000, 1)
        return None


class IntervalsICUComponentSensor(CoordinatorEntity, SensorEntity):
    """Sensor for components (chains, tyres, cassettes, etc.)."""

    _attr_device_class = SensorDeviceClass.DISTANCE
    _attr_state_class = SensorStateClass.TOTAL
    _attr_native_unit_of_measurement = UnitOfLength.KILOMETERS

    def __init__(self, coordinator, comp, parent_gear):
        super().__init__(coordinator)
        self._comp_id = comp["id"]
        self._parent_gear_id = parent_gear["id"] if parent_gear else None

        # Name includes parent gear if attached
        if parent_gear:
            self._attr_name = f"{parent_gear['name']} - {comp['name']} Mileage"
        else:
            self._attr_name = f"{comp['name']} Mileage"

        self._attr_unique_id = f"intervals_icu_component_{comp['id']}"

        # If attached to a parent, group under that device; otherwise create standalone device
        if parent_gear:
            self._attr_device_info = {
                "identifiers": {(DOMAIN, parent_gear["id"])},
                "name": parent_gear["name"],
                "manufacturer": "Intervals.icu",
                "model": parent_gear.get("type", "Gear"),
                "entry_type": DeviceEntryType.SERVICE,
            }
        else:
            self._attr_device_info = {
                "identifiers": {(DOMAIN, comp["id"])},
                "name": comp["name"],
                "manufacturer": "Intervals.icu",
                "model": comp.get("type", "Component"),
                "entry_type": DeviceEntryType.SERVICE,
            }

    @property
    def _comp(self):
        """Get current component data from coordinator."""
        for g in self.coordinator.data or []:
            if g["id"] == self._comp_id:
                return g
        return {}

    @property
    def extra_state_attributes(self):
        comp = self._comp
        return {
            "gear_id": comp.get("id"),
            "component_type": comp.get("type"),
            "activities": comp.get("activities"),
            "time_seconds": comp.get("time"),
            "parent_gear_id": self._parent_gear_id,
        }

    @property
    def native_value(self):
        """Return distance in km (API returns meters)."""
        distance = self._comp.get("distance")
        if distance is not None:
            return round(distance / 1000, 1)
        return None
