# Raspberry Pi

## Basic sensor loop

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

## With a DHT22 sensor

```python
import time
import adafruit_dht
import board
from meow_sdk import Meow

sensor = adafruit_dht.DHT22(board.D4)
api = Meow(api_key="your-key")

while True:
    try:
        api.send("my-pi-app", "readings", {
            "temperature": sensor.temperature,
            "humidity": sensor.humidity,
        })
        print(f"{sensor.temperature}°C, {sensor.humidity}%")
    except Exception as e:
        print(f"Error: {e}")

    time.sleep(10)
```

## Tips

- Use `time.sleep()` between sends to avoid hitting rate limits.
- Wrap your sensor reads in `try/except` — hardware can be flaky.
- Run your script on boot with a systemd service or crontab `@reboot`.
