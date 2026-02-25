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

api = Meow("https://meowmeowscratch.com", api_key="your-key")

api.send("my-weather-app", "readings", {
    "temperature": 22.5,
    "humidity": 65,
})
```

### Read data from a public endpoint

```python
from meow_sdk import Meow

api = Meow("https://meowmeowscratch.com", username="jake")

data = api.get("my-weather-app", "current-temp")
print(data)
```

Your public API URL is: `/api/v1/<username>/<app>/<endpoint>/`
