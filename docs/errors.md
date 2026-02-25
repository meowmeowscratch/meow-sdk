# Error Handling

All errors extend `MeowError`, so you can catch everything or be specific.

| Exception | When |
|-----------|------|
| `AuthError` | 401/403 — missing or invalid API key |
| `NotFoundError` | 404 — app or endpoint doesn't exist |
| `ValidationError` | 400 — bad data |
| `RateLimitError` | 429 — too many requests |
| `MeowError` | Any other API error |

## Example

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

```python
try:
    api.send("my-app", "readings", {"value": 42})
except MeowError as e:
    print(e.status_code)  # e.g. 400
    print(e.response)     # full response dict
```
