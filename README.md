# Intervals.icu Gear Home Assistant Integration

<p align="center">
  <img src="custom_components/intervals_icu_gear/icons/icon.svg" alt="Intervals.icu Gear Logo" width="120" height="120">
</p>

This custom integration allows you to view and manage your Intervals.icu bikes and their components directly from Home Assistant. It supports HACS installation and provides a service to equip components to bikes, including exclusivity logic.

## Features
- Lists all bikes from Intervals.icu as Home Assistant devices
- Lists all components as sensor entities, showing their mileage
- Shows equipped components on each bike with their mileage
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

## Entities

For each **bike** (or main gear), the integration creates:
- **Mileage sensor** - Total distance in kilometers
- **Equipped component sensors** - One for each component type showing the name of the equipped component
- **Equipped component mileage sensors** - Mileage of each equipped component

For each **component** (chain, cassette, tyre, etc.):
- **Mileage sensor** - Total distance on the component, with attributes showing which bike it's equipped on

## Services
### `intervals_icu_gear.equip_component`
Equip a component to a bike. You can call this from automations, scripts, or the UI.

**Fields:**
- `bike_device_id`: The bike device to attach the component to
- `component_device_id`: The component device to attach (e.g., chain, tyre, cassette)
- `exclusive`: (optional, default `false`) If true, removes other components of the same type before attaching

**Example service call:**
```yaml
service: intervals_icu_gear.equip_component
data:
  bike_device_id: "abc123..."  # Device ID from Home Assistant
  component_device_id: "def456..."  # Device ID from Home Assistant
  exclusive: true
```

> **Tip:** In the Home Assistant UI, you can use the device picker to select your bike and component directly by name.

## Issues & Feedback
Please open issues or feature requests on [GitHub](https://github.com/jowlo/ha-intervals-icu-gear`).
