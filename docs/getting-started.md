# Getting Started

## Installation

```
pip install meow-sdk
```

## Create a client

```python
from meow_sdk import Meow

# Public reads only (requires username)
api = Meow(username="jake")

# With an API key for writing/managing + reading private endpoints
api = Meow(api_key="your-key")

# Both — read public endpoints by username and write data
api = Meow(username="jake", api_key="your-key")

# Local development — override the base URL
api = Meow("http://localhost:8099", api_key="your-key")
```

- **`base_url`** — where the API lives. Defaults to `"https://meowmeowscratch.com"`.
- **`username`** — needed for reading public endpoints (it's part of the URL).
- **`api_key`** — needed for writing data, managing apps, and reading private endpoints.

## Send your first record

```python
from meow_sdk import Meow

api = Meow(api_key="your-key")

result = api.send("my-app", "readings", {
    "temperature": 22.5,
})

print(result["uuid"])  # new record ID
```

## Read data back

```python
data = api.get("my-app", "readings")
print(data)
```

## Create a control panel

Dashboards let you build control panels with widgets that read and write data across your endpoints.

```python
from meow_sdk import Meow

api = Meow(api_key="your-key")

# Create a dashboard
api.create_dashboard("My Room", "my-room")

# Add a toggle widget pointing at a static endpoint's key
api.create_dashboard_widget("my-room", "endpoint-uuid",
    "lights_on", "toggle", "Lights On")

# Read all widget data
data = api.dashboard_data("my-room")

# Toggle the light
api.dashboard_patch("my-room", "endpoint-uuid", "lights_on", True)
```
