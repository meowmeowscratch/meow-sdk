"""meow meow scratch CLI — send and read API data from your terminal.

Configure with environment variables:
    export MEOW_API_KEY=your-api-key
    export MEOW_USERNAME=your-username
    export MEOW_URL=https://meowmeowscratch.com  (optional)

Usage:
    meow send weather-app readings temperature=22.5 humidity=65
    meow get weather-app readings
    meow get weather-app readings temperature__gte=20
    meow aggregate weather-app readings avg,max --field temperature
    meow csv weather-app readings
    meow records weather-app readings
    meow apps
"""

import argparse
import json
import os
import sys

from .client import Meow


def get_client():
    base_url = os.environ.get('MEOW_URL', 'https://meowmeowscratch.com')
    username = os.environ.get('MEOW_USERNAME', '')
    api_key = os.environ.get('MEOW_API_KEY', '')
    return Meow(base_url=base_url, username=username or None, api_key=api_key or None)


def _parse_filters(pairs):
    """Parse key=value pairs into a dict, auto-detecting types."""
    filters = {}
    for pair in (pairs or []):
        key, sep, value = pair.partition('=')
        if not sep:
            print(f'Error: expected key=value, got: {pair}', file=sys.stderr)
            sys.exit(1)
        try:
            value = json.loads(value)
        except (json.JSONDecodeError, ValueError):
            pass
        filters[key] = value
    return filters


def _print(data):
    print(json.dumps(data, indent=2, default=str))


def cmd_send(args):
    client = get_client()
    data = _parse_filters(args.data)
    result = client.send(args.app, args.endpoint, data)
    _print(result)


def cmd_get(args):
    client = get_client()
    filters = _parse_filters(args.filters)
    result = client.get(args.app, args.endpoint, **filters)
    _print(result)


def cmd_aggregate(args):
    client = get_client()
    aggregates = [a.strip() for a in args.aggregates.split(',')]
    filters = _parse_filters(args.filters)
    result = client.aggregate(args.app, args.endpoint, aggregates,
                              field=args.field, **filters)
    _print(result)


def cmd_csv(args):
    client = get_client()
    filters = _parse_filters(args.filters)
    print(client.export_csv(args.app, args.endpoint, **filters))


def cmd_apps(args):
    client = get_client()
    result = client.apps()
    if isinstance(result, list):
        for app in result:
            print(f"  {app.get('slug', '?'):20s}  {app.get('name', '')}")
    else:
        _print(result)


def cmd_records(args):
    client = get_client()
    result = client.records(args.app, args.endpoint, limit=args.limit)
    _print(result)


def cmd_get_app(args):
    client = get_client()
    _print(client.get_app(args.app))


def cmd_create_app(args):
    client = get_client()
    result = client.create_app(args.name, args.slug,
                               description=args.description or '',
                               is_public=not args.private)
    _print(result)


def cmd_update_app(args):
    client = get_client()
    kwargs = {}
    if args.name is not None:
        kwargs['name'] = args.name
    if args.description is not None:
        kwargs['description'] = args.description
    if args.public:
        kwargs['is_public'] = True
    if args.private:
        kwargs['is_public'] = False
    result = client.update_app(args.app, **kwargs)
    _print(result)


def cmd_delete_app(args):
    client = get_client()
    client.delete_app(args.app)
    print(f'Deleted app: {args.app}')


def cmd_endpoints(args):
    client = get_client()
    result = client.endpoints(args.app)
    if isinstance(result, list):
        for ep in result:
            t = ep.get('endpoint_type', '?')
            print(f"  {ep.get('slug', '?'):20s}  [{t:10s}]  {ep.get('name', '')}")
    else:
        _print(result)


def cmd_get_endpoint(args):
    client = get_client()
    _print(client.get_endpoint(args.app, args.endpoint))


def cmd_create_endpoint(args):
    client = get_client()
    result = client.create_endpoint(args.app, args.name, args.slug,
                                     args.type, description=args.description or '',
                                     is_public=not args.private)
    _print(result)


def cmd_update_endpoint(args):
    client = get_client()
    kwargs = {}
    if args.name is not None:
        kwargs['name'] = args.name
    if args.description is not None:
        kwargs['description'] = args.description
    if args.public:
        kwargs['is_public'] = True
    if args.private:
        kwargs['is_public'] = False
    if args.delay_ms is not None:
        kwargs['delay_ms'] = args.delay_ms
    if args.error_rate is not None:
        kwargs['error_rate'] = args.error_rate
    if args.ttl is not None:
        kwargs['ttl_seconds'] = args.ttl
    result = client.update_endpoint(args.app, args.endpoint, **kwargs)
    _print(result)


def cmd_delete_endpoint(args):
    client = get_client()
    client.delete_endpoint(args.app, args.endpoint)
    print(f'Deleted endpoint: {args.app}/{args.endpoint}')


def cmd_fields(args):
    client = get_client()
    result = client.fields(args.app, args.endpoint)
    if isinstance(result, list):
        for f in result:
            req = '*' if f.get('required') else ' '
            print(f"  {req} {f.get('name', '?'):20s}  [{f.get('field_type', '?'):10s}]  {f.get('label', '')}")
    else:
        _print(result)


def cmd_create_field(args):
    client = get_client()
    kwargs = {}
    if args.required:
        kwargs['required'] = True
    result = client.create_field(args.app, args.endpoint, args.name,
                                  args.label, args.field_type, **kwargs)
    _print(result)


def cmd_update_field(args):
    client = get_client()
    kwargs = {}
    if args.label is not None:
        kwargs['label'] = args.label
    if args.required is not None:
        kwargs['required'] = args.required
    result = client.update_field(args.app, args.endpoint, args.uuid, **kwargs)
    _print(result)


def cmd_delete_field(args):
    client = get_client()
    client.delete_field(args.app, args.endpoint, args.uuid)
    print(f'Deleted field: {args.uuid}')


def cmd_update_record(args):
    client = get_client()
    data = _parse_filters(args.data)
    result = client.update(args.app, args.endpoint, args.uuid, data)
    _print(result)


def cmd_delete_record(args):
    client = get_client()
    client.delete_record(args.app, args.endpoint, args.uuid)
    print(f'Deleted record: {args.uuid}')


def cmd_get_record(args):
    client = get_client()
    _print(client.get_record(args.app, args.endpoint, args.uuid))


def cmd_payload_get(args):
    client = get_client()
    _print(client.get_payload(args.app, args.endpoint))


def cmd_payload_set(args):
    client = get_client()
    data = _parse_filters(args.data)
    result = client.set_payload(args.app, args.endpoint, data)
    _print(result)


def cmd_proxy_get(args):
    client = get_client()
    _print(client.get_proxy(args.app, args.endpoint))


def cmd_proxy_set(args):
    client = get_client()
    kwargs = {}
    if args.method:
        kwargs['method'] = args.method
    result = client.set_proxy(args.app, args.endpoint, args.url, **kwargs)
    _print(result)


def cmd_encryption(args):
    client = get_client()
    _print(client.get_encryption(args.app, args.endpoint))


def cmd_encrypt_enable(args):
    client = get_client()
    result = client.enable_encryption(args.app, args.endpoint)
    _print(result)
    if isinstance(result, dict) and 'key' in result:
        print('\n⚠️  Save this key! It will only be shown once.', file=sys.stderr)


def cmd_encrypt_disable(args):
    client = get_client()
    client.disable_encryption(args.app, args.endpoint)
    print('Encryption disabled.')


def cmd_logs(args):
    client = get_client()
    _print(client.request_logs(args.app, args.endpoint))


def cmd_webhooks(args):
    client = get_client()
    result = client.webhooks(args.app, args.endpoint)
    if isinstance(result, list):
        for wh in result:
            active = '✓' if wh.get('is_active') else '✗'
            events = ', '.join(wh.get('events', []))
            print(f"  [{active}] {wh.get('uuid', '?')[:8]}  {wh.get('target_url', '')}  ({events})")
    else:
        _print(result)


def cmd_webhook_create(args):
    client = get_client()
    events = [e.strip() for e in args.events.split(',')]
    result = client.create_webhook(args.app, args.endpoint, args.url, events,
                                    secret=args.secret)
    _print(result)


def cmd_webhook_delete(args):
    client = get_client()
    client.delete_webhook(args.app, args.endpoint, args.uuid)
    print(f'Deleted webhook: {args.uuid}')


def cmd_webhook_get(args):
    client = get_client()
    _print(client.get_webhook(args.app, args.endpoint, args.uuid))


def cmd_webhook_update(args):
    client = get_client()
    kwargs = {}
    if args.url is not None:
        kwargs['target_url'] = args.url
    if args.events is not None:
        kwargs['events'] = [e.strip() for e in args.events.split(',')]
    if args.active is not None:
        kwargs['is_active'] = args.active
    if args.secret is not None:
        kwargs['secret'] = args.secret
    result = client.update_webhook(args.app, args.endpoint, args.uuid, **kwargs)
    _print(result)


def cmd_public_dashboard(args):
    client = get_client()
    _print(client.public_dashboard(args.token))


def cmd_field_types(args):
    client = get_client()
    result = client.field_types()
    if isinstance(result, list):
        for ft in result:
            if isinstance(ft, dict):
                print(f"  {ft.get('value', '?'):15s}  {ft.get('label', '')}")
            else:
                print(f"  {ft}")
    else:
        _print(result)


def cmd_dashboards(args):
    client = get_client()
    result = client.dashboards()
    if isinstance(result, list):
        for d in result:
            print(f"  {d.get('slug', '?'):20s}  {d.get('name', '')}")
    else:
        _print(result)


def cmd_dashboard_get(args):
    client = get_client()
    _print(client.get_dashboard(args.slug))


def cmd_dashboard_create(args):
    client = get_client()
    result = client.create_dashboard(args.name, args.slug,
                                      description=args.description or '')
    _print(result)


def cmd_dashboard_update(args):
    client = get_client()
    kwargs = {}
    if args.name is not None:
        kwargs['name'] = args.name
    if args.description is not None:
        kwargs['description'] = args.description
    result = client.update_dashboard(args.slug, **kwargs)
    _print(result)


def cmd_dashboard_delete(args):
    client = get_client()
    client.delete_dashboard(args.slug)
    print(f'Deleted dashboard: {args.slug}')


def cmd_widgets(args):
    client = get_client()
    _print(client.dashboard_widgets(args.dashboard))


def cmd_widget_create(args):
    client = get_client()
    result = client.create_dashboard_widget(args.dashboard, args.endpoint_id,
                                             args.key_path, args.widget_type,
                                             args.label)
    _print(result)


def cmd_widget_delete(args):
    client = get_client()
    client.delete_dashboard_widget(args.dashboard, args.uuid)
    print(f'Deleted widget: {args.uuid}')


def cmd_widget_update(args):
    client = get_client()
    kwargs = {}
    if args.label is not None:
        kwargs['label'] = args.label
    if args.type is not None:
        kwargs['widget_type'] = args.type
    if args.key_path is not None:
        kwargs['key_path'] = args.key_path
    if args.sort_order is not None:
        kwargs['sort_order'] = args.sort_order
    result = client.update_dashboard_widget(args.dashboard, args.uuid, **kwargs)
    _print(result)


def cmd_dashboard_data(args):
    client = get_client()
    _print(client.dashboard_data(args.dashboard))


def cmd_dashboard_patch(args):
    client = get_client()
    try:
        value = json.loads(args.value)
    except (json.JSONDecodeError, ValueError):
        value = args.value
    result = client.dashboard_patch(args.dashboard, args.endpoint_uuid,
                                     args.key_path, value)
    _print(result)


def cmd_keys(args):
    client = get_client()
    _print(client.app_keys(args.app))


def cmd_key_create(args):
    client = get_client()
    result = client.create_app_key(args.app)
    _print(result)
    if isinstance(result, dict) and 'key' in result:
        print('\n⚠️  Save this key! It will only be shown once.', file=sys.stderr)


def cmd_key_delete(args):
    client = get_client()
    client.delete_app_key(args.app, args.uuid)
    print(f'Deactivated key: {args.uuid}')


def cmd_platform_tokens(args):
    client = get_client()
    result = client.platform_tokens()
    if isinstance(result, list):
        for t in result:
            name = t.get('name', '?')
            prefix = t.get('prefix', '')
            created = t.get('created', '')
            last_used = t.get('last_used', 'never')
            print(f"  {name:20s}  {prefix:10s}  created={created}  last_used={last_used}")
    else:
        _print(result)


def cmd_platform_token_create(args):
    client = get_client()
    result = client.create_platform_token(args.name)
    _print(result)
    if isinstance(result, dict) and 'key' in result:
        print(f"\n  KEY: {result['key']}", file=sys.stderr)
        print('\n⚠️  Save this key! It will only be shown once.', file=sys.stderr)


def cmd_platform_token_revoke(args):
    client = get_client()
    client.revoke_platform_token(args.uuid)
    print(f'Revoked platform token: {args.uuid}')


def cmd_billing_status(args):
    client = get_client()
    result = client.billing_status()
    if isinstance(result, dict):
        plan = result.get('plan', '?')
        print(f"  Plan: {plan}")
        for key, val in result.items():
            if key != 'plan':
                print(f"  {key}: {val}")
    else:
        _print(result)


def main():
    parser = argparse.ArgumentParser(
        prog='meow',
        description='meow meow scratch — send and read API data from your terminal',
    )
    sub = parser.add_subparsers(dest='command')

    # meow send <app> <endpoint> key=value ...
    p_send = sub.add_parser('send', help='Send data to an endpoint')
    p_send.add_argument('app', help='App slug')
    p_send.add_argument('endpoint', help='Endpoint slug')
    p_send.add_argument('data', nargs='+', metavar='key=value',
                        help='Data as key=value pairs (numbers auto-detected)')
    p_send.set_defaults(func=cmd_send)

    # meow get <app> <endpoint> [filters...]
    p_get = sub.add_parser('get', help='Read data from a public endpoint')
    p_get.add_argument('app', help='App slug')
    p_get.add_argument('endpoint', help='Endpoint slug')
    p_get.add_argument('filters', nargs='*', metavar='field=value',
                        help='Filter (e.g. temperature__gte=20)')
    p_get.set_defaults(func=cmd_get)

    # meow aggregate <app> <endpoint> <funcs> --field <name> [filters...]
    p_agg = sub.add_parser('aggregate', help='Run aggregations on a collection')
    p_agg.add_argument('app', help='App slug')
    p_agg.add_argument('endpoint', help='Endpoint slug')
    p_agg.add_argument('aggregates', help='Comma-separated: avg,min,max,sum,count')
    p_agg.add_argument('--field', help='Field to aggregate on (required for avg/min/max/sum)')
    p_agg.add_argument('filters', nargs='*', metavar='field=value',
                        help='Filter before aggregating')
    p_agg.set_defaults(func=cmd_aggregate)

    # meow csv <app> <endpoint> [filters...]
    p_csv = sub.add_parser('csv', help='Download CSV from a collection endpoint')
    p_csv.add_argument('app', help='App slug')
    p_csv.add_argument('endpoint', help='Endpoint slug')
    p_csv.add_argument('filters', nargs='*', metavar='field=value',
                        help='Filter (e.g. temperature__gte=20)')
    p_csv.set_defaults(func=cmd_csv)

    # meow apps
    p_apps = sub.add_parser('apps', help='List your apps')
    p_apps.set_defaults(func=cmd_apps)

    # meow records <app> <endpoint>
    p_records = sub.add_parser('records', help='List records for an endpoint')
    p_records.add_argument('app', help='App slug')
    p_records.add_argument('endpoint', help='Endpoint slug')
    p_records.add_argument('--limit', type=int, default=25, help='Max records (default: 25)')
    p_records.set_defaults(func=cmd_records)

    # meow get-app <app>
    p = sub.add_parser('get-app', help='Get details for an app')
    p.add_argument('app', help='App slug')
    p.set_defaults(func=cmd_get_app)

    # meow create-app <name> <slug>
    p = sub.add_parser('create-app', help='Create a new app')
    p.add_argument('name', help='Display name')
    p.add_argument('slug', help='URL slug')
    p.add_argument('--description', help='Description')
    p.add_argument('--private', action='store_true', help='Make private')
    p.set_defaults(func=cmd_create_app)

    # meow update-app <app>
    p = sub.add_parser('update-app', help='Update an app')
    p.add_argument('app', help='App slug')
    p.add_argument('--name', help='New name')
    p.add_argument('--description', help='New description')
    p.add_argument('--public', action='store_true')
    p.add_argument('--private', action='store_true')
    p.set_defaults(func=cmd_update_app)

    # meow delete-app <app>
    p = sub.add_parser('delete-app', help='Delete an app')
    p.add_argument('app', help='App slug')
    p.set_defaults(func=cmd_delete_app)

    # meow endpoints <app>
    p = sub.add_parser('endpoints', help='List endpoints in an app')
    p.add_argument('app', help='App slug')
    p.set_defaults(func=cmd_endpoints)

    # meow get-endpoint <app> <endpoint>
    p = sub.add_parser('get-endpoint', help='Get endpoint details')
    p.add_argument('app', help='App slug')
    p.add_argument('endpoint', help='Endpoint slug')
    p.set_defaults(func=cmd_get_endpoint)

    # meow create-endpoint <app> <name> <slug> <type>
    p = sub.add_parser('create-endpoint', help='Create a new endpoint')
    p.add_argument('app', help='App slug')
    p.add_argument('name', help='Display name')
    p.add_argument('slug', help='URL slug')
    p.add_argument('type', choices=['collection', 'static', 'proxy'], help='Endpoint type')
    p.add_argument('--description', help='Description')
    p.add_argument('--private', action='store_true', help='Make private')
    p.set_defaults(func=cmd_create_endpoint)

    # meow update-endpoint <app> <endpoint>
    p = sub.add_parser('update-endpoint', help='Update an endpoint')
    p.add_argument('app', help='App slug')
    p.add_argument('endpoint', help='Endpoint slug')
    p.add_argument('--name', help='New name')
    p.add_argument('--description', help='New description')
    p.add_argument('--public', action='store_true')
    p.add_argument('--private', action='store_true')
    p.add_argument('--delay-ms', type=int, help='Simulated delay (ms)')
    p.add_argument('--error-rate', type=float, help='Error rate 0.0-1.0')
    p.add_argument('--ttl', type=int, help='TTL in seconds')
    p.set_defaults(func=cmd_update_endpoint)

    # meow delete-endpoint <app> <endpoint>
    p = sub.add_parser('delete-endpoint', help='Delete an endpoint')
    p.add_argument('app', help='App slug')
    p.add_argument('endpoint', help='Endpoint slug')
    p.set_defaults(func=cmd_delete_endpoint)

    # meow fields <app> <endpoint>
    p = sub.add_parser('fields', help='List fields for a collection endpoint')
    p.add_argument('app', help='App slug')
    p.add_argument('endpoint', help='Endpoint slug')
    p.set_defaults(func=cmd_fields)

    # meow create-field <app> <endpoint> <name> <label> <type>
    p = sub.add_parser('create-field', help='Add a field to an endpoint')
    p.add_argument('app', help='App slug')
    p.add_argument('endpoint', help='Endpoint slug')
    p.add_argument('name', help='Field name')
    p.add_argument('label', help='Display label')
    p.add_argument('field_type', choices=['text', 'textarea', 'number', 'boolean', 'date', 'datetime', 'time', 'color', 'email', 'url', 'select', 'rating', 'image_url', 'json'], help='Field type')
    p.add_argument('--required', action='store_true', help='Make required')
    p.set_defaults(func=cmd_create_field)

    # meow update-field <app> <endpoint> <uuid>
    p = sub.add_parser('update-field', help='Update a field')
    p.add_argument('app', help='App slug')
    p.add_argument('endpoint', help='Endpoint slug')
    p.add_argument('uuid', help='Field UUID')
    p.add_argument('--label', help='New label')
    p.add_argument('--required', type=bool, help='Required (true/false)')
    p.set_defaults(func=cmd_update_field)

    # meow delete-field <app> <endpoint> <uuid>
    p = sub.add_parser('delete-field', help='Delete a field')
    p.add_argument('app', help='App slug')
    p.add_argument('endpoint', help='Endpoint slug')
    p.add_argument('uuid', help='Field UUID')
    p.set_defaults(func=cmd_delete_field)

    # meow update-record <app> <endpoint> <uuid> key=value ...
    p = sub.add_parser('update-record', help='Update a record')
    p.add_argument('app', help='App slug')
    p.add_argument('endpoint', help='Endpoint slug')
    p.add_argument('uuid', help='Record UUID')
    p.add_argument('data', nargs='+', metavar='key=value', help='Updated data')
    p.set_defaults(func=cmd_update_record)

    # meow delete-record <app> <endpoint> <uuid>
    p = sub.add_parser('delete-record', help='Delete a record')
    p.add_argument('app', help='App slug')
    p.add_argument('endpoint', help='Endpoint slug')
    p.add_argument('uuid', help='Record UUID')
    p.set_defaults(func=cmd_delete_record)

    # meow get-record <app> <endpoint> <uuid>
    p = sub.add_parser('get-record', help='Get a single record')
    p.add_argument('app', help='App slug')
    p.add_argument('endpoint', help='Endpoint slug')
    p.add_argument('uuid', help='Record UUID')
    p.set_defaults(func=cmd_get_record)

    # meow payload-get <app> <endpoint>
    p = sub.add_parser('payload-get', help='Get static payload')
    p.add_argument('app', help='App slug')
    p.add_argument('endpoint', help='Endpoint slug')
    p.set_defaults(func=cmd_payload_get)

    # meow payload-set <app> <endpoint> key=value ...
    p = sub.add_parser('payload-set', help='Set static payload')
    p.add_argument('app', help='App slug')
    p.add_argument('endpoint', help='Endpoint slug')
    p.add_argument('data', nargs='+', metavar='key=value', help='Payload data')
    p.set_defaults(func=cmd_payload_set)

    # meow proxy-get <app> <endpoint>
    p = sub.add_parser('proxy-get', help='Get proxy config')
    p.add_argument('app', help='App slug')
    p.add_argument('endpoint', help='Endpoint slug')
    p.set_defaults(func=cmd_proxy_get)

    # meow proxy-set <app> <endpoint> <url>
    p = sub.add_parser('proxy-set', help='Set proxy upstream URL')
    p.add_argument('app', help='App slug')
    p.add_argument('endpoint', help='Endpoint slug')
    p.add_argument('url', help='Upstream URL')
    p.add_argument('--method', default='GET', help='HTTP method (default: GET)')
    p.set_defaults(func=cmd_proxy_set)

    # meow encryption <app> <endpoint>
    p = sub.add_parser('encryption', help='Get encryption status')
    p.add_argument('app', help='App slug')
    p.add_argument('endpoint', help='Endpoint slug')
    p.set_defaults(func=cmd_encryption)

    # meow encrypt-enable <app> <endpoint>
    p = sub.add_parser('encrypt-enable', help='Enable encryption (key shown once!)')
    p.add_argument('app', help='App slug')
    p.add_argument('endpoint', help='Endpoint slug')
    p.set_defaults(func=cmd_encrypt_enable)

    # meow encrypt-disable <app> <endpoint>
    p = sub.add_parser('encrypt-disable', help='Disable encryption')
    p.add_argument('app', help='App slug')
    p.add_argument('endpoint', help='Endpoint slug')
    p.set_defaults(func=cmd_encrypt_disable)

    # meow logs <app> <endpoint>
    p = sub.add_parser('logs', help='View request logs')
    p.add_argument('app', help='App slug')
    p.add_argument('endpoint', help='Endpoint slug')
    p.set_defaults(func=cmd_logs)

    # meow webhooks <app> <endpoint>
    p = sub.add_parser('webhooks', help='List webhooks')
    p.add_argument('app', help='App slug')
    p.add_argument('endpoint', help='Endpoint slug')
    p.set_defaults(func=cmd_webhooks)

    # meow webhook-create <app> <endpoint> <url> <events>
    p = sub.add_parser('webhook-create', help='Create a webhook')
    p.add_argument('app', help='App slug')
    p.add_argument('endpoint', help='Endpoint slug')
    p.add_argument('url', help='Target URL')
    p.add_argument('events', help='Comma-separated events (record.created,record.updated,...)')
    p.add_argument('--secret', help='Signing secret')
    p.set_defaults(func=cmd_webhook_create)

    # meow webhook-delete <app> <endpoint> <uuid>
    p = sub.add_parser('webhook-delete', help='Delete a webhook')
    p.add_argument('app', help='App slug')
    p.add_argument('endpoint', help='Endpoint slug')
    p.add_argument('uuid', help='Webhook UUID')
    p.set_defaults(func=cmd_webhook_delete)

    # meow webhook-get <app> <endpoint> <uuid>
    p = sub.add_parser('webhook-get', help='Get a single webhook')
    p.add_argument('app', help='App slug')
    p.add_argument('endpoint', help='Endpoint slug')
    p.add_argument('uuid', help='Webhook UUID')
    p.set_defaults(func=cmd_webhook_get)

    # meow webhook-update <app> <endpoint> <uuid>
    p = sub.add_parser('webhook-update', help='Update a webhook')
    p.add_argument('app', help='App slug')
    p.add_argument('endpoint', help='Endpoint slug')
    p.add_argument('uuid', help='Webhook UUID')
    p.add_argument('--url', help='New target URL')
    p.add_argument('--events', help='Comma-separated events (record.created,record.updated,...)')
    p.add_argument('--active', type=bool, help='Active (true/false)')
    p.add_argument('--secret', help='New signing secret')
    p.set_defaults(func=cmd_webhook_update)

    # meow dashboards
    p = sub.add_parser('dashboards', help='List dashboards')
    p.set_defaults(func=cmd_dashboards)

    # meow dashboard-get <slug>
    p = sub.add_parser('dashboard-get', help='Get dashboard details')
    p.add_argument('slug', help='Dashboard slug')
    p.set_defaults(func=cmd_dashboard_get)

    # meow dashboard-create <name> <slug>
    p = sub.add_parser('dashboard-create', help='Create a dashboard')
    p.add_argument('name', help='Display name')
    p.add_argument('slug', help='URL slug')
    p.add_argument('--description', help='Description')
    p.set_defaults(func=cmd_dashboard_create)

    # meow dashboard-update <slug>
    p = sub.add_parser('dashboard-update', help='Update a dashboard')
    p.add_argument('slug', help='Dashboard slug')
    p.add_argument('--name', help='New name')
    p.add_argument('--description', help='New description')
    p.set_defaults(func=cmd_dashboard_update)

    # meow dashboard-delete <slug>
    p = sub.add_parser('dashboard-delete', help='Delete a dashboard')
    p.add_argument('slug', help='Dashboard slug')
    p.set_defaults(func=cmd_dashboard_delete)

    # meow public-dashboard <token>
    p = sub.add_parser('public-dashboard', help='Get a public dashboard by share token')
    p.add_argument('token', help='Share token')
    p.set_defaults(func=cmd_public_dashboard)

    # meow widgets <dashboard>
    p = sub.add_parser('widgets', help='List dashboard widgets')
    p.add_argument('dashboard', help='Dashboard slug')
    p.set_defaults(func=cmd_widgets)

    # meow widget-create <dashboard> <endpoint_id> <key_path> <type> <label>
    p = sub.add_parser('widget-create', help='Add a widget to a dashboard')
    p.add_argument('dashboard', help='Dashboard slug')
    p.add_argument('endpoint_id', help='Endpoint UUID')
    p.add_argument('key_path', help='Data key path')
    p.add_argument('widget_type', choices=['toggle', 'color', 'slider', 'number', 'text', 'select', 'display'], help='Widget type')
    p.add_argument('label', help='Display label')
    p.set_defaults(func=cmd_widget_create)

    # meow widget-update <dashboard> <uuid>
    p = sub.add_parser('widget-update', help='Update a widget')
    p.add_argument('dashboard', help='Dashboard slug')
    p.add_argument('uuid', help='Widget UUID')
    p.add_argument('--label', help='New label')
    p.add_argument('--type', dest='type', help='New widget type')
    p.add_argument('--key-path', help='New key path')
    p.add_argument('--sort-order', type=int, help='New sort order')
    p.set_defaults(func=cmd_widget_update)

    # meow widget-delete <dashboard> <uuid>
    p = sub.add_parser('widget-delete', help='Remove a widget')
    p.add_argument('dashboard', help='Dashboard slug')
    p.add_argument('uuid', help='Widget UUID')
    p.set_defaults(func=cmd_widget_delete)

    # meow dashboard-data <dashboard>
    p = sub.add_parser('dashboard-data', help='Get live dashboard data')
    p.add_argument('dashboard', help='Dashboard slug')
    p.set_defaults(func=cmd_dashboard_data)

    # meow dashboard-patch <dashboard> <endpoint_uuid> <key_path> <value>
    p = sub.add_parser('dashboard-patch', help='Update a value via dashboard widget')
    p.add_argument('dashboard', help='Dashboard slug')
    p.add_argument('endpoint_uuid', help='Endpoint UUID')
    p.add_argument('key_path', help='Data key path')
    p.add_argument('value', help='New value (JSON auto-detected)')
    p.set_defaults(func=cmd_dashboard_patch)

    # meow keys <app>
    p = sub.add_parser('keys', help='List app-scoped API keys')
    p.add_argument('app', help='App slug')
    p.set_defaults(func=cmd_keys)

    # meow key-create <app>
    p = sub.add_parser('key-create', help='Create an app-scoped API key')
    p.add_argument('app', help='App slug')
    p.set_defaults(func=cmd_key_create)

    # meow key-delete <app> <uuid>
    p = sub.add_parser('key-delete', help='Deactivate an API key')
    p.add_argument('app', help='App slug')
    p.add_argument('uuid', help='Key UUID')
    p.set_defaults(func=cmd_key_delete)

    # meow field-types
    p = sub.add_parser('field-types', help='List available field types')
    p.set_defaults(func=cmd_field_types)

    # meow platform-tokens
    p = sub.add_parser('platform-tokens', help='List platform tokens')
    p.set_defaults(func=cmd_platform_tokens)

    # meow platform-token-create <name>
    p = sub.add_parser('platform-token-create', help='Create a platform token')
    p.add_argument('name', help='Token name')
    p.set_defaults(func=cmd_platform_token_create)

    # meow platform-token-revoke <uuid>
    p = sub.add_parser('platform-token-revoke', help='Revoke a platform token')
    p.add_argument('uuid', help='Token UUID')
    p.set_defaults(func=cmd_platform_token_revoke)

    # meow billing-status
    p = sub.add_parser('billing-status', help='Show plan info and usage')
    p.set_defaults(func=cmd_billing_status)

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        sys.exit(1)

    try:
        args.func(args)
    except Exception as e:
        print(f'Error: {e}', file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
