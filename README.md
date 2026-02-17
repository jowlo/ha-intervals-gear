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

## Example Lovelace Card

Here's an example dashboard card with gauges for chain and cassette wear, assuming a bike named 'dengfu':

```yaml
type: vertical-stack
cards:
  # Header with bike name and total mileage
  - type: entities
    title: Dengfu
    entities:
      - entity: sensor.dengfu_mileage
        name: Total Mileage
        icon: mdi:bike

  # Gauges for chain and cassette wear
  - type: horizontal-stack
    cards:
      - type: gauge
        entity: sensor.dengfu_chain_mileage
        name: Chain Wear
        unit: km
        min: 0
        max: 500
        severity:
          green: 0
          yellow: 350
          red: 450
        needle: true

      - type: gauge
        entity: sensor.dengfu_cassette_mileage
        name: Cassette Wear
        unit: km
        min: 0
        max: 10000
        severity:
          green: 0
          yellow: 7000
          red: 9000
        needle: true

  # Component details
  - type: entities
    title: Equipped Components
    entities:
      - entity: sensor.dengfu_chain
        name: Chain
        icon: mdi:link-variant
      - entity: sensor.dengfu_chain_mileage
        name: Chain Mileage
        icon: mdi:counter

      - entity: sensor.dengfu_cassette
        name: Cassette
        icon: mdi:cog
      - entity: sensor.dengfu_cassette_mileage
        name: Cassette Mileage
        icon: mdi:counter

      # Tyres are numbered when multiple exist
      - entity: sensor.dengfu_tyre_1
        name: Tyre 1
        icon: mdi:tire
      - entity: sensor.dengfu_tyre_1_mileage
        name: Tyre 1 Mileage
        icon: mdi:counter

      - entity: sensor.dengfu_tyre_2
        name: Tyre 2
        icon: mdi:tire
      - entity: sensor.dengfu_tyre_2_mileage
        name: Tyre 2 Mileage
        icon: mdi:counter
```

## Issues & Feedback
Please open issues or feature requests on [GitHub](https://github.com/jowlo/ha-intervals-icu-gear`).
