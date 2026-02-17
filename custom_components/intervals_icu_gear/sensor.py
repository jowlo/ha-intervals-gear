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

# Map gear/component types to MDI icons
ICON_MAP = {
    # Main gear
    "Bike": "mdi:bike",
    "Shoes": "mdi:shoe-sneaker",
    "Wetsuit": "mdi:diving-scuba-mask",
    "RowingMachine": "mdi:rowing",
    "Skis": "mdi:ski",
    "Snowboard": "mdi:snowboard",
    "Boat": "mdi:sail-boat",
    "Board": "mdi:surfing",
    "Equipment": "mdi:dumbbell",
    # Components
    "Chain": "mdi:link-variant",
    "Cassette": "mdi:cog",
    "Tyre": "mdi:tire",
    "Wheel": "mdi:tire",
    "Wheelset": "mdi:tire",
    "Brake": "mdi:car-brake-hold",
    "BrakePads": "mdi:car-brake-hold",
    "Rotor": "mdi:circle-outline",
    "Drivetrain": "mdi:cog-transfer",
    "BottomBracket": "mdi:cog",
    "Chainrings": "mdi:cog",
    "Crankset": "mdi:cog",
    "Derailleur": "mdi:cog-transfer",
    "Pedals": "mdi:foot-print",
    "Lever": "mdi:lever",
    "Cable": "mdi:cable-data",
    "Frame": "mdi:bike",
    "Fork": "mdi:bike",
    "Handlebar": "mdi:steering",
    "Headset": "mdi:circle-double",
    "Saddle": "mdi:seat",
    "Seatpost": "mdi:seat",
    "Shock": "mdi:arrow-collapse-vertical",
    "Stem": "mdi:steering",
    "Axel": "mdi:axis-arrow",
    "Hub": "mdi:circle-slice-8",
    "Trainer": "mdi:bike-fast",
    "Tube": "mdi:tire",
    "PowerMeter": "mdi:flash",
    "Cleats": "mdi:shoe-cleat",
    "CyclingShoes": "mdi:shoe-cleat",
    "Paddle": "mdi:oar",
    "Computer": "mdi:speedometer",
    "Light": "mdi:flashlight",
    "Battery": "mdi:battery",
    "Accessories": "mdi:bag-personal",
    "Apparel": "mdi:tshirt-crew",
}

DEFAULT_ICON = "mdi:cog"


def get_icon_for_type(gear_type: str) -> str:
    """Get MDI icon for gear type."""
    return ICON_MAP.get(gear_type, DEFAULT_ICON)


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

    # Store coordinator in hass.data so the service can access it
    hass.data[DOMAIN]["coordinator"] = coordinator

    entities = []

    # Build a lookup of all gear by ID
    gear_by_id = {g["id"]: g for g in coordinator.data}

    for gear in coordinator.data:
        is_component = gear.get("component", False)

        _LOGGER.debug("Processing gear: %s, type: %s, is_component: %s",
                      gear.get("name"), gear.get("type"), is_component)

        if not is_component:
            # Create mileage entity for main gear (bikes, shoes, etc.)
            entities.append(IntervalsICUGearMileageSensor(coordinator, gear))

            # For bikes, create sensors for each equipped component
            if gear.get("type") == "Bike":
                component_ids = gear.get("component_ids") or []

                # Group components by type to determine if numbering is needed
                components_by_type = {}
                for comp_id in component_ids:
                    comp = gear_by_id.get(comp_id)
                    if comp:
                        comp_type = comp.get("type", "Component")
                        if comp_type not in components_by_type:
                            components_by_type[comp_type] = []
                        components_by_type[comp_type].append(comp)

                # Create sensors with numbered suffixes only when multiple of same type
                for comp_type, comps in components_by_type.items():
                    # Sort by ID for consistent slot assignment
                    comps.sort(key=lambda c: c.get("id", ""))
                    needs_numbering = len(comps) > 1
                    for idx, comp in enumerate(comps, start=1):
                        suffix = f"_{idx}" if needs_numbering else ""
                        # Sensor showing equipped component name
                        entities.append(IntervalsICUEquippedComponentSensor(
                            coordinator, gear, comp, comp_type, suffix, idx
                        ))
                        # Sensor showing equipped component mileage
                        entities.append(IntervalsICUEquippedComponentMileageSensor(
                            coordinator, gear, comp, comp_type, suffix, idx
                        ))
        else:
            # Create entity for components (chains, tyres, cassettes, etc.)
            entities.append(IntervalsICUComponentSensor(coordinator, gear))

    _LOGGER.info("Created %d Intervals.icu gear entities", len(entities))
    async_add_entities(entities)


class IntervalsICUGearMileageSensor(CoordinatorEntity, SensorEntity):
    """Mileage sensor for main gear (bikes, shoes, etc.)."""

    _attr_device_class = SensorDeviceClass.DISTANCE
    _attr_state_class = SensorStateClass.TOTAL
    _attr_native_unit_of_measurement = UnitOfLength.KILOMETERS
    _attr_has_entity_name = True

    def __init__(self, coordinator, gear):
        super().__init__(coordinator)
        self._gear_id = gear["id"]
        self._gear_type = gear.get("type", "Gear")
        self._gear_name = gear.get("name", "Unknown")
        self._attr_unique_id = f"intervals_icu_gear_{gear['id']}_mileage"
        self._attr_icon = get_icon_for_type(self._gear_type)

    @property
    def _gear(self):
        """Get current gear data from coordinator."""
        for g in self.coordinator.data or []:
            if g["id"] == self._gear_id:
                return g
        return {}

    def _get_equipped_components(self):
        """Get list of equipped components with their details."""
        gear = self._gear
        component_ids = gear.get("component_ids") or []
        components = []
        for g in self.coordinator.data or []:
            if g["id"] in component_ids:
                components.append({
                    "id": g["id"],
                    "name": g.get("name"),
                    "type": g.get("type"),
                    "distance_km": round(g.get("distance", 0) / 1000, 1) if g.get("distance") else None,
                })
        return components

    @property
    def name(self):
        return "Mileage"

    @property
    def device_info(self):
        gear = self._gear
        return {
            "identifiers": {(DOMAIN, self._gear_id)},
            "name": gear.get("name", self._gear_name),
            "manufacturer": "Intervals.icu",
            "model": gear.get("type", self._gear_type),
            "entry_type": DeviceEntryType.SERVICE,
        }

    @property
    def extra_state_attributes(self):
        gear = self._gear
        equipped = self._get_equipped_components()
        # Build a dict of component type -> name for easy reference
        equipped_by_type = {c["type"]: c["name"] for c in equipped}
        return {
            "gear_id": gear.get("id"),
            "gear_type": gear.get("type"),
            "activities": gear.get("activities"),
            "time_seconds": gear.get("time"),
            "component_ids": gear.get("component_ids") or [],
            "equipped_components": equipped,
            "equipped_by_type": equipped_by_type,
        }

    @property
    def native_value(self):
        distance = self._gear.get("distance")
        if distance is not None:
            return round(distance / 1000, 1)
        return None


class IntervalsICUEquippedComponentSensor(CoordinatorEntity, SensorEntity):
    """Sensor showing the name of the equipped component of a specific type on a bike."""

    _attr_has_entity_name = True

    def __init__(self, coordinator, gear, component, comp_type, suffix, slot_index):
        super().__init__(coordinator)
        self._gear_id = gear["id"]
        self._gear_name = gear.get("name", "Unknown")
        self._gear_type = gear.get("type", "Gear")
        self._component_type = comp_type
        self._slot_index = slot_index  # Which slot (1, 2, etc.) for this type
        self._suffix = suffix
        # Unique ID based on gear, component TYPE and slot - not the actual component ID
        self._attr_unique_id = f"intervals_icu_gear_{gear['id']}_equipped_{comp_type}{suffix}"
        self._attr_icon = get_icon_for_type(self._component_type)

    @property
    def _gear(self):
        for g in self.coordinator.data or []:
            if g["id"] == self._gear_id:
                return g
        return {}

    def _get_equipped_component(self):
        """Get the equipped component at this slot."""
        gear = self._gear
        component_ids = gear.get("component_ids") or []
        # Find all components of this type equipped on this bike
        matching_comps = []
        for g in self.coordinator.data or []:
            if g["id"] in component_ids and g.get("type") == self._component_type:
                matching_comps.append(g)
        # Sort by ID for consistent slot assignment
        matching_comps.sort(key=lambda c: c.get("id", ""))
        # Return the component at this slot index (1-based)
        if self._slot_index <= len(matching_comps):
            return matching_comps[self._slot_index - 1]
        return None

    @property
    def name(self):
        return f"{self._component_type}{self._suffix}"

    @property
    def device_info(self):
        gear = self._gear
        return {
            "identifiers": {(DOMAIN, self._gear_id)},
            "name": gear.get("name", self._gear_name),
            "manufacturer": "Intervals.icu",
            "model": gear.get("type", self._gear_type),
            "entry_type": DeviceEntryType.SERVICE,
        }

    @property
    def extra_state_attributes(self):
        comp = self._get_equipped_component()
        if comp:
            return {
                "component_id": comp.get("id"),
                "component_name": comp.get("name"),
                "component_type": comp.get("type"),
            }m
        return {}

    @property
    def native_value(self):
        comp = self._get_equipped_component()
        if comp:
            return comp.get("name")
        return None


class IntervalsICUEquippedComponentMileageSensor(CoordinatorEntity, SensorEntity):
    """Sensor showing the mileage of the equipped component of a specific type on a bike."""

    _attr_device_class = SensorDeviceClass.DISTANCE
    _attr_state_class = SensorStateClass.TOTAL
    _attr_native_unit_of_measurement = UnitOfLength.KILOMETERS
    _attr_has_entity_name = True

    def __init__(self, coordinator, gear, component, comp_type, suffix, slot_index):
        super().__init__(coordinator)
        self._gear_id = gear["id"]
        self._gear_name = gear.get("name", "Unknown")
        self._gear_type = gear.get("type", "Gear")
        self._component_type = comp_type
        self._slot_index = slot_index
        self._suffix = suffix
        # Unique ID based on gear, component TYPE and slot - not the actual component ID
        self._attr_unique_id = f"intervals_icu_gear_{gear['id']}_equipped_{comp_type}{suffix}_mileage"
        self._attr_icon = get_icon_for_type(self._component_type)

    @property
    def _gear(self):
        for g in self.coordinator.data or []:
            if g["id"] == self._gear_id:
                return g
        return {}

    def _get_equipped_component(self):
        """Get the equipped component at this slot."""
        gear = self._gear
        component_ids = gear.get("component_ids") or []
        # Find all components of this type equipped on this bike
        matching_comps = []
        for g in self.coordinator.data or []:
            if g["id"] in component_ids and g.get("type") == self._component_type:
                matching_comps.append(g)
        # Sort by ID for consistent slot assignment
        matching_comps.sort(key=lambda c: c.get("id", ""))
        # Return the component at this slot index (1-based)
        if self._slot_index <= len(matching_comps):
            return matching_comps[self._slot_index - 1]
        return None

    @property
    def name(self):
        return f"{self._component_type}{self._suffix} Mileage"

    @property
    def device_info(self):
        gear = self._gear
        return {
            "identifiers": {(DOMAIN, self._gear_id)},
            "name": gear.get("name", self._gear_name),
            "manufacturer": "Intervals.icu",
            "model": gear.get("type", self._gear_type),
            "entry_type": DeviceEntryType.SERVICE,
        }

    @property
    def extra_state_attributes(self):
        comp = self._get_equipped_component()
        if comp:
            return {
                "component_id": comp.get("id"),
                "component_name": comp.get("name"),
                "component_type": comp.get("type"),
                "activities": comp.get("activities"),
                "time_seconds": comp.get("time"),
            }
        return {}

    @property
    def native_value(self):
        comp = self._get_equipped_component()
        if comp:
            distance = comp.get("distance")
            if distance is not None:
                return round(distance / 1000, 1)
        return None


class IntervalsICUComponentSensor(CoordinatorEntity, SensorEntity):
    """Mileage sensor for components (chains, tyres, cassettes, etc.)."""

    _attr_device_class = SensorDeviceClass.DISTANCE
    _attr_state_class = SensorStateClass.TOTAL
    _attr_native_unit_of_measurement = UnitOfLength.KILOMETERS
    _attr_has_entity_name = True

    def __init__(self, coordinator, comp):
        super().__init__(coordinator)
        self._comp_id = comp["id"]
        self._comp_type = comp.get("type", "Component")
        self._comp_name = comp.get("name", "Unknown")
        self._attr_unique_id = f"intervals_icu_component_{comp['id']}_mileage"
        self._attr_icon = get_icon_for_type(self._comp_type)

    @property
    def _comp(self):
        for g in self.coordinator.data or []:
            if g["id"] == self._comp_id:
                return g
        return {}

    def _get_equipped_on(self):
        """Find which gear this component is currently equipped on."""
        for g in self.coordinator.data or []:
            if not g.get("component", False):
                component_ids = g.get("component_ids") or []
                if self._comp_id in component_ids:
                    return {"id": g["id"], "name": g.get("name"), "type": g.get("type")}
        return None

    @property
    def name(self):
        return "Mileage"

    @property
    def device_info(self):
        comp = self._comp
        return {
            "identifiers": {(DOMAIN, self._comp_id)},
            "name": comp.get("name", self._comp_name),
            "manufacturer": "Intervals.icu",
            "model": comp.get("type", self._comp_type),
            "entry_type": DeviceEntryType.SERVICE,
        }

    @property
    def extra_state_attributes(self):
        comp = self._comp
        equipped_on = self._get_equipped_on()
        return {
            "gear_id": comp.get("id"),
            "component_type": comp.get("type"),
            "activities": comp.get("activities"),
            "time_seconds": comp.get("time"),
            "equipped_on_id": equipped_on["id"] if equipped_on else None,
            "equipped_on_name": equipped_on["name"] if equipped_on else None,
            "equipped_on_type": equipped_on["type"] if equipped_on else None,
        }

    @property
    def native_value(self):
        distance = self._comp.get("distance")
        if distance is not None:
            return round(distance / 1000, 1)
        return None
