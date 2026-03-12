<p align="center">
  <img src="https://meowmeowscratch.com/meowmeowscratch-text.svg" alt="meow meow scratch" width="300" />
</p>

<h3 align="center">Python SDK for the meow meow scratch API</h3>

<p align="center">
  Build your own APIs and send data from your Raspberry Pi, Arduino, or any Python project.
</p>

<p align="center">
  <a href="https://pypi.org/project/meow-sdk/"><img src="https://img.shields.io/pypi/v/meow-sdk?color=black&label=pypi" alt="PyPI"></a>
  <a href="https://pypi.org/project/meow-sdk/"><img src="https://img.shields.io/pypi/pyversions/meow-sdk?color=black" alt="Python"></a>
  <a href="https://github.com/meowmeowscratch/meow-sdk/blob/main/LICENSE"><img src="https://img.shields.io/github/license/meowmeowscratch/meow-sdk?color=black" alt="License"></a>
</p>

<p align="center">
  <a href="https://meow-sdk.readthedocs.io">Docs</a> &middot;
  <a href="https://meow-sdk.readthedocs.io/getting-started/">Getting Started</a> &middot;
  <a href="https://meow-sdk.readthedocs.io/api-reference/">API Reference</a> &middot;
  <a href="https://meow-sdk.readthedocs.io/cli/">CLI Reference</a>
</p>

---

## Install

```
pip install meow-sdk
```

## 30-second quickstart

```python
from meow_sdk import Meow

# 1. Connect with your API key
api = Meow(api_key="mms_your_key_here")

# 2. Send data
api.send("weather-station", "readings", {
    "temperature": 22.5,
    "humidity": 65,
})

# 3. Read it back
data = api.records("weather-station", "readings")
print(data["results"])
```

> Get your API key at [meowmeowscratch.com](https://meowmeowscratch.com) under Account > Platform Tokens.

## Read public data (no key needed)

Anyone can read public endpoints using a username:

```python
api = Meow(username="jake")

data = api.get("weather-station", "readings")
print(data)
```

Your public API lives at: `https://meowmeowscratch.com/api/v1/<username>/<app>/<endpoint>/`

## Raspberry Pi

Read a sensor and send data every 10 seconds:

```python
import time
import adafruit_dht
import board
from meow_sdk import Meow

sensor = adafruit_dht.DHT22(board.D4)
api = Meow(api_key="mms_your_key_here")

while True:
    try:
        api.send("my-pi", "sensors", {
            "temperature": sensor.temperature,
            "humidity": sensor.humidity,
        })
        print(f"{sensor.temperature}°C, {sensor.humidity}%")
    except Exception as e:
        print(f"Sensor error: {e}")

    time.sleep(10)
```

See the [Raspberry Pi guide](https://meow-sdk.readthedocs.io/raspberry-pi/) for more examples (buttons, LEDs, camera, systemd).

## Control panels

Build real-time dashboards with interactive widgets:

```python
api = Meow(api_key="mms_your_key_here")

# Create a dashboard
api.create_dashboard("My Room", "my-room")

# Add a light switch
api.create_dashboard_widget(
    "my-room", "endpoint-uuid",
    "lights_on", "toggle", "Bedroom Lights"
)

# Toggle it from your Pi
api.dashboard_patch("my-room", "endpoint-uuid", "lights_on", True)
```

Widget types: `toggle`, `slider`, `color`, `number`, `text`, `select`, `display`.

## CLI

The SDK includes a full CLI. Configure it once:

```bash
export MEOW_API_KEY=mms_your_key_here
export MEOW_USERNAME=jake
```

Then use it:

```bash
# Send data
meow send weather-station readings temperature=22.5 humidity=65

# Read data
meow get weather-station readings

# List your apps
meow apps

# Export as CSV
meow csv weather-station readings

# Manage dashboards
meow dashboards
meow dashboard-data my-room
meow dashboard-patch my-room endpoint-uuid lights_on true
```

See the [CLI reference](https://meow-sdk.readthedocs.io/cli/) for all 40+ commands.

## Error handling

```python
from meow_sdk import Meow, AuthError, NotFoundError, MeowError

api = Meow(api_key="mms_your_key_here")

try:
    api.send("my-app", "readings", {"value": 42})
except AuthError:
    print("Bad API key")
except NotFoundError:
    print("App or endpoint doesn't exist")
except MeowError as e:
    print(f"API error {e.status_code}: {e}")
```

## What you can do

| Feature | SDK | CLI |
|---------|-----|-----|
| Send & read records | `api.send()` | `meow send` |
| Manage apps & endpoints | `api.create_app()` | `meow create-app` |
| Define field schemas | `api.create_field()` | `meow create-field` |
| Static payloads | `api.set_payload()` | `meow payload-set` |
| Proxy endpoints | `api.set_proxy()` | `meow proxy-set` |
| Control panel dashboards | `api.dashboard_patch()` | `meow dashboard-patch` |
| Webhooks | `api.create_webhook()` | `meow webhook-create` |
| Encryption | `api.enable_encryption()` | `meow encrypt-enable` |
| Request logs | `api.request_logs()` | `meow logs` |
| CSV export | `api.export_csv()` | `meow csv` |
| Aggregations | `api.aggregate()` | `meow aggregate` |
| API keys | `api.create_app_key()` | `meow key-create` |
| Platform tokens | `api.create_platform_token()` | `meow platform-token-create` |
| Billing | `api.billing_status()` | `meow billing-status` |

## Links

- [Full documentation](https://meow-sdk.readthedocs.io)
- [API reference](https://meow-sdk.readthedocs.io/api-reference/)
- [CLI reference](https://meow-sdk.readthedocs.io/cli/)
- [Raspberry Pi guide](https://meow-sdk.readthedocs.io/raspberry-pi/)
- [GitHub](https://github.com/meowmeowscratch/meow-sdk)
- [PyPI](https://pypi.org/project/meow-sdk/)

## License

MIT
