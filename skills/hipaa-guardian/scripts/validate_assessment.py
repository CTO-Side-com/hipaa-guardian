#!/usr/bin/env python3
"""Validate structure and minimum evidence without making a compliance judgment."""
import argparse
import re
from datetime import date
from common import (
    VALID_EVIDENCE_TYPES, VALID_SEVERITIES, VALID_STATUSES, load_controls, load_json
)


def nonempty(value):
    return isinstance(value, str) and bool(value.strip()) and value.strip().upper() not in ('TBD', 'UNKNOWN', 'UNASSIGNED', 'N/A')


def calendar_date(value):
    if not isinstance(value, str) or not re.fullmatch(r'\d{4}-\d{2}-\d{2}', value):
        return False
    try:
        date.fromisoformat(value)
    except ValueError:
        return False
    return True


def validate(data):
    errors = []
    library = load_controls()
    expected = {c['id'] for c in library['controls']}
    if not isinstance(data, dict):
        return ['Assessment must be a JSON object']
    for field in ('product', 'created_on'):
        if not nonempty(data.get(field)):
            errors.append(f'Missing or empty assessment field: {field}')
    items = data.get('controls', [])
    if not isinstance(items, list):
        return errors + ['controls must be an array']
    ids = [x.get('id') for x in items if isinstance(x, dict)]
    if len(ids) != len(set(ids)):
        errors.append('Duplicate control ids')
    for missing in sorted(expected - set(ids)):
        errors.append(f'Missing control: {missing}')
    for extra in sorted(set(ids) - expected, key=str):
        errors.append(f'Unknown control: {extra}')
    for item in items:
        if not isinstance(item, dict):
            errors.append('Control entry is not a JSON object')
            continue
        cid = item.get('id', 'UNSPECIFIED')
        status = item.get('status')
        if status not in VALID_STATUSES:
            errors.append(f'{cid}: invalid status {status!r}')
            continue
        evidence = item.get('evidence', [])
        if not isinstance(evidence, list):
            errors.append(f'{cid}: evidence must be an array')
            continue
        if status != 'insufficient_evidence' and not nonempty(item.get('rationale')):
            errors.append(f'{cid}: rationale required for status {status}')
        if status in ('verified', 'partially_verified', 'failed'):
            if not nonempty(item.get('reviewer')):
                errors.append(f'{cid}: named reviewer required')
            if not evidence:
                errors.append(f'{cid}: evidence reference required for asserted status')
        if status == 'not_applicable':
            if not nonempty(item.get('approved_by')):
                errors.append(f'{cid}: not_applicable requires human approval')
        for i, ev in enumerate(evidence):
            if not isinstance(ev, dict):
                errors.append(f'{cid}: evidence[{i}] not an object')
                continue
            if ev.get('type') not in VALID_EVIDENCE_TYPES:
                errors.append(f'{cid}: evidence[{i}] has invalid type')
            if not nonempty(ev.get('ref')):
                errors.append(f'{cid}: evidence[{i}] missing file/record reference')
            if not nonempty(ev.get('method')):
                errors.append(f'{cid}: evidence[{i}] missing verification method')
            if not calendar_date(ev.get('verified_on')):
                errors.append(f'{cid}: evidence[{i}] needs YYYY-MM-DD verified_on')
            if not nonempty(ev.get('reviewer')):
                errors.append(f'{cid}: evidence[{i}] needs reviewer')
        risk = item.get('risk', {})
        if not isinstance(risk, dict):
            errors.append(f'{cid}: risk must be an object')
            continue
        severity = risk.get('severity', '')
        if severity and severity not in VALID_SEVERITIES:
            errors.append(f'{cid}: invalid risk severity')
        if status in ('failed', 'partially_verified'):
            for field in ('observation', 'recommendation'):
                if not nonempty(risk.get(field)):
                    errors.append(f'{cid}: risk.{field} required for gap finding')
    return errors


def main():
    ap = argparse.ArgumentParser(description='Check evidence integrity and readiness assessment completeness')
    ap.add_argument('--assessment', required=True)
    args = ap.parse_args()
    try:
        errors = validate(load_json(args.assessment))
    except (OSError, ValueError) as exc:
        ap.error(str(exc))
    if errors:
        for error in errors:
            print('ERROR:', error)
        raise SystemExit(1)
    print('Assessment JSON structure and minimum evidence requirements are valid.')
    print('This does NOT confirm truth of evidence or HIPAA compliance.')


if __name__ == '__main__':
    main()
