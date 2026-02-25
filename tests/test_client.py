"""Tests for the meow-sdk client.

Uses unittest.mock to patch requests.Session so no real HTTP calls are made.
"""

import json
import unittest
from unittest.mock import MagicMock, patch

from meow_sdk import Meow, AuthError, MeowError, NotFoundError, RateLimitError, ValidationError


def _mock_response(status_code=200, json_data=None, text=""):
    """Create a mock requests.Response."""
    resp = MagicMock()
    resp.status_code = status_code
    resp.text = text or json.dumps(json_data or {})
    resp.json.return_value = json_data if json_data is not None else {}
    return resp


class TestClientInit(unittest.TestCase):
    """Constructor and configuration."""

    def test_default_base_url(self):
        api = Meow()
        self.assertEqual(api.base_url, "https://meowmeowscratch.com")

    def test_base_url_trailing_slash_stripped(self):
        api = Meow("http://example.com/")
        self.assertEqual(api.base_url, "http://example.com")

    def test_base_url_no_trailing_slash(self):
        api = Meow("http://example.com")
        self.assertEqual(api.base_url, "http://example.com")

    def test_username_stored(self):
        api = Meow("http://example.com", username="jake")
        self.assertEqual(api.username, "jake")

    def test_username_defaults_to_none(self):
        api = Meow("http://example.com")
        self.assertIsNone(api.username)

    def test_api_key_sets_auth_header(self):
        api = Meow("http://example.com", api_key="test-key-123")
        self.assertEqual(
            api.session.headers["Authorization"],
            "Bearer test-key-123",
        )

    def test_no_api_key_no_auth_header(self):
        api = Meow("http://example.com")
        self.assertNotIn("Authorization", api.session.headers)

    def test_all_params(self):
        api = Meow("http://example.com/", username="jake", api_key="key-abc")
        self.assertEqual(api.base_url, "http://example.com")
        self.assertEqual(api.username, "jake")
        self.assertEqual(api.session.headers["Authorization"], "Bearer key-abc")


class TestURLBuilding(unittest.TestCase):
    """Internal _url helper."""

    def test_url_construction(self):
        api = Meow("http://example.com")
        self.assertEqual(api._url("apps/"), "http://example.com/api/apps/")

    def test_url_strips_leading_slash(self):
        api = Meow("http://example.com")
        self.assertEqual(api._url("/apps/"), "http://example.com/api/apps/")


class TestErrorHandling(unittest.TestCase):
    """HTTP error status codes raise the right exceptions."""

    def setUp(self):
        self.api = Meow("http://example.com", username="jake", api_key="key")

    @patch.object(Meow, "_request")
    def _call_get(self, mock_request):
        """Helper — not a test itself."""
        pass

    def test_401_raises_auth_error(self):
        with patch.object(self.api.session, "request") as mock:
            mock.return_value = _mock_response(
                401, {"detail": "Invalid token"}
            )
            with self.assertRaises(AuthError) as ctx:
                self.api.apps()
            self.assertEqual(ctx.exception.status_code, 401)

    def test_403_raises_auth_error(self):
        with patch.object(self.api.session, "request") as mock:
            mock.return_value = _mock_response(
                403, {"detail": "Permission denied"}
            )
            with self.assertRaises(AuthError) as ctx:
                self.api.apps()
            self.assertEqual(ctx.exception.status_code, 403)

    def test_404_raises_not_found_error(self):
        with patch.object(self.api.session, "request") as mock:
            mock.return_value = _mock_response(
                404, {"error": "Endpoint not found."}
            )
            with self.assertRaises(NotFoundError) as ctx:
                self.api.get("bad-app", "bad-ep")
            self.assertEqual(ctx.exception.status_code, 404)
            self.assertIn("not found", str(ctx.exception).lower())

    def test_400_raises_validation_error(self):
        with patch.object(self.api.session, "request") as mock:
            mock.return_value = _mock_response(
                400, {"slug": ["This field is required."]}
            )
            with self.assertRaises(ValidationError) as ctx:
                self.api.create_app("Test", "")
            self.assertEqual(ctx.exception.status_code, 400)

    def test_429_raises_rate_limit_error(self):
        with patch.object(self.api.session, "request") as mock:
            mock.return_value = _mock_response(
                429, {"detail": "Request was throttled."}
            )
            with self.assertRaises(RateLimitError) as ctx:
                self.api.get("app", "ep")
            self.assertEqual(ctx.exception.status_code, 429)

    def test_500_raises_meow_error(self):
        with patch.object(self.api.session, "request") as mock:
            mock.return_value = _mock_response(500, {"detail": "Server error"})
            with self.assertRaises(MeowError) as ctx:
                self.api.apps()
            self.assertEqual(ctx.exception.status_code, 500)

    def test_204_returns_none(self):
        with patch.object(self.api.session, "request") as mock:
            mock.return_value = _mock_response(204)
            result = self.api.delete_app("some-app")
            self.assertIsNone(result)

    def test_error_message_from_detail(self):
        resp = _mock_response(400, {"detail": "Bad slug"})
        msg = Meow._error_message(resp, "fallback")
        self.assertEqual(msg, "Bad slug")

    def test_error_message_from_error_key(self):
        resp = _mock_response(404, {"error": "Not found"})
        msg = Meow._error_message(resp, "fallback")
        self.assertEqual(msg, "Not found")

    def test_error_message_fallback_on_non_json(self):
        resp = MagicMock()
        resp.json.side_effect = ValueError("no json")
        msg = Meow._error_message(resp, "fallback msg")
        self.assertEqual(msg, "fallback msg")

    def test_error_has_response_attribute(self):
        with patch.object(self.api.session, "request") as mock:
            mock_resp = _mock_response(404, {"error": "gone"})
            mock.return_value = mock_resp
            with self.assertRaises(NotFoundError) as ctx:
                self.api.get("x", "y")
            self.assertIs(ctx.exception.response, mock_resp)


class TestRequireUsername(unittest.TestCase):
    """Consumer methods require username."""

    def test_get_without_username_raises(self):
        api = Meow("http://example.com")
        with self.assertRaises(MeowError) as ctx:
            api.get("app", "endpoint")
        self.assertIn("Username is required", str(ctx.exception))
        self.assertIn("Meow(username=", str(ctx.exception))

    def test_get_record_without_username_raises(self):
        api = Meow("http://example.com")
        with self.assertRaises(MeowError):
            api.get_record("app", "endpoint", "uuid-123")

    def test_get_with_username_works(self):
        api = Meow("http://example.com", username="jake")
        with patch.object(api.session, "request") as mock:
            mock.return_value = _mock_response(200, {"temp": 22})
            result = api.get("weather", "temp")
            self.assertEqual(result, {"temp": 22})


class TestConsumerAPI(unittest.TestCase):
    """Public read methods."""

    def setUp(self):
        self.api = Meow("http://example.com", username="jake")

    def test_get_calls_correct_url(self):
        with patch.object(self.api.session, "request") as mock:
            mock.return_value = _mock_response(200, {"data": "ok"})
            self.api.get("my-app", "my-endpoint")
            mock.assert_called_once_with(
                "GET",
                "http://example.com/api/v1/jake/my-app/my-endpoint/",
            )

    def test_get_returns_json(self):
        with patch.object(self.api.session, "request") as mock:
            mock.return_value = _mock_response(200, {"temp": 22.5, "humid": 65})
            result = self.api.get("weather", "current")
            self.assertEqual(result["temp"], 22.5)
            self.assertEqual(result["humid"], 65)

    def test_get_record_calls_correct_url(self):
        with patch.object(self.api.session, "request") as mock:
            mock.return_value = _mock_response(200, {"uuid": "abc"})
            self.api.get_record("my-app", "readings", "abc-uuid")
            mock.assert_called_once_with(
                "GET",
                "http://example.com/api/v1/jake/my-app/readings/abc-uuid/",
            )

    def test_get_record_returns_data(self):
        with patch.object(self.api.session, "request") as mock:
            mock.return_value = _mock_response(200, {
                "uuid": "abc",
                "data": {"temperature": 22},
            })
            result = self.api.get_record("app", "ep", "abc")
            self.assertEqual(result["data"]["temperature"], 22)


class TestRecordWrite(unittest.TestCase):
    """Record CRUD methods (require API key)."""

    def setUp(self):
        self.api = Meow("http://example.com", api_key="test-key")

    def test_send_posts_to_correct_url(self):
        with patch.object(self.api.session, "request") as mock:
            mock.return_value = _mock_response(201, {"uuid": "new-id"})
            self.api.send("my-app", "readings", {"temp": 22})
            call_args = mock.call_args
            self.assertEqual(call_args[0][0], "POST")
            self.assertIn("my-app/endpoints/readings/records/", call_args[0][1])

    def test_send_passes_data_wrapped(self):
        with patch.object(self.api.session, "request") as mock:
            mock.return_value = _mock_response(201, {"uuid": "id"})
            self.api.send("app", "ep", {"value": 42})
            call_kwargs = mock.call_args[1]
            self.assertEqual(call_kwargs["json"], {"data": {"value": 42}})

    def test_send_returns_created_record(self):
        with patch.object(self.api.session, "request") as mock:
            mock.return_value = _mock_response(201, {
                "uuid": "new-uuid",
                "data": {"value": 42},
            })
            result = self.api.send("app", "ep", {"value": 42})
            self.assertEqual(result["uuid"], "new-uuid")

    def test_update_patches_correct_url(self):
        with patch.object(self.api.session, "request") as mock:
            mock.return_value = _mock_response(200, {"uuid": "id"})
            self.api.update("app", "ep", "rec-id", {"value": 99})
            call_args = mock.call_args
            self.assertEqual(call_args[0][0], "PATCH")
            self.assertIn("records/rec-id/", call_args[0][1])

    def test_update_passes_data_wrapped(self):
        with patch.object(self.api.session, "request") as mock:
            mock.return_value = _mock_response(200, {})
            self.api.update("app", "ep", "id", {"x": 1})
            call_kwargs = mock.call_args[1]
            self.assertEqual(call_kwargs["json"], {"data": {"x": 1}})

    def test_delete_record_calls_delete(self):
        with patch.object(self.api.session, "request") as mock:
            mock.return_value = _mock_response(204)
            result = self.api.delete_record("app", "ep", "rec-id")
            self.assertIsNone(result)
            call_args = mock.call_args
            self.assertEqual(call_args[0][0], "DELETE")
            self.assertIn("records/rec-id/", call_args[0][1])


class TestRecordList(unittest.TestCase):
    """Pagination methods."""

    def setUp(self):
        self.api = Meow("http://example.com", api_key="key")

    def test_records_passes_pagination_params(self):
        with patch.object(self.api.session, "request") as mock:
            mock.return_value = _mock_response(200, {
                "count": 50, "results": [], "next": None,
            })
            self.api.records("app", "ep", limit=10, offset=20)
            call_kwargs = mock.call_args[1]
            self.assertEqual(call_kwargs["params"], {"limit": 10, "offset": 20})

    def test_records_defaults(self):
        with patch.object(self.api.session, "request") as mock:
            mock.return_value = _mock_response(200, {
                "count": 0, "results": [], "next": None,
            })
            self.api.records("app", "ep")
            call_kwargs = mock.call_args[1]
            self.assertEqual(call_kwargs["params"], {"limit": 25, "offset": 0})

    def test_all_records_single_page(self):
        with patch.object(self.api.session, "request") as mock:
            mock.return_value = _mock_response(200, {
                "count": 2,
                "results": [{"uuid": "a"}, {"uuid": "b"}],
                "next": None,
            })
            result = self.api.all_records("app", "ep")
            self.assertEqual(len(result), 2)
            self.assertEqual(mock.call_count, 1)

    def test_all_records_multi_page(self):
        with patch.object(self.api.session, "request") as mock:
            page1 = _mock_response(200, {
                "count": 3,
                "results": [{"uuid": "a"}, {"uuid": "b"}],
                "next": "http://example.com/api/apps/app/endpoints/ep/records/?offset=2",
            })
            page2 = _mock_response(200, {
                "count": 3,
                "results": [{"uuid": "c"}],
                "next": None,
            })
            mock.side_effect = [page1, page2]
            result = self.api.all_records("app", "ep")
            self.assertEqual(len(result), 3)
            self.assertEqual(mock.call_count, 2)

    def test_all_records_empty(self):
        with patch.object(self.api.session, "request") as mock:
            mock.return_value = _mock_response(200, {
                "count": 0, "results": [], "next": None,
            })
            result = self.api.all_records("app", "ep")
            self.assertEqual(result, [])


class TestAppManagement(unittest.TestCase):
    """App CRUD."""

    def setUp(self):
        self.api = Meow("http://example.com", api_key="key")

    def test_apps_calls_get(self):
        with patch.object(self.api.session, "request") as mock:
            mock.return_value = _mock_response(200, [])
            self.api.apps()
            mock.assert_called_once_with(
                "GET", "http://example.com/api/apps/"
            )

    def test_create_app_posts_data(self):
        with patch.object(self.api.session, "request") as mock:
            mock.return_value = _mock_response(201, {"slug": "new-app"})
            self.api.create_app("New App", "new-app", description="desc")
            call_args = mock.call_args
            self.assertEqual(call_args[0][0], "POST")
            body = call_args[1]["json"]
            self.assertEqual(body["name"], "New App")
            self.assertEqual(body["slug"], "new-app")
            self.assertEqual(body["description"], "desc")
            self.assertTrue(body["is_public"])

    def test_create_app_private(self):
        with patch.object(self.api.session, "request") as mock:
            mock.return_value = _mock_response(201, {})
            self.api.create_app("Secret", "secret", is_public=False)
            body = mock.call_args[1]["json"]
            self.assertFalse(body["is_public"])

    def test_get_app(self):
        with patch.object(self.api.session, "request") as mock:
            mock.return_value = _mock_response(200, {
                "slug": "my-app", "name": "My App", "endpoint_count": 3,
            })
            result = self.api.get_app("my-app")
            mock.assert_called_once_with(
                "GET", "http://example.com/api/apps/my-app/"
            )
            self.assertEqual(result["endpoint_count"], 3)

    def test_update_app(self):
        with patch.object(self.api.session, "request") as mock:
            mock.return_value = _mock_response(200, {"name": "New Name"})
            self.api.update_app("my-app", name="New Name", description="updated")
            call_args = mock.call_args
            self.assertEqual(call_args[0][0], "PATCH")
            self.assertIn("apps/my-app/", call_args[0][1])
            body = call_args[1]["json"]
            self.assertEqual(body["name"], "New Name")
            self.assertEqual(body["description"], "updated")

    def test_update_app_partial(self):
        with patch.object(self.api.session, "request") as mock:
            mock.return_value = _mock_response(200, {})
            self.api.update_app("my-app", is_public=False)
            body = mock.call_args[1]["json"]
            self.assertFalse(body["is_public"])
            self.assertNotIn("name", body)

    def test_delete_app_calls_delete(self):
        with patch.object(self.api.session, "request") as mock:
            mock.return_value = _mock_response(204)
            self.api.delete_app("old-app")
            mock.assert_called_once_with(
                "DELETE", "http://example.com/api/apps/old-app/"
            )


class TestEndpointManagement(unittest.TestCase):
    """Endpoint CRUD."""

    def setUp(self):
        self.api = Meow("http://example.com", api_key="key")

    def test_endpoints_list(self):
        with patch.object(self.api.session, "request") as mock:
            mock.return_value = _mock_response(200, [])
            self.api.endpoints("my-app")
            mock.assert_called_once_with(
                "GET", "http://example.com/api/apps/my-app/endpoints/"
            )

    def test_create_endpoint_defaults(self):
        with patch.object(self.api.session, "request") as mock:
            mock.return_value = _mock_response(201, {})
            self.api.create_endpoint("app", "Readings", "readings")
            body = mock.call_args[1]["json"]
            self.assertEqual(body["endpoint_type"], "collection")
            self.assertTrue(body["is_public"])

    def test_create_endpoint_static(self):
        with patch.object(self.api.session, "request") as mock:
            mock.return_value = _mock_response(201, {})
            self.api.create_endpoint("app", "Status", "status", endpoint_type="static")
            body = mock.call_args[1]["json"]
            self.assertEqual(body["endpoint_type"], "static")

    def test_get_endpoint(self):
        with patch.object(self.api.session, "request") as mock:
            mock.return_value = _mock_response(200, {
                "slug": "readings", "record_count": 42,
            })
            result = self.api.get_endpoint("app", "readings")
            mock.assert_called_once_with(
                "GET", "http://example.com/api/apps/app/endpoints/readings/"
            )
            self.assertEqual(result["record_count"], 42)

    def test_update_endpoint(self):
        with patch.object(self.api.session, "request") as mock:
            mock.return_value = _mock_response(200, {"name": "Updated"})
            self.api.update_endpoint("app", "ep", name="Updated", is_public=False)
            call_args = mock.call_args
            self.assertEqual(call_args[0][0], "PATCH")
            self.assertIn("apps/app/endpoints/ep/", call_args[0][1])
            body = call_args[1]["json"]
            self.assertEqual(body["name"], "Updated")
            self.assertFalse(body["is_public"])

    def test_delete_endpoint(self):
        with patch.object(self.api.session, "request") as mock:
            mock.return_value = _mock_response(204)
            self.api.delete_endpoint("app", "ep")
            mock.assert_called_once_with(
                "DELETE", "http://example.com/api/apps/app/endpoints/ep/"
            )


class TestStaticPayload(unittest.TestCase):
    """Static payload methods."""

    def setUp(self):
        self.api = Meow("http://example.com", api_key="key")

    def test_get_payload(self):
        with patch.object(self.api.session, "request") as mock:
            mock.return_value = _mock_response(200, {
                "data": {"open": True},
                "updated_at": "2024-01-01T00:00:00Z",
            })
            result = self.api.get_payload("app", "status")
            self.assertTrue(result["data"]["open"])

    def test_set_payload_puts_data(self):
        with patch.object(self.api.session, "request") as mock:
            mock.return_value = _mock_response(200, {"data": {"x": 1}})
            self.api.set_payload("app", "status", {"x": 1})
            call_args = mock.call_args
            self.assertEqual(call_args[0][0], "PUT")
            self.assertEqual(call_args[1]["json"], {"data": {"x": 1}})

    def test_get_payload_url(self):
        with patch.object(self.api.session, "request") as mock:
            mock.return_value = _mock_response(200, {})
            self.api.get_payload("weather", "info")
            mock.assert_called_once_with(
                "GET",
                "http://example.com/api/apps/weather/endpoints/info/payload/",
            )


class TestFieldManagement(unittest.TestCase):
    """Collection field CRUD."""

    def setUp(self):
        self.api = Meow("http://example.com", api_key="key")

    def test_list_fields(self):
        with patch.object(self.api.session, "request") as mock:
            mock.return_value = _mock_response(200, [
                {"uuid": "f1", "name": "temp", "field_type": "number"},
            ])
            result = self.api.fields("app", "readings")
            mock.assert_called_once_with(
                "GET",
                "http://example.com/api/apps/app/endpoints/readings/fields/",
            )
            self.assertEqual(len(result), 1)
            self.assertEqual(result[0]["name"], "temp")

    def test_create_field_basic(self):
        with patch.object(self.api.session, "request") as mock:
            mock.return_value = _mock_response(201, {"uuid": "new-f"})
            self.api.create_field("app", "readings", "temp", "Temperature", "number")
            call_args = mock.call_args
            self.assertEqual(call_args[0][0], "POST")
            body = call_args[1]["json"]
            self.assertEqual(body["name"], "temp")
            self.assertEqual(body["label"], "Temperature")
            self.assertEqual(body["field_type"], "number")

    def test_create_field_with_options(self):
        with patch.object(self.api.session, "request") as mock:
            mock.return_value = _mock_response(201, {})
            self.api.create_field(
                "app", "readings", "color", "Color", "color",
                required=True, options={"format": "hex"},
            )
            body = mock.call_args[1]["json"]
            self.assertTrue(body["required"])
            self.assertEqual(body["options"], {"format": "hex"})

    def test_update_field(self):
        with patch.object(self.api.session, "request") as mock:
            mock.return_value = _mock_response(200, {"label": "Temp (°C)"})
            self.api.update_field("app", "readings", "f-uuid", label="Temp (°C)")
            call_args = mock.call_args
            self.assertEqual(call_args[0][0], "PATCH")
            self.assertIn("fields/f-uuid/", call_args[0][1])
            self.assertEqual(call_args[1]["json"]["label"], "Temp (°C)")

    def test_delete_field(self):
        with patch.object(self.api.session, "request") as mock:
            mock.return_value = _mock_response(204)
            result = self.api.delete_field("app", "readings", "f-uuid")
            self.assertIsNone(result)
            call_args = mock.call_args
            self.assertEqual(call_args[0][0], "DELETE")
            self.assertIn("fields/f-uuid/", call_args[0][1])

    def test_create_field_url(self):
        with patch.object(self.api.session, "request") as mock:
            mock.return_value = _mock_response(201, {})
            self.api.create_field("my-app", "sensors", "x", "X", "text")
            mock.assert_called_once()
            url = mock.call_args[0][1]
            self.assertEqual(
                url,
                "http://example.com/api/apps/my-app/endpoints/sensors/fields/",
            )


class TestResponseParsing(unittest.TestCase):
    """Edge cases in response handling."""

    def setUp(self):
        self.api = Meow("http://example.com", username="jake")

    def test_non_json_response_returns_text(self):
        with patch.object(self.api.session, "request") as mock:
            resp = MagicMock()
            resp.status_code = 200
            resp.json.side_effect = ValueError("not json")
            resp.text = "plain text"
            mock.return_value = resp
            result = self.api.get("app", "ep")
            self.assertEqual(result, "plain text")

    def test_json_array_response(self):
        with patch.object(self.api.session, "request") as mock:
            mock.return_value = _mock_response(200, [{"a": 1}, {"b": 2}])
            result = self.api.get("app", "ep")
            self.assertEqual(len(result), 2)


class TestExceptions(unittest.TestCase):
    """Exception class behavior."""

    def test_meow_error_is_exception(self):
        self.assertTrue(issubclass(MeowError, Exception))

    def test_auth_error_is_meow_error(self):
        self.assertTrue(issubclass(AuthError, MeowError))

    def test_not_found_is_meow_error(self):
        self.assertTrue(issubclass(NotFoundError, MeowError))

    def test_validation_is_meow_error(self):
        self.assertTrue(issubclass(ValidationError, MeowError))

    def test_rate_limit_is_meow_error(self):
        self.assertTrue(issubclass(RateLimitError, MeowError))

    def test_exception_attributes(self):
        err = MeowError("test", status_code=418, response="resp")
        self.assertEqual(str(err), "test")
        self.assertEqual(err.status_code, 418)
        self.assertEqual(err.response, "resp")

    def test_exception_defaults(self):
        err = MeowError("oops")
        self.assertIsNone(err.status_code)
        self.assertIsNone(err.response)

    def test_catch_specific_before_generic(self):
        """AuthError can be caught as AuthError or MeowError."""
        try:
            raise AuthError("no key", status_code=401)
        except AuthError:
            pass  # caught specifically

        try:
            raise AuthError("no key", status_code=401)
        except MeowError:
            pass  # caught generically


class TestDashboardManagement(unittest.TestCase):
    """Dashboard CRUD."""

    def setUp(self):
        self.api = Meow("http://example.com", api_key="key")

    def test_dashboards_list(self):
        with patch.object(self.api.session, "request") as mock:
            mock.return_value = _mock_response(200, [])
            self.api.dashboards()
            mock.assert_called_once_with(
                "GET", "http://example.com/api/dashboards/"
            )

    def test_get_dashboard(self):
        with patch.object(self.api.session, "request") as mock:
            mock.return_value = _mock_response(200, {
                "slug": "my-room", "name": "My Room", "widget_count": 3,
            })
            result = self.api.get_dashboard("my-room")
            mock.assert_called_once_with(
                "GET", "http://example.com/api/dashboards/my-room/"
            )
            self.assertEqual(result["widget_count"], 3)

    def test_create_dashboard(self):
        with patch.object(self.api.session, "request") as mock:
            mock.return_value = _mock_response(201, {"slug": "my-room"})
            self.api.create_dashboard("My Room", "my-room", description="desc")
            call_args = mock.call_args
            self.assertEqual(call_args[0][0], "POST")
            body = call_args[1]["json"]
            self.assertEqual(body["name"], "My Room")
            self.assertEqual(body["slug"], "my-room")
            self.assertEqual(body["description"], "desc")

    def test_create_dashboard_minimal(self):
        with patch.object(self.api.session, "request") as mock:
            mock.return_value = _mock_response(201, {})
            self.api.create_dashboard("Test", "test")
            body = mock.call_args[1]["json"]
            self.assertEqual(body["description"], "")

    def test_update_dashboard(self):
        with patch.object(self.api.session, "request") as mock:
            mock.return_value = _mock_response(200, {"name": "Living Room"})
            self.api.update_dashboard("my-room", name="Living Room")
            call_args = mock.call_args
            self.assertEqual(call_args[0][0], "PATCH")
            self.assertIn("dashboards/my-room/", call_args[0][1])
            self.assertEqual(call_args[1]["json"]["name"], "Living Room")

    def test_update_dashboard_partial(self):
        with patch.object(self.api.session, "request") as mock:
            mock.return_value = _mock_response(200, {})
            self.api.update_dashboard("my-room", description="updated")
            body = mock.call_args[1]["json"]
            self.assertEqual(body["description"], "updated")
            self.assertNotIn("name", body)

    def test_delete_dashboard(self):
        with patch.object(self.api.session, "request") as mock:
            mock.return_value = _mock_response(204)
            self.api.delete_dashboard("old-panel")
            mock.assert_called_once_with(
                "DELETE", "http://example.com/api/dashboards/old-panel/"
            )


class TestDashboardWidgets(unittest.TestCase):
    """Dashboard widget CRUD."""

    def setUp(self):
        self.api = Meow("http://example.com", api_key="key")

    def test_list_widgets(self):
        with patch.object(self.api.session, "request") as mock:
            mock.return_value = _mock_response(200, [
                {"uuid": "w1", "label": "Lights", "widget_type": "toggle"},
            ])
            result = self.api.dashboard_widgets("my-room")
            mock.assert_called_once_with(
                "GET", "http://example.com/api/dashboards/my-room/widgets/"
            )
            self.assertEqual(len(result), 1)
            self.assertEqual(result[0]["label"], "Lights")

    def test_create_widget(self):
        with patch.object(self.api.session, "request") as mock:
            mock.return_value = _mock_response(201, {"uuid": "new-w"})
            self.api.create_dashboard_widget(
                "my-room", "ep-uuid", "lights_on", "toggle", "Lights On"
            )
            call_args = mock.call_args
            self.assertEqual(call_args[0][0], "POST")
            self.assertIn("dashboards/my-room/widgets/", call_args[0][1])
            body = call_args[1]["json"]
            self.assertEqual(body["endpoint_id"], "ep-uuid")
            self.assertEqual(body["key_path"], "lights_on")
            self.assertEqual(body["widget_type"], "toggle")
            self.assertEqual(body["label"], "Lights On")

    def test_create_widget_with_config(self):
        with patch.object(self.api.session, "request") as mock:
            mock.return_value = _mock_response(201, {})
            self.api.create_dashboard_widget(
                "my-room", "ep-uuid", "temp", "slider", "Temperature",
                config={"min": 0, "max": 100},
            )
            body = mock.call_args[1]["json"]
            self.assertEqual(body["config"], {"min": 0, "max": 100})

    def test_delete_widget(self):
        with patch.object(self.api.session, "request") as mock:
            mock.return_value = _mock_response(204)
            result = self.api.delete_dashboard_widget("my-room", "w-uuid")
            self.assertIsNone(result)
            mock.assert_called_once_with(
                "DELETE",
                "http://example.com/api/dashboards/my-room/widgets/w-uuid/",
            )


class TestDashboardData(unittest.TestCase):
    """Dashboard aggregate data and patching."""

    def setUp(self):
        self.api = Meow("http://example.com", api_key="key")

    def test_dashboard_data(self):
        with patch.object(self.api.session, "request") as mock:
            mock.return_value = _mock_response(200, {
                "dashboard": {"uuid": "d1", "name": "My Room"},
                "widgets": [{"uuid": "w1", "label": "Lights"}],
                "endpoints": {
                    "ep-uuid": {
                        "data": {"lights_on": True},
                        "source": "static",
                        "endpoint_name": "Lights",
                        "endpoint_slug": "lights",
                        "app_slug": "my-room",
                    },
                },
            })
            result = self.api.dashboard_data("my-room")
            mock.assert_called_once_with(
                "GET", "http://example.com/api/dashboards/my-room/data/"
            )
            self.assertIn("dashboard", result)
            self.assertIn("widgets", result)
            self.assertIn("endpoints", result)
            self.assertTrue(result["endpoints"]["ep-uuid"]["data"]["lights_on"])

    def test_dashboard_data_empty(self):
        with patch.object(self.api.session, "request") as mock:
            mock.return_value = _mock_response(200, {
                "dashboard": {"uuid": "d1", "name": "Empty"},
                "widgets": [],
                "endpoints": {},
            })
            result = self.api.dashboard_data("empty")
            self.assertEqual(result["widgets"], [])
            self.assertEqual(result["endpoints"], {})

    def test_dashboard_patch(self):
        with patch.object(self.api.session, "request") as mock:
            mock.return_value = _mock_response(200, {"status": "ok"})
            self.api.dashboard_patch("my-room", "ep-uuid", "lights_on", True)
            call_args = mock.call_args
            self.assertEqual(call_args[0][0], "PATCH")
            self.assertIn("dashboards/my-room/patch/", call_args[0][1])
            body = call_args[1]["json"]
            self.assertEqual(body["endpoint_uuid"], "ep-uuid")
            self.assertEqual(body["key_path"], "lights_on")
            self.assertTrue(body["value"])

    def test_dashboard_patch_numeric_value(self):
        with patch.object(self.api.session, "request") as mock:
            mock.return_value = _mock_response(200, {"status": "ok"})
            self.api.dashboard_patch("my-room", "ep-uuid", "temp", 22.5)
            body = mock.call_args[1]["json"]
            self.assertEqual(body["value"], 22.5)

    def test_dashboard_patch_string_value(self):
        with patch.object(self.api.session, "request") as mock:
            mock.return_value = _mock_response(200, {"status": "ok"})
            self.api.dashboard_patch("my-room", "ep-uuid", "color", "#ff0000")
            body = mock.call_args[1]["json"]
            self.assertEqual(body["value"], "#ff0000")


class TestImports(unittest.TestCase):
    """Package exports."""

    def test_version_exists(self):
        import meow_sdk
        self.assertTrue(hasattr(meow_sdk, "__version__"))
        self.assertEqual(meow_sdk.__version__, "0.4.0")

    def test_all_exports(self):
        import meow_sdk
        self.assertIn("Meow", meow_sdk.__all__)
        self.assertIn("MeowError", meow_sdk.__all__)
        self.assertIn("AuthError", meow_sdk.__all__)
        self.assertIn("NotFoundError", meow_sdk.__all__)
        self.assertIn("ValidationError", meow_sdk.__all__)
        self.assertIn("RateLimitError", meow_sdk.__all__)


if __name__ == "__main__":
    unittest.main()
