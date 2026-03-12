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
        """Helper -- not a test itself."""
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

    def test_aggregate_without_username_raises(self):
        api = Meow("http://example.com")
        with self.assertRaises(MeowError):
            api.aggregate("app", "ep", ["avg"])

    def test_export_csv_without_username_raises(self):
        api = Meow("http://example.com")
        with self.assertRaises(MeowError):
            api.export_csv("app", "ep")

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
                params=None,
                timeout=30,
            )

    def test_get_returns_json(self):
        with patch.object(self.api.session, "request") as mock:
            mock.return_value = _mock_response(200, {"temp": 22.5, "humid": 65})
            result = self.api.get("weather", "current")
            self.assertEqual(result["temp"], 22.5)
            self.assertEqual(result["humid"], 65)

    def test_get_with_filters(self):
        """Keyword arguments are passed as query params."""
        with patch.object(self.api.session, "request") as mock:
            mock.return_value = _mock_response(200, {"results": []})
            self.api.get("weather", "readings", temperature__gte=20, location="London")
            call_kwargs = mock.call_args[1]
            self.assertEqual(call_kwargs["params"]["temperature__gte"], 20)
            self.assertEqual(call_kwargs["params"]["location"], "London")

    def test_get_without_filters_passes_none_params(self):
        """No filters means params=None."""
        with patch.object(self.api.session, "request") as mock:
            mock.return_value = _mock_response(200, {})
            self.api.get("app", "ep")
            call_kwargs = mock.call_args[1]
            self.assertIsNone(call_kwargs.get("params"))

    def test_get_record_calls_correct_url(self):
        with patch.object(self.api.session, "request") as mock:
            mock.return_value = _mock_response(200, {"uuid": "abc"})
            self.api.get_record("my-app", "readings", "abc-uuid")
            mock.assert_called_once_with(
                "GET",
                "http://example.com/api/v1/jake/my-app/readings/abc-uuid/",
                timeout=30,
            )

    def test_get_record_returns_data(self):
        with patch.object(self.api.session, "request") as mock:
            mock.return_value = _mock_response(200, {
                "uuid": "abc",
                "data": {"temperature": 22},
            })
            result = self.api.get_record("app", "ep", "abc")
            self.assertEqual(result["data"]["temperature"], 22)


class TestAggregate(unittest.TestCase):
    """Aggregation queries on collection endpoints."""

    def setUp(self):
        self.api = Meow("http://example.com", username="jake")

    def test_aggregate_url_and_params(self):
        with patch.object(self.api.session, "request") as mock:
            mock.return_value = _mock_response(200, {
                "field": "temperature",
                "aggregations": {"avg": 22.3, "max": 31.0},
            })
            self.api.aggregate("weather", "readings", ["avg", "max"], field="temperature")
            call_args = mock.call_args
            self.assertEqual(call_args[0][0], "GET")
            self.assertIn("v1/jake/weather/readings/", call_args[0][1])
            params = call_args[1]["params"]
            self.assertEqual(params["aggregate"], "avg,max")
            self.assertEqual(params["field"], "temperature")

    def test_aggregate_returns_data(self):
        with patch.object(self.api.session, "request") as mock:
            mock.return_value = _mock_response(200, {
                "field": "temperature",
                "aggregations": {"avg": 22.3},
            })
            result = self.api.aggregate("weather", "readings", ["avg"], field="temperature")
            self.assertEqual(result["aggregations"]["avg"], 22.3)

    def test_aggregate_without_field(self):
        """When field is not specified, only aggregate param is sent."""
        with patch.object(self.api.session, "request") as mock:
            mock.return_value = _mock_response(200, {
                "aggregations": {"count": 42},
            })
            self.api.aggregate("weather", "readings", ["count"])
            params = mock.call_args[1]["params"]
            self.assertEqual(params["aggregate"], "count")
            self.assertNotIn("field", params)

    def test_aggregate_with_filters(self):
        """Extra keyword arguments become query params (filters)."""
        with patch.object(self.api.session, "request") as mock:
            mock.return_value = _mock_response(200, {
                "aggregations": {"avg": 18.0},
            })
            self.api.aggregate(
                "weather", "readings", ["avg"],
                field="temperature", location="London",
            )
            params = mock.call_args[1]["params"]
            self.assertEqual(params["aggregate"], "avg")
            self.assertEqual(params["field"], "temperature")
            self.assertEqual(params["location"], "London")

    def test_aggregate_single_aggregation(self):
        with patch.object(self.api.session, "request") as mock:
            mock.return_value = _mock_response(200, {})
            self.api.aggregate("app", "ep", ["sum"], field="value")
            params = mock.call_args[1]["params"]
            self.assertEqual(params["aggregate"], "sum")

    def test_aggregate_multiple_aggregations(self):
        with patch.object(self.api.session, "request") as mock:
            mock.return_value = _mock_response(200, {})
            self.api.aggregate("app", "ep", ["avg", "min", "max", "sum", "count"], field="val")
            params = mock.call_args[1]["params"]
            self.assertEqual(params["aggregate"], "avg,min,max,sum,count")


class TestExportCSV(unittest.TestCase):
    """CSV export (uses session.get directly, not _request)."""

    def setUp(self):
        self.api = Meow("http://example.com", username="jake")

    def test_export_csv_url_and_params(self):
        with patch.object(self.api.session, "get") as mock:
            mock.return_value = _mock_response(200, text="id,temp\n1,22\n2,23\n")
            self.api.export_csv("weather", "readings")
            call_args = mock.call_args
            self.assertEqual(
                call_args[0][0],
                "http://example.com/api/v1/jake/weather/readings/",
            )
            self.assertEqual(call_args[1]["params"]["format"], "csv")

    def test_export_csv_returns_text(self):
        with patch.object(self.api.session, "get") as mock:
            csv_text = "id,temperature\n1,22.5\n2,23.0\n"
            resp = _mock_response(200, text=csv_text)
            resp.text = csv_text
            mock.return_value = resp
            result = self.api.export_csv("weather", "readings")
            self.assertEqual(result, csv_text)

    def test_export_csv_with_filters(self):
        with patch.object(self.api.session, "get") as mock:
            mock.return_value = _mock_response(200, text="id,temp\n1,22\n")
            self.api.export_csv("weather", "readings", temperature__gte=20)
            params = mock.call_args[1]["params"]
            self.assertEqual(params["format"], "csv")
            self.assertEqual(params["temperature__gte"], 20)

    def test_export_csv_error_raises_meow_error(self):
        with patch.object(self.api.session, "get") as mock:
            mock.return_value = _mock_response(500, {"detail": "Server error"})
            with self.assertRaises(MeowError) as ctx:
                self.api.export_csv("app", "ep")
            self.assertEqual(ctx.exception.status_code, 500)

    def test_export_csv_429_raises_rate_limit_error(self):
        with patch.object(self.api.session, "get") as mock:
            mock.return_value = _mock_response(429, {"detail": "Throttled"})
            with self.assertRaises(RateLimitError) as ctx:
                self.api.export_csv("app", "ep")
            self.assertEqual(ctx.exception.status_code, 429)

    def test_export_csv_without_username_raises(self):
        api = Meow("http://example.com")
        with self.assertRaises(MeowError):
            api.export_csv("app", "ep")


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

    def test_records_url(self):
        with patch.object(self.api.session, "request") as mock:
            mock.return_value = _mock_response(200, {
                "count": 0, "results": [], "next": None,
            })
            self.api.records("my-app", "readings")
            mock.assert_called_once_with(
                "GET",
                "http://example.com/api/apps/my-app/endpoints/readings/records/",
                params={"limit": 25, "offset": 0},
                timeout=30,
            )

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

    def test_all_records_uses_limit_100(self):
        """all_records should use limit=100 per page for efficiency."""
        with patch.object(self.api.session, "request") as mock:
            mock.return_value = _mock_response(200, {
                "count": 0, "results": [], "next": None,
            })
            self.api.all_records("app", "ep")
            call_kwargs = mock.call_args[1]
            self.assertEqual(call_kwargs["params"]["limit"], 100)
            self.assertEqual(call_kwargs["params"]["offset"], 0)

    def test_all_records_increments_offset(self):
        """all_records increments offset by 100 each page."""
        with patch.object(self.api.session, "request") as mock:
            page1 = _mock_response(200, {
                "count": 150,
                "results": [{"uuid": str(i)} for i in range(100)],
                "next": "http://example.com/next",
            })
            page2 = _mock_response(200, {
                "count": 150,
                "results": [{"uuid": str(i)} for i in range(100, 150)],
                "next": None,
            })
            mock.side_effect = [page1, page2]
            result = self.api.all_records("app", "ep")
            self.assertEqual(len(result), 150)
            # Second call should have offset=100
            second_call_kwargs = mock.call_args_list[1][1]
            self.assertEqual(second_call_kwargs["params"]["offset"], 100)


class TestAppManagement(unittest.TestCase):
    """App CRUD."""

    def setUp(self):
        self.api = Meow("http://example.com", api_key="key")

    def test_apps_calls_get(self):
        with patch.object(self.api.session, "request") as mock:
            mock.return_value = _mock_response(200, [])
            self.api.apps()
            mock.assert_called_once_with(
                "GET", "http://example.com/api/apps/",
                timeout=30,
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

    def test_create_app_defaults(self):
        with patch.object(self.api.session, "request") as mock:
            mock.return_value = _mock_response(201, {})
            self.api.create_app("App", "app")
            body = mock.call_args[1]["json"]
            self.assertEqual(body["description"], "")
            self.assertTrue(body["is_public"])

    def test_get_app(self):
        with patch.object(self.api.session, "request") as mock:
            mock.return_value = _mock_response(200, {
                "slug": "my-app", "name": "My App", "endpoint_count": 3,
            })
            result = self.api.get_app("my-app")
            mock.assert_called_once_with(
                "GET", "http://example.com/api/apps/my-app/",
                timeout=30,
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
                "DELETE", "http://example.com/api/apps/old-app/",
                timeout=30,
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
                "GET", "http://example.com/api/apps/my-app/endpoints/",
                timeout=30,
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

    def test_create_endpoint_full_params(self):
        with patch.object(self.api.session, "request") as mock:
            mock.return_value = _mock_response(201, {})
            self.api.create_endpoint(
                "app", "Private Data", "private-data",
                endpoint_type="collection", description="Secret stuff", is_public=False,
            )
            body = mock.call_args[1]["json"]
            self.assertEqual(body["name"], "Private Data")
            self.assertEqual(body["slug"], "private-data")
            self.assertEqual(body["endpoint_type"], "collection")
            self.assertEqual(body["description"], "Secret stuff")
            self.assertFalse(body["is_public"])

    def test_create_endpoint_url(self):
        with patch.object(self.api.session, "request") as mock:
            mock.return_value = _mock_response(201, {})
            self.api.create_endpoint("my-app", "Test", "test")
            url = mock.call_args[0][1]
            self.assertEqual(url, "http://example.com/api/apps/my-app/endpoints/")

    def test_get_endpoint(self):
        with patch.object(self.api.session, "request") as mock:
            mock.return_value = _mock_response(200, {
                "slug": "readings", "record_count": 42,
            })
            result = self.api.get_endpoint("app", "readings")
            mock.assert_called_once_with(
                "GET", "http://example.com/api/apps/app/endpoints/readings/",
                timeout=30,
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
                "DELETE", "http://example.com/api/apps/app/endpoints/ep/",
                timeout=30,
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
                timeout=30,
            )

    def test_set_payload_url(self):
        with patch.object(self.api.session, "request") as mock:
            mock.return_value = _mock_response(200, {})
            self.api.set_payload("weather", "info", {"temp": 22})
            url = mock.call_args[0][1]
            self.assertEqual(
                url,
                "http://example.com/api/apps/weather/endpoints/info/payload/",
            )

    def test_set_payload_complex_data(self):
        with patch.object(self.api.session, "request") as mock:
            mock.return_value = _mock_response(200, {})
            payload = {"nested": {"list": [1, 2, 3]}, "flag": True, "count": 42}
            self.api.set_payload("app", "ep", payload)
            body = mock.call_args[1]["json"]
            self.assertEqual(body["data"], payload)


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
                timeout=30,
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

    def test_create_field_all_types(self):
        """Ensure all 14 field types can be passed."""
        field_types = [
            "text", "textarea", "number", "boolean", "date", "datetime",
            "time", "color", "email", "url", "select", "rating", "image_url", "json",
        ]
        for ft in field_types:
            with patch.object(self.api.session, "request") as mock:
                mock.return_value = _mock_response(201, {})
                self.api.create_field("app", "ep", "f", "F", ft)
                body = mock.call_args[1]["json"]
                self.assertEqual(body["field_type"], ft)

    def test_update_field(self):
        with patch.object(self.api.session, "request") as mock:
            mock.return_value = _mock_response(200, {"label": "Temp (C)"})
            self.api.update_field("app", "readings", "f-uuid", label="Temp (C)")
            call_args = mock.call_args
            self.assertEqual(call_args[0][0], "PATCH")
            self.assertIn("fields/f-uuid/", call_args[0][1])
            self.assertEqual(call_args[1]["json"]["label"], "Temp (C)")

    def test_update_field_multiple_kwargs(self):
        with patch.object(self.api.session, "request") as mock:
            mock.return_value = _mock_response(200, {})
            self.api.update_field("app", "ep", "f-uuid", label="New", required=True)
            body = mock.call_args[1]["json"]
            self.assertEqual(body["label"], "New")
            self.assertTrue(body["required"])

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


class TestFieldTypes(unittest.TestCase):
    """Field types reference endpoint."""

    def setUp(self):
        self.api = Meow("http://example.com", api_key="key")

    def test_field_types_url(self):
        with patch.object(self.api.session, "request") as mock:
            mock.return_value = _mock_response(200, [])
            self.api.field_types()
            mock.assert_called_once_with(
                "GET", "http://example.com/api/field-types/",
                timeout=30,
            )

    def test_field_types_returns_list(self):
        with patch.object(self.api.session, "request") as mock:
            types_data = [
                {"name": "text", "label": "Text"},
                {"name": "number", "label": "Number"},
                {"name": "boolean", "label": "Boolean"},
            ]
            mock.return_value = _mock_response(200, types_data)
            result = self.api.field_types()
            self.assertEqual(len(result), 3)
            self.assertEqual(result[0]["name"], "text")
            self.assertEqual(result[1]["name"], "number")


class TestProxyConfig(unittest.TestCase):
    """Proxy configuration for proxy endpoints."""

    def setUp(self):
        self.api = Meow("http://example.com", api_key="key")

    def test_get_proxy_url(self):
        with patch.object(self.api.session, "request") as mock:
            mock.return_value = _mock_response(200, {
                "upstream_url": "https://api.example.com/data",
                "method": "GET",
            })
            result = self.api.get_proxy("weather", "external-api")
            mock.assert_called_once_with(
                "GET",
                "http://example.com/api/apps/weather/endpoints/external-api/proxy/",
                timeout=30,
            )
            self.assertEqual(result["upstream_url"], "https://api.example.com/data")

    def test_get_proxy_returns_full_config(self):
        with patch.object(self.api.session, "request") as mock:
            config = {
                "upstream_url": "https://api.example.com/data",
                "method": "POST",
                "headers": {"X-API-Key": "secret"},
                "query_params": {"format": "json"},
                "body_template": '{"query": "test"}',
                "jmespath_transform": "data.items",
            }
            mock.return_value = _mock_response(200, config)
            result = self.api.get_proxy("app", "proxy-ep")
            self.assertEqual(result["method"], "POST")
            self.assertEqual(result["headers"], {"X-API-Key": "secret"})
            self.assertEqual(result["jmespath_transform"], "data.items")

    def test_set_proxy_minimal(self):
        """set_proxy with only required params."""
        with patch.object(self.api.session, "request") as mock:
            mock.return_value = _mock_response(200, {})
            self.api.set_proxy("app", "ep", "https://api.example.com/data")
            call_args = mock.call_args
            self.assertEqual(call_args[0][0], "PUT")
            self.assertIn("apps/app/endpoints/ep/proxy/", call_args[0][1])
            body = call_args[1]["json"]
            self.assertEqual(body["upstream_url"], "https://api.example.com/data")
            self.assertEqual(body["method"], "GET")
            self.assertNotIn("headers", body)
            self.assertNotIn("query_params", body)
            self.assertNotIn("body_template", body)
            self.assertNotIn("jmespath_transform", body)

    def test_set_proxy_all_params(self):
        """set_proxy with all optional params."""
        with patch.object(self.api.session, "request") as mock:
            mock.return_value = _mock_response(200, {})
            self.api.set_proxy(
                "app", "ep",
                "https://api.example.com/data",
                method="POST",
                headers={"Authorization": "Bearer token"},
                query_params={"limit": "10"},
                body_template='{"search": "{{query}}"}',
                jmespath_transform="results[].name",
            )
            body = mock.call_args[1]["json"]
            self.assertEqual(body["upstream_url"], "https://api.example.com/data")
            self.assertEqual(body["method"], "POST")
            self.assertEqual(body["headers"], {"Authorization": "Bearer token"})
            self.assertEqual(body["query_params"], {"limit": "10"})
            self.assertEqual(body["body_template"], '{"search": "{{query}}"}')
            self.assertEqual(body["jmespath_transform"], "results[].name")

    def test_set_proxy_url(self):
        with patch.object(self.api.session, "request") as mock:
            mock.return_value = _mock_response(200, {})
            self.api.set_proxy("weather", "ext", "https://api.example.com")
            url = mock.call_args[0][1]
            self.assertEqual(
                url,
                "http://example.com/api/apps/weather/endpoints/ext/proxy/",
            )

    def test_set_proxy_partial_optional_params(self):
        """Only some optional params are set."""
        with patch.object(self.api.session, "request") as mock:
            mock.return_value = _mock_response(200, {})
            self.api.set_proxy(
                "app", "ep", "https://api.example.com",
                headers={"X-Key": "val"},
                jmespath_transform="data",
            )
            body = mock.call_args[1]["json"]
            self.assertIn("headers", body)
            self.assertIn("jmespath_transform", body)
            self.assertNotIn("query_params", body)
            self.assertNotIn("body_template", body)


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


class TestEncryption(unittest.TestCase):
    """Encryption key management."""

    def setUp(self):
        self.api = Meow("http://example.com", api_key="key")

    def test_get_encryption_status(self):
        with patch.object(self.api.session, "request") as mock:
            mock.return_value = _mock_response(200, {
                "encryption_enabled": True,
                "key": {"fingerprint": "abc123", "created_at": "2025-01-01T00:00:00Z"},
            })
            result = self.api.get_encryption("app", "ep")
            mock.assert_called_once_with(
                "GET", "http://example.com/api/apps/app/endpoints/ep/encryption/",
                timeout=30,
            )
            self.assertTrue(result["encryption_enabled"])

    def test_get_encryption_disabled(self):
        with patch.object(self.api.session, "request") as mock:
            mock.return_value = _mock_response(200, {
                "encryption_enabled": False,
                "key": None,
            })
            result = self.api.get_encryption("app", "ep")
            self.assertFalse(result["encryption_enabled"])
            self.assertIsNone(result["key"])

    def test_enable_encryption(self):
        with patch.object(self.api.session, "request") as mock:
            mock.return_value = _mock_response(201, {
                "encryption_enabled": True,
                "key": "secret-key-value",
                "fingerprint": "abc123",
            })
            result = self.api.enable_encryption("app", "ep")
            call_args = mock.call_args
            self.assertEqual(call_args[0][0], "POST")
            self.assertIn("encryption/", call_args[0][1])
            self.assertEqual(result["key"], "secret-key-value")

    def test_enable_encryption_url(self):
        with patch.object(self.api.session, "request") as mock:
            mock.return_value = _mock_response(201, {})
            self.api.enable_encryption("weather", "readings")
            url = mock.call_args[0][1]
            self.assertEqual(
                url,
                "http://example.com/api/apps/weather/endpoints/readings/encryption/",
            )

    def test_disable_encryption(self):
        with patch.object(self.api.session, "request") as mock:
            mock.return_value = _mock_response(204)
            result = self.api.disable_encryption("app", "ep")
            self.assertIsNone(result)
            call_args = mock.call_args
            self.assertEqual(call_args[0][0], "DELETE")
            self.assertIn("encryption/", call_args[0][1])


class TestRequestLogs(unittest.TestCase):
    """Request log retrieval."""

    def setUp(self):
        self.api = Meow("http://example.com", api_key="key")

    def test_request_logs_url(self):
        with patch.object(self.api.session, "request") as mock:
            mock.return_value = _mock_response(200, [])
            self.api.request_logs("app", "ep")
            mock.assert_called_once_with(
                "GET", "http://example.com/api/apps/app/endpoints/ep/logs/",
                timeout=30,
            )

    def test_request_logs_returns_list(self):
        with patch.object(self.api.session, "request") as mock:
            mock.return_value = _mock_response(200, [
                {"uuid": "log1", "status_code": 200, "ip_address": "127.0.0.1",
                 "response_time_ms": 12, "created_at": "2025-01-01T00:00:00Z"},
                {"uuid": "log2", "status_code": 500, "ip_address": "10.0.0.1",
                 "response_time_ms": 3, "created_at": "2025-01-01T00:00:01Z"},
            ])
            result = self.api.request_logs("app", "ep")
            self.assertEqual(len(result), 2)
            self.assertEqual(result[0]["status_code"], 200)
            self.assertEqual(result[1]["status_code"], 500)

    def test_request_logs_empty(self):
        with patch.object(self.api.session, "request") as mock:
            mock.return_value = _mock_response(200, [])
            result = self.api.request_logs("app", "ep")
            self.assertEqual(result, [])


class TestWebhooks(unittest.TestCase):
    """Webhook CRUD."""

    def setUp(self):
        self.api = Meow("http://example.com", api_key="key")

    def test_list_webhooks(self):
        with patch.object(self.api.session, "request") as mock:
            mock.return_value = _mock_response(200, [
                {"uuid": "wh1", "target_url": "https://example.com/hook",
                 "events": ["record.created"], "is_active": True},
            ])
            result = self.api.webhooks("app", "ep")
            mock.assert_called_once_with(
                "GET", "http://example.com/api/apps/app/endpoints/ep/webhooks/",
                timeout=30,
            )
            self.assertEqual(len(result), 1)

    def test_list_webhooks_empty(self):
        with patch.object(self.api.session, "request") as mock:
            mock.return_value = _mock_response(200, [])
            result = self.api.webhooks("app", "ep")
            self.assertEqual(result, [])

    def test_get_webhook(self):
        with patch.object(self.api.session, "request") as mock:
            mock.return_value = _mock_response(200, {
                "uuid": "wh1", "target_url": "https://example.com/hook",
            })
            result = self.api.get_webhook("app", "ep", "wh1")
            mock.assert_called_once_with(
                "GET", "http://example.com/api/apps/app/endpoints/ep/webhooks/wh1/",
                timeout=30,
            )
            self.assertEqual(result["uuid"], "wh1")

    def test_create_webhook(self):
        with patch.object(self.api.session, "request") as mock:
            mock.return_value = _mock_response(201, {"uuid": "new-wh"})
            self.api.create_webhook(
                "app", "ep", "https://example.com/hook", ["record.created"]
            )
            call_args = mock.call_args
            self.assertEqual(call_args[0][0], "POST")
            body = call_args[1]["json"]
            self.assertEqual(body["target_url"], "https://example.com/hook")
            self.assertEqual(body["events"], ["record.created"])
            self.assertTrue(body["is_active"])
            self.assertNotIn("secret", body)

    def test_create_webhook_with_secret(self):
        with patch.object(self.api.session, "request") as mock:
            mock.return_value = _mock_response(201, {})
            self.api.create_webhook(
                "app", "ep", "https://example.com/hook",
                ["record.created", "record.deleted"],
                secret="my-secret",
            )
            body = mock.call_args[1]["json"]
            self.assertEqual(body["secret"], "my-secret")
            self.assertEqual(len(body["events"]), 2)

    def test_create_webhook_inactive(self):
        with patch.object(self.api.session, "request") as mock:
            mock.return_value = _mock_response(201, {})
            self.api.create_webhook(
                "app", "ep", "https://example.com/hook",
                ["record.created"], is_active=False,
            )
            body = mock.call_args[1]["json"]
            self.assertFalse(body["is_active"])

    def test_create_webhook_url(self):
        with patch.object(self.api.session, "request") as mock:
            mock.return_value = _mock_response(201, {})
            self.api.create_webhook("my-app", "readings", "https://hook.io", ["record.created"])
            url = mock.call_args[0][1]
            self.assertEqual(
                url,
                "http://example.com/api/apps/my-app/endpoints/readings/webhooks/",
            )

    def test_create_webhook_all_events(self):
        with patch.object(self.api.session, "request") as mock:
            mock.return_value = _mock_response(201, {})
            all_events = ["record.created", "record.updated", "record.deleted", "payload.updated"]
            self.api.create_webhook("app", "ep", "https://hook.io", all_events)
            body = mock.call_args[1]["json"]
            self.assertEqual(body["events"], all_events)

    def test_update_webhook(self):
        with patch.object(self.api.session, "request") as mock:
            mock.return_value = _mock_response(200, {})
            self.api.update_webhook(
                "app", "ep", "wh-uuid",
                events=["record.created", "record.deleted"],
                is_active=False,
            )
            call_args = mock.call_args
            self.assertEqual(call_args[0][0], "PATCH")
            self.assertIn("webhooks/wh-uuid/", call_args[0][1])
            body = call_args[1]["json"]
            self.assertEqual(len(body["events"]), 2)
            self.assertFalse(body["is_active"])

    def test_update_webhook_url_only(self):
        with patch.object(self.api.session, "request") as mock:
            mock.return_value = _mock_response(200, {})
            self.api.update_webhook("app", "ep", "wh-uuid", target_url="https://new.url")
            body = mock.call_args[1]["json"]
            self.assertEqual(body["target_url"], "https://new.url")
            self.assertNotIn("events", body)
            self.assertNotIn("is_active", body)

    def test_delete_webhook(self):
        with patch.object(self.api.session, "request") as mock:
            mock.return_value = _mock_response(204)
            result = self.api.delete_webhook("app", "ep", "wh-uuid")
            self.assertIsNone(result)
            mock.assert_called_once_with(
                "DELETE",
                "http://example.com/api/apps/app/endpoints/ep/webhooks/wh-uuid/",
                timeout=30,
            )


class TestChaosMode(unittest.TestCase):
    """Chaos mode via endpoint update."""

    def setUp(self):
        self.api = Meow("http://example.com", api_key="key")

    def test_enable_chaos_via_update(self):
        with patch.object(self.api.session, "request") as mock:
            mock.return_value = _mock_response(200, {
                "delay_ms": 500, "error_rate": 0.1,
            })
            result = self.api.update_endpoint(
                "app", "ep", delay_ms=500, error_rate=0.1,
            )
            body = mock.call_args[1]["json"]
            self.assertEqual(body["delay_ms"], 500)
            self.assertEqual(body["error_rate"], 0.1)
            self.assertEqual(result["delay_ms"], 500)

    def test_disable_chaos_via_update(self):
        with patch.object(self.api.session, "request") as mock:
            mock.return_value = _mock_response(200, {
                "delay_ms": 0, "error_rate": 0,
            })
            self.api.update_endpoint("app", "ep", delay_ms=0, error_rate=0)
            body = mock.call_args[1]["json"]
            self.assertEqual(body["delay_ms"], 0)
            self.assertEqual(body["error_rate"], 0)


class TestDashboardManagement(unittest.TestCase):
    """Dashboard CRUD."""

    def setUp(self):
        self.api = Meow("http://example.com", api_key="key")

    def test_dashboards_list(self):
        with patch.object(self.api.session, "request") as mock:
            mock.return_value = _mock_response(200, [])
            self.api.dashboards()
            mock.assert_called_once_with(
                "GET", "http://example.com/api/dashboards/",
                timeout=30,
            )

    def test_dashboards_returns_list(self):
        with patch.object(self.api.session, "request") as mock:
            mock.return_value = _mock_response(200, [
                {"slug": "room-1", "name": "Room 1"},
                {"slug": "room-2", "name": "Room 2"},
            ])
            result = self.api.dashboards()
            self.assertEqual(len(result), 2)
            self.assertEqual(result[0]["slug"], "room-1")

    def test_get_dashboard(self):
        with patch.object(self.api.session, "request") as mock:
            mock.return_value = _mock_response(200, {
                "slug": "my-room", "name": "My Room", "widget_count": 3,
            })
            result = self.api.get_dashboard("my-room")
            mock.assert_called_once_with(
                "GET", "http://example.com/api/dashboards/my-room/",
                timeout=30,
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

    def test_create_dashboard_url(self):
        with patch.object(self.api.session, "request") as mock:
            mock.return_value = _mock_response(201, {})
            self.api.create_dashboard("X", "x")
            url = mock.call_args[0][1]
            self.assertEqual(url, "http://example.com/api/dashboards/")

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
                "DELETE", "http://example.com/api/dashboards/old-panel/",
                timeout=30,
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
                "GET", "http://example.com/api/dashboards/my-room/widgets/",
                timeout=30,
            )
            self.assertEqual(len(result), 1)
            self.assertEqual(result[0]["label"], "Lights")

    def test_list_widgets_empty(self):
        with patch.object(self.api.session, "request") as mock:
            mock.return_value = _mock_response(200, [])
            result = self.api.dashboard_widgets("empty-room")
            self.assertEqual(result, [])

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

    def test_create_widget_with_sort_order(self):
        with patch.object(self.api.session, "request") as mock:
            mock.return_value = _mock_response(201, {})
            self.api.create_dashboard_widget(
                "my-room", "ep-uuid", "temp", "display", "Temp",
                sort_order=5,
            )
            body = mock.call_args[1]["json"]
            self.assertEqual(body["sort_order"], 5)

    def test_create_widget_all_types(self):
        """All widget types can be passed."""
        widget_types = ["toggle", "color", "slider", "number", "text", "select", "display"]
        for wt in widget_types:
            with patch.object(self.api.session, "request") as mock:
                mock.return_value = _mock_response(201, {})
                self.api.create_dashboard_widget("room", "ep", "key", wt, "Label")
                body = mock.call_args[1]["json"]
                self.assertEqual(body["widget_type"], wt)

    def test_update_widget(self):
        with patch.object(self.api.session, "request") as mock:
            mock.return_value = _mock_response(200, {"label": "Bedroom Lights"})
            self.api.update_dashboard_widget(
                "my-room", "widget-uuid", label="Bedroom Lights", sort_order=2,
            )
            call_args = mock.call_args
            self.assertEqual(call_args[0][0], "PATCH")
            self.assertIn("dashboards/my-room/widgets/widget-uuid/", call_args[0][1])
            body = call_args[1]["json"]
            self.assertEqual(body["label"], "Bedroom Lights")
            self.assertEqual(body["sort_order"], 2)

    def test_update_widget_url(self):
        with patch.object(self.api.session, "request") as mock:
            mock.return_value = _mock_response(200, {})
            self.api.update_dashboard_widget("room", "w-uuid", label="X")
            url = mock.call_args[0][1]
            self.assertEqual(
                url,
                "http://example.com/api/dashboards/room/widgets/w-uuid/",
            )

    def test_update_widget_single_field(self):
        with patch.object(self.api.session, "request") as mock:
            mock.return_value = _mock_response(200, {})
            self.api.update_dashboard_widget("room", "w-uuid", widget_type="slider")
            body = mock.call_args[1]["json"]
            self.assertEqual(body["widget_type"], "slider")
            self.assertNotIn("label", body)
            self.assertNotIn("sort_order", body)

    def test_update_widget_config(self):
        with patch.object(self.api.session, "request") as mock:
            mock.return_value = _mock_response(200, {})
            self.api.update_dashboard_widget(
                "room", "w-uuid", config={"min": 10, "max": 50},
            )
            body = mock.call_args[1]["json"]
            self.assertEqual(body["config"], {"min": 10, "max": 50})

    def test_delete_widget(self):
        with patch.object(self.api.session, "request") as mock:
            mock.return_value = _mock_response(204)
            result = self.api.delete_dashboard_widget("my-room", "w-uuid")
            self.assertIsNone(result)
            mock.assert_called_once_with(
                "DELETE",
                "http://example.com/api/dashboards/my-room/widgets/w-uuid/",
                timeout=30,
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
                "GET", "http://example.com/api/dashboards/my-room/data/",
                timeout=30,
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

    def test_dashboard_patch_url(self):
        with patch.object(self.api.session, "request") as mock:
            mock.return_value = _mock_response(200, {})
            self.api.dashboard_patch("room", "ep", "key", "val")
            url = mock.call_args[0][1]
            self.assertEqual(url, "http://example.com/api/dashboards/room/patch/")

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

    def test_dashboard_patch_false_value(self):
        """Ensure False is properly sent (not None or missing)."""
        with patch.object(self.api.session, "request") as mock:
            mock.return_value = _mock_response(200, {})
            self.api.dashboard_patch("room", "ep", "lights_on", False)
            body = mock.call_args[1]["json"]
            self.assertFalse(body["value"])
            self.assertIn("value", body)

    def test_dashboard_patch_zero_value(self):
        """Ensure 0 is properly sent."""
        with patch.object(self.api.session, "request") as mock:
            mock.return_value = _mock_response(200, {})
            self.api.dashboard_patch("room", "ep", "brightness", 0)
            body = mock.call_args[1]["json"]
            self.assertEqual(body["value"], 0)


class TestAppAPIKeys(unittest.TestCase):
    """App-scoped API key management."""

    def setUp(self):
        self.api = Meow("http://example.com", api_key="key")

    def test_app_keys_url(self):
        with patch.object(self.api.session, "request") as mock:
            mock.return_value = _mock_response(200, [])
            self.api.app_keys("weather-app")
            mock.assert_called_once_with(
                "GET", "http://example.com/api/apps/weather-app/keys/",
                timeout=30,
            )

    def test_app_keys_returns_list(self):
        with patch.object(self.api.session, "request") as mock:
            mock.return_value = _mock_response(200, [
                {"uuid": "k1", "prefix": "mms_", "created_at": "2025-01-01T00:00:00Z"},
                {"uuid": "k2", "prefix": "mms_", "created_at": "2025-01-02T00:00:00Z"},
            ])
            result = self.api.app_keys("weather-app")
            self.assertEqual(len(result), 2)
            self.assertEqual(result[0]["uuid"], "k1")

    def test_app_keys_empty(self):
        with patch.object(self.api.session, "request") as mock:
            mock.return_value = _mock_response(200, [])
            result = self.api.app_keys("app")
            self.assertEqual(result, [])

    def test_create_app_key_url(self):
        with patch.object(self.api.session, "request") as mock:
            mock.return_value = _mock_response(201, {
                "uuid": "new-key-uuid",
                "key": "mms_live_abc123",
            })
            self.api.create_app_key("weather-app")
            call_args = mock.call_args
            self.assertEqual(call_args[0][0], "POST")
            self.assertEqual(
                call_args[0][1],
                "http://example.com/api/apps/weather-app/keys/",
            )

    def test_create_app_key_returns_key(self):
        with patch.object(self.api.session, "request") as mock:
            mock.return_value = _mock_response(201, {
                "uuid": "new-key-uuid",
                "key": "mms_live_abc123",
            })
            result = self.api.create_app_key("weather-app")
            self.assertEqual(result["key"], "mms_live_abc123")
            self.assertEqual(result["uuid"], "new-key-uuid")

    def test_create_app_key_no_body(self):
        """create_app_key sends no JSON body."""
        with patch.object(self.api.session, "request") as mock:
            mock.return_value = _mock_response(201, {})
            self.api.create_app_key("app")
            call_kwargs = mock.call_args[1]
            self.assertNotIn("json", call_kwargs)

    def test_delete_app_key_url(self):
        with patch.object(self.api.session, "request") as mock:
            mock.return_value = _mock_response(204)
            self.api.delete_app_key("weather-app", "key-uuid-123")
            mock.assert_called_once_with(
                "DELETE",
                "http://example.com/api/apps/weather-app/keys/key-uuid-123/",
                timeout=30,
            )

    def test_delete_app_key_returns_none(self):
        with patch.object(self.api.session, "request") as mock:
            mock.return_value = _mock_response(204)
            result = self.api.delete_app_key("app", "key-uuid")
            self.assertIsNone(result)


class TestPlatformTokens(unittest.TestCase):
    """Platform token management."""

    def setUp(self):
        self.api = Meow("http://example.com", api_key="key")

    def test_platform_tokens_url(self):
        with patch.object(self.api.session, "request") as mock:
            mock.return_value = _mock_response(200, [])
            self.api.platform_tokens()
            mock.assert_called_once_with(
                "GET", "http://example.com/api/auth/tokens/",
                timeout=30,
            )

    def test_platform_tokens_returns_list(self):
        with patch.object(self.api.session, "request") as mock:
            mock.return_value = _mock_response(200, [
                {"uuid": "t1", "name": "my-pi", "created_at": "2025-01-01T00:00:00Z"},
                {"uuid": "t2", "name": "my-laptop", "created_at": "2025-01-02T00:00:00Z"},
            ])
            result = self.api.platform_tokens()
            self.assertEqual(len(result), 2)
            self.assertEqual(result[0]["name"], "my-pi")

    def test_platform_tokens_empty(self):
        with patch.object(self.api.session, "request") as mock:
            mock.return_value = _mock_response(200, [])
            result = self.api.platform_tokens()
            self.assertEqual(result, [])

    def test_create_platform_token_url_and_body(self):
        with patch.object(self.api.session, "request") as mock:
            mock.return_value = _mock_response(201, {
                "uuid": "new-token-uuid",
                "name": "my-pi",
                "key": "mms_platform_xyz789",
            })
            self.api.create_platform_token("my-pi")
            call_args = mock.call_args
            self.assertEqual(call_args[0][0], "POST")
            self.assertEqual(
                call_args[0][1],
                "http://example.com/api/auth/tokens/",
            )
            body = call_args[1]["json"]
            self.assertEqual(body["name"], "my-pi")

    def test_create_platform_token_returns_key(self):
        with patch.object(self.api.session, "request") as mock:
            mock.return_value = _mock_response(201, {
                "uuid": "new-token-uuid",
                "name": "my-pi",
                "key": "mms_platform_xyz789",
            })
            result = self.api.create_platform_token("my-pi")
            self.assertEqual(result["key"], "mms_platform_xyz789")
            self.assertEqual(result["name"], "my-pi")

    def test_revoke_platform_token_url(self):
        with patch.object(self.api.session, "request") as mock:
            mock.return_value = _mock_response(204)
            self.api.revoke_platform_token("token-uuid-123")
            mock.assert_called_once_with(
                "DELETE",
                "http://example.com/api/auth/tokens/token-uuid-123/",
                timeout=30,
            )

    def test_revoke_platform_token_returns_none(self):
        with patch.object(self.api.session, "request") as mock:
            mock.return_value = _mock_response(204)
            result = self.api.revoke_platform_token("token-uuid")
            self.assertIsNone(result)


class TestBilling(unittest.TestCase):
    """Billing status endpoint."""

    def setUp(self):
        self.api = Meow("http://example.com", api_key="key")

    def test_billing_status_url(self):
        with patch.object(self.api.session, "request") as mock:
            mock.return_value = _mock_response(200, {
                "plan": "free",
                "usage": {"apps": 2, "max_apps": 5},
            })
            self.api.billing_status()
            mock.assert_called_once_with(
                "GET", "http://example.com/api/billing/status/",
                timeout=30,
            )

    def test_billing_status_returns_data(self):
        with patch.object(self.api.session, "request") as mock:
            status_data = {
                "plan": "free",
                "usage": {"apps": 2, "max_apps": 5},
                "limits": {"records_per_endpoint": 1000},
            }
            mock.return_value = _mock_response(200, status_data)
            result = self.api.billing_status()
            self.assertEqual(result["plan"], "free")
            self.assertEqual(result["usage"]["apps"], 2)
            self.assertEqual(result["limits"]["records_per_endpoint"], 1000)

    def test_billing_status_paid_plan(self):
        with patch.object(self.api.session, "request") as mock:
            mock.return_value = _mock_response(200, {
                "plan": "pro",
                "usage": {"apps": 10, "max_apps": 50},
            })
            result = self.api.billing_status()
            self.assertEqual(result["plan"], "pro")


class TestPublicDashboard(unittest.TestCase):
    """Public dashboard access via share token."""

    def setUp(self):
        self.api = Meow("http://example.com")

    def test_public_dashboard_url(self):
        with patch.object(self.api.session, "request") as mock:
            mock.return_value = _mock_response(200, {
                "dashboard": {"name": "My Room"},
                "widgets": [],
                "endpoints": {},
            })
            self.api.public_dashboard("abc123token")
            mock.assert_called_once_with(
                "GET", "http://example.com/api/v1/dashboards/abc123token/",
                timeout=30,
            )

    def test_public_dashboard_returns_data(self):
        with patch.object(self.api.session, "request") as mock:
            mock.return_value = _mock_response(200, {
                "dashboard": {"name": "My Room", "slug": "my-room"},
                "widgets": [{"uuid": "w1", "label": "Lights"}],
                "endpoints": {"ep-uuid": {"data": {"lights_on": True}}},
            })
            result = self.api.public_dashboard("token123")
            self.assertEqual(result["dashboard"]["name"], "My Room")
            self.assertEqual(len(result["widgets"]), 1)
            self.assertTrue(result["endpoints"]["ep-uuid"]["data"]["lights_on"])

    def test_public_dashboard_no_auth_needed(self):
        """No API key is required to read a public dashboard."""
        api = Meow("http://example.com")  # no api_key
        with patch.object(api.session, "request") as mock:
            mock.return_value = _mock_response(200, {
                "dashboard": {}, "widgets": [], "endpoints": {},
            })
            api.public_dashboard("token")
            # Should not raise


class TestImports(unittest.TestCase):
    """Package exports."""

    def test_version_exists(self):
        import meow_sdk
        self.assertTrue(hasattr(meow_sdk, "__version__"))
        self.assertEqual(meow_sdk.__version__, "0.6.0")

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
