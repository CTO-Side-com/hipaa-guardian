#!/usr/bin/env python3
"""Regenerate the synthetic example outputs shown in the README. Every name and finding is invented."""
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCRIPTS = HERE.parents[1] / 'skills' / 'hipaa-guardian' / 'scripts'
sys.path.insert(0, str(SCRIPTS))

from common import write_json  # noqa: E402
from init_assessment import create  # noqa: E402

REVIEWER = 'Synthetic Reviewer'


def evidence(kind, ref, method):
    return [{'type': kind, 'ref': ref, 'method': method, 'verified_on': '2026-11-18', 'reviewer': REVIEWER}]


FINDINGS = {
    'TEC-001': ('failed', 'critical', {
        'observation': 'The appointment export endpoint loads records by ID without a clinic filter (src/exports/views.py:41).',
        'impact': "A user of clinic A can download clinic B's appointment export.",
        'recommendation': "Scope the export query by the session's clinic_id and add a negative cross-tenant test.",
        'owner': 'Platform team', 'due_date': '2026-12-05',
        'verification_test': 'tests/test_exports.py::test_cross_tenant_export_denied returns 403 for synthetic clinic B',
    }, evidence('code', 'src/exports/views.py:41', 'Code trace of export query and tenant resolution')),
    'ENG-003': ('failed', 'high', {
        'observation': 'Booking errors log the full request payload, including patient name and insurance ID, to the APM service (src/booking/handlers.py:118).',
        'impact': 'PHI is copied to a telemetry vendor that has no BAA on record.',
        'recommendation': 'Log request IDs only, add a redaction filter, and assert in a test that no patient fields reach logs.',
        'owner': 'Backend team', 'due_date': '2026-12-12',
        'verification_test': 'Force a synthetic booking error and confirm the captured log event has no patient fields',
    }, evidence('code', 'src/booking/handlers.py:118', 'Code trace of exception logging path')),
    'ENG-002': ('partially_verified', 'critical', {
        'observation': "Tool calls check tenant scope, but the send_reminder tool accepts any phone number the model returns.",
        'impact': 'A prompt-injected conversation could send appointment details to an arbitrary number.',
        'recommendation': 'Resolve reminder recipients server-side from the verified patient record and reject model-supplied numbers.',
        'owner': 'AI team', 'due_date': '2026-12-19',
        'verification_test': 'Inject a synthetic instruction to text a different number; the tool call must be refused',
    }, evidence('test', 'tests/test_agent_tools.py:57', 'Ran tenant-scope tests; reviewed tool argument validation')),
    'ADM-023': ('partially_verified', 'high', {
        'observation': 'Nightly database snapshots exist (infra/db.tf:22), but no restore has ever been tested.',
        'recommendation': 'Run and document a restore of a synthetic snapshot into an isolated environment.',
        'owner': 'Infrastructure', 'due_date': '2027-01-15',
    }, evidence('configuration', 'infra/db.tf:22', 'Reviewed backup retention and schedule configuration')),
}
VERIFIED = {
    'TEC-012': evidence('configuration', 'infra/load_balancer.tf:14', 'Confirmed TLS 1.2+ policy and HTTP-to-HTTPS redirect'),
    'TEC-002': evidence('test', 'tests/test_auth.py:12', 'Ran unique-account and shared-login rejection tests'),
    'TEC-004': evidence('test', 'tests/test_sessions.py:30', 'Ran idle-timeout test against staging configuration'),
}


def build():
    doc = create('Example Dental Cloud (synthetic)', 'staging (synthetic data)')
    doc.update({
        'assessor': REVIEWER,
        'legal_role': 'Business associate (assumed, unverified)',
        'in_scope_systems': ['Web app and API (this repository)', 'AI scheduling assistant', 'Managed PostgreSQL'],
        'excluded_systems': ['Clinic practice-management systems', 'Corporate IT'],
        'regulatory_status_checked_on': '2026-11-18',
        'notes': 'Synthetic example for documentation. Every product name, path and finding is invented.',
    })
    controls = {c['id']: c for c in doc['controls']}
    for cid, (status, severity, risk, ev) in FINDINGS.items():
        controls[cid].update({'status': status, 'rationale': risk['observation'], 'reviewer': REVIEWER, 'evidence': ev})
        controls[cid]['risk'].update(risk, severity=severity)
    for cid, ev in VERIFIED.items():
        controls[cid].update({'status': 'verified', 'rationale': ev[0]['method'], 'reviewer': REVIEWER, 'evidence': ev})
    controls['ADM-012'].update({
        'status': 'not_applicable', 'approved_by': 'Compliance lead (synthetic)',
        'rationale': 'The product is not a health care clearinghouse.',
    })
    return doc


def main():
    target = HERE / 'assessment.json'
    write_json(target, build())
    run = [sys.executable]
    subprocess.run(run + [str(SCRIPTS / 'validate_assessment.py'), '--assessment', str(target)], check=True)
    subprocess.run(run + [str(SCRIPTS / 'render_report.py'), '--assessment', str(target), '--out', str(HERE), '--pdf'], check=True)
    subprocess.run(run + [str(SCRIPTS / 'export_tasks.py'), '--assessment', str(target), '--out', str(HERE)], check=True)


if __name__ == '__main__':
    main()
