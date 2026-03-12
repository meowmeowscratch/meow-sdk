# Raspberry Pi

Connect sensors, buttons, LEDs, and more to your meow meow scratch API.

---

## Setup

Install the SDK on your Pi:

```bash
pip install meow-sdk
```

Set your API key:

```bash
export MEOW_API_KEY=mms_your_key_here
```

!!! tip "Python version"
    The SDK works with Python 3.8+. Raspberry Pi OS ships with Python 3.11+.

---

## Temperature & humidity (DHT22)

```bash
pip install adafruit-circuitpython-dht
```

```python
import time
import adafruit_dht
import board
from meow_sdk import Meow

sensor = adafruit_dht.DHT22(board.D4)  # GPIO pin 4
api = Meow(api_key="mms_your_key_here")

while True:
    try:
        api.send("my-pi", "climate", {
            "temperature": sensor.temperature,
            "humidity": sensor.humidity,
        })
        print(f"{sensor.temperature}°C, {sensor.humidity}%")
    except RuntimeError as e:
        # DHT sensors occasionally fail — just retry
        print(f"Sensor glitch: {e}")
    except Exception as e:
        print(f"API error: {e}")

    time.sleep(10)
```

---

## Button press counter

```python
import RPi.GPIO as GPIO
from meow_sdk import Meow

GPIO.setmode(GPIO.BCM)
GPIO.setup(17, GPIO.IN, pull_up_down=GPIO.PUD_UP)

api = Meow(api_key="mms_your_key_here")
count = 0

def on_press(channel):
    global count
    count += 1
    api.send("my-pi", "buttons", {"count": count, "pin": 17})
    print(f"Button pressed! Count: {count}")

GPIO.add_event_detect(17, GPIO.FALLING, callback=on_press, bouncetime=300)

print("Waiting for button presses... (Ctrl+C to exit)")
try:
    GPIO.wait_for_edge(17, GPIO.FALLING)  # keep alive
    while True:
        pass
except KeyboardInterrupt:
    GPIO.cleanup()
```

---

## LED control from dashboard

Use a dashboard widget to control a physical LED:

```python
import time
import RPi.GPIO as GPIO
from meow_sdk import Meow

GPIO.setmode(GPIO.BCM)
GPIO.setup(17, GPIO.OUT)

api = Meow(api_key="mms_your_key_here")

while True:
    data = api.dashboard_data("my-room")

    for widget in data["widgets"]:
        if widget["key_path"] == "led_on":
            GPIO.output(17, widget.get("current_value", False))

    time.sleep(2)
```

Set up the dashboard:

```python
api.create_dashboard("My Room", "my-room")
api.create_dashboard_widget(
    "my-room", "endpoint-uuid",
    "led_on", "toggle", "LED Light"
)
```

Now toggle the LED from the web app or your phone.

---

## Camera snapshot

```bash
pip install picamera2
```

```python
import time
import base64
from picamera2 import Picamera2
from meow_sdk import Meow

cam = Picamera2()
cam.configure(cam.create_still_configuration())
cam.start()

api = Meow(api_key="mms_your_key_here")

while True:
    cam.capture_file("/tmp/snapshot.jpg")

    with open("/tmp/snapshot.jpg", "rb") as f:
        img_b64 = base64.b64encode(f.read()).decode()

    api.set_payload("my-pi", "camera", {
        "image": f"data:image/jpeg;base64,{img_b64}",
        "captured_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    })

    print("Snapshot uploaded")
    time.sleep(60)
```

---

## One-shot with CLI

Don't need a long-running script? Use the CLI in a cron job:

```bash
# Send a heartbeat every 5 minutes
*/5 * * * * MEOW_API_KEY=mms_xxx meow send my-pi heartbeat ts="$(date -u +\%Y-\%m-\%dT\%H:\%M:\%SZ)" host="$(hostname)"
```

Or read a value from a shell command:

```bash
# Send CPU temperature
meow send my-pi system cpu_temp=$(vcgencmd measure_temp | grep -o '[0-9.]*')
```

---

## Run on boot with systemd

Create a service file so your script starts automatically:

```bash
sudo nano /etc/systemd/system/meow-sensor.service
```

```ini
[Unit]
Description=meow meow scratch sensor
After=network-online.target
Wants=network-online.target

[Service]
User=pi
Environment=MEOW_API_KEY=mms_your_key_here
ExecStart=/usr/bin/python3 /home/pi/sensor.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start:

```bash
sudo systemctl enable meow-sensor
sudo systemctl start meow-sensor

# Check status
sudo systemctl status meow-sensor

# View logs
journalctl -u meow-sensor -f
```

---

## Tips

- **Rate limits** — the API allows 300 requests per minute. A 10-second `sleep()` keeps you well under.
- **Error handling** — always wrap sensor reads in `try/except`. Hardware is flaky. The script should never crash.
- **Offline buffering** — if the network drops, catch the exception and queue data locally. Send it when the connection comes back.
- **Multiple sensors** — send all readings in a single `api.send()` call rather than one per sensor. Fewer API calls, same data.
- **Static endpoints** — use `set_payload()` for "current state" data (like a thermostat reading). Use `send()` for time-series data you want to keep.
