"""Offline regression tests for HIPAA Guardian, no external packages."""
import copy
import json
import tempfile
import unittest
from pathlib import Path
import sys

SCRIPTS = Path(__file__).resolve().parents[1] / 'scripts'
sys.path.insert(0, str(SCRIPTS))

import repo_scan
from common import csv_safe, load_controls, redact, safe_text
from init_assessment import create
from repo_scan import scan
from validate_assessment import validate
from render_report import render


class GuardianTests(unittest.TestCase):
    def test_controls_consistent(self):
        library = load_controls()
        ids = [c['id'] for c in library['controls']]
        self.assertEqual(len(ids), len(set(ids)))
        self.assertGreaterEqual(len(ids), 65)
        for control in library['controls']:
            self.assertIn(control['source_type'], ('regulatory', 'engineering'))
            self.assertIn(control['kind'], ('standard', 'required', 'addressable', 'related_rule', 'practice'))
            self.assertTrue(control['source_url'].startswith('https://'))

    def test_empty_assessment_is_valid_but_not_verified(self):
        doc = create('Synthetic Health App')
        self.assertFalse(validate(doc))
        self.assertTrue(all(c['status'] == 'insufficient_evidence' for c in doc['controls']))
        report, risk = render(doc)
        self.assertIn('NOT A HIPAA CERTIFICATE', report)
        self.assertEqual(len(risk), len(load_controls()['controls']))
        self.assertNotIn('100% compliant', report)

    def test_unsupported_verified_status_rejected(self):
        doc = create('Synthetic Health App')
        doc['controls'][0]['status'] = 'verified'
        errors = validate(doc)
        self.assertTrue(any('evidence reference required' in e for e in errors))
        self.assertTrue(any('named reviewer required' in e for e in errors))

    def test_verified_with_full_metadata_accepted(self):
        doc = create('Synthetic Health App')
        doc['controls'][0].update({
            'status': 'verified',
            'rationale': 'Reviewed synthetic access control tests only',
            'reviewer': 'Independent reviewer',
            'evidence': [{
                'type': 'test', 'ref': 'tests/test_auth.py:42',
                'method': 'Run negative tenant boundary test',
                'verified_on': '2026-11-18', 'reviewer': 'Independent reviewer'
            }]
        })
        self.assertEqual([], validate(doc))

    def test_na_requires_human_approval(self):
        doc = create('Synthetic Health App')
        doc['controls'][0].update({'status': 'not_applicable', 'rationale': 'Needs human sign-off'})
        self.assertTrue(any('human approval' in e for e in validate(doc)))

    def test_scan_never_emits_literal_secrets_or_env_files(self):
        with tempfile.TemporaryDirectory() as root:
            base = Path(root)
            (base / 'api.py').write_text("token = 'test_value_not_real_abcdef123456'\nrequests.get(url, verify=False)\nprint(patient)\n")
            (base / '.env').write_text('password=do_not_print\n')
            (base / 'node_modules').mkdir()
            (base / 'node_modules' / 'file.js').write_text('console.log(patient)\n')
            report = scan(base)
            string = json.dumps(report)
            self.assertIn('tls-verification-disabled', string)
            self.assertIn('phi-log-candidate', string)
            self.assertNotIn('test_value_not_real', string)
            self.assertNotIn('do_not_print', string)
            self.assertNotIn('node_modules/file.js', string)
            self.assertNotIn('password=do_not_print', string)

    def test_report_redaction_does_not_remove_dates(self):
        self.assertEqual(safe_text('2026-11-18'), '2026-11-18')
        self.assertIn('[REDACTED_EMAIL]', safe_text('person@example.com'))
        self.assertIn('[REDACTED_IDENTIFIER]', safe_text('123-45-6789'))
        self.assertIn('[REDACTED_NUMBER]', safe_text('+1 (212) 555-1234'))

    def test_redaction_scrubs_before_truncating(self):
        self.assertNotIn('jane.doe@', redact('x' * 790 + ' jane.doe@clinic.example', 800))
        self.assertNotIn('123-45-67', redact('x' * 790 + ' 123-45-6789', 800))
        self.assertNotIn('212555123', redact('x' * 1490 + ' 2125551234567', 1500))
        self.assertEqual(len(redact('y' * 5000, 800)), 800)

    def test_validator_reports_odd_shapes_instead_of_crashing(self):
        doc = create('Synthetic Health App')
        doc['controls'][0]['id'] = ['ADM-001']
        errors = validate(doc)
        self.assertTrue(any('id must be a string' in e for e in errors), errors)

    def test_due_dates_must_be_iso_dates(self):
        doc = create('Synthetic Health App')
        doc['controls'][0]['risk']['due_date'] = '12/01/2026'
        self.assertTrue(any('due_date' in e for e in validate(doc)))
        doc['controls'][0]['risk']['due_date'] = '2026-12-01'
        self.assertEqual([], validate(doc))

    def test_scan_rules_match_quoted_and_camelcase_keys_but_not_xml_namespaces(self):
        risky = {
            'stack.yaml': 'StorageEncrypted: false\nPubliclyAccessible: true\nBlockPublicAcls: false\n',
            'settings.json': '{"encrypted": false, "x": 1}\n{"publicly_accessible": true}\n',
            'client.py': "BASE = 'http://api.example.hospital.com/v1'\n",
        }
        safe = {
            'pom.xml': '<project xmlns="http://maven.apache.org/POM/4.0.0" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">\n',
            'beans.xml': '<beans xmlns="http://www.springframework.org/schema/beans">\n',
            'docs.py': "URL = 'http://api.example/v1'\n",
        }
        with tempfile.TemporaryDirectory() as root:
            base = Path(root)
            for name, text in {**risky, **safe}.items():
                (base / name).write_text(text)
            findings = scan(base)['findings']
        by_file = {}
        for f in findings:
            by_file.setdefault(f['file'], set()).add(f['line'])
        self.assertEqual(by_file.get('stack.yaml'), {1, 2, 3})
        self.assertEqual(by_file.get('settings.json'), {1, 2})
        self.assertEqual(by_file.get('client.py'), {1})
        self.assertFalse(set(safe) & set(by_file), by_file)

    def test_redact_keeps_pipes_for_non_markdown_outputs(self):
        self.assertEqual(redact('a | b'), 'a | b')
        self.assertEqual(safe_text('a | b'), 'a \\| b')

    def test_csv_safe_neutralizes_tab_and_formula_prefixes(self):
        for value in ('=1+1', '+SUM(A1)', '-2', '@cmd', '\tx'):
            self.assertTrue(csv_safe(value).startswith("'"), value)
        self.assertEqual(csv_safe('Fix: access'), 'Fix: access')

    def test_bad_evidence_dates_are_errors_not_crashes(self):
        doc = create('Synthetic Health App')
        doc['controls'][0].update({
            'status': 'verified', 'rationale': 'Reviewed', 'reviewer': 'Reviewer',
            'evidence': [
                {'type': 'test', 'ref': 'a.py:1', 'method': 'run', 'verified_on': None, 'reviewer': 'Reviewer'},
                {'type': 'test', 'ref': 'a.py:1', 'method': 'run', 'verified_on': '2026-02-30', 'reviewer': 'Reviewer'},
            ]
        })
        errors = validate(doc)
        self.assertEqual(sum('verified_on' in e for e in errors), 2)

    def test_new_scan_rules_flag_risky_lines_only(self):
        risky = {
            'infra.tf': 'storage_encrypted = false\nacl = "public-read"\npublicly_accessible = true\n',
            'auth.py': 'jwt.decode(token, key, options={"verify_signature": False})\n',
            'settings.py': 'DEBUG = True\n',
            'client.ts': "const api = 'http://records.partner-clinic.invalid/api';\nfetch(`/visits?patient_id=${id}`)\n",
        }
        safe = "const local = 'http://localhost:3000';\nconst ns = 'http://www.w3.org/2000/svg';\nDEBUG = False\n"
        with tempfile.TemporaryDirectory() as root:
            base = Path(root)
            for name, text in risky.items():
                (base / name).write_text(text)
            (base / 'safe.ts').write_text(safe)
            findings = scan(base)['findings']
        rules = {f['rule_id'] for f in findings}
        self.assertTrue({
            'encryption-disabled-config', 'public-resource-exposure', 'jwt-verification-disabled',
            'debug-mode-enabled', 'plaintext-http-endpoint', 'patient-identifier-in-url',
        } <= rules, rules)
        self.assertFalse([f for f in findings if f['file'] == 'safe.ts'])
        self.assertEqual(len([f for f in findings if f['file'] == 'infra.tf']), 3)

    def test_scan_skips_the_skill_own_directory(self):
        with tempfile.TemporaryDirectory() as root:
            base = Path(root)
            vendored = base / '.agents' / 'skills' / 'hipaa-guardian'
            vendored.mkdir(parents=True)
            (vendored / 'fixture.py').write_text('requests.get(url, verify=False)\n')
            (base / 'app.py').write_text('requests.get(url, verify=False)\n')
            original = repo_scan.SKILL_ROOT
            repo_scan.SKILL_ROOT = vendored.resolve()
            try:
                files = {f['file'] for f in scan(base)['findings']}
            finally:
                repo_scan.SKILL_ROOT = original
        self.assertEqual(files, {'app.py'})


if __name__ == '__main__':
    unittest.main()
