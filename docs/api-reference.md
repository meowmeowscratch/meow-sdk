# API Reference

## Records

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
| `api.records(app, endpoint)` | List records with your API key (works for private and public endpoints) |

```python
data = api.get("weather-app", "current-temp")

record = api.get_record("weather-app", "readings", "abc-123")
```

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
result = api.send("weather-app", "readings", {"temperature": 22.5})
print(result["uuid"])

api.update("weather-app", "readings", "abc-123", {"temperature": 23.0})

page = api.records("weather-app", "readings", limit=10)
print(page["count"])
print(page["results"])

everything = api.all_records("weather-app", "readings")
```

---

## Apps

API key required.

| Method | Description |
|--------|-------------|
| `api.apps()` | List your apps |
| `api.get_app(slug)` | Get details for a single app |
| `api.create_app(name, slug, description="", is_public=True)` | Create a new app |
| `api.update_app(slug, **kwargs)` | Update an app (pass only fields to change) |
| `api.delete_app(slug)` | Delete an app |

```python
my_apps = api.apps()

app = api.get_app("weather-app")
print(app["endpoint_count"])

api.create_app("Weather App", "weather-app")
api.create_app("Secret App", "secret-app", is_public=False)

api.update_app("weather-app", name="My Weather App", description="Updated!")

api.delete_app("old-app")
```

---

## Endpoints

API key required. Endpoint types: `"collection"`, `"static"`, `"proxy"`.

| Method | Description |
|--------|-------------|
| `api.endpoints(app)` | List endpoints in an app |
| `api.get_endpoint(app, endpoint)` | Get details for a single endpoint |
| `api.create_endpoint(app, name, slug, endpoint_type="collection", ...)` | Create an endpoint |
| `api.update_endpoint(app, endpoint, **kwargs)` | Update an endpoint |
| `api.delete_endpoint(app, endpoint)` | Delete an endpoint |

```python
eps = api.endpoints("weather-app")

ep = api.get_endpoint("weather-app", "readings")
print(ep["record_count"])

api.create_endpoint("weather-app", "Readings", "readings")
api.create_endpoint("weather-app", "Status", "status", endpoint_type="static")

api.update_endpoint("weather-app", "readings", name="Sensor Readings")

api.delete_endpoint("weather-app", "old-endpoint")
```

---

## Fields

API key required. Define the schema for a collection endpoint.

Field types: `text`, `textarea`, `number`, `boolean`, `date`, `datetime`, `time`, `color`, `email`, `url`, `select`, `rating`, `image_url`, `json`.

| Method | Description |
|--------|-------------|
| `api.fields(app, endpoint)` | List fields for a collection endpoint |
| `api.create_field(app, endpoint, name, label, field_type, **kwargs)` | Create a new field |
| `api.update_field(app, endpoint, field_uuid, **kwargs)` | Update a field |
| `api.delete_field(app, endpoint, field_uuid)` | Delete a field |

```python
schema = api.fields("weather-app", "readings")

api.create_field("weather-app", "readings", "temperature", "Temperature", "number")
api.create_field("weather-app", "readings", "location", "Location", "text",
                 required=True, help_text="Where the reading was taken")

api.update_field("weather-app", "readings", "field-uuid-123", label="Temp (C)")

api.delete_field("weather-app", "readings", "field-uuid-123")
```

Optional `create_field` keyword arguments: `required`, `default_value`, `options`, `help_text`, `sort_order`.

---

## Static Payloads

API key required. For endpoints with type `"static"`.

| Method | Description |
|--------|-------------|
| `api.get_payload(app, endpoint)` | Get the static payload |
| `api.set_payload(app, endpoint, data)` | Set the static payload |

```python
api.set_payload("weather-app", "status", {"open": True, "message": "All good!"})
payload = api.get_payload("weather-app", "status")
```
