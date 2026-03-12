# meow-sdk

**Python SDK and CLI for the [meow meow scratch](https://meowmeowscratch.com) API.**

Build your own APIs, send sensor data from your Raspberry Pi, and control hardware from anywhere — all in a few lines of Python.

---

## Install

```
pip install meow-sdk
```

Requires Python 3.8+. No extra dependencies beyond `requests`.

---

## Quick example

=== "Send data"

    ```python
    from meow_sdk import Meow

    api = Meow(api_key="mms_your_key_here")

    api.send("weather-station", "readings", {
        "temperature": 22.5,
        "humidity": 65,
    })
    ```

=== "Read data"

    ```python
    from meow_sdk import Meow

    api = Meow(username="jake")
    data = api.get("weather-station", "readings")
    print(data)
    ```

=== "CLI"

    ```bash
    export MEOW_API_KEY=mms_your_key_here

    meow send weather-station readings temperature=22.5 humidity=65
    meow get weather-station readings
    ```

---

## What's included

<div class="grid" markdown>

**Python SDK**
:   Full API client with methods for records, apps, endpoints, dashboards, webhooks, encryption, and more. Typed exceptions for clean error handling.

**CLI tool**
:   40+ commands for managing your APIs from the terminal. Pipe-friendly JSON output. Configure once with environment variables.

**Raspberry Pi ready**
:   Works on any Python environment. Examples for DHT22, buttons, LEDs, camera modules, and GPIO. Run as a systemd service for always-on data collection.

**Control panels**
:   Build interactive dashboards with toggle switches, sliders, color pickers, and live displays. Control hardware remotely from the web or your phone.

</div>

---

## Next steps

- **[Getting Started](getting-started.md)** — create your first app and send data in 5 minutes
- **[Raspberry Pi guide](raspberry-pi.md)** — connect sensors, buttons, and LEDs
- **[CLI Reference](cli.md)** — all 40+ terminal commands
- **[API Reference](api-reference.md)** — every SDK method documented
- **[Dashboards](dashboards.md)** — build control panels with interactive widgets
