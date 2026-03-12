# Dashboards

Dashboards are interactive control panels that let you read and write data through widgets. Each widget connects to a key in one of your endpoints — toggle a light, slide a temperature, pick a color, all from the web or your phone.

---

## Overview

A dashboard can pull widgets from **multiple endpoints across different apps**. This lets you build a single control panel for your whole setup — bedroom lights, kitchen temperature, garage door — all in one place.

```
Dashboard: "My Room"
├── Toggle widget   → bedroom-lights endpoint → "lights_on" key
├── Slider widget   → thermostat endpoint     → "target_temp" key
├── Color widget    → led-strip endpoint      → "color" key
└── Display widget  → sensors endpoint        → "temperature" key
```

---

## Create a dashboard

```python
from meow_sdk import Meow

api = Meow(api_key="mms_your_key_here")

api.create_dashboard("My Room", "my-room", description="Bedroom controls")
```

---

## Add widgets

Each widget needs:

- **endpoint_id** — the UUID of the endpoint it reads/writes
- **key_path** — which key in the endpoint's data to bind to
- **widget_type** — how to display and interact with the value
- **label** — what the user sees

```python
# On/off toggle for a light
api.create_dashboard_widget(
    "my-room", "endpoint-uuid",
    "lights_on", "toggle", "Bedroom Lights"
)

# Temperature slider with min/max
api.create_dashboard_widget(
    "my-room", "endpoint-uuid",
    "target_temp", "slider", "Temperature",
    config={"min": 15, "max": 30}
)

# Color picker for an LED strip
api.create_dashboard_widget(
    "my-room", "endpoint-uuid",
    "color", "color", "LED Color"
)

# Read-only display
api.create_dashboard_widget(
    "my-room", "endpoint-uuid",
    "temperature", "display", "Current Temp"
)
```

### Widget types

| Type | Interaction | Best for |
|------|------------|---------|
| `toggle` | On/off switch | Lights, motors, relays |
| `slider` | Drag to set a number | Temperature, brightness, volume |
| `number` | Type a number | Precise values, thresholds |
| `text` | Type text | Names, messages, labels |
| `color` | Color picker | RGB LEDs, themes |
| `select` | Dropdown menu | Modes, presets, options |
| `display` | Read-only value | Sensor readings, status |

---

## Read data

Get current values for all widgets at once:

```python
data = api.dashboard_data("my-room")

# Dashboard info
print(data["dashboard"]["name"])

# All widgets and their current values
for widget in data["widgets"]:
    print(f"{widget['label']}: {widget.get('current_value')}")

# Raw endpoint data
print(data["endpoints"])
```

---

## Update values

Write a single value through a widget:

```python
# Turn on the lights
api.dashboard_patch("my-room", "endpoint-uuid", "lights_on", True)

# Set temperature to 22
api.dashboard_patch("my-room", "endpoint-uuid", "target_temp", 22)

# Change LED color
api.dashboard_patch("my-room", "endpoint-uuid", "color", "#ff6600")
```

---

## Raspberry Pi example

A Pi that reads its dashboard and controls GPIO pins:

```python
import time
import RPi.GPIO as GPIO
from meow_sdk import Meow

GPIO.setmode(GPIO.BCM)
GPIO.setup(17, GPIO.OUT)  # LED on pin 17

api = Meow(api_key="mms_your_key_here")

while True:
    data = api.dashboard_data("my-room")

    for widget in data["widgets"]:
        if widget["key_path"] == "lights_on":
            GPIO.output(17, widget.get("current_value", False))

    time.sleep(2)
```

---

## Public dashboards

Share a read-only view of your dashboard with a public link:

```python
# Anyone with the share token can view (no API key needed)
data = api.public_dashboard("share-token-abc")
print(data["dashboard"]["name"])
print(data["widgets"])
```

---

## CLI

```bash
# Create and manage
meow dashboard-create "My Room" my-room
meow dashboards
meow dashboard-get my-room

# Add widgets
meow widget-create my-room endpoint-uuid lights_on toggle "Bedroom Lights"

# Read and write
meow dashboard-data my-room
meow dashboard-patch my-room endpoint-uuid lights_on true

# Public view
meow public-dashboard share-token-abc
```

---

## Full API

| Method | Description |
|--------|-------------|
| `api.dashboards()` | List dashboards |
| `api.get_dashboard(slug)` | Get dashboard details |
| `api.create_dashboard(name, slug, description="")` | Create a dashboard |
| `api.update_dashboard(slug, **kwargs)` | Update a dashboard |
| `api.delete_dashboard(slug)` | Delete a dashboard |
| `api.dashboard_widgets(dashboard)` | List widgets |
| `api.create_dashboard_widget(dashboard, endpoint_id, key_path, widget_type, label, **kwargs)` | Add a widget |
| `api.update_dashboard_widget(dashboard, widget_uuid, **kwargs)` | Update a widget |
| `api.delete_dashboard_widget(dashboard, widget_uuid)` | Remove a widget |
| `api.dashboard_data(dashboard)` | Read all widget values |
| `api.dashboard_patch(dashboard, endpoint_uuid, key_path, value)` | Write a value |
| `api.public_dashboard(share_token)` | Read a public dashboard |
