# Intervals.icu Gear Home Assistant Integration

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.typing import ConfigType
import voluptuous as vol
from homeassistant.helpers import config_validation as cv, device_registry as dr
from .const import CONF_API_KEY, CONF_ATHLETE_ID, DOMAIN
from .api import IntervalsICUClient
import logging

_LOGGER = logging.getLogger(__name__)

EQUIP_SERVICE = "equip_component"

EQUIP_SCHEMA = vol.Schema({
    vol.Required("bike_device_id"): cv.string,
    vol.Required("component_device_id"): cv.string,
    vol.Optional("exclusive", default=False): bool,
})

async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    return True

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    # Initialize hass.data for this domain
    hass.data.setdefault(DOMAIN, {})

    await hass.config_entries.async_forward_entry_setups(entry, ["sensor"])

    async def async_equip_component_service(call):
        api_key = entry.data[CONF_API_KEY]
        athlete_id = entry.data[CONF_ATHLETE_ID]

        bike_device_id = call.data["bike_device_id"]
        component_device_id = call.data["component_device_id"]
        exclusive = call.data.get("exclusive", False)

        # Get device registry to resolve device IDs to gear IDs
        device_reg = dr.async_get(hass)

        bike_device = device_reg.async_get(bike_device_id)
        comp_device = device_reg.async_get(component_device_id)

        if not bike_device or not comp_device:
            raise ValueError("Bike or component device not found")

        # Extract gear_id from device identifiers
        # Identifiers are stored as {(DOMAIN, gear_id)}
        bike_gear_id = None
        comp_gear_id = None

        for domain, identifier in bike_device.identifiers:
            if domain == DOMAIN:
                bike_gear_id = identifier
                break

        for domain, identifier in comp_device.identifiers:
            if domain == DOMAIN:
                comp_gear_id = identifier
                break

        if not bike_gear_id or not comp_gear_id:
            raise ValueError("Could not resolve gear IDs from device identifiers")

        client = IntervalsICUClient(api_key, athlete_id)
        # 1. Fetch all gear
        gear_list = await client.async_get_gear()
        # 2. Find bike and component by id
        gear_by_id = {g["id"]: g for g in gear_list}
        bike = gear_by_id.get(bike_gear_id)
        component = gear_by_id.get(comp_gear_id)
        if not bike or not component:
            raise ValueError("Bike or component not found in Intervals.icu gear list")
        bike_id = bike["id"]
        existing_component_ids = bike.get("component_ids") or []
        component_id = component["id"]
        component_type = component.get("type")
        # 4. Build new component_ids
        new_component_ids = list(existing_component_ids)
        if exclusive:
            filtered = []
            for cid in new_component_ids:
                g = gear_by_id.get(cid)
                if not g or g.get("type") != component_type:
                    filtered.append(cid)
            new_component_ids = filtered
        if component_id not in new_component_ids:
            new_component_ids.append(component_id)
        # 5. PUT update
        await client.async_update_bike_components(bike_id, new_component_ids)

        # 6. Refresh coordinator data to update all entities
        coordinator = hass.data[DOMAIN].get("coordinator")
        if coordinator:
            _LOGGER.info("Refreshing coordinator data after equipping component")
            await coordinator.async_refresh()
            _LOGGER.info("Coordinator refresh complete")

        # Fire event
        hass.bus.async_fire(f"{DOMAIN}_component_equipped", {
            "bike_id": bike_id,
            "component_ids": new_component_ids,
            "status": "updated",
        })

    hass.services.async_register(
        DOMAIN, EQUIP_SERVICE, async_equip_component_service, schema=EQUIP_SCHEMA
    )
    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    hass.data.pop(DOMAIN, None)
    return await hass.config_entries.async_unload_platforms(entry, ["sensor"])
