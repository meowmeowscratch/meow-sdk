"""Tests for the meow-sdk CLI.

Mocks get_client() so no real HTTP calls are made.
Each test verifies that the CLI subcommand calls the correct SDK method
with the correct arguments and produces the expected output.
"""

import json
import sys
from argparse import Namespace
from io import StringIO
from unittest.mock import MagicMock, patch

import pytest

from meow_sdk.cli import (
    _parse_filters,
    _print,
    cmd_aggregate,
    cmd_apps,
    cmd_billing_status,
    cmd_create_app,
    cmd_create_endpoint,
    cmd_create_field,
    cmd_csv,
    cmd_dashboard_create,
    cmd_dashboard_data,
    cmd_dashboard_delete,
    cmd_dashboard_get,
    cmd_dashboard_patch,
    cmd_dashboard_update,
    cmd_dashboards,
    cmd_delete_app,
    cmd_delete_endpoint,
    cmd_delete_field,
    cmd_delete_record,
    cmd_encrypt_disable,
    cmd_encrypt_enable,
    cmd_encryption,
    cmd_endpoints,
    cmd_field_types,
    cmd_fields,
    cmd_get,
    cmd_get_app,
    cmd_get_endpoint,
    cmd_get_record,
    cmd_key_create,
    cmd_key_delete,
    cmd_keys,
    cmd_logs,
    cmd_payload_get,
    cmd_payload_set,
    cmd_platform_token_create,
    cmd_platform_token_revoke,
    cmd_platform_tokens,
    cmd_proxy_get,
    cmd_proxy_set,
    cmd_public_dashboard,
    cmd_records,
    cmd_send,
    cmd_update_app,
    cmd_update_endpoint,
    cmd_update_field,
    cmd_update_record,
    cmd_webhook_create,
    cmd_webhook_delete,
    cmd_webhook_get,
    cmd_webhook_update,
    cmd_webhooks,
    cmd_widgets,
    cmd_widget_create,
    cmd_widget_delete,
    cmd_widget_update,
    get_client,
    main,
)


# ── Fixtures ────────────────────────────────────────────────────────


@pytest.fixture
def mock_client():
    """Return a MagicMock that stands in for a Meow instance."""
    return MagicMock()


@pytest.fixture
def patch_get_client(mock_client):
    """Patch get_client() so every cmd_* function uses our mock."""
    with patch("meow_sdk.cli.get_client", return_value=mock_client):
        yield mock_client


# ── Helpers ─────────────────────────────────────────────────────────


class TestParseFilters:
    """_parse_filters converts key=value strings into a dict."""

    def test_empty_list(self):
        assert _parse_filters([]) == {}

    def test_none_input(self):
        assert _parse_filters(None) == {}

    def test_string_value(self):
        assert _parse_filters(["name=alice"]) == {"name": "alice"}

    def test_numeric_value_auto_detected(self):
        result = _parse_filters(["temperature=22.5"])
        assert result == {"temperature": 22.5}

    def test_integer_value_auto_detected(self):
        result = _parse_filters(["count=10"])
        assert result == {"count": 10}

    def test_boolean_value_auto_detected(self):
        result = _parse_filters(["active=true"])
        assert result == {"active": True}

    def test_json_object_auto_detected(self):
        result = _parse_filters(['config={"a":1}'])
        assert result == {"config": {"a": 1}}

    def test_multiple_pairs(self):
        result = _parse_filters(["a=1", "b=hello", "c=true"])
        assert result == {"a": 1, "b": "hello", "c": True}

    def test_missing_equals_exits(self):
        with pytest.raises(SystemExit):
            _parse_filters(["badvalue"])

    def test_value_with_equals_sign(self):
        result = _parse_filters(["formula=a=b"])
        assert result == {"formula": "a=b"}


class TestPrint:
    """_print outputs JSON with indent=2."""

    def test_prints_json(self, capsys):
        _print({"key": "value"})
        out = capsys.readouterr().out
        assert json.loads(out) == {"key": "value"}

    def test_prints_list(self, capsys):
        _print([1, 2, 3])
        out = capsys.readouterr().out
        assert json.loads(out) == [1, 2, 3]


class TestGetClient:
    """get_client reads env vars and returns a Meow instance."""

    @patch.dict("os.environ", {"MEOW_URL": "http://test.local", "MEOW_USERNAME": "bob", "MEOW_API_KEY": "key-123"})
    @patch("meow_sdk.cli.Meow")
    def test_reads_env_vars(self, MockMeow):
        get_client()
        MockMeow.assert_called_once_with(base_url="http://test.local", username="bob", api_key="key-123")

    @patch.dict("os.environ", {}, clear=True)
    @patch("meow_sdk.cli.Meow")
    def test_defaults(self, MockMeow):
        get_client()
        MockMeow.assert_called_once_with(
            base_url="https://meowmeowscratch.com",
            username=None,
            api_key=None,
        )

    @patch.dict("os.environ", {"MEOW_USERNAME": "", "MEOW_API_KEY": ""}, clear=True)
    @patch("meow_sdk.cli.Meow")
    def test_empty_strings_become_none(self, MockMeow):
        get_client()
        MockMeow.assert_called_once_with(
            base_url="https://meowmeowscratch.com",
            username=None,
            api_key=None,
        )


# ── App commands ────────────────────────────────────────────────────


class TestCmdApps:
    def test_apps_list(self, patch_get_client, capsys):
        patch_get_client.apps.return_value = [
            {"slug": "weather", "name": "Weather App"},
            {"slug": "lights", "name": "Smart Lights"},
        ]
        cmd_apps(Namespace())
        out = capsys.readouterr().out
        assert "weather" in out
        assert "Weather App" in out
        assert "lights" in out

    def test_apps_non_list(self, patch_get_client, capsys):
        patch_get_client.apps.return_value = {"error": "oops"}
        cmd_apps(Namespace())
        out = capsys.readouterr().out
        assert json.loads(out) == {"error": "oops"}


class TestCmdGetApp:
    def test_get_app(self, patch_get_client, capsys):
        patch_get_client.get_app.return_value = {"slug": "weather", "name": "Weather"}
        cmd_get_app(Namespace(app="weather"))
        patch_get_client.get_app.assert_called_once_with("weather")
        assert json.loads(capsys.readouterr().out)["slug"] == "weather"


class TestCmdCreateApp:
    def test_create_app_defaults(self, patch_get_client, capsys):
        patch_get_client.create_app.return_value = {"slug": "weather"}
        cmd_create_app(Namespace(name="Weather", slug="weather", description=None, private=False))
        patch_get_client.create_app.assert_called_once_with(
            "Weather", "weather", description="", is_public=True
        )

    def test_create_app_private(self, patch_get_client, capsys):
        patch_get_client.create_app.return_value = {"slug": "secret"}
        cmd_create_app(Namespace(name="Secret", slug="secret", description="desc", private=True))
        patch_get_client.create_app.assert_called_once_with(
            "Secret", "secret", description="desc", is_public=False
        )


class TestCmdUpdateApp:
    def test_update_with_name(self, patch_get_client, capsys):
        patch_get_client.update_app.return_value = {"slug": "weather"}
        cmd_update_app(Namespace(app="weather", name="New Name", description=None, public=False, private=False))
        patch_get_client.update_app.assert_called_once_with("weather", name="New Name")

    def test_update_public(self, patch_get_client, capsys):
        patch_get_client.update_app.return_value = {"slug": "weather"}
        cmd_update_app(Namespace(app="weather", name=None, description=None, public=True, private=False))
        patch_get_client.update_app.assert_called_once_with("weather", is_public=True)

    def test_update_private(self, patch_get_client, capsys):
        patch_get_client.update_app.return_value = {"slug": "weather"}
        cmd_update_app(Namespace(app="weather", name=None, description=None, public=False, private=True))
        patch_get_client.update_app.assert_called_once_with("weather", is_public=False)

    def test_update_no_args(self, patch_get_client, capsys):
        patch_get_client.update_app.return_value = {"slug": "weather"}
        cmd_update_app(Namespace(app="weather", name=None, description=None, public=False, private=False))
        patch_get_client.update_app.assert_called_once_with("weather")


class TestCmdDeleteApp:
    def test_delete_app(self, patch_get_client, capsys):
        cmd_delete_app(Namespace(app="weather"))
        patch_get_client.delete_app.assert_called_once_with("weather")
        assert "Deleted app: weather" in capsys.readouterr().out


# ── Endpoint commands ───────────────────────────────────────────────


class TestCmdEndpoints:
    def test_endpoints_list(self, patch_get_client, capsys):
        patch_get_client.endpoints.return_value = [
            {"slug": "readings", "endpoint_type": "collection", "name": "Readings"},
        ]
        cmd_endpoints(Namespace(app="weather"))
        patch_get_client.endpoints.assert_called_once_with("weather")
        out = capsys.readouterr().out
        assert "readings" in out
        assert "collection" in out

    def test_endpoints_non_list(self, patch_get_client, capsys):
        patch_get_client.endpoints.return_value = {"count": 0}
        cmd_endpoints(Namespace(app="weather"))
        assert json.loads(capsys.readouterr().out) == {"count": 0}


class TestCmdGetEndpoint:
    def test_get_endpoint(self, patch_get_client, capsys):
        patch_get_client.get_endpoint.return_value = {"slug": "readings"}
        cmd_get_endpoint(Namespace(app="weather", endpoint="readings"))
        patch_get_client.get_endpoint.assert_called_once_with("weather", "readings")


class TestCmdCreateEndpoint:
    def test_create_endpoint_defaults(self, patch_get_client, capsys):
        patch_get_client.create_endpoint.return_value = {"slug": "readings"}
        cmd_create_endpoint(Namespace(
            app="weather", name="Readings", slug="readings",
            type="collection", description=None, private=False,
        ))
        patch_get_client.create_endpoint.assert_called_once_with(
            "weather", "Readings", "readings", "collection",
            description="", is_public=True,
        )

    def test_create_endpoint_private(self, patch_get_client, capsys):
        patch_get_client.create_endpoint.return_value = {"slug": "secret"}
        cmd_create_endpoint(Namespace(
            app="weather", name="Secret", slug="secret",
            type="static", description="my desc", private=True,
        ))
        patch_get_client.create_endpoint.assert_called_once_with(
            "weather", "Secret", "secret", "static",
            description="my desc", is_public=False,
        )


class TestCmdUpdateEndpoint:
    def test_update_name_only(self, patch_get_client, capsys):
        patch_get_client.update_endpoint.return_value = {"slug": "readings"}
        cmd_update_endpoint(Namespace(
            app="weather", endpoint="readings",
            name="New Name", description=None,
            public=False, private=False,
            delay_ms=None, error_rate=None, ttl=None,
        ))
        patch_get_client.update_endpoint.assert_called_once_with(
            "weather", "readings", name="New Name",
        )

    def test_update_chaos_and_ttl(self, patch_get_client, capsys):
        patch_get_client.update_endpoint.return_value = {"slug": "readings"}
        cmd_update_endpoint(Namespace(
            app="weather", endpoint="readings",
            name=None, description=None,
            public=False, private=False,
            delay_ms=500, error_rate=0.1, ttl=3600,
        ))
        patch_get_client.update_endpoint.assert_called_once_with(
            "weather", "readings",
            delay_ms=500, error_rate=0.1, ttl_seconds=3600,
        )

    def test_update_public_flag(self, patch_get_client, capsys):
        patch_get_client.update_endpoint.return_value = {}
        cmd_update_endpoint(Namespace(
            app="weather", endpoint="readings",
            name=None, description=None,
            public=True, private=False,
            delay_ms=None, error_rate=None, ttl=None,
        ))
        patch_get_client.update_endpoint.assert_called_once_with(
            "weather", "readings", is_public=True,
        )

    def test_update_private_flag(self, patch_get_client, capsys):
        patch_get_client.update_endpoint.return_value = {}
        cmd_update_endpoint(Namespace(
            app="weather", endpoint="readings",
            name=None, description=None,
            public=False, private=True,
            delay_ms=None, error_rate=None, ttl=None,
        ))
        patch_get_client.update_endpoint.assert_called_once_with(
            "weather", "readings", is_public=False,
        )


class TestCmdDeleteEndpoint:
    def test_delete_endpoint(self, patch_get_client, capsys):
        cmd_delete_endpoint(Namespace(app="weather", endpoint="readings"))
        patch_get_client.delete_endpoint.assert_called_once_with("weather", "readings")
        assert "Deleted endpoint: weather/readings" in capsys.readouterr().out


# ── Field commands ──────────────────────────────────────────────────


class TestCmdFields:
    def test_fields_list(self, patch_get_client, capsys):
        patch_get_client.fields.return_value = [
            {"name": "temp", "field_type": "number", "label": "Temperature", "required": True},
            {"name": "city", "field_type": "text", "label": "City", "required": False},
        ]
        cmd_fields(Namespace(app="weather", endpoint="readings"))
        patch_get_client.fields.assert_called_once_with("weather", "readings")
        out = capsys.readouterr().out
        assert "temp" in out
        assert "number" in out
        assert "*" in out  # required marker

    def test_fields_non_list(self, patch_get_client, capsys):
        patch_get_client.fields.return_value = {"detail": "not found"}
        cmd_fields(Namespace(app="weather", endpoint="readings"))
        assert json.loads(capsys.readouterr().out) == {"detail": "not found"}


class TestCmdCreateField:
    def test_create_field_basic(self, patch_get_client, capsys):
        patch_get_client.create_field.return_value = {"name": "temp"}
        cmd_create_field(Namespace(
            app="weather", endpoint="readings",
            name="temp", label="Temperature", field_type="number",
            required=False,
        ))
        patch_get_client.create_field.assert_called_once_with(
            "weather", "readings", "temp", "Temperature", "number",
        )

    def test_create_field_required(self, patch_get_client, capsys):
        patch_get_client.create_field.return_value = {"name": "temp"}
        cmd_create_field(Namespace(
            app="weather", endpoint="readings",
            name="temp", label="Temperature", field_type="number",
            required=True,
        ))
        patch_get_client.create_field.assert_called_once_with(
            "weather", "readings", "temp", "Temperature", "number",
            required=True,
        )


class TestCmdUpdateField:
    def test_update_field_label(self, patch_get_client, capsys):
        patch_get_client.update_field.return_value = {"uuid": "abc"}
        cmd_update_field(Namespace(
            app="weather", endpoint="readings", uuid="abc",
            label="New Label", required=None,
        ))
        patch_get_client.update_field.assert_called_once_with(
            "weather", "readings", "abc", label="New Label",
        )

    def test_update_field_required(self, patch_get_client, capsys):
        patch_get_client.update_field.return_value = {"uuid": "abc"}
        cmd_update_field(Namespace(
            app="weather", endpoint="readings", uuid="abc",
            label=None, required=True,
        ))
        patch_get_client.update_field.assert_called_once_with(
            "weather", "readings", "abc", required=True,
        )

    def test_update_field_no_args(self, patch_get_client, capsys):
        patch_get_client.update_field.return_value = {"uuid": "abc"}
        cmd_update_field(Namespace(
            app="weather", endpoint="readings", uuid="abc",
            label=None, required=None,
        ))
        patch_get_client.update_field.assert_called_once_with(
            "weather", "readings", "abc",
        )


class TestCmdDeleteField:
    def test_delete_field(self, patch_get_client, capsys):
        cmd_delete_field(Namespace(app="weather", endpoint="readings", uuid="field-uuid"))
        patch_get_client.delete_field.assert_called_once_with("weather", "readings", "field-uuid")
        assert "Deleted field: field-uuid" in capsys.readouterr().out


# ── Record commands ─────────────────────────────────────────────────


class TestCmdRecords:
    def test_records_default_limit(self, patch_get_client, capsys):
        patch_get_client.records.return_value = {"results": [], "count": 0}
        cmd_records(Namespace(app="weather", endpoint="readings", limit=25))
        patch_get_client.records.assert_called_once_with("weather", "readings", limit=25)

    def test_records_custom_limit(self, patch_get_client, capsys):
        patch_get_client.records.return_value = {"results": []}
        cmd_records(Namespace(app="weather", endpoint="readings", limit=5))
        patch_get_client.records.assert_called_once_with("weather", "readings", limit=5)


class TestCmdGetRecord:
    def test_get_record(self, patch_get_client, capsys):
        patch_get_client.get_record.return_value = {"uuid": "rec-1", "data": {"temp": 22}}
        cmd_get_record(Namespace(app="weather", endpoint="readings", uuid="rec-1"))
        patch_get_client.get_record.assert_called_once_with("weather", "readings", "rec-1")
        assert json.loads(capsys.readouterr().out)["uuid"] == "rec-1"


class TestCmdSend:
    def test_send_data(self, patch_get_client, capsys):
        patch_get_client.send.return_value = {"uuid": "new-rec"}
        cmd_send(Namespace(app="weather", endpoint="readings", data=["temperature=22.5", "humidity=65"]))
        patch_get_client.send.assert_called_once_with(
            "weather", "readings", {"temperature": 22.5, "humidity": 65},
        )
        assert json.loads(capsys.readouterr().out) == {"uuid": "new-rec"}


class TestCmdUpdateRecord:
    def test_update_record(self, patch_get_client, capsys):
        patch_get_client.update.return_value = {"uuid": "rec-1"}
        cmd_update_record(Namespace(
            app="weather", endpoint="readings", uuid="rec-1",
            data=["temperature=23.0"],
        ))
        patch_get_client.update.assert_called_once_with(
            "weather", "readings", "rec-1", {"temperature": 23.0},
        )


class TestCmdDeleteRecord:
    def test_delete_record(self, patch_get_client, capsys):
        cmd_delete_record(Namespace(app="weather", endpoint="readings", uuid="rec-1"))
        patch_get_client.delete_record.assert_called_once_with("weather", "readings", "rec-1")
        assert "Deleted record: rec-1" in capsys.readouterr().out


# ── Payload commands ────────────────────────────────────────────────


class TestCmdPayloadGet:
    def test_payload_get(self, patch_get_client, capsys):
        patch_get_client.get_payload.return_value = {"open": True}
        cmd_payload_get(Namespace(app="weather", endpoint="status"))
        patch_get_client.get_payload.assert_called_once_with("weather", "status")
        assert json.loads(capsys.readouterr().out) == {"open": True}


class TestCmdPayloadSet:
    def test_payload_set(self, patch_get_client, capsys):
        patch_get_client.set_payload.return_value = {"data": {"open": False}}
        cmd_payload_set(Namespace(app="weather", endpoint="status", data=["open=false"]))
        patch_get_client.set_payload.assert_called_once_with(
            "weather", "status", {"open": False},
        )


# ── Proxy commands ──────────────────────────────────────────────────


class TestCmdProxyGet:
    def test_proxy_get(self, patch_get_client, capsys):
        patch_get_client.get_proxy.return_value = {"upstream_url": "https://api.example.com"}
        cmd_proxy_get(Namespace(app="weather", endpoint="external"))
        patch_get_client.get_proxy.assert_called_once_with("weather", "external")
        assert "api.example.com" in capsys.readouterr().out


class TestCmdProxySet:
    def test_proxy_set_with_method(self, patch_get_client, capsys):
        patch_get_client.set_proxy.return_value = {"upstream_url": "https://api.example.com"}
        cmd_proxy_set(Namespace(
            app="weather", endpoint="external",
            url="https://api.example.com", method="POST",
        ))
        patch_get_client.set_proxy.assert_called_once_with(
            "weather", "external", "https://api.example.com", method="POST",
        )

    def test_proxy_set_no_method(self, patch_get_client, capsys):
        patch_get_client.set_proxy.return_value = {"upstream_url": "https://api.example.com"}
        cmd_proxy_set(Namespace(
            app="weather", endpoint="external",
            url="https://api.example.com", method=None,
        ))
        # method=None means --method not passed, so no method kwarg
        patch_get_client.set_proxy.assert_called_once_with(
            "weather", "external", "https://api.example.com",
        )


# ── Encryption commands ────────────────────────────────────────────


class TestCmdEncryption:
    def test_encryption_status(self, patch_get_client, capsys):
        patch_get_client.get_encryption.return_value = {"encryption_enabled": True}
        cmd_encryption(Namespace(app="weather", endpoint="readings"))
        patch_get_client.get_encryption.assert_called_once_with("weather", "readings")
        assert json.loads(capsys.readouterr().out)["encryption_enabled"] is True


class TestCmdEncryptEnable:
    def test_enable_encryption_shows_key_warning(self, patch_get_client, capsys):
        patch_get_client.enable_encryption.return_value = {"key": "secret-key-123", "encryption_enabled": True}
        cmd_encrypt_enable(Namespace(app="weather", endpoint="readings"))
        patch_get_client.enable_encryption.assert_called_once_with("weather", "readings")
        stdout = capsys.readouterr()
        assert "secret-key-123" in stdout.out
        assert "Save this key" in stdout.err

    def test_enable_encryption_no_key_no_warning(self, patch_get_client, capsys):
        patch_get_client.enable_encryption.return_value = {"encryption_enabled": True}
        cmd_encrypt_enable(Namespace(app="weather", endpoint="readings"))
        stdout = capsys.readouterr()
        assert "Save this key" not in stdout.err


class TestCmdEncryptDisable:
    def test_disable_encryption(self, patch_get_client, capsys):
        cmd_encrypt_disable(Namespace(app="weather", endpoint="readings"))
        patch_get_client.disable_encryption.assert_called_once_with("weather", "readings")
        assert "Encryption disabled" in capsys.readouterr().out


# ── Logs command ────────────────────────────────────────────────────


class TestCmdLogs:
    def test_logs(self, patch_get_client, capsys):
        patch_get_client.request_logs.return_value = [{"status_code": 200, "method": "GET"}]
        cmd_logs(Namespace(app="weather", endpoint="readings"))
        patch_get_client.request_logs.assert_called_once_with("weather", "readings")
        out = json.loads(capsys.readouterr().out)
        assert out[0]["status_code"] == 200


# ── Webhook commands ────────────────────────────────────────────────


class TestCmdWebhooks:
    def test_webhooks_list(self, patch_get_client, capsys):
        patch_get_client.webhooks.return_value = [
            {"uuid": "wh-1", "target_url": "https://hook.example.com", "is_active": True, "events": ["record.created"]},
        ]
        cmd_webhooks(Namespace(app="weather", endpoint="readings"))
        patch_get_client.webhooks.assert_called_once_with("weather", "readings")
        out = capsys.readouterr().out
        assert "hook.example.com" in out
        assert "record.created" in out

    def test_webhooks_non_list(self, patch_get_client, capsys):
        patch_get_client.webhooks.return_value = {"count": 0}
        cmd_webhooks(Namespace(app="weather", endpoint="readings"))
        assert json.loads(capsys.readouterr().out) == {"count": 0}


class TestCmdWebhookGet:
    def test_webhook_get(self, patch_get_client, capsys):
        patch_get_client.get_webhook.return_value = {"uuid": "wh-1", "target_url": "https://hook.example.com"}
        cmd_webhook_get(Namespace(app="weather", endpoint="readings", uuid="wh-1"))
        patch_get_client.get_webhook.assert_called_once_with("weather", "readings", "wh-1")


class TestCmdWebhookCreate:
    def test_create_webhook_basic(self, patch_get_client, capsys):
        patch_get_client.create_webhook.return_value = {"uuid": "wh-new"}
        cmd_webhook_create(Namespace(
            app="weather", endpoint="readings",
            url="https://hook.example.com",
            events="record.created,record.updated",
            secret=None,
        ))
        patch_get_client.create_webhook.assert_called_once_with(
            "weather", "readings", "https://hook.example.com",
            ["record.created", "record.updated"],
            secret=None,
        )

    def test_create_webhook_with_secret(self, patch_get_client, capsys):
        patch_get_client.create_webhook.return_value = {"uuid": "wh-new"}
        cmd_webhook_create(Namespace(
            app="weather", endpoint="readings",
            url="https://hook.example.com",
            events="record.created",
            secret="my-secret",
        ))
        patch_get_client.create_webhook.assert_called_once_with(
            "weather", "readings", "https://hook.example.com",
            ["record.created"],
            secret="my-secret",
        )


class TestCmdWebhookUpdate:
    def test_update_webhook_url(self, patch_get_client, capsys):
        patch_get_client.update_webhook.return_value = {"uuid": "wh-1"}
        cmd_webhook_update(Namespace(
            app="weather", endpoint="readings", uuid="wh-1",
            url="https://new.example.com", events=None, active=None, secret=None,
        ))
        patch_get_client.update_webhook.assert_called_once_with(
            "weather", "readings", "wh-1",
            target_url="https://new.example.com",
        )

    def test_update_webhook_events(self, patch_get_client, capsys):
        patch_get_client.update_webhook.return_value = {"uuid": "wh-1"}
        cmd_webhook_update(Namespace(
            app="weather", endpoint="readings", uuid="wh-1",
            url=None, events="record.deleted", active=None, secret=None,
        ))
        patch_get_client.update_webhook.assert_called_once_with(
            "weather", "readings", "wh-1",
            events=["record.deleted"],
        )

    def test_update_webhook_active_and_secret(self, patch_get_client, capsys):
        patch_get_client.update_webhook.return_value = {"uuid": "wh-1"}
        cmd_webhook_update(Namespace(
            app="weather", endpoint="readings", uuid="wh-1",
            url=None, events=None, active=True, secret="new-secret",
        ))
        patch_get_client.update_webhook.assert_called_once_with(
            "weather", "readings", "wh-1",
            is_active=True, secret="new-secret",
        )

    def test_update_webhook_no_args(self, patch_get_client, capsys):
        patch_get_client.update_webhook.return_value = {"uuid": "wh-1"}
        cmd_webhook_update(Namespace(
            app="weather", endpoint="readings", uuid="wh-1",
            url=None, events=None, active=None, secret=None,
        ))
        patch_get_client.update_webhook.assert_called_once_with(
            "weather", "readings", "wh-1",
        )


class TestCmdWebhookDelete:
    def test_delete_webhook(self, patch_get_client, capsys):
        cmd_webhook_delete(Namespace(app="weather", endpoint="readings", uuid="wh-1"))
        patch_get_client.delete_webhook.assert_called_once_with("weather", "readings", "wh-1")
        assert "Deleted webhook: wh-1" in capsys.readouterr().out


# ── Key commands ────────────────────────────────────────────────────


class TestCmdKeys:
    def test_keys(self, patch_get_client, capsys):
        patch_get_client.app_keys.return_value = [{"uuid": "k1", "prefix": "mms_"}]
        cmd_keys(Namespace(app="weather"))
        patch_get_client.app_keys.assert_called_once_with("weather")


class TestCmdKeyCreate:
    def test_key_create_shows_warning(self, patch_get_client, capsys):
        patch_get_client.create_app_key.return_value = {"key": "mms_abc123", "uuid": "k1"}
        cmd_key_create(Namespace(app="weather"))
        patch_get_client.create_app_key.assert_called_once_with("weather")
        stdout = capsys.readouterr()
        assert "mms_abc123" in stdout.out
        assert "Save this key" in stdout.err

    def test_key_create_no_key_field(self, patch_get_client, capsys):
        patch_get_client.create_app_key.return_value = {"uuid": "k1"}
        cmd_key_create(Namespace(app="weather"))
        stdout = capsys.readouterr()
        assert "Save this key" not in stdout.err


class TestCmdKeyDelete:
    def test_key_delete(self, patch_get_client, capsys):
        cmd_key_delete(Namespace(app="weather", uuid="key-uuid"))
        patch_get_client.delete_app_key.assert_called_once_with("weather", "key-uuid")
        assert "Deactivated key: key-uuid" in capsys.readouterr().out


# ── Dashboard commands ──────────────────────────────────────────────


class TestCmdDashboards:
    def test_dashboards_list(self, patch_get_client, capsys):
        patch_get_client.dashboards.return_value = [
            {"slug": "my-room", "name": "My Room"},
        ]
        cmd_dashboards(Namespace())
        patch_get_client.dashboards.assert_called_once()
        out = capsys.readouterr().out
        assert "my-room" in out
        assert "My Room" in out

    def test_dashboards_non_list(self, patch_get_client, capsys):
        patch_get_client.dashboards.return_value = {"error": "forbidden"}
        cmd_dashboards(Namespace())
        assert json.loads(capsys.readouterr().out) == {"error": "forbidden"}


class TestCmdDashboardGet:
    def test_dashboard_get(self, patch_get_client, capsys):
        patch_get_client.get_dashboard.return_value = {"slug": "my-room", "name": "My Room"}
        cmd_dashboard_get(Namespace(slug="my-room"))
        patch_get_client.get_dashboard.assert_called_once_with("my-room")


class TestCmdDashboardCreate:
    def test_dashboard_create(self, patch_get_client, capsys):
        patch_get_client.create_dashboard.return_value = {"slug": "my-room"}
        cmd_dashboard_create(Namespace(name="My Room", slug="my-room", description="A room"))
        patch_get_client.create_dashboard.assert_called_once_with(
            "My Room", "my-room", description="A room",
        )

    def test_dashboard_create_no_desc(self, patch_get_client, capsys):
        patch_get_client.create_dashboard.return_value = {"slug": "my-room"}
        cmd_dashboard_create(Namespace(name="My Room", slug="my-room", description=None))
        patch_get_client.create_dashboard.assert_called_once_with(
            "My Room", "my-room", description="",
        )


class TestCmdDashboardUpdate:
    def test_dashboard_update_name(self, patch_get_client, capsys):
        patch_get_client.update_dashboard.return_value = {"slug": "my-room"}
        cmd_dashboard_update(Namespace(slug="my-room", name="Living Room", description=None))
        patch_get_client.update_dashboard.assert_called_once_with(
            "my-room", name="Living Room",
        )

    def test_dashboard_update_description(self, patch_get_client, capsys):
        patch_get_client.update_dashboard.return_value = {"slug": "my-room"}
        cmd_dashboard_update(Namespace(slug="my-room", name=None, description="Updated"))
        patch_get_client.update_dashboard.assert_called_once_with(
            "my-room", description="Updated",
        )

    def test_dashboard_update_no_args(self, patch_get_client, capsys):
        patch_get_client.update_dashboard.return_value = {"slug": "my-room"}
        cmd_dashboard_update(Namespace(slug="my-room", name=None, description=None))
        patch_get_client.update_dashboard.assert_called_once_with("my-room")


class TestCmdDashboardDelete:
    def test_dashboard_delete(self, patch_get_client, capsys):
        cmd_dashboard_delete(Namespace(slug="my-room"))
        patch_get_client.delete_dashboard.assert_called_once_with("my-room")
        assert "Deleted dashboard: my-room" in capsys.readouterr().out


# ── Widget commands ─────────────────────────────────────────────────


class TestCmdWidgets:
    def test_widgets(self, patch_get_client, capsys):
        patch_get_client.dashboard_widgets.return_value = [{"uuid": "w1", "label": "Lights"}]
        cmd_widgets(Namespace(dashboard="my-room"))
        patch_get_client.dashboard_widgets.assert_called_once_with("my-room")


class TestCmdWidgetCreate:
    def test_widget_create(self, patch_get_client, capsys):
        patch_get_client.create_dashboard_widget.return_value = {"uuid": "w-new"}
        cmd_widget_create(Namespace(
            dashboard="my-room", endpoint_id="ep-uuid",
            key_path="lights_on", widget_type="toggle", label="Lights",
        ))
        patch_get_client.create_dashboard_widget.assert_called_once_with(
            "my-room", "ep-uuid", "lights_on", "toggle", "Lights",
        )


class TestCmdWidgetUpdate:
    def test_widget_update_label(self, patch_get_client, capsys):
        patch_get_client.update_dashboard_widget.return_value = {"uuid": "w1"}
        cmd_widget_update(Namespace(
            dashboard="my-room", uuid="w1",
            label="Bedroom Lights", type=None, key_path=None, sort_order=None,
        ))
        patch_get_client.update_dashboard_widget.assert_called_once_with(
            "my-room", "w1", label="Bedroom Lights",
        )

    def test_widget_update_type(self, patch_get_client, capsys):
        patch_get_client.update_dashboard_widget.return_value = {"uuid": "w1"}
        cmd_widget_update(Namespace(
            dashboard="my-room", uuid="w1",
            label=None, type="slider", key_path=None, sort_order=None,
        ))
        patch_get_client.update_dashboard_widget.assert_called_once_with(
            "my-room", "w1", widget_type="slider",
        )

    def test_widget_update_key_path_and_sort_order(self, patch_get_client, capsys):
        patch_get_client.update_dashboard_widget.return_value = {"uuid": "w1"}
        cmd_widget_update(Namespace(
            dashboard="my-room", uuid="w1",
            label=None, type=None, key_path="brightness", sort_order=3,
        ))
        patch_get_client.update_dashboard_widget.assert_called_once_with(
            "my-room", "w1", key_path="brightness", sort_order=3,
        )

    def test_widget_update_no_args(self, patch_get_client, capsys):
        patch_get_client.update_dashboard_widget.return_value = {"uuid": "w1"}
        cmd_widget_update(Namespace(
            dashboard="my-room", uuid="w1",
            label=None, type=None, key_path=None, sort_order=None,
        ))
        patch_get_client.update_dashboard_widget.assert_called_once_with(
            "my-room", "w1",
        )


class TestCmdWidgetDelete:
    def test_widget_delete(self, patch_get_client, capsys):
        cmd_widget_delete(Namespace(dashboard="my-room", uuid="w1"))
        patch_get_client.delete_dashboard_widget.assert_called_once_with("my-room", "w1")
        assert "Deleted widget: w1" in capsys.readouterr().out


# ── Dashboard data and patch ────────────────────────────────────────


class TestCmdDashboardData:
    def test_dashboard_data(self, patch_get_client, capsys):
        patch_get_client.dashboard_data.return_value = {"widgets": [], "endpoints": {}}
        cmd_dashboard_data(Namespace(dashboard="my-room"))
        patch_get_client.dashboard_data.assert_called_once_with("my-room")
        assert json.loads(capsys.readouterr().out) == {"widgets": [], "endpoints": {}}


class TestCmdDashboardPatch:
    def test_dashboard_patch_json_value(self, patch_get_client, capsys):
        patch_get_client.dashboard_patch.return_value = {"ok": True}
        cmd_dashboard_patch(Namespace(
            dashboard="my-room", endpoint_uuid="ep-uuid",
            key_path="lights_on", value="true",
        ))
        patch_get_client.dashboard_patch.assert_called_once_with(
            "my-room", "ep-uuid", "lights_on", True,
        )

    def test_dashboard_patch_string_value(self, patch_get_client, capsys):
        patch_get_client.dashboard_patch.return_value = {"ok": True}
        cmd_dashboard_patch(Namespace(
            dashboard="my-room", endpoint_uuid="ep-uuid",
            key_path="color", value="red",
        ))
        patch_get_client.dashboard_patch.assert_called_once_with(
            "my-room", "ep-uuid", "color", "red",
        )

    def test_dashboard_patch_numeric_value(self, patch_get_client, capsys):
        patch_get_client.dashboard_patch.return_value = {"ok": True}
        cmd_dashboard_patch(Namespace(
            dashboard="my-room", endpoint_uuid="ep-uuid",
            key_path="brightness", value="75",
        ))
        patch_get_client.dashboard_patch.assert_called_once_with(
            "my-room", "ep-uuid", "brightness", 75,
        )


# ── Get / Aggregate / CSV commands ──────────────────────────────────


class TestCmdGet:
    def test_get_no_filters(self, patch_get_client, capsys):
        patch_get_client.get.return_value = {"temperature": 22}
        cmd_get(Namespace(app="weather", endpoint="readings", filters=[]))
        patch_get_client.get.assert_called_once_with("weather", "readings")
        assert json.loads(capsys.readouterr().out) == {"temperature": 22}

    def test_get_with_filters(self, patch_get_client, capsys):
        patch_get_client.get.return_value = [{"temperature": 25}]
        cmd_get(Namespace(app="weather", endpoint="readings", filters=["temperature__gte=20"]))
        patch_get_client.get.assert_called_once_with("weather", "readings", temperature__gte=20)


class TestCmdAggregate:
    def test_aggregate_basic(self, patch_get_client, capsys):
        patch_get_client.aggregate.return_value = {"field": "temp", "aggregations": {"avg": 22.3}}
        cmd_aggregate(Namespace(
            app="weather", endpoint="readings",
            aggregates="avg,max", field="temp", filters=[],
        ))
        patch_get_client.aggregate.assert_called_once_with(
            "weather", "readings", ["avg", "max"], field="temp",
        )

    def test_aggregate_with_filters(self, patch_get_client, capsys):
        patch_get_client.aggregate.return_value = {"count": 5}
        cmd_aggregate(Namespace(
            app="weather", endpoint="readings",
            aggregates="count", field=None, filters=["city=London"],
        ))
        patch_get_client.aggregate.assert_called_once_with(
            "weather", "readings", ["count"], field=None, city="London",
        )


class TestCmdCsv:
    def test_csv_no_filters(self, patch_get_client, capsys):
        patch_get_client.export_csv.return_value = "temp,humidity\n22.5,65\n"
        cmd_csv(Namespace(app="weather", endpoint="readings", filters=[]))
        patch_get_client.export_csv.assert_called_once_with("weather", "readings")
        assert "temp,humidity" in capsys.readouterr().out

    def test_csv_with_filters(self, patch_get_client, capsys):
        patch_get_client.export_csv.return_value = "temp\n25\n"
        cmd_csv(Namespace(app="weather", endpoint="readings", filters=["temp__gte=20"]))
        patch_get_client.export_csv.assert_called_once_with("weather", "readings", temp__gte=20)


# ── Public dashboard ────────────────────────────────────────────────


class TestCmdPublicDashboard:
    def test_public_dashboard(self, patch_get_client, capsys):
        patch_get_client.public_dashboard.return_value = {"dashboard": {"name": "My Room"}}
        cmd_public_dashboard(Namespace(token="abc123"))
        patch_get_client.public_dashboard.assert_called_once_with("abc123")
        assert json.loads(capsys.readouterr().out)["dashboard"]["name"] == "My Room"


# ── Platform token commands ─────────────────────────────────────────


class TestCmdPlatformTokens:
    def test_platform_tokens_list(self, patch_get_client, capsys):
        patch_get_client.platform_tokens.return_value = [
            {"name": "my-pi", "prefix": "mms_", "created": "2026-01-01", "last_used": "2026-02-01"},
        ]
        cmd_platform_tokens(Namespace())
        patch_get_client.platform_tokens.assert_called_once()
        out = capsys.readouterr().out
        assert "my-pi" in out
        assert "mms_" in out

    def test_platform_tokens_non_list(self, patch_get_client, capsys):
        patch_get_client.platform_tokens.return_value = {"error": "nope"}
        cmd_platform_tokens(Namespace())
        assert json.loads(capsys.readouterr().out) == {"error": "nope"}


class TestCmdPlatformTokenCreate:
    def test_create_shows_key_warning(self, patch_get_client, capsys):
        patch_get_client.create_platform_token.return_value = {"key": "mms_secretkey", "uuid": "t1"}
        cmd_platform_token_create(Namespace(name="my-pi"))
        patch_get_client.create_platform_token.assert_called_once_with("my-pi")
        stdout = capsys.readouterr()
        assert "mms_secretkey" in stdout.out or "mms_secretkey" in stdout.err
        assert "Save this key" in stdout.err

    def test_create_no_key_field(self, patch_get_client, capsys):
        patch_get_client.create_platform_token.return_value = {"uuid": "t1"}
        cmd_platform_token_create(Namespace(name="my-pi"))
        stdout = capsys.readouterr()
        assert "Save this key" not in stdout.err


class TestCmdPlatformTokenRevoke:
    def test_revoke(self, patch_get_client, capsys):
        cmd_platform_token_revoke(Namespace(uuid="token-uuid"))
        patch_get_client.revoke_platform_token.assert_called_once_with("token-uuid")
        assert "Revoked platform token: token-uuid" in capsys.readouterr().out


# ── Billing ─────────────────────────────────────────────────────────


class TestCmdBillingStatus:
    def test_billing_status_dict(self, patch_get_client, capsys):
        patch_get_client.billing_status.return_value = {
            "plan": "free", "apps_used": 2, "apps_limit": 5,
        }
        cmd_billing_status(Namespace())
        patch_get_client.billing_status.assert_called_once()
        out = capsys.readouterr().out
        assert "Plan: free" in out
        assert "apps_used" in out

    def test_billing_status_non_dict(self, patch_get_client, capsys):
        patch_get_client.billing_status.return_value = "unexpected"
        cmd_billing_status(Namespace())
        out = capsys.readouterr().out
        assert "unexpected" in out


# ── Field types ─────────────────────────────────────────────────────


class TestCmdFieldTypes:
    def test_field_types_list_of_dicts(self, patch_get_client, capsys):
        patch_get_client.field_types.return_value = [
            {"value": "text", "label": "Text"},
            {"value": "number", "label": "Number"},
        ]
        cmd_field_types(Namespace())
        patch_get_client.field_types.assert_called_once()
        out = capsys.readouterr().out
        assert "text" in out
        assert "number" in out

    def test_field_types_list_of_strings(self, patch_get_client, capsys):
        patch_get_client.field_types.return_value = ["text", "number"]
        cmd_field_types(Namespace())
        out = capsys.readouterr().out
        assert "text" in out
        assert "number" in out

    def test_field_types_non_list(self, patch_get_client, capsys):
        patch_get_client.field_types.return_value = {"error": "nope"}
        cmd_field_types(Namespace())
        assert json.loads(capsys.readouterr().out) == {"error": "nope"}


# ── main() integration tests ───────────────────────────────────────


class TestMain:
    """Test main() dispatches to the correct handler via sys.argv."""

    def test_no_command_exits(self):
        with patch("sys.argv", ["meow"]):
            with pytest.raises(SystemExit) as exc:
                main()
            assert exc.value.code == 1

    @patch("meow_sdk.cli.get_client")
    def test_send_via_main(self, mock_get_client, capsys):
        client = MagicMock()
        client.send.return_value = {"uuid": "r1"}
        mock_get_client.return_value = client
        with patch("sys.argv", ["meow", "send", "myapp", "myep", "temp=22"]):
            main()
        client.send.assert_called_once_with("myapp", "myep", {"temp": 22})
        assert json.loads(capsys.readouterr().out) == {"uuid": "r1"}

    @patch("meow_sdk.cli.get_client")
    def test_get_via_main(self, mock_get_client, capsys):
        client = MagicMock()
        client.get.return_value = {"temp": 22}
        mock_get_client.return_value = client
        with patch("sys.argv", ["meow", "get", "myapp", "myep"]):
            main()
        client.get.assert_called_once_with("myapp", "myep")

    @patch("meow_sdk.cli.get_client")
    def test_apps_via_main(self, mock_get_client, capsys):
        client = MagicMock()
        client.apps.return_value = [{"slug": "app1", "name": "App One"}]
        mock_get_client.return_value = client
        with patch("sys.argv", ["meow", "apps"]):
            main()
        client.apps.assert_called_once()
        assert "app1" in capsys.readouterr().out

    @patch("meow_sdk.cli.get_client")
    def test_records_via_main(self, mock_get_client, capsys):
        client = MagicMock()
        client.records.return_value = {"results": []}
        mock_get_client.return_value = client
        with patch("sys.argv", ["meow", "records", "myapp", "myep", "--limit", "10"]):
            main()
        client.records.assert_called_once_with("myapp", "myep", limit=10)

    @patch("meow_sdk.cli.get_client")
    def test_aggregate_via_main(self, mock_get_client, capsys):
        client = MagicMock()
        client.aggregate.return_value = {"avg": 22}
        mock_get_client.return_value = client
        with patch("sys.argv", ["meow", "aggregate", "myapp", "myep", "avg,max", "--field", "temp"]):
            main()
        client.aggregate.assert_called_once_with(
            "myapp", "myep", ["avg", "max"], field="temp",
        )

    @patch("meow_sdk.cli.get_client")
    def test_csv_via_main(self, mock_get_client, capsys):
        client = MagicMock()
        client.export_csv.return_value = "a,b\n1,2\n"
        mock_get_client.return_value = client
        with patch("sys.argv", ["meow", "csv", "myapp", "myep"]):
            main()
        client.export_csv.assert_called_once_with("myapp", "myep")

    @patch("meow_sdk.cli.get_client")
    def test_create_app_via_main(self, mock_get_client, capsys):
        client = MagicMock()
        client.create_app.return_value = {"slug": "new-app"}
        mock_get_client.return_value = client
        with patch("sys.argv", ["meow", "create-app", "New App", "new-app", "--description", "A new app", "--private"]):
            main()
        client.create_app.assert_called_once_with(
            "New App", "new-app", description="A new app", is_public=False,
        )

    @patch("meow_sdk.cli.get_client")
    def test_create_endpoint_via_main(self, mock_get_client, capsys):
        client = MagicMock()
        client.create_endpoint.return_value = {"slug": "readings"}
        mock_get_client.return_value = client
        with patch("sys.argv", ["meow", "create-endpoint", "weather", "Readings", "readings", "collection"]):
            main()
        client.create_endpoint.assert_called_once_with(
            "weather", "Readings", "readings", "collection",
            description="", is_public=True,
        )

    @patch("meow_sdk.cli.get_client")
    def test_update_endpoint_via_main(self, mock_get_client, capsys):
        client = MagicMock()
        client.update_endpoint.return_value = {"slug": "readings"}
        mock_get_client.return_value = client
        with patch("sys.argv", ["meow", "update-endpoint", "weather", "readings", "--delay-ms", "500", "--error-rate", "0.1", "--ttl", "3600"]):
            main()
        client.update_endpoint.assert_called_once_with(
            "weather", "readings",
            delay_ms=500, error_rate=0.1, ttl_seconds=3600,
        )

    @patch("meow_sdk.cli.get_client")
    def test_delete_app_via_main(self, mock_get_client, capsys):
        client = MagicMock()
        mock_get_client.return_value = client
        with patch("sys.argv", ["meow", "delete-app", "old-app"]):
            main()
        client.delete_app.assert_called_once_with("old-app")

    @patch("meow_sdk.cli.get_client")
    def test_widget_create_via_main(self, mock_get_client, capsys):
        client = MagicMock()
        client.create_dashboard_widget.return_value = {"uuid": "w1"}
        mock_get_client.return_value = client
        with patch("sys.argv", ["meow", "widget-create", "my-room", "ep-uuid", "lights_on", "toggle", "Lights"]):
            main()
        client.create_dashboard_widget.assert_called_once_with(
            "my-room", "ep-uuid", "lights_on", "toggle", "Lights",
        )

    @patch("meow_sdk.cli.get_client")
    def test_dashboard_patch_via_main(self, mock_get_client, capsys):
        client = MagicMock()
        client.dashboard_patch.return_value = {"ok": True}
        mock_get_client.return_value = client
        with patch("sys.argv", ["meow", "dashboard-patch", "my-room", "ep-uuid", "lights_on", "true"]):
            main()
        client.dashboard_patch.assert_called_once_with(
            "my-room", "ep-uuid", "lights_on", True,
        )

    @patch("meow_sdk.cli.get_client")
    def test_field_types_via_main(self, mock_get_client, capsys):
        client = MagicMock()
        client.field_types.return_value = [{"value": "text", "label": "Text"}]
        mock_get_client.return_value = client
        with patch("sys.argv", ["meow", "field-types"]):
            main()
        client.field_types.assert_called_once()

    @patch("meow_sdk.cli.get_client")
    def test_billing_status_via_main(self, mock_get_client, capsys):
        client = MagicMock()
        client.billing_status.return_value = {"plan": "free"}
        mock_get_client.return_value = client
        with patch("sys.argv", ["meow", "billing-status"]):
            main()
        client.billing_status.assert_called_once()

    @patch("meow_sdk.cli.get_client")
    def test_platform_tokens_via_main(self, mock_get_client, capsys):
        client = MagicMock()
        client.platform_tokens.return_value = []
        mock_get_client.return_value = client
        with patch("sys.argv", ["meow", "platform-tokens"]):
            main()
        client.platform_tokens.assert_called_once()

    @patch("meow_sdk.cli.get_client")
    def test_platform_token_create_via_main(self, mock_get_client, capsys):
        client = MagicMock()
        client.create_platform_token.return_value = {"uuid": "t1"}
        mock_get_client.return_value = client
        with patch("sys.argv", ["meow", "platform-token-create", "my-pi"]):
            main()
        client.create_platform_token.assert_called_once_with("my-pi")

    @patch("meow_sdk.cli.get_client")
    def test_platform_token_revoke_via_main(self, mock_get_client, capsys):
        client = MagicMock()
        mock_get_client.return_value = client
        with patch("sys.argv", ["meow", "platform-token-revoke", "token-uuid"]):
            main()
        client.revoke_platform_token.assert_called_once_with("token-uuid")

    @patch("meow_sdk.cli.get_client")
    def test_public_dashboard_via_main(self, mock_get_client, capsys):
        client = MagicMock()
        client.public_dashboard.return_value = {"dashboard": {"name": "Shared"}}
        mock_get_client.return_value = client
        with patch("sys.argv", ["meow", "public-dashboard", "share-token-abc"]):
            main()
        client.public_dashboard.assert_called_once_with("share-token-abc")

    @patch("meow_sdk.cli.get_client")
    def test_exception_exits_with_error(self, mock_get_client, capsys):
        client = MagicMock()
        client.apps.side_effect = RuntimeError("connection refused")
        mock_get_client.return_value = client
        with patch("sys.argv", ["meow", "apps"]):
            with pytest.raises(SystemExit) as exc:
                main()
            assert exc.value.code == 1
        assert "connection refused" in capsys.readouterr().err

    @patch("meow_sdk.cli.get_client")
    def test_get_app_via_main(self, mock_get_client, capsys):
        client = MagicMock()
        client.get_app.return_value = {"slug": "myapp"}
        mock_get_client.return_value = client
        with patch("sys.argv", ["meow", "get-app", "myapp"]):
            main()
        client.get_app.assert_called_once_with("myapp")

    @patch("meow_sdk.cli.get_client")
    def test_update_app_via_main(self, mock_get_client, capsys):
        client = MagicMock()
        client.update_app.return_value = {"slug": "myapp"}
        mock_get_client.return_value = client
        with patch("sys.argv", ["meow", "update-app", "myapp", "--name", "New Name", "--public"]):
            main()
        client.update_app.assert_called_once_with("myapp", name="New Name", is_public=True)

    @patch("meow_sdk.cli.get_client")
    def test_get_endpoint_via_main(self, mock_get_client, capsys):
        client = MagicMock()
        client.get_endpoint.return_value = {"slug": "readings"}
        mock_get_client.return_value = client
        with patch("sys.argv", ["meow", "get-endpoint", "weather", "readings"]):
            main()
        client.get_endpoint.assert_called_once_with("weather", "readings")

    @patch("meow_sdk.cli.get_client")
    def test_delete_endpoint_via_main(self, mock_get_client, capsys):
        client = MagicMock()
        mock_get_client.return_value = client
        with patch("sys.argv", ["meow", "delete-endpoint", "weather", "readings"]):
            main()
        client.delete_endpoint.assert_called_once_with("weather", "readings")

    @patch("meow_sdk.cli.get_client")
    def test_endpoints_via_main(self, mock_get_client, capsys):
        client = MagicMock()
        client.endpoints.return_value = []
        mock_get_client.return_value = client
        with patch("sys.argv", ["meow", "endpoints", "weather"]):
            main()
        client.endpoints.assert_called_once_with("weather")

    @patch("meow_sdk.cli.get_client")
    def test_fields_via_main(self, mock_get_client, capsys):
        client = MagicMock()
        client.fields.return_value = []
        mock_get_client.return_value = client
        with patch("sys.argv", ["meow", "fields", "weather", "readings"]):
            main()
        client.fields.assert_called_once_with("weather", "readings")

    @patch("meow_sdk.cli.get_client")
    def test_create_field_via_main(self, mock_get_client, capsys):
        client = MagicMock()
        client.create_field.return_value = {"name": "temp"}
        mock_get_client.return_value = client
        with patch("sys.argv", ["meow", "create-field", "weather", "readings", "temp", "Temperature", "number", "--required"]):
            main()
        client.create_field.assert_called_once_with(
            "weather", "readings", "temp", "Temperature", "number", required=True,
        )

    @patch("meow_sdk.cli.get_client")
    def test_update_field_via_main(self, mock_get_client, capsys):
        client = MagicMock()
        client.update_field.return_value = {"uuid": "f1"}
        mock_get_client.return_value = client
        with patch("sys.argv", ["meow", "update-field", "weather", "readings", "f1", "--label", "Temp (C)"]):
            main()
        client.update_field.assert_called_once_with(
            "weather", "readings", "f1", label="Temp (C)",
        )

    @patch("meow_sdk.cli.get_client")
    def test_delete_field_via_main(self, mock_get_client, capsys):
        client = MagicMock()
        mock_get_client.return_value = client
        with patch("sys.argv", ["meow", "delete-field", "weather", "readings", "f1"]):
            main()
        client.delete_field.assert_called_once_with("weather", "readings", "f1")

    @patch("meow_sdk.cli.get_client")
    def test_get_record_via_main(self, mock_get_client, capsys):
        client = MagicMock()
        client.get_record.return_value = {"uuid": "r1"}
        mock_get_client.return_value = client
        with patch("sys.argv", ["meow", "get-record", "weather", "readings", "r1"]):
            main()
        client.get_record.assert_called_once_with("weather", "readings", "r1")

    @patch("meow_sdk.cli.get_client")
    def test_update_record_via_main(self, mock_get_client, capsys):
        client = MagicMock()
        client.update.return_value = {"uuid": "r1"}
        mock_get_client.return_value = client
        with patch("sys.argv", ["meow", "update-record", "weather", "readings", "r1", "temp=25"]):
            main()
        client.update.assert_called_once_with("weather", "readings", "r1", {"temp": 25})

    @patch("meow_sdk.cli.get_client")
    def test_delete_record_via_main(self, mock_get_client, capsys):
        client = MagicMock()
        mock_get_client.return_value = client
        with patch("sys.argv", ["meow", "delete-record", "weather", "readings", "r1"]):
            main()
        client.delete_record.assert_called_once_with("weather", "readings", "r1")

    @patch("meow_sdk.cli.get_client")
    def test_payload_get_via_main(self, mock_get_client, capsys):
        client = MagicMock()
        client.get_payload.return_value = {"open": True}
        mock_get_client.return_value = client
        with patch("sys.argv", ["meow", "payload-get", "weather", "status"]):
            main()
        client.get_payload.assert_called_once_with("weather", "status")

    @patch("meow_sdk.cli.get_client")
    def test_payload_set_via_main(self, mock_get_client, capsys):
        client = MagicMock()
        client.set_payload.return_value = {"data": {"open": False}}
        mock_get_client.return_value = client
        with patch("sys.argv", ["meow", "payload-set", "weather", "status", "open=false"]):
            main()
        client.set_payload.assert_called_once_with("weather", "status", {"open": False})

    @patch("meow_sdk.cli.get_client")
    def test_proxy_get_via_main(self, mock_get_client, capsys):
        client = MagicMock()
        client.get_proxy.return_value = {"upstream_url": "http://example.com"}
        mock_get_client.return_value = client
        with patch("sys.argv", ["meow", "proxy-get", "weather", "external"]):
            main()
        client.get_proxy.assert_called_once_with("weather", "external")

    @patch("meow_sdk.cli.get_client")
    def test_proxy_set_via_main(self, mock_get_client, capsys):
        client = MagicMock()
        client.set_proxy.return_value = {"upstream_url": "http://api.example.com"}
        mock_get_client.return_value = client
        with patch("sys.argv", ["meow", "proxy-set", "weather", "external", "http://api.example.com", "--method", "POST"]):
            main()
        client.set_proxy.assert_called_once_with(
            "weather", "external", "http://api.example.com", method="POST",
        )

    @patch("meow_sdk.cli.get_client")
    def test_encryption_via_main(self, mock_get_client, capsys):
        client = MagicMock()
        client.get_encryption.return_value = {"encryption_enabled": False}
        mock_get_client.return_value = client
        with patch("sys.argv", ["meow", "encryption", "weather", "readings"]):
            main()
        client.get_encryption.assert_called_once_with("weather", "readings")

    @patch("meow_sdk.cli.get_client")
    def test_encrypt_enable_via_main(self, mock_get_client, capsys):
        client = MagicMock()
        client.enable_encryption.return_value = {"key": "secret", "encryption_enabled": True}
        mock_get_client.return_value = client
        with patch("sys.argv", ["meow", "encrypt-enable", "weather", "readings"]):
            main()
        client.enable_encryption.assert_called_once_with("weather", "readings")

    @patch("meow_sdk.cli.get_client")
    def test_encrypt_disable_via_main(self, mock_get_client, capsys):
        client = MagicMock()
        mock_get_client.return_value = client
        with patch("sys.argv", ["meow", "encrypt-disable", "weather", "readings"]):
            main()
        client.disable_encryption.assert_called_once_with("weather", "readings")

    @patch("meow_sdk.cli.get_client")
    def test_logs_via_main(self, mock_get_client, capsys):
        client = MagicMock()
        client.request_logs.return_value = []
        mock_get_client.return_value = client
        with patch("sys.argv", ["meow", "logs", "weather", "readings"]):
            main()
        client.request_logs.assert_called_once_with("weather", "readings")

    @patch("meow_sdk.cli.get_client")
    def test_webhooks_via_main(self, mock_get_client, capsys):
        client = MagicMock()
        client.webhooks.return_value = []
        mock_get_client.return_value = client
        with patch("sys.argv", ["meow", "webhooks", "weather", "readings"]):
            main()
        client.webhooks.assert_called_once_with("weather", "readings")

    @patch("meow_sdk.cli.get_client")
    def test_webhook_get_via_main(self, mock_get_client, capsys):
        client = MagicMock()
        client.get_webhook.return_value = {"uuid": "wh-1"}
        mock_get_client.return_value = client
        with patch("sys.argv", ["meow", "webhook-get", "weather", "readings", "wh-1"]):
            main()
        client.get_webhook.assert_called_once_with("weather", "readings", "wh-1")

    @patch("meow_sdk.cli.get_client")
    def test_webhook_create_via_main(self, mock_get_client, capsys):
        client = MagicMock()
        client.create_webhook.return_value = {"uuid": "wh-new"}
        mock_get_client.return_value = client
        with patch("sys.argv", ["meow", "webhook-create", "weather", "readings", "https://hook.example.com", "record.created,record.updated", "--secret", "s3cret"]):
            main()
        client.create_webhook.assert_called_once_with(
            "weather", "readings", "https://hook.example.com",
            ["record.created", "record.updated"], secret="s3cret",
        )

    @patch("meow_sdk.cli.get_client")
    def test_webhook_update_via_main(self, mock_get_client, capsys):
        client = MagicMock()
        client.update_webhook.return_value = {"uuid": "wh-1"}
        mock_get_client.return_value = client
        with patch("sys.argv", ["meow", "webhook-update", "weather", "readings", "wh-1", "--url", "https://new.example.com"]):
            main()
        client.update_webhook.assert_called_once_with(
            "weather", "readings", "wh-1", target_url="https://new.example.com",
        )

    @patch("meow_sdk.cli.get_client")
    def test_webhook_delete_via_main(self, mock_get_client, capsys):
        client = MagicMock()
        mock_get_client.return_value = client
        with patch("sys.argv", ["meow", "webhook-delete", "weather", "readings", "wh-1"]):
            main()
        client.delete_webhook.assert_called_once_with("weather", "readings", "wh-1")

    @patch("meow_sdk.cli.get_client")
    def test_dashboards_via_main(self, mock_get_client, capsys):
        client = MagicMock()
        client.dashboards.return_value = []
        mock_get_client.return_value = client
        with patch("sys.argv", ["meow", "dashboards"]):
            main()
        client.dashboards.assert_called_once()

    @patch("meow_sdk.cli.get_client")
    def test_dashboard_get_via_main(self, mock_get_client, capsys):
        client = MagicMock()
        client.get_dashboard.return_value = {"slug": "my-room"}
        mock_get_client.return_value = client
        with patch("sys.argv", ["meow", "dashboard-get", "my-room"]):
            main()
        client.get_dashboard.assert_called_once_with("my-room")

    @patch("meow_sdk.cli.get_client")
    def test_dashboard_create_via_main(self, mock_get_client, capsys):
        client = MagicMock()
        client.create_dashboard.return_value = {"slug": "my-room"}
        mock_get_client.return_value = client
        with patch("sys.argv", ["meow", "dashboard-create", "My Room", "my-room", "--description", "A room"]):
            main()
        client.create_dashboard.assert_called_once_with("My Room", "my-room", description="A room")

    @patch("meow_sdk.cli.get_client")
    def test_dashboard_update_via_main(self, mock_get_client, capsys):
        client = MagicMock()
        client.update_dashboard.return_value = {"slug": "my-room"}
        mock_get_client.return_value = client
        with patch("sys.argv", ["meow", "dashboard-update", "my-room", "--name", "Living Room"]):
            main()
        client.update_dashboard.assert_called_once_with("my-room", name="Living Room")

    @patch("meow_sdk.cli.get_client")
    def test_dashboard_delete_via_main(self, mock_get_client, capsys):
        client = MagicMock()
        mock_get_client.return_value = client
        with patch("sys.argv", ["meow", "dashboard-delete", "my-room"]):
            main()
        client.delete_dashboard.assert_called_once_with("my-room")

    @patch("meow_sdk.cli.get_client")
    def test_widgets_via_main(self, mock_get_client, capsys):
        client = MagicMock()
        client.dashboard_widgets.return_value = []
        mock_get_client.return_value = client
        with patch("sys.argv", ["meow", "widgets", "my-room"]):
            main()
        client.dashboard_widgets.assert_called_once_with("my-room")

    @patch("meow_sdk.cli.get_client")
    def test_widget_update_via_main(self, mock_get_client, capsys):
        client = MagicMock()
        client.update_dashboard_widget.return_value = {"uuid": "w1"}
        mock_get_client.return_value = client
        with patch("sys.argv", ["meow", "widget-update", "my-room", "w1", "--label", "New Label", "--sort-order", "2"]):
            main()
        client.update_dashboard_widget.assert_called_once_with(
            "my-room", "w1", label="New Label", sort_order=2,
        )

    @patch("meow_sdk.cli.get_client")
    def test_widget_delete_via_main(self, mock_get_client, capsys):
        client = MagicMock()
        mock_get_client.return_value = client
        with patch("sys.argv", ["meow", "widget-delete", "my-room", "w1"]):
            main()
        client.delete_dashboard_widget.assert_called_once_with("my-room", "w1")

    @patch("meow_sdk.cli.get_client")
    def test_dashboard_data_via_main(self, mock_get_client, capsys):
        client = MagicMock()
        client.dashboard_data.return_value = {"widgets": []}
        mock_get_client.return_value = client
        with patch("sys.argv", ["meow", "dashboard-data", "my-room"]):
            main()
        client.dashboard_data.assert_called_once_with("my-room")

    @patch("meow_sdk.cli.get_client")
    def test_keys_via_main(self, mock_get_client, capsys):
        client = MagicMock()
        client.app_keys.return_value = []
        mock_get_client.return_value = client
        with patch("sys.argv", ["meow", "keys", "weather"]):
            main()
        client.app_keys.assert_called_once_with("weather")

    @patch("meow_sdk.cli.get_client")
    def test_key_create_via_main(self, mock_get_client, capsys):
        client = MagicMock()
        client.create_app_key.return_value = {"uuid": "k1"}
        mock_get_client.return_value = client
        with patch("sys.argv", ["meow", "key-create", "weather"]):
            main()
        client.create_app_key.assert_called_once_with("weather")

    @patch("meow_sdk.cli.get_client")
    def test_key_delete_via_main(self, mock_get_client, capsys):
        client = MagicMock()
        mock_get_client.return_value = client
        with patch("sys.argv", ["meow", "key-delete", "weather", "k1"]):
            main()
        client.delete_app_key.assert_called_once_with("weather", "k1")

    @patch("meow_sdk.cli.get_client")
    def test_get_with_filters_via_main(self, mock_get_client, capsys):
        client = MagicMock()
        client.get.return_value = [{"temp": 25}]
        mock_get_client.return_value = client
        with patch("sys.argv", ["meow", "get", "weather", "readings", "temp__gte=20", "city=London"]):
            main()
        client.get.assert_called_once_with("weather", "readings", temp__gte=20, city="London")

    @patch("meow_sdk.cli.get_client")
    def test_csv_with_filters_via_main(self, mock_get_client, capsys):
        client = MagicMock()
        client.export_csv.return_value = "temp\n25\n"
        mock_get_client.return_value = client
        with patch("sys.argv", ["meow", "csv", "weather", "readings", "temp__gte=20"]):
            main()
        client.export_csv.assert_called_once_with("weather", "readings", temp__gte=20)
