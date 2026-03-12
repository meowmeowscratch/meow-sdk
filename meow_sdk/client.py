import requests

from .exceptions import AuthError, MeowError, NotFoundError, RateLimitError, ValidationError


class Meow:
    """Talk to the meow meow scratch API.

    Args:
        base_url: Where the API lives. Defaults to "https://meowmeowscratch.com".
        username: Your meow meow scratch username (used for public reads).
        api_key:  Your API key. Needed for writing data, managing apps, and reading private endpoints.
    """

    def __init__(self, base_url="https://meowmeowscratch.com", username=None, api_key=None,
                 timeout=30):
        self.base_url = base_url.rstrip("/")
        self.username = username
        self.session = requests.Session()
        self.timeout = timeout
        if api_key:
            self.session.headers["Authorization"] = f"Bearer {api_key}"

    # ── Internal helpers ────────────────────────────────────────────

    def _url(self, path):
        return f"{self.base_url}/api/{path.lstrip('/')}"

    def _request(self, method, path, **kwargs):
        url = self._url(path)
        kwargs.setdefault("timeout", self.timeout)
        resp = self.session.request(method, url, **kwargs)
        if resp.status_code == 204:
            return None
        if resp.status_code == 401 or resp.status_code == 403:
            msg = self._error_message(resp, "Authentication required — did you set your API key?")
            raise AuthError(msg, status_code=resp.status_code, response=resp)
        if resp.status_code == 404:
            msg = self._error_message(resp, "Not found — check your app and endpoint slugs.")
            raise NotFoundError(msg, status_code=resp.status_code, response=resp)
        if resp.status_code == 400:
            msg = self._error_message(resp, "Bad request — check your data.")
            raise ValidationError(msg, status_code=resp.status_code, response=resp)
        if resp.status_code == 429:
            msg = self._error_message(resp, "Too many requests — slow down!")
            raise RateLimitError(msg, status_code=resp.status_code, response=resp)
        if resp.status_code >= 400:
            msg = self._error_message(resp, f"Request failed (status {resp.status_code}).")
            raise MeowError(msg, status_code=resp.status_code, response=resp)
        try:
            return resp.json()
        except ValueError:
            return resp.text

    @staticmethod
    def _error_message(resp, fallback):
        try:
            body = resp.json()
            if isinstance(body, dict):
                return body.get("detail") or body.get("error") or str(body)
            return str(body)
        except (ValueError, AttributeError):
            return fallback

    def _require_username(self):
        if not self.username:
            raise MeowError(
                "Username is required for reading public endpoints. "
                "Pass it when creating the client: Meow(username='jake')"
            )

    # ── Consumer API (public reads) ─────────────────────────────────

    def get(self, app, endpoint, **filters):
        """Read data from a public endpoint (requires username).

        For private endpoints, use records() with an API key instead.
        Pass keyword arguments to filter collection data.

        >>> api = Meow(username="jake")
        >>> data = api.get("weather-app", "current-temp")
        >>> data = api.get("weather-app", "readings", temperature__gte=20)
        """
        self._require_username()
        return self._request("GET", f"v1/{self.username}/{app}/{endpoint}/",
                             params=filters or None)

    def get_record(self, app, endpoint, record_id):
        """Read a single record by ID.

        >>> record = api.get_record("weather-app", "readings", "abc-123")
        """
        self._require_username()
        return self._request("GET", f"v1/{self.username}/{app}/{endpoint}/{record_id}/")

    def aggregate(self, app, endpoint, aggregates, field=None, **filters):
        """Run aggregations on a collection endpoint (requires username).

        Aggregates: avg, min, max, sum, count.

        >>> api.aggregate("weather-app", "readings", ["avg", "max"], field="temperature")
        {'field': 'temperature', 'aggregations': {'avg': 22.3, 'max': 31.0}}
        >>> api.aggregate("weather-app", "readings", ["avg"], field="temperature",
        ...               location="London")
        """
        self._require_username()
        params = {"aggregate": ",".join(aggregates), **filters}
        if field:
            params["field"] = field
        return self._request("GET", f"v1/{self.username}/{app}/{endpoint}/",
                             params=params)

    def export_csv(self, app, endpoint, **filters):
        """Download CSV data from a collection endpoint (requires username).

        Returns the raw CSV string.

        >>> csv_data = api.export_csv("weather-app", "readings")
        >>> csv_data = api.export_csv("weather-app", "readings", temperature__gte=20)
        """
        self._require_username()
        params = {"format": "csv", **filters}
        url = self._url(f"v1/{self.username}/{app}/{endpoint}/")
        resp = self.session.get(url, params=params, timeout=self.timeout)
        if resp.status_code >= 400:
            msg = self._error_message(resp, f"Request failed (status {resp.status_code}).")
            if resp.status_code == 429:
                raise RateLimitError(msg, status_code=resp.status_code, response=resp)
            raise MeowError(msg, status_code=resp.status_code, response=resp)
        return resp.text

    # ── Records (write) ─────────────────────────────────────────────

    def send(self, app, endpoint, data):
        """Send a new record to an endpoint. This is the main thing!

        >>> api.send("weather-app", "readings", {"temperature": 22.5})
        """
        return self._request(
            "POST",
            f"apps/{app}/endpoints/{endpoint}/records/",
            json={"data": data},
        )

    def update(self, app, endpoint, record_id, data):
        """Update an existing record.

        >>> api.update("weather-app", "readings", "abc-123", {"temperature": 23.0})
        """
        return self._request(
            "PATCH",
            f"apps/{app}/endpoints/{endpoint}/records/{record_id}/",
            json={"data": data},
        )

    def delete_record(self, app, endpoint, record_id):
        """Delete a record.

        >>> api.delete_record("weather-app", "readings", "abc-123")
        """
        return self._request(
            "DELETE",
            f"apps/{app}/endpoints/{endpoint}/records/{record_id}/",
        )

    # ── Records (list / paginate) ───────────────────────────────────

    def records(self, app, endpoint, limit=25, offset=0):
        """List records for an endpoint (paginated). Requires API key.

        Works for both public and private endpoints.

        >>> page = api.records("weather-app", "readings", limit=10)
        """
        return self._request(
            "GET",
            f"apps/{app}/endpoints/{endpoint}/records/",
            params={"limit": limit, "offset": offset},
        )

    def all_records(self, app, endpoint):
        """Fetch every record from an endpoint (auto-paginates).

        >>> all_data = api.all_records("weather-app", "readings")
        """
        records = []
        offset = 0
        limit = 100
        while True:
            page = self.records(app, endpoint, limit=limit, offset=offset)
            results = page.get("results", [])
            records.extend(results)
            if not page.get("next"):
                break
            offset += limit
        return records

    # ── Apps ────────────────────────────────────────────────────────

    def apps(self):
        """List your apps.

        >>> my_apps = api.apps()
        """
        return self._request("GET", "apps/")

    def get_app(self, slug):
        """Get details for a single app.

        >>> app = api.get_app("weather-app")
        """
        return self._request("GET", f"apps/{slug}/")

    def create_app(self, name, slug, description="", is_public=True):
        """Create a new app.

        >>> api.create_app("Weather App", "weather-app")
        """
        return self._request("POST", "apps/", json={
            "name": name,
            "slug": slug,
            "description": description,
            "is_public": is_public,
        })

    def update_app(self, slug, **kwargs):
        """Update an app. Pass only the fields you want to change.

        >>> api.update_app("weather-app", name="My Weather App")
        >>> api.update_app("weather-app", is_public=False, description="Private app")
        """
        return self._request("PATCH", f"apps/{slug}/", json=kwargs)

    def delete_app(self, slug):
        """Delete an app.

        >>> api.delete_app("weather-app")
        """
        return self._request("DELETE", f"apps/{slug}/")

    # ── Endpoints ───────────────────────────────────────────────────

    def endpoints(self, app):
        """List endpoints in an app.

        >>> api.endpoints("weather-app")
        """
        return self._request("GET", f"apps/{app}/endpoints/")

    def get_endpoint(self, app, endpoint):
        """Get details for a single endpoint.

        >>> ep = api.get_endpoint("weather-app", "readings")
        """
        return self._request("GET", f"apps/{app}/endpoints/{endpoint}/")

    def create_endpoint(self, app, name, slug, endpoint_type="collection",
                        description="", is_public=True):
        """Create a new endpoint in an app.

        >>> api.create_endpoint("weather-app", "Readings", "readings", "collection")
        """
        return self._request("POST", f"apps/{app}/endpoints/", json={
            "name": name,
            "slug": slug,
            "endpoint_type": endpoint_type,
            "description": description,
            "is_public": is_public,
        })

    def update_endpoint(self, app, endpoint, **kwargs):
        """Update an endpoint. Pass only the fields you want to change.

        >>> api.update_endpoint("weather-app", "readings", name="Sensor Readings")
        >>> api.update_endpoint("weather-app", "readings", is_public=False)
        """
        return self._request("PATCH", f"apps/{app}/endpoints/{endpoint}/", json=kwargs)

    def delete_endpoint(self, app, endpoint):
        """Delete an endpoint.

        >>> api.delete_endpoint("weather-app", "readings")
        """
        return self._request("DELETE", f"apps/{app}/endpoints/{endpoint}/")

    # ── Proxy Config ─────────────────────────────────────────────────

    def get_proxy(self, app, endpoint):
        """Get the proxy configuration for a proxy endpoint.

        >>> config = api.get_proxy("weather-app", "external-api")
        """
        return self._request("GET", f"apps/{app}/endpoints/{endpoint}/proxy/")

    def set_proxy(self, app, endpoint, upstream_url, method="GET",
                  headers=None, query_params=None, body_template=None,
                  jmespath_transform=None):
        """Set the proxy configuration for a proxy endpoint.

        >>> api.set_proxy("weather-app", "external-api",
        ...     "https://api.example.com/data", method="GET")
        """
        body = {"upstream_url": upstream_url, "method": method}
        if headers is not None:
            body["headers"] = headers
        if query_params is not None:
            body["query_params"] = query_params
        if body_template is not None:
            body["body_template"] = body_template
        if jmespath_transform is not None:
            body["jmespath_transform"] = jmespath_transform
        return self._request("PUT", f"apps/{app}/endpoints/{endpoint}/proxy/", json=body)

    # ── Encryption ────────────────────────────────────────────────

    def get_encryption(self, app, endpoint):
        """Get encryption status for an endpoint.

        >>> info = api.get_encryption("weather-app", "readings")
        >>> info["encryption_enabled"]
        True
        """
        return self._request(
            "GET",
            f"apps/{app}/endpoints/{endpoint}/encryption/",
        )

    def enable_encryption(self, app, endpoint):
        """Generate an encryption key and enable encryption.

        Returns the key — save it! It will only be shown once.

        >>> result = api.enable_encryption("weather-app", "readings")
        >>> result["key"]   # save this!
        'your-secret-key-here'
        """
        return self._request(
            "POST",
            f"apps/{app}/endpoints/{endpoint}/encryption/",
        )

    def disable_encryption(self, app, endpoint):
        """Disable encryption and delete the key.

        >>> api.disable_encryption("weather-app", "readings")
        """
        return self._request(
            "DELETE",
            f"apps/{app}/endpoints/{endpoint}/encryption/",
        )

    # ── Request Logs ──────────────────────────────────────────────

    def request_logs(self, app, endpoint):
        """Get the latest request logs for an endpoint (up to 50).

        >>> logs = api.request_logs("weather-app", "readings")
        >>> logs[0]["status_code"]
        200
        """
        return self._request(
            "GET",
            f"apps/{app}/endpoints/{endpoint}/logs/",
        )

    # ── Webhooks ─────────────────────────────────────────────────

    def webhooks(self, app, endpoint):
        """List webhooks for an endpoint.

        >>> hooks = api.webhooks("weather-app", "readings")
        """
        return self._request(
            "GET",
            f"apps/{app}/endpoints/{endpoint}/webhooks/",
        )

    def get_webhook(self, app, endpoint, webhook_uuid):
        """Get a single webhook.

        >>> hook = api.get_webhook("weather-app", "readings", "uuid-123")
        """
        return self._request(
            "GET",
            f"apps/{app}/endpoints/{endpoint}/webhooks/{webhook_uuid}/",
        )

    def create_webhook(self, app, endpoint, target_url, events,
                       secret=None, is_active=True):
        """Create a webhook on an endpoint.

        Events: record.created, record.updated, record.deleted, payload.updated.

        >>> api.create_webhook("weather-app", "readings",
        ...     "https://example.com/hook", ["record.created"])
        """
        body = {
            "target_url": target_url,
            "events": events,
            "is_active": is_active,
        }
        if secret is not None:
            body["secret"] = secret
        return self._request(
            "POST",
            f"apps/{app}/endpoints/{endpoint}/webhooks/",
            json=body,
        )

    def update_webhook(self, app, endpoint, webhook_uuid, **kwargs):
        """Update a webhook. Pass only the fields you want to change.

        >>> api.update_webhook("weather-app", "readings", "uuid-123",
        ...     events=["record.created", "record.deleted"])
        """
        return self._request(
            "PATCH",
            f"apps/{app}/endpoints/{endpoint}/webhooks/{webhook_uuid}/",
            json=kwargs,
        )

    def delete_webhook(self, app, endpoint, webhook_uuid):
        """Delete a webhook.

        >>> api.delete_webhook("weather-app", "readings", "uuid-123")
        """
        return self._request(
            "DELETE",
            f"apps/{app}/endpoints/{endpoint}/webhooks/{webhook_uuid}/",
        )

    # ── Static Payload ──────────────────────────────────────────────

    def get_payload(self, app, endpoint):
        """Get the static payload for an endpoint.

        >>> api.get_payload("weather-app", "status")
        """
        return self._request("GET", f"apps/{app}/endpoints/{endpoint}/payload/")

    def set_payload(self, app, endpoint, data):
        """Set the static payload for an endpoint.

        >>> api.set_payload("weather-app", "status", {"open": True})
        """
        return self._request("PUT", f"apps/{app}/endpoints/{endpoint}/payload/", json={
            "data": data,
        })

    # ── Collection Fields (schema) ───────────────────────────────

    def fields(self, app, endpoint):
        """List fields for a collection endpoint.

        >>> schema = api.fields("weather-app", "readings")
        """
        return self._request("GET", f"apps/{app}/endpoints/{endpoint}/fields/")

    def create_field(self, app, endpoint, name, label, field_type, **kwargs):
        """Create a new field on a collection endpoint.

        Field types: text, textarea, number, boolean, date, datetime,
        time, color, email, url, select, rating, image_url, json.

        >>> api.create_field("weather-app", "readings", "temp", "Temperature", "number")
        >>> api.create_field("weather-app", "readings", "color", "Color", "color",
        ...                  required=True, options={"format": "hex"})
        """
        body = {"name": name, "label": label, "field_type": field_type}
        body.update(kwargs)
        return self._request("POST", f"apps/{app}/endpoints/{endpoint}/fields/", json=body)

    def update_field(self, app, endpoint, field_uuid, **kwargs):
        """Update a field. Pass only the fields you want to change.

        >>> api.update_field("weather-app", "readings", "uuid-123", label="Temp (C)")
        """
        return self._request(
            "PATCH",
            f"apps/{app}/endpoints/{endpoint}/fields/{field_uuid}/",
            json=kwargs,
        )

    def delete_field(self, app, endpoint, field_uuid):
        """Delete a field from a collection endpoint.

        >>> api.delete_field("weather-app", "readings", "uuid-123")
        """
        return self._request(
            "DELETE",
            f"apps/{app}/endpoints/{endpoint}/fields/{field_uuid}/",
        )

    # ── Field Types (reference) ────────────────────────────────────

    def field_types(self):
        """List available field types for collection endpoints.

        >>> types = api.field_types()
        """
        return self._request("GET", "field-types/")

    # ── Dashboards (Control Panels) ───────────────────────────────

    def dashboards(self):
        """List your dashboards.

        >>> panels = api.dashboards()
        """
        return self._request("GET", "dashboards/")

    def get_dashboard(self, slug):
        """Get details for a single dashboard.

        >>> panel = api.get_dashboard("my-room")
        """
        return self._request("GET", f"dashboards/{slug}/")

    def create_dashboard(self, name, slug, description=""):
        """Create a new dashboard.

        >>> api.create_dashboard("My Room", "my-room")
        """
        return self._request("POST", "dashboards/", json={
            "name": name,
            "slug": slug,
            "description": description,
        })

    def update_dashboard(self, slug, **kwargs):
        """Update a dashboard. Pass only the fields you want to change.

        >>> api.update_dashboard("my-room", name="Living Room")
        """
        return self._request("PATCH", f"dashboards/{slug}/", json=kwargs)

    def delete_dashboard(self, slug):
        """Delete a dashboard.

        >>> api.delete_dashboard("old-panel")
        """
        return self._request("DELETE", f"dashboards/{slug}/")

    # ── Dashboard Widgets ─────────────────────────────────────────

    def dashboard_widgets(self, dashboard):
        """List widgets in a dashboard.

        >>> widgets = api.dashboard_widgets("my-room")
        """
        return self._request("GET", f"dashboards/{dashboard}/widgets/")

    def create_dashboard_widget(self, dashboard, endpoint_id, key_path,
                                widget_type, label, **kwargs):
        """Add a widget to a dashboard.

        Widget types: toggle, color, slider, number, text, select, display.

        >>> api.create_dashboard_widget("my-room", "endpoint-uuid",
        ...     "lights_on", "toggle", "Lights On")
        """
        body = {
            "endpoint_id": endpoint_id,
            "key_path": key_path,
            "widget_type": widget_type,
            "label": label,
        }
        body.update(kwargs)
        return self._request("POST", f"dashboards/{dashboard}/widgets/", json=body)

    def update_dashboard_widget(self, dashboard, widget_uuid, **kwargs):
        """Update a widget. Pass only the fields you want to change.

        Accepts: label, widget_type, key_path, config, sort_order.

        >>> api.update_dashboard_widget("my-room", "widget-uuid-123",
        ...     label="Bedroom Lights", sort_order=2)
        """
        return self._request(
            "PATCH",
            f"dashboards/{dashboard}/widgets/{widget_uuid}/",
            json=kwargs,
        )

    def delete_dashboard_widget(self, dashboard, widget_uuid):
        """Remove a widget from a dashboard.

        >>> api.delete_dashboard_widget("my-room", "widget-uuid-123")
        """
        return self._request(
            "DELETE",
            f"dashboards/{dashboard}/widgets/{widget_uuid}/",
        )

    # ── Dashboard Data & Patch ────────────────────────────────────

    def dashboard_data(self, dashboard):
        """Get aggregated data for all widgets in a dashboard.

        Returns dashboard info, widgets, and current values from all endpoints.

        >>> data = api.dashboard_data("my-room")
        >>> data["widgets"]       # list of widgets
        >>> data["endpoints"]     # dict of endpoint data keyed by UUID
        """
        return self._request("GET", f"dashboards/{dashboard}/data/")

    def dashboard_patch(self, dashboard, endpoint_uuid, key_path, value):
        """Update a single value through a dashboard widget.

        >>> api.dashboard_patch("my-room", "endpoint-uuid", "lights_on", True)
        """
        return self._request("PATCH", f"dashboards/{dashboard}/patch/", json={
            "endpoint_uuid": endpoint_uuid,
            "key_path": key_path,
            "value": value,
        })

    # ── App-Scoped API Keys ──────────────────────────────────────────

    def app_keys(self, app):
        """List active API keys scoped to an app.

        >>> keys = api.app_keys("weather-app")
        """
        return self._request("GET", f"apps/{app}/keys/")

    def create_app_key(self, app):
        """Create a new API key scoped to an app. Save the returned key — shown only once!

        >>> result = api.create_app_key("weather-app")
        >>> result["key"]  # save this!
        """
        return self._request("POST", f"apps/{app}/keys/")

    def delete_app_key(self, app, key_uuid):
        """Deactivate an app-scoped API key.

        >>> api.delete_app_key("weather-app", "key-uuid-123")
        """
        return self._request("DELETE", f"apps/{app}/keys/{key_uuid}/")

    # ── Platform Tokens ─────────────────────────────────────────

    def platform_tokens(self):
        """List your platform tokens.

        >>> tokens = api.platform_tokens()
        """
        return self._request("GET", "auth/tokens/")

    def create_platform_token(self, name):
        """Create a new platform token. Save the returned key — shown only once!

        >>> result = api.create_platform_token("my-pi")
        >>> result["key"]  # save this!
        """
        return self._request("POST", "auth/tokens/", json={"name": name})

    def revoke_platform_token(self, uuid):
        """Revoke a platform token.

        >>> api.revoke_platform_token("token-uuid-123")
        """
        return self._request("DELETE", f"auth/tokens/{uuid}/")

    # ── Billing ──────────────────────────────────────────────────

    def billing_status(self):
        """Get billing status, plan info, and usage limits.

        >>> status = api.billing_status()
        >>> status["plan"]
        'free'
        """
        return self._request("GET", "billing/status/")

    # ── Public Dashboard ─────────────────────────────────────────

    def public_dashboard(self, share_token):
        """Get a public shared dashboard by its share token.

        No API key required — anyone with the token can read the data.

        >>> data = api.public_dashboard("abc123token")
        >>> data["dashboard"]["name"]
        'My Room'
        """
        return self._request("GET", f"v1/dashboards/{share_token}/")
