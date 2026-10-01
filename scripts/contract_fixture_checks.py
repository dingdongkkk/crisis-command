"""Targeted CC-01 fixture checks, not the canonical CC-02 application schema.

Negative specimens are full valid bases plus RFC6901-addressed add/replace/remove
operations. These diagnostics cover the named example defects and cross-file
invariants; Pydantic/OpenAPI/TypeScript and runtime behavior remain CC-02+ work.
"""
import copy
import json
import re
from pathlib import Path

EXAMPLES = Path(__file__).resolve().parents[1] / 'docs/decisions/examples'


def load(name):
    return json.loads((EXAMPLES / name).read_text())


def tokens(pointer):
    if not pointer:
        return []
    if not pointer.startswith('/'):
        raise ValueError('Expected JSON pointer')
    return [s.replace('~1', '/').replace('~0', '~') for s in pointer[1:].split('/')]


def select(value, pointer):
    for token in tokens(pointer):
        value = value[int(token)] if isinstance(value, list) else value[token]
    return value


def materialize(case, patched=True):
    base = case['base']
    value = copy.deepcopy(select(load(base['file']), base['pointer']))
    if not patched:
        return value
    for patch in case['patches']:
        parts = tokens(patch['path'])
        if not parts:
            raise ValueError('Root patches are not used in these fixtures')
        parent = value
        for part in parts[:-1]:
            parent = parent[int(part)] if isinstance(parent, list) else parent[part]
        key = int(parts[-1]) if isinstance(parent, list) else parts[-1]
        if patch['op'] == 'remove':
            del parent[key]
        elif patch['op'] in {'add', 'replace'}:
            if patch['op'] == 'replace':
                parent[key]  # Require an existing target, unlike add.
            parent[key] = copy.deepcopy(patch['value'])
        else:
            raise ValueError('Unsupported patch operation')
    return value


def diagnostic_errors(entity, value, layer='schema'):
    errors = set()
    if entity == 'Report':
        point = value.get('location', {})
        if point.get('type') != 'Point' or set(point) != {'type', 'coordinates'}:
            errors.add('GEOJSON_POINT_REQUIRED')
    elif entity == 'Unit' and layer == 'fixture':
        lon, lat = value['position']['coordinates']
        if not (77.45 <= lon <= 77.80 and 12.80 <= lat <= 13.15):
            errors.add('OUTSIDE_DEMO_BOUNDS')
    elif entity == 'EventEnvelope':
        if not re.fullmatch(r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}Z', value['occurred_at']):
            errors.add('UTC_Z_REQUIRED')
        if type(value['sequence']) is not int or value['sequence'] < 1:
            errors.add('POSITIVE_SEQUENCE_REQUIRED')
        if value['schema_version'].split('.')[0] != '1':
            errors.add('UNKNOWN_SCHEMA_MAJOR')
        if 'text' in value['payload']:
            errors.add('RAW_TEXT_FORBIDDEN')
    elif entity == 'TriageFact':
        if value['key'] == 'people_count':
            if value['count']['status'] == 'unknown' and value['count']['value'] is not None:
                errors.add('UNKNOWN_COUNT_MUST_BE_NULL')
        elif 'value' not in value:
            errors.add('FACT_VALUE_REQUIRED')
        elif value['value'] not in ('yes', 'no', 'unknown'):
            errors.add('TRISTATE_REQUIRED')
        elif value['source'] in {'model_adapter', 'rule_adapter'} and value['value'] != 'unknown' and not value['evidence']:
            errors.add('ASSERTION_WITHOUT_EVIDENCE')
    elif entity == 'Assignment':
        if type(value['eta_s']) is not int or value['eta_s'] < 0:
            errors.add('INTEGER_SECONDS_REQUIRED')
        if value['role'] == 'bridge' and value['satisfies_need']:
            errors.add('BRIDGE_CANNOT_SATISFY')
    elif entity == 'Plan':
        units = {u['unit_id']: u for u in load('world.before.json')['units']}
        incidents = load('world.before.json')['incidents'] + [load('entities.valid.json')['Incident']]
        needs = {n['need_id']: n for i in incidents for n in i['needs']}
        eligible = {'als': {'als'}, 'bls': {'als', 'bls'}, 'fire': {'fire'}, 'tow': {'tow'}, 'water_rescue': {'boat'}}
        seen = set()
        for assignment in value['assignments']:
            uid = assignment['unit_id']
            if uid in seen:
                errors.add('DUPLICATE_UNIT')
            seen.add(uid)
            if assignment['role'] == 'primary' and units[uid]['type'] not in eligible[needs[assignment['need_id']]['type']]:
                errors.add('TYPE_INELIGIBLE')
            if assignment['route']['route_status'] != 'ok':
                errors.add('ROUTE_UNAVAILABLE')
    elif entity == 'PolicyFlag':
        if 'requires_ack' not in value:
            errors.add('ACK_FIELD_REQUIRED')
    return errors
