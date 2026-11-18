#!/usr/bin/env python3
"""Create a complete blank evidence matrix; nothing is automatically marked compliant."""
import argparse
from common import load_controls, today, write_json


def create(product, environment='unknown'):
    library = load_controls()
    return {
        'schema_version': '1.0',
        'product': product,
        'environment': environment,
        'created_on': today(),
        'assessor': 'UNASSIGNED',
        'legal_role': 'unverified',
        'in_scope_systems': [],
        'excluded_systems': [],
        'regulatory_status_checked_on': '',
        'control_library_reviewed_as_of': library['reviewed_as_of'],
        'notes': 'Internal readiness assessment. A repository scan alone cannot establish HIPAA compliance.',
        'controls': [
            {
                'id': x['id'],
                'status': 'insufficient_evidence',
                'rationale': '',
                'reviewer': '',
                'approved_by': '',
                'evidence': [],
                'risk': {
                    'severity': '', 'observation': '', 'impact': '',
                    'recommendation': '', 'owner': '', 'due_date': '',
                    'verification_test': ''
                }
            }
            for x in library['controls']
        ]
    }


def main():
    ap = argparse.ArgumentParser(description='Initialize HIPAA readiness control-by-control evidence matrix')
    ap.add_argument('--product', required=True)
    ap.add_argument('--environment', default='unknown')
    ap.add_argument('--out', required=True)
    ap.add_argument('--force', action='store_true', help='Overwrite existing assessment (not recommended)')
    args = ap.parse_args()
    try:
        write_json(args.out, create(args.product, args.environment), overwrite=args.force)
    except FileExistsError:
        ap.error('Assessment exists; refusing to replace it. Supply a new output path or --force.')
    print(f'Created unverified assessment at {args.out} (all controls require review)')


if __name__ == '__main__':
    main()
