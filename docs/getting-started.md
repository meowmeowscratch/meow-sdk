# Getting Started

This guide walks you through installing the SDK, creating an app, and sending your first data — all in about 5 minutes.

---

## 1. Install the SDK

```
pip install meow-sdk
```

This also installs the `meow` CLI tool.

---

## 2. Get your API key

Sign up at [meowmeowscratch.com](https://meowmeowscratch.com), then go to **Account > Platform Tokens** and create a token. Copy the key — it starts with `mms_`.

!!! warning "Save your key"
    The full key is only shown once. If you lose it, revoke it and create a new one.

---

## 3. Create a client

```python
from meow_sdk import Meow

api = Meow(api_key="mms_your_key_here")
```

The client has three optional parameters:

| Parameter | What it does | When you need it |
|-----------|-------------|------------------|
| `api_key` | Authenticates your requests | Writing data, managing apps, reading private endpoints |
| `username` | Sets the username for public reads | Reading someone's public endpoints |
| `base_url` | Override the API URL (default: `https://meowmeowscratch.com`) | Local development, self-hosted instances |

```python
# Read-only (public endpoints)
api = Meow(username="jake")

# Read + write
api = Meow(username="jake", api_key="mms_your_key_here")

# Local development
api = Meow("http://localhost:8099", api_key="mms_your_key_here")
```

---

## 4. Create an app and endpoint

Apps are containers for your endpoints. Endpoints hold your data.

```python
# Create an app
api.create_app("Weather Station", "weather-station")

# Add a collection endpoint for sensor readings
api.create_endpoint("weather-station", "Readings", "readings")

# Define the schema
api.create_field("weather-station", "readings",
    "temperature", "Temperature", "number")
api.create_field("weather-station", "readings",
    "humidity", "Humidity", "number")
```

!!! tip
    You can also create apps and endpoints from the [web dashboard](https://meowmeowscratch.com) — the SDK and website are interchangeable.

---

## 5. Send data

```python
result = api.send("weather-station", "readings", {
    "temperature": 22.5,
    "humidity": 65,
})

print(result["uuid"])  # unique ID for this record
```

---

## 6. Read it back

=== "With API key (your own data)"

    ```python
    page = api.records("weather-station", "readings")
    print(page["count"])    # total records
    print(page["results"])  # this page of records
    ```

=== "Public read (anyone)"

    ```python
    api = Meow(username="jake")
    data = api.get("weather-station", "readings")
    ```

Your public API lives at:

```
https://meowmeowscratch.com/api/v1/jake/weather-station/readings/
```

Anyone can read this URL — from a browser, curl, another Raspberry Pi, or a phone app.

---

## 7. Try the CLI

Set your credentials once:

```bash
export MEOW_API_KEY=mms_your_key_here
export MEOW_USERNAME=jake
```

Then use the `meow` command:

```bash
# Send data
meow send weather-station readings temperature=22.5 humidity=65

# Read it back
meow get weather-station readings

# List your apps
meow apps

# See all commands
meow --help
```

---

## Three types of endpoints

| Type | What it's for | Example |
|------|--------------|---------|
| **collection** | Time-series data — each `send()` adds a new record | Sensor readings, form submissions, event logs |
| **static** | A single JSON blob — `set_payload()` replaces it | Device status, config, feature flags |
| **proxy** | Wraps an external API — meow caches and transforms it | Weather API, stock prices, any third-party data |

```python
# Collection — stores many records
api.create_endpoint("my-app", "Readings", "readings", "collection")
api.send("my-app", "readings", {"temp": 22.5})

# Static — one payload, overwritten each time
api.create_endpoint("my-app", "Status", "status", "static")
api.set_payload("my-app", "status", {"online": True, "version": "1.2"})

# Proxy — wraps an external URL
api.create_endpoint("my-app", "Weather", "weather", "proxy")
api.set_proxy("my-app", "weather", "https://api.weather.com/v1/current")
```

---

## What's next

- **[Raspberry Pi](raspberry-pi.md)** — connect real sensors and hardware
- **[Dashboards](dashboards.md)** — build control panels with toggles, sliders, and live displays
- **[API Reference](api-reference.md)** — every SDK method
- **[CLI Reference](cli.md)** — every terminal command
- **[Error Handling](errors.md)** — catch and handle API errors
