# Intervals.icu Gear Home Assistant Integration

[![Add to Home Assistant](https://my.home-assistant.io/badges/custom_integrations.svg)](https://my.home-assistant.io/redirect/custom_integrations/)

This custom integration allows you to view and manage your Intervals.icu bikes and their components directly from Home Assistant. It supports HACS installation and provides a service to equip components to bikes, including exclusivity logic.

## Features
- Lists all bikes from Intervals.icu as Home Assistant devices
- Lists all components as sensor entities, showing their mileage
- Periodically updates gear data
- Service to equip a component to a bike, with optional exclusivity
- HACS compatible

## Installation
### HACS (Recommended)
1. Go to **HACS > Integrations** in Home Assistant.
2. Click the three dots (⋮) in the top right and select **Custom repositories**.
3. Add your repository URL: `https://github.com/jowlo/ha-intervals-icu-gear` and select **Integration**.
4. Search for "Intervals.icu Gear" and install.
5. Restart Home Assistant.

### Manual
1. Copy the `custom_components/intervals_icu_gear` folder to your Home Assistant `custom_components` directory.
2. Restart Home Assistant.

## Configuration
1. Go to **Settings > Devices & Services**.
2. Click **Add Integration** and search for "Intervals.icu Gear".
3. Enter your Intervals.icu API key and athlete ID.

## Services
### `intervals_icu_gear.equip_component`
Equip a component to a bike. You can call this from automations, scripts, or the UI.

**Fields:**
- `bike_entity_id`: Entity ID of the bike (e.g., `sensor.my_bike_mileage`)
- `component_entity_id`: Entity ID of the component (e.g., `sensor.my_chain_mileage`)
- `exclusive`: (optional, default `false`) If true, removes other components of the same type before attaching

**Example service call:**
```yaml
service: intervals_icu_gear.equip_component
data:
  bike_entity_id: sensor.my_bike_mileage
  component_entity_id: sensor.my_chain_mileage
  exclusive: true
```

## Add to Home Assistant Button
[![Add to Home Assistant](https://my.home-assistant.io/badges/custom_integrations.svg)](https://my.home-assistant.io/redirect/custom_integrations/)

## Issues & Feedback
Please open issues or feature requests on [GitHub](https://github.com/jowlo/ha-intervals-icu-gear).

