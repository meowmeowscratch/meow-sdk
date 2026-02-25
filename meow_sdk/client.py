import requests

from .exceptions import AuthError, MeowError, NotFoundError, RateLimitError, ValidationError


class Meow:
    """Talk to the meow meow scratch API.

    Args:
        base_url: Where the API lives. Defaults to "https://meowmeowscratch.com".
        username: Your meow meow scratch username (used for public reads).
        api_key:  Your API key. Needed for writing data, managing apps, and reading private endpoints.
    """

    def __init__(self, base_url="https://meowmeowscratch.com", username=None, api_key=None):
        self.base_url = base_url.rstrip("/")
        self.username = username
        self.session = requests.Session()
        if api_key:
            self.session.headers["Authorization"] = f"Bearer {api_key}"

    # ── Internal helpers ────────────────────────────────────────────

    def _url(self, path):
        return f"{self.base_url}/api/{path.lstrip('/')}"

    def _request(self, method, path, **kwargs):
        url = self._url(path)
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

    def get(self, app, endpoint):
        """Read data from a public endpoint (requires username).

        For private endpoints, use records() with an API key instead.

        >>> api = Meow(username="jake")
        >>> data = api.get("weather-app", "current-temp")
        """
        self._require_username()
        return self._request("GET", f"v1/{self.username}/{app}/{endpoint}/")

    def get_record(self, app, endpoint, record_id):
        """Read a single record by ID.

        >>> record = api.get_record("weather-app", "readings", "abc-123")
        """
        self._require_username()
        return self._request("GET", f"v1/{self.username}/{app}/{endpoint}/{record_id}/")

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
