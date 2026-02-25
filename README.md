# meow-sdk

Python client for the [meow meow scratch](https://meowmeowscratch.com) API. Build your own APIs and send data from your Raspberry Pi!

## Install

```
pip install meow-sdk
```

## Quick start

### Send data to your API

```python
from meow_sdk import Meow

api = Meow(api_key="your-key")

api.send("my-weather-app", "readings", {
    "temperature": 22.5,
    "humidity": 65,
})
```

### Read data from a public endpoint

```python
from meow_sdk import Meow

api = Meow(username="jake")

data = api.get("my-weather-app", "current-temp")
print(data)
```

Your public API URL is: `/api/v1/<username>/<app>/<endpoint>/`

## Raspberry Pi example

Read a sensor and send the value to your API every 10 seconds:

```python
import time
from meow_sdk import Meow

api = Meow(api_key="your-key")

while True:
    # Replace this with your real sensor code!
    temperature = 22.5

    api.send("my-pi-app", "sensor-data", {
        "temperature": temperature,
    })

    print(f"Sent {temperature}°C")
    time.sleep(10)
```

## API reference

### `Meow(base_url="https://meowmeowscratch.com", username=None, api_key=None)`

Create a client.

- `base_url` — where the API lives. Defaults to `"https://meowmeowscratch.com"`. Override for local dev or self-hosted instances.
- `username` — needed for reading public endpoints (it's part of the URL).
- `api_key` — needed for writing data, managing apps, and reading private endpoints.

```python
# Public reads only
api = Meow(username="jake")

# With an API key for writing/managing + reading private endpoints
api = Meow(api_key="your-key")

# Both — read public endpoints and write data
api = Meow(username="jake", api_key="your-key")

# Local development
api = Meow("http://localhost:8099", api_key="your-key")
```

---

### Reading data

**Public endpoints** — no API key needed, requires `username`:

```python
api = Meow(username="jake")
data = api.get("weather-app", "current-temp")
```

**Private endpoints** — requires an API key. Use `records()` to read your own private endpoint data:

```python
api = Meow(api_key="your-key")
data = api.records("my-app", "secret-data")
```

| Method | Description |
|--------|-------------|
| `api.get(app, endpoint)` | Read data from a public endpoint (requires `username`) |
| `api.get_record(app, endpoint, record_id)` | Read a single public record by ID (requires `username`) |
| `api.records(app, endpoint)` | List records with your API key (works for private and public) |

```python
data = api.get("weather-app", "current-temp")

record = api.get_record("weather-app", "readings", "abc-123")
```

---

### Sending and managing records

API key required.

| Method | Description |
|--------|-------------|
| `api.send(app, endpoint, data)` | Send a new record |
| `api.update(app, endpoint, record_id, data)` | Update an existing record |
| `api.delete_record(app, endpoint, record_id)` | Delete a record |
| `api.records(app, endpoint, limit=25, offset=0)` | List records (paginated) |
| `api.all_records(app, endpoint)` | Fetch every record (auto-paginates) |

```python
# Send a record
result = api.send("weather-app", "readings", {"temperature": 22.5})
print(result["uuid"])  # new record ID

# Update it
api.update("weather-app", "readings", "abc-123", {"temperature": 23.0})

# List records
page = api.records("weather-app", "readings", limit=10)
print(page["count"])   # total records
print(page["results"]) # this page

# Or get them all at once
everything = api.all_records("weather-app", "readings")
```

---

### Managing apps

API key required.

| Method | Description |
|--------|-------------|
| `api.apps()` | List your apps |
| `api.get_app(slug)` | Get details for a single app |
| `api.create_app(name, slug, description="", is_public=True)` | Create a new app |
| `api.update_app(slug, **kwargs)` | Update an app (pass only fields to change) |
| `api.delete_app(slug)` | Delete an app |

```python
# List all apps
my_apps = api.apps()

# Get one app's details
app = api.get_app("weather-app")
print(app["endpoint_count"])

# Create apps
api.create_app("Weather App", "weather-app")
api.create_app("Secret App", "secret-app", is_public=False)

# Update an app
api.update_app("weather-app", name="My Weather App", description="Updated!")

# Delete an app
api.delete_app("old-app")
```

---

### Managing endpoints

API key required. Endpoint types: `"collection"`, `"static"`, `"proxy"`.

| Method | Description |
|--------|-------------|
| `api.endpoints(app)` | List endpoints in an app |
| `api.get_endpoint(app, endpoint)` | Get details for a single endpoint |
| `api.create_endpoint(app, name, slug, endpoint_type="collection", ...)` | Create an endpoint |
| `api.update_endpoint(app, endpoint, **kwargs)` | Update an endpoint |
| `api.delete_endpoint(app, endpoint)` | Delete an endpoint |

```python
# List endpoints
eps = api.endpoints("weather-app")

# Get endpoint details (includes field schema, record count, etc.)
ep = api.get_endpoint("weather-app", "readings")
print(ep["record_count"])

# Create endpoints
api.create_endpoint("weather-app", "Readings", "readings")
api.create_endpoint("weather-app", "Status", "status", endpoint_type="static")

# Update an endpoint
api.update_endpoint("weather-app", "readings", name="Sensor Readings")

# Delete an endpoint
api.delete_endpoint("weather-app", "old-endpoint")
```

---

### Managing fields (collection schema)

API key required. Define the schema for a collection endpoint.

Field types: `text`, `textarea`, `number`, `boolean`, `date`, `datetime`, `time`, `color`, `email`, `url`, `select`, `rating`, `image_url`, `json`.

| Method | Description |
|--------|-------------|
| `api.fields(app, endpoint)` | List fields for a collection endpoint |
| `api.create_field(app, endpoint, name, label, field_type, **kwargs)` | Create a new field |
| `api.update_field(app, endpoint, field_uuid, **kwargs)` | Update a field |
| `api.delete_field(app, endpoint, field_uuid)` | Delete a field |

```python
# List fields
schema = api.fields("weather-app", "readings")

# Create fields
api.create_field("weather-app", "readings", "temperature", "Temperature", "number")
api.create_field("weather-app", "readings", "location", "Location", "text",
                 required=True, help_text="Where the reading was taken")
api.create_field("weather-app", "readings", "color", "LED Color", "color",
                 options={"format": "hex"})

# Update a field
api.update_field("weather-app", "readings", "field-uuid-123", label="Temp (°C)")

# Delete a field
api.delete_field("weather-app", "readings", "field-uuid-123")
```

Optional `create_field` keyword arguments: `required`, `default_value`, `options`, `help_text`, `sort_order`.

---

### Static payloads

API key required. For endpoints with type `"static"`.

| Method | Description |
|--------|-------------|
| `api.get_payload(app, endpoint)` | Get the static payload |
| `api.set_payload(app, endpoint, data)` | Set the static payload |

```python
api.set_payload("weather-app", "status", {"open": True, "message": "All good!"})
payload = api.get_payload("weather-app", "status")
```

---

## Error handling

All errors extend `MeowError`, so you can catch everything or be specific.

| Exception | When |
|-----------|------|
| `AuthError` | 401/403 — missing or invalid API key |
| `NotFoundError` | 404 — app or endpoint doesn't exist |
| `ValidationError` | 400 — bad data |
| `RateLimitError` | 429 — too many requests |
| `MeowError` | Any other API error |

```python
from meow_sdk import Meow, MeowError, NotFoundError, AuthError

api = Meow(username="jake", api_key="your-key")

try:
    api.send("my-app", "readings", {"value": 42})
except AuthError:
    print("Check your API key!")
except NotFoundError:
    print("App or endpoint not found!")
except MeowError as e:
    print(f"Something went wrong: {e}")
```

Every exception has `status_code` and `response` attributes if you need more detail.

## License

MIT
