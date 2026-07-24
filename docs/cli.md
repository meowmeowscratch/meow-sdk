# CLI Reference

The `meow` CLI lets you manage your APIs and send data from the terminal. It installs automatically with the SDK.

---

## Setup

Set your credentials as environment variables:

```bash
export MEOW_PLATFORM_API_KEY=YOUR_PLATFORM_TOKEN
export MEOW_APP_API_KEY=YOUR_APP_API_KEY
export MEOW_USERNAME=jake
```

| Variable | Required | Description |
|----------|----------|-------------|
| `MEOW_PLATFORM_API_KEY` | For management | Your account-wide platform token |
| `MEOW_APP_API_KEY` | For data operations | An app-scoped key used by record, consumer-read, aggregate, CSV, and static-payload commands |
| `MEOW_USERNAME` | For public reads | Your Meow Meow Scratch® username |
| `MEOW_URL` | No | API base URL (default: `https://meowmeowscratch.com`) |

The variable names are intentionally role-specific. The CLI does not read
`MEOW_API_KEY`: management commands use the platform token, while direct data
and static-payload commands use the app-scoped key.

!!! tip "Add to your shell profile"
    Put the `export` lines in `~/.bashrc` or `~/.zshrc` so they persist across sessions.

---

## Records

### Send data

```bash
meow send <app> <endpoint> key=value [key=value ...]
```

Values are auto-detected — numbers become numbers, `true`/`false` become booleans, everything else is a string.

```bash
meow send weather-station readings temperature=22.5 humidity=65 location=London

# JSON output with the new record's UUID
# {
#   "uuid": "abc-123",
#   "data": {"temperature": 22.5, "humidity": 65, "location": "London"},
#   ...
# }
```

### Send an atomic batch

Pass an inline JSON array or prefix a JSON file with `@`. A batch contains one
to 100 bare record objects and is all-or-none.

```bash
meow send-batch weather-station readings \
  '[{"temperature":22.5},{"temperature":22.7}]'
meow send-batch weather-station readings @records.json
```

### Read public data

```bash
meow get <app> <endpoint> [filters...]
```

Requires `MEOW_USERNAME`. Supports field filters:

```bash
meow get weather-station readings
meow get weather-station readings temperature__gte=20
meow get weather-station readings location=London
```

### List records (with API key)

```bash
meow records <app> <endpoint> [--limit N]
```

```bash
meow records weather-station readings
meow records weather-station readings --limit 5
```

### Get, update, delete a single record

```bash
meow get-record <app> <endpoint> <uuid>
meow update-record <app> <endpoint> <uuid> key=value [key=value ...]
meow delete-record <app> <endpoint> <uuid>
```

```bash
meow get-record weather-station readings abc-123
meow update-record weather-station readings abc-123 temperature=23.0
meow delete-record weather-station readings abc-123
```

### Aggregations

```bash
meow aggregate <app> <endpoint> <funcs> --field <name> [filters...]
```

Functions: `avg`, `min`, `max`, `sum`, `count` (comma-separated).

```bash
meow aggregate weather-station readings avg,max --field temperature
meow aggregate weather-station readings avg --field temperature location=London
```

### CSV export

```bash
meow csv <app> <endpoint> [filters...]
```

```bash
meow csv weather-station readings
meow csv weather-station readings temperature__gte=20 > data.csv
```

---

## Apps

```bash
meow apps                                           # List all apps
meow get-app <app>                                   # Get app details
meow create-app <name> <slug> [--description TEXT] [--public]
meow update-app <app> [--name TEXT] [--description TEXT] [--public | --private]
meow delete-app <app>
```

```bash
meow apps
meow create-app "Weather Station" weather-station
meow create-app "Public Demo" public-demo --public
meow update-app weather-station --name "My Weather Station"
meow delete-app old-project
```

---

## Endpoints

```bash
meow endpoints <app>                                 # List endpoints
meow get-endpoint <app> <endpoint>                   # Get details
meow create-endpoint <app> <name> <slug> <type> [--description TEXT] [--public]
meow update-endpoint <app> <endpoint> [--name TEXT] [--public | --private]
                                      [--delay-ms N] [--error-rate F] [--ttl N]
meow delete-endpoint <app> <endpoint>
```

Type is one of: `collection`, `static`, `proxy`.
Apps and endpoints are private unless `--public` is supplied.

```bash
meow endpoints weather-station
meow create-endpoint weather-station "Readings" readings collection
meow create-endpoint weather-station "Status" status static
meow update-endpoint weather-station readings --delay-ms 500 --error-rate 0.1
meow delete-endpoint weather-station old-endpoint
```

---

## Fields

Define the schema for collection endpoints.

```bash
meow fields <app> <endpoint>                         # List fields
meow create-field <app> <endpoint> <name> <label> <type> [--required]
meow update-field <app> <endpoint> <uuid> [--label TEXT] [--required BOOL]
meow delete-field <app> <endpoint> <uuid>
```

Field types: `text`, `textarea`, `number`, `boolean`, `date`, `datetime`, `time`, `color`, `email`, `url`, `select`, `rating`, `image_url`, `json`.

```bash
meow fields weather-station readings
meow create-field weather-station readings temperature Temperature number
meow create-field weather-station readings location Location text --required
meow delete-field weather-station readings field-uuid-123
```

---

## Static payloads

For endpoints with type `static`:

```bash
meow payload-get <app> <endpoint> [--metadata]
meow payload-set <app> <endpoint> key=value [key=value ...]
```

```bash
meow payload-set weather-station status online=true version=1.2
meow payload-get weather-station status
meow payload-get weather-station status --metadata
```

---

## Proxy config

For endpoints with type `proxy`:

```bash
meow proxy-get <app> <endpoint>
meow proxy-set <app> <endpoint> <url> [--method METHOD]
```

```bash
meow proxy-set weather-station forecast https://api.weather.com/v1/forecast --method GET
meow proxy-get weather-station forecast
```

---

## Dashboards

Interactive control panels with widgets.

```bash
meow dashboards                                      # List dashboards
meow dashboard-get <slug>                            # Get details
meow dashboard-create <name> <slug> [--description TEXT]
meow dashboard-update <slug> [--name TEXT] [--description TEXT]
meow dashboard-delete <slug>
```

### Widgets

```bash
meow widgets <dashboard>                             # List widgets
meow widget-create <dashboard> <app> <endpoint> <key_path> <type> <label>
                   [--config JSON_OR_@FILE] [--sort-order N]
meow widget-update <dashboard> <uuid> [--label TEXT] [--type TYPE]
                                      [--key-path PATH] [--sort-order N]
meow widget-delete <dashboard> <uuid>
```

Widget types: `toggle`, `color`, `slider`, `number`, `text`, `select`, `display`.

### Live data

```bash
meow dashboard-data <dashboard>                      # Read all widget values
meow widget-set <dashboard> <widget_uuid> <value>
```

```bash
meow dashboard-data my-room
meow widget-set my-room WIDGET_UUID true
meow widget-set my-room WIDGET_UUID 22.5
```

### Public dashboards

```bash
meow public-dashboard <share_token>
```

---

## Webhooks

```bash
meow webhooks <app> <endpoint>                       # List webhooks
meow webhook-get <app> <endpoint> <uuid>             # Get details
meow webhook-create <app> <endpoint> <url> <events> [--secret TEXT]
meow webhook-update <app> <endpoint> <uuid> [--url TEXT] [--events TEXT]
                                             [--active BOOL] [--secret TEXT]
meow webhook-delete <app> <endpoint> <uuid>
```

Events: `record.created`, `record.updated`, `record.deleted`, `payload.updated` (comma-separated).

```bash
meow webhook-create weather-station readings https://example.com/hook record.created,record.updated
meow webhook-update weather-station readings hook-uuid --active false
meow webhooks weather-station readings
```

---

## Encryption

Per-endpoint Fernet encryption.

```bash
meow encryption <app> <endpoint>                     # Check status
meow encrypt-enable <app> <endpoint>                 # Enable (key shown once!)
meow encrypt-disable <app> <endpoint>                # Disable
```

!!! warning
    `encrypt-enable` displays the encryption key exactly once. Save it somewhere safe.

---

## Request logs

```bash
meow logs <app> <endpoint>
```

Shows the last 50 API requests to an endpoint with method, status code, and response time.

---

## API keys

App-scoped API keys for sharing access to a single app:

```bash
meow keys <app>                                      # List keys
meow key-create <app>                                # Create (shown once!)
meow key-delete <app> <uuid>                         # Revoke
```

---

## Platform tokens

Personal tokens for SDK, CLI, and MCP authentication:

```bash
meow platform-tokens                                 # List tokens
meow platform-token-create <name>                    # Create (shown once!)
meow platform-token-revoke <uuid>                    # Revoke
```

---

## Limits

```bash
meow limits                                          # Enforced limits and capacity
```

---

## Field types

```bash
meow field-types                                     # List all available types
```

---

## Tips

**Pipe JSON output** — most commands output JSON, so you can pipe to `jq`:

```bash
meow get weather-station readings | jq '.results[0].data.temperature'
```

**Use in scripts** — the CLI exits with code 1 on errors, so you can chain with `&&`:

```bash
meow send my-app readings temp=22.5 && echo "Sent!"
```

**Cron jobs** — send data on a schedule without a long-running process:

```bash
# Every 5 minutes, send the current date
*/5 * * * * MEOW_APP_API_KEY=YOUR_APP_API_KEY meow send my-app heartbeat ts="$(date -u +\%Y-\%m-\%dT\%H:\%M:\%SZ)"
```
