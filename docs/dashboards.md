# Dashboards

Dashboards turn endpoint values into web and mobile controls. A widget binds to
an app slug, endpoint slug, and dot-separated key path. Endpoint UUIDs are an
internal implementation detail and are not needed.

## Choose the endpoint type

- **Static endpoints** support interactive controls and read-only displays.
- **Collection endpoints** support displays from the latest record.
- **Proxy endpoints** do not support widgets.

Static endpoints are the best fit for remote device configuration. A dashboard
updates the settings document, while a Raspberry Pi reads the same document
with an app API key.

```text
dashboard slider -> static settings endpoint <- Raspberry Pi polls
```

## Create settings and a dashboard

```python
from meow_sdk import Meow

api = Meow(api_key="YOUR_PLATFORM_TOKEN")

api.create_app("Home", "home")
api.create_endpoint("home", "Settings", "settings", endpoint_type="static")
api.set_payload("home", "settings", {
    "lights": {"on": False, "brightness": 50},
    "camera": {"thresholds": {"confidence": 0.65}},
})

api.create_dashboard("Home Controls", "home-controls")
```

Resources are private unless `is_public=True` is deliberately supplied.

## Add widgets

```python
light = api.create_dashboard_widget(
    "home-controls",
    "home",
    "settings",
    "lights.on",
    "toggle",
    "Lights",
)

confidence = api.create_dashboard_widget(
    "home-controls",
    "home",
    "settings",
    "camera.thresholds.confidence",
    "slider",
    "Tracking confidence",
    config={"min": 0, "max": 1, "step": 0.05},
)
```

A key path uses dot notation. Literal periods in JSON key names are unsupported.
Static writes create missing dictionaries, but never replace a non-object
intermediate value silently.

## Widget configuration

| Type | Configuration |
|---|---|
| `toggle` | none |
| `color` | none |
| `slider` | `min`, `max`, and positive `step` |
| `number` | optional `min`, `max`, and positive `step` |
| `text` | optional `placeholder` and positive `max_length` |
| `select` | `choices: [{"value": "...", "label": "..."}]` |
| `display` | optional `prefix` and `suffix` |

Unknown keys are rejected. Slider bounds belong inside `config`; passing
top-level `min`, `max`, or `step` returns a validation error.

## Read state

```python
state = api.dashboard_state("home-controls")

for widget in state["widgets"]:
    binding = widget["binding"]
    current = widget["state"]
    print(binding["key_path"], current["has_value"], current["value"])
```

The state response returns only configured widget values. It does not expose
endpoint UUIDs or unbound sibling keys.

## Change a value

```python
api.set_dashboard_widget_value("home-controls", light["uuid"], True)
api.set_dashboard_widget_value("home-controls", confidence["uuid"], 0.7)
```

The widget already owns its endpoint and key-path binding, so a write needs only
the dashboard slug, widget UUID, and new value. The API validates the value
against the widget type and configuration.

## Raspberry Pi runtime

Use a platform token for provisioning. Give the deployed device an app API key
limited to `home`.

```python
import os
import time
from meow_sdk import Meow

device = Meow(api_key=os.environ["MEOW_APP_API_KEY"])

while True:
    settings = device.get_payload("home", "settings")
    confidence = settings["camera"]["thresholds"]["confidence"]
    apply_confidence_threshold(confidence)
    time.sleep(60)
```

`get_payload()` returns the bare JSON document. Use `get_payload_state()` when
you also need `updated_at`.

## Public dashboards

Public sharing is read-only. Anyone holding the share token can read the
configured widget state, but cannot use the authenticated widget-value route.

```python
shared = Meow().public_dashboard("share-token")
```

## CLI

```bash
meow dashboard-create "Home Controls" home-controls
meow widget-create home-controls home settings lights.on toggle "Lights"
meow widget-create home-controls home settings camera.thresholds.confidence \
  slider "Tracking confidence" --config '{"min":0,"max":1,"step":0.05}'
meow dashboard-data home-controls
meow widget-set home-controls WIDGET_UUID true
```

## Method reference

| Method | Description |
|---|---|
| `api.dashboards()` | List dashboards |
| `api.get_dashboard(slug)` | Get dashboard details and capacity |
| `api.create_dashboard(name, slug, description="")` | Create a dashboard |
| `api.update_dashboard(slug, **kwargs)` | Update a dashboard |
| `api.delete_dashboard(slug)` | Delete a dashboard |
| `api.dashboard_widgets(dashboard)` | List widgets through the compatibility route |
| `api.create_dashboard_widget(dashboard, app, endpoint, key_path, widget_type, label, config=None, sort_order=0)` | Add a slug-bound widget |
| `api.update_dashboard_widget(dashboard, widget_uuid, **kwargs)` | Update widget presentation or key path |
| `api.delete_dashboard_widget(dashboard, widget_uuid)` | Remove a widget |
| `api.dashboard_state(dashboard)` | Read configured values |
| `api.set_dashboard_widget_value(dashboard, widget_uuid, value)` | Write through an interactive widget |
| `api.public_dashboard(share_token)` | Read a shared dashboard |
