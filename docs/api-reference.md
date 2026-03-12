# API Reference

Complete reference for every method in the `Meow` client. Methods are grouped by feature.

---

## Client

```python
from meow_sdk import Meow

api = Meow(
    base_url="https://meowmeowscratch.com",  # optional
    username="jake",                           # for public reads
    api_key="mms_your_key_here",              # for writes + management
)
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `base_url` | `str` | `"https://meowmeowscratch.com"` | API base URL |
| `username` | `str` | `None` | Required for public endpoint reads |
| `api_key` | `str` | `None` | Required for writes, management, and private reads |

---

## Records

### `api.send(app, endpoint, data)` { #send }

Send a new record to a collection endpoint. **This is the main thing.**

| Parameter | Type | Description |
|-----------|------|-------------|
| `app` | `str` | App slug |
| `endpoint` | `str` | Endpoint slug |
| `data` | `dict` | Record data |

Returns the created record (including `uuid`).

```python
result = api.send("weather-station", "readings", {
    "temperature": 22.5,
    "humidity": 65,
})
print(result["uuid"])
```

---

### `api.records(app, endpoint, limit=25, offset=0)` { #records }

List records for an endpoint (paginated). Requires API key.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `app` | `str` | | App slug |
| `endpoint` | `str` | | Endpoint slug |
| `limit` | `int` | `25` | Records per page |
| `offset` | `int` | `0` | Skip this many records |

Returns `{"count": N, "next": url, "previous": url, "results": [...]}`.

```python
page = api.records("weather-station", "readings", limit=10)
print(page["count"])
print(page["results"])
```

---

### `api.all_records(app, endpoint)` { #all-records }

Fetch every record from an endpoint (auto-paginates). Requires API key.

Returns a flat list of all records.

```python
everything = api.all_records("weather-station", "readings")
print(len(everything))
```

!!! note
    This makes multiple API calls under the hood. For large datasets, prefer `records()` with pagination.

---

### `api.update(app, endpoint, record_id, data)` { #update }

Update an existing record.

```python
api.update("weather-station", "readings", "abc-123", {
    "temperature": 23.0,
})
```

---

### `api.delete_record(app, endpoint, record_id)` { #delete-record }

Delete a record.

```python
api.delete_record("weather-station", "readings", "abc-123")
```

---

## Public reads

These methods read from public endpoints. They require `username` but **not** an API key.

### `api.get(app, endpoint, **filters)` { #get }

Read data from a public endpoint. Supports keyword argument filters.

```python
api = Meow(username="jake")

# All records
data = api.get("weather-station", "readings")

# With filters
data = api.get("weather-station", "readings", temperature__gte=20)
```

---

### `api.get_record(app, endpoint, record_id)` { #get-record }

Read a single public record by UUID.

```python
record = api.get_record("weather-station", "readings", "abc-123")
```

---

### `api.aggregate(app, endpoint, aggregates, field=None, **filters)` { #aggregate }

Run aggregations on a collection endpoint.

| Parameter | Type | Description |
|-----------|------|-------------|
| `aggregates` | `list[str]` | Functions: `"avg"`, `"min"`, `"max"`, `"sum"`, `"count"` |
| `field` | `str` | Field to aggregate on (required for avg/min/max/sum) |
| `**filters` | | Optional filters applied before aggregating |

```python
result = api.aggregate("weather-station", "readings",
    ["avg", "max"], field="temperature")
print(result["aggregations"]["avg"])

# With filters
result = api.aggregate("weather-station", "readings",
    ["avg"], field="temperature", location="London")
```

---

### `api.export_csv(app, endpoint, **filters)` { #export-csv }

Download records as a CSV string.

```python
csv_data = api.export_csv("weather-station", "readings")

# Save to file
with open("data.csv", "w") as f:
    f.write(csv_data)

# With filters
csv_data = api.export_csv("weather-station", "readings", temperature__gte=20)
```

---

## Apps

All app methods require an API key.

### `api.apps()` { #apps }

List your apps.

```python
my_apps = api.apps()
for app in my_apps:
    print(app["slug"], app["name"])
```

---

### `api.get_app(slug)` { #get-app }

Get details for a single app.

```python
app = api.get_app("weather-station")
print(app["endpoint_count"])
```

---

### `api.create_app(name, slug, description="", is_public=True)` { #create-app }

Create a new app.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `name` | `str` | | Display name |
| `slug` | `str` | | URL slug (letters, numbers, hyphens) |
| `description` | `str` | `""` | Optional description |
| `is_public` | `bool` | `True` | Whether endpoints are publicly readable |

```python
api.create_app("Weather Station", "weather-station")
api.create_app("Secret Project", "secret", is_public=False)
```

---

### `api.update_app(slug, **kwargs)` { #update-app }

Update an app. Pass only the fields you want to change.

```python
api.update_app("weather-station", name="My Weather Station")
api.update_app("weather-station", is_public=False, description="Private")
```

---

### `api.delete_app(slug)` { #delete-app }

Delete an app and all its endpoints, records, and config.

```python
api.delete_app("old-project")
```

---

## Endpoints

All endpoint methods require an API key.

### `api.endpoints(app)` { #endpoints }

List endpoints in an app.

```python
eps = api.endpoints("weather-station")
for ep in eps:
    print(ep["slug"], ep["endpoint_type"])
```

---

### `api.get_endpoint(app, endpoint)` { #get-endpoint }

Get details for a single endpoint.

```python
ep = api.get_endpoint("weather-station", "readings")
print(ep["record_count"])
```

---

### `api.create_endpoint(app, name, slug, endpoint_type="collection", description="", is_public=True)` { #create-endpoint }

Create a new endpoint.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `endpoint_type` | `str` | `"collection"` | `"collection"`, `"static"`, or `"proxy"` |

```python
api.create_endpoint("weather-station", "Readings", "readings")
api.create_endpoint("weather-station", "Status", "status", "static")
api.create_endpoint("weather-station", "Forecast", "forecast", "proxy")
```

---

### `api.update_endpoint(app, endpoint, **kwargs)` { #update-endpoint }

Update an endpoint. Pass only the fields you want to change.

```python
api.update_endpoint("weather-station", "readings", name="Sensor Readings")
api.update_endpoint("weather-station", "readings", is_public=False)
```

---

### `api.delete_endpoint(app, endpoint)` { #delete-endpoint }

Delete an endpoint and all its data.

```python
api.delete_endpoint("weather-station", "old-endpoint")
```

---

## Fields

Define the schema for collection endpoints. All methods require an API key.

### `api.fields(app, endpoint)` { #fields }

List fields for a collection endpoint.

```python
schema = api.fields("weather-station", "readings")
for field in schema:
    print(field["name"], field["field_type"])
```

---

### `api.create_field(app, endpoint, name, label, field_type, **kwargs)` { #create-field }

Create a new field.

| Parameter | Type | Description |
|-----------|------|-------------|
| `name` | `str` | Machine name (used in record data) |
| `label` | `str` | Display label |
| `field_type` | `str` | One of the 14 types below |
| `required` | `bool` | Whether the field is required |
| `default_value` | `any` | Default value |
| `options` | `dict` | Type-specific options |
| `help_text` | `str` | Help text shown in forms |
| `sort_order` | `int` | Display order |

**Field types:** `text`, `textarea`, `number`, `boolean`, `date`, `datetime`, `time`, `color`, `email`, `url`, `select`, `rating`, `image_url`, `json`

```python
api.create_field("weather-station", "readings",
    "temperature", "Temperature", "number")

api.create_field("weather-station", "readings",
    "location", "Location", "text",
    required=True, help_text="City name")

api.create_field("weather-station", "readings",
    "mood", "Mood", "select",
    options={"choices": ["sunny", "cloudy", "rainy"]})
```

---

### `api.update_field(app, endpoint, field_uuid, **kwargs)` { #update-field }

Update a field.

```python
api.update_field("weather-station", "readings", "uuid-123", label="Temp (C)")
```

---

### `api.delete_field(app, endpoint, field_uuid)` { #delete-field }

Delete a field from the schema.

```python
api.delete_field("weather-station", "readings", "uuid-123")
```

---

### `api.field_types()` { #field-types }

List all available field types. No authentication required.

```python
types = api.field_types()
for t in types:
    print(t["value"], t["label"])
```

---

## Static payloads

For endpoints with type `"static"`. Requires an API key.

### `api.get_payload(app, endpoint)` { #get-payload }

Get the current static payload.

```python
payload = api.get_payload("weather-station", "status")
```

---

### `api.set_payload(app, endpoint, data)` { #set-payload }

Set (replace) the static payload.

```python
api.set_payload("weather-station", "status", {
    "online": True,
    "version": "1.2",
    "message": "All systems go",
})
```

---

## Proxy config

For endpoints with type `"proxy"`. Requires an API key.

### `api.get_proxy(app, endpoint)` { #get-proxy }

Get the proxy configuration.

```python
config = api.get_proxy("weather-station", "forecast")
```

---

### `api.set_proxy(app, endpoint, upstream_url, method="GET", headers=None, query_params=None, body_template=None, jmespath_transform=None)` { #set-proxy }

Configure a proxy endpoint to wrap an external API.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `upstream_url` | `str` | | The external URL to proxy |
| `method` | `str` | `"GET"` | HTTP method |
| `headers` | `dict` | `None` | Custom headers to send upstream |
| `query_params` | `dict` | `None` | Query parameters to add |
| `body_template` | `dict` | `None` | Request body template |
| `jmespath_transform` | `str` | `None` | JMESPath expression to transform the response |

```python
api.set_proxy("weather-station", "forecast",
    "https://api.weather.com/v1/forecast",
    method="GET",
    headers={"X-Api-Key": "weather-key"},
    jmespath_transform="data.forecast[0]",
)
```

---

## Encryption

Per-endpoint Fernet encryption. Requires an API key.

### `api.get_encryption(app, endpoint)` { #get-encryption }

Check encryption status.

```python
info = api.get_encryption("weather-station", "readings")
print(info["encryption_enabled"])
```

---

### `api.enable_encryption(app, endpoint)` { #enable-encryption }

Generate an encryption key and enable encryption.

!!! warning
    The key is only shown once. Save it immediately.

```python
result = api.enable_encryption("weather-station", "readings")
print(result["key"])  # save this!
```

---

### `api.disable_encryption(app, endpoint)` { #disable-encryption }

Disable encryption and delete the key.

```python
api.disable_encryption("weather-station", "readings")
```

---

## Request logs

### `api.request_logs(app, endpoint)` { #request-logs }

Get the last 50 API requests to an endpoint. Requires an API key.

```python
logs = api.request_logs("weather-station", "readings")
for log in logs:
    print(log["method"], log["status_code"], f"{log['response_time_ms']}ms")
```

---

## Webhooks

Requires an API key.

### `api.webhooks(app, endpoint)` { #webhooks }

List webhooks for an endpoint.

```python
hooks = api.webhooks("weather-station", "readings")
```

---

### `api.get_webhook(app, endpoint, webhook_uuid)` { #get-webhook }

Get a single webhook.

```python
hook = api.get_webhook("weather-station", "readings", "uuid-123")
```

---

### `api.create_webhook(app, endpoint, target_url, events, secret=None, is_active=True)` { #create-webhook }

Create a webhook.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `target_url` | `str` | | URL to send webhook payloads to |
| `events` | `list[str]` | | Events to subscribe to |
| `secret` | `str` | `None` | Signing secret for payload verification |
| `is_active` | `bool` | `True` | Whether the webhook is active |

Events: `record.created`, `record.updated`, `record.deleted`, `payload.updated`

```python
api.create_webhook("weather-station", "readings",
    "https://example.com/hook",
    ["record.created", "record.updated"],
    secret="my-signing-secret",
)
```

---

### `api.update_webhook(app, endpoint, webhook_uuid, **kwargs)` { #update-webhook }

Update a webhook. Pass only the fields you want to change.

```python
api.update_webhook("weather-station", "readings", "uuid-123",
    is_active=False)

api.update_webhook("weather-station", "readings", "uuid-123",
    events=["record.created", "record.deleted"],
    target_url="https://new-url.com/hook")
```

---

### `api.delete_webhook(app, endpoint, webhook_uuid)` { #delete-webhook }

Delete a webhook.

```python
api.delete_webhook("weather-station", "readings", "uuid-123")
```

---

## Dashboards

See the [Dashboards guide](dashboards.md) for a full walkthrough.

### CRUD

| Method | Description |
|--------|-------------|
| `api.dashboards()` | List dashboards |
| `api.get_dashboard(slug)` | Get dashboard details |
| `api.create_dashboard(name, slug, description="")` | Create a dashboard |
| `api.update_dashboard(slug, **kwargs)` | Update a dashboard |
| `api.delete_dashboard(slug)` | Delete a dashboard |

### Widgets

| Method | Description |
|--------|-------------|
| `api.dashboard_widgets(dashboard)` | List widgets |
| `api.create_dashboard_widget(dashboard, endpoint_id, key_path, widget_type, label, **kwargs)` | Add a widget |
| `api.update_dashboard_widget(dashboard, widget_uuid, **kwargs)` | Update a widget |
| `api.delete_dashboard_widget(dashboard, widget_uuid)` | Remove a widget |

### Data

| Method | Description |
|--------|-------------|
| `api.dashboard_data(dashboard)` | Read all current values |
| `api.dashboard_patch(dashboard, endpoint_uuid, key_path, value)` | Write a single value |
| `api.public_dashboard(share_token)` | Read a public dashboard (no API key) |

---

## API keys

App-scoped keys for sharing access to a single app. Requires an API key.

### `api.app_keys(app)` { #app-keys }

List active API keys for an app.

```python
keys = api.app_keys("weather-station")
```

---

### `api.create_app_key(app)` { #create-app-key }

Create a new app-scoped API key.

!!! warning
    The key is only shown once.

```python
result = api.create_app_key("weather-station")
print(result["key"])  # save this!
```

---

### `api.delete_app_key(app, key_uuid)` { #delete-app-key }

Revoke an app-scoped API key.

```python
api.delete_app_key("weather-station", "key-uuid-123")
```

---

## Platform tokens

Personal tokens for SDK, CLI, and MCP authentication. Requires an API key.

### `api.platform_tokens()` { #platform-tokens }

List your platform tokens.

```python
tokens = api.platform_tokens()
```

---

### `api.create_platform_token(name)` { #create-platform-token }

Create a new platform token.

!!! warning
    The key is only shown once.

```python
result = api.create_platform_token("My Raspberry Pi")
print(result["key"])  # save this!
```

---

### `api.revoke_platform_token(uuid)` { #revoke-platform-token }

Revoke a platform token.

```python
api.revoke_platform_token("token-uuid-123")
```

---

## Billing

### `api.billing_status()` { #billing-status }

Get your current plan, usage, and limits. Requires an API key.

```python
status = api.billing_status()
print(f"{status['plan']}: {status['apps_used']}/{status['apps_limit']} apps")
```
