# Error Handling

All SDK errors extend `MeowError`. You can catch everything with `MeowError`, or handle specific cases.

---

## Exception hierarchy

```
MeowError
├── AuthError          # 401, 403
├── NotFoundError      # 404
├── ValidationError    # 400
└── RateLimitError     # 429
```

| Exception | HTTP status | When it happens |
|-----------|-------------|-----------------|
| `AuthError` | 401, 403 | Missing, invalid, or expired API key |
| `NotFoundError` | 404 | App or endpoint slug doesn't exist |
| `ValidationError` | 400 | Bad data — wrong types, missing required fields |
| `RateLimitError` | 429 | Too many requests (300/min for API keys, 120/min anonymous) |
| `MeowError` | Any 4xx/5xx | Catch-all for other API errors |

---

## Basic usage

```python
from meow_sdk import Meow, AuthError, NotFoundError, MeowError

api = Meow(api_key="YOUR_PLATFORM_TOKEN")

try:
    api.send("my-app", "readings", {"value": 42})
except AuthError:
    print("Check your API key")
except NotFoundError:
    print("App or endpoint not found")
except MeowError as e:
    print(f"API error: {e}")
```

---

## Exception attributes

Every exception exposes structured server details when available:

| Attribute | Type | Description |
|-----------|------|-------------|
| `status_code` | `int` | HTTP status code (e.g. `400`, `404`) |
| `response` | `Response` | The full `requests.Response` object |
| `code` | `str` | Stable machine-readable error code |
| `field` | `str` | Offending request field, when applicable |
| `hint` | `str` | Suggested remediation |
| `details` | `dict` | Structured validation or quota details |

```python
try:
    api.send("my-app", "readings", {"value": 42})
except MeowError as e:
    print(e.status_code)       # 400
    print(e.code, e.field)
    print(e.hint)
    print(e.response.json())   # full error body
```

---

## Handling rate limits

The API allows 300 requests per minute with an API key, 120 per minute without.

```python
import time
from meow_sdk import Meow, RateLimitError

api = Meow(api_key="YOUR_PLATFORM_TOKEN")

for reading in sensor_data:
    try:
        api.send("my-app", "readings", reading)
    except RateLimitError:
        print("Rate limited — waiting 60s")
        time.sleep(60)
        api.send("my-app", "readings", reading)
```

---

## Importing

Import only what you need:

```python
# Just the client
from meow_sdk import Meow

# Client + specific exceptions
from meow_sdk import Meow, AuthError, NotFoundError

# Everything
from meow_sdk import (
    Meow,
    MeowError,
    AuthError,
    NotFoundError,
    ValidationError,
    RateLimitError,
)
```
