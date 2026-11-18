"""Offline tests for the PDF report and task exports, no external packages."""
import csv
import re
import subprocess
import sys
import tempfile
import unittest
import zlib
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1] / 'scripts'
sys.path.insert(0, str(SCRIPTS))

from common import write_json
from init_assessment import create
from export_tasks import FORMATS, build_tasks, write_exports
from pdf_report import render_pdf
from render_report import summarize

FORMULA_START = ('=', '+', '-', '@', '\t', '\r')


def synthetic_assessment():
    doc = create('Synthetic Dental Cloud', 'staging')
    first, second, third = doc['controls'][0], doc['controls'][1], doc['controls'][2]
    evidence = [{
        'type': 'code', 'ref': 'src/auth/tenant.py:88', 'method': 'Code trace of tenant filter',
        'verified_on': '2026-11-18', 'reviewer': 'Synthetic Reviewer',
    }]
    first.update({
        'status': 'failed', 'rationale': 'Tenant filter missing on export path',
        'reviewer': 'Synthetic Reviewer', 'evidence': evidence,
    })
    first['risk'].update({
        'severity': 'critical',
        'observation': '=HYPERLINK("http://attacker.invalid") contact jane.doe@clinic.example or +1 (212) 555-1234',
        'recommendation': 'Scope export queries by tenant <!channel> & verify',
        'owner': 'Platform team', 'due_date': '2026-12-01',
        'verification_test': 'Cross-tenant export returns 403 for synthetic clinic B',
    })
    second.update({
        'status': 'partially_verified', 'rationale': 'Backups exist; restore untested',
        'reviewer': 'Synthetic Reviewer', 'evidence': evidence,
    })
    second['risk'].update({'severity': 'high', 'observation': 'Restore never exercised', 'recommendation': 'Run restore drill'})
    third.update({'status': 'verified', 'rationale': 'Reviewed', 'reviewer': 'Synthetic Reviewer', 'evidence': evidence})
    return doc


def pdf_streams(data):
    return [zlib.decompress(m.group(1)) for m in re.finditer(rb'stream\n(.*?)\nendstream', data, re.S)]


class PdfReportTests(unittest.TestCase):
    def test_pdf_cross_reference_table_points_at_every_object(self):
        data = render_pdf(synthetic_assessment())
        self.assertTrue(data.startswith(b'%PDF-1.4'))
        self.assertTrue(data.rstrip().endswith(b'%%EOF'))
        startxref = int(re.search(rb'startxref\s+(\d+)\s+%%EOF', data).group(1))
        self.assertEqual(data[startxref:startxref + 4], b'xref')
        header = re.match(rb'xref\n0 (\d+)\n', data[startxref:])
        count = int(header.group(1))
        entries = data[startxref + header.end():].split(b'\n')[:count]
        self.assertEqual(entries[0].strip(), b'0000000000 65535 f')
        for number, entry in enumerate(entries[1:], 1):
            offset = int(entry[:10])
            self.assertTrue(data[offset:].startswith(f'{number} 0 obj'.encode()), f'object {number} offset is wrong')

    def test_page_count_matches_page_tree(self):
        data = render_pdf(synthetic_assessment())
        pages = len(re.findall(rb'/Type /Page\b(?!s)', data))
        declared = int(re.search(rb'/Type /Pages /Kids \[[^\]]*\] /Count (\d+)', data).group(1))
        self.assertEqual(pages, declared)
        self.assertGreaterEqual(pages, 5)

    def test_every_page_carries_the_not_a_certificate_notice(self):
        streams = pdf_streams(render_pdf(synthetic_assessment()))
        self.assertTrue(streams)
        for stream in streams:
            self.assertIn(b'not a HIPAA certificate or legal opinion', stream)

    def test_pdf_redacts_contact_details_and_keeps_findings(self):
        text = b'\n'.join(pdf_streams(render_pdf(synthetic_assessment())))
        self.assertNotIn(b'jane.doe', text)
        self.assertNotIn(b'555-1234', text)
        self.assertIn(b'[REDACTED_EMAIL]', text)
        self.assertIn(b'Restore never exercised', text)

    def test_non_latin_text_does_not_crash_the_writer(self):
        doc = synthetic_assessment()
        doc['product'] = 'Clinic کلینیک \U0001F9B7 (\\) test'
        data = render_pdf(doc)
        self.assertTrue(data.startswith(b'%PDF'))

    def test_render_report_cli_writes_pdf_alongside_markdown(self):
        with tempfile.TemporaryDirectory() as root:
            base = Path(root)
            write_json(base / 'assessment.json', synthetic_assessment())
            subprocess.run(
                [sys.executable, str(SCRIPTS / 'render_report.py'), '--assessment', str(base / 'assessment.json'),
                 '--out', str(base / 'out'), '--pdf'],
                check=True, capture_output=True, text=True,
            )
            self.assertTrue((base / 'out' / 'HIPAA-READINESS.md').exists())
            self.assertTrue((base / 'out' / 'HIPAA-READINESS.pdf').read_bytes().startswith(b'%PDF'))


class TaskExportTests(unittest.TestCase):
    def setUp(self):
        self.doc = synthetic_assessment()
        self.tmp = tempfile.TemporaryDirectory()
        self.out = Path(self.tmp.name)
        self.paths = write_exports(self.doc, self.out)

    def tearDown(self):
        self.tmp.cleanup()

    def read_csv(self, name):
        with (self.out / name).open(newline='', encoding='utf-8') as f:
            return list(csv.reader(f))

    def test_one_task_per_open_item_in_risk_order(self):
        tasks = build_tasks(self.doc)
        risks = summarize(self.doc)['risk_items']
        self.assertEqual([t['key'] for t in tasks], [r['id'] for r in risks])
        self.assertTrue(tasks[0]['summary'].startswith('Fix: '))
        self.assertTrue(tasks[-1]['summary'].startswith('Collect evidence: '))

    def test_gaps_only_drops_evidence_requests(self):
        keys = [t['key'] for t in build_tasks(self.doc, gaps_only=True)]
        self.assertEqual(len(keys), 2)

    def test_jira_csv_uses_importer_columns_and_default_priorities(self):
        rows = self.read_csv('tasks-jira.csv')
        header = rows[0]
        self.assertEqual(header[0], 'Summary')
        self.assertGreaterEqual(header.count('Labels'), 2)
        priority = header.index('Priority')
        self.assertTrue({r[priority] for r in rows[1:]} <= {'Highest', 'High', 'Medium', 'Low'})
        self.assertEqual(rows[1][priority], 'Highest')
        for row in rows[1:]:
            for i, name in enumerate(header):
                if name == 'Labels':
                    self.assertNotIn(' ', row[i])
        self.assertEqual(len(rows) - 1, len(summarize(self.doc)['risk_items']))

    def test_notion_and_slack_list_csv_put_the_task_name_first(self):
        for name in ('tasks-notion.csv', 'tasks-slack-list.csv'):
            rows = self.read_csv(name)
            self.assertEqual(rows[0][0], 'Task')
            self.assertTrue(rows[1][0].startswith('Fix: '))

    def test_no_csv_cell_can_be_evaluated_as_a_formula(self):
        for name in ('tasks-jira.csv', 'tasks-notion.csv', 'tasks-slack-list.csv'):
            for row in self.read_csv(name):
                for cell in row:
                    for line in cell.split('\n'):
                        self.assertFalse(line.startswith(FORMULA_START), f'{name}: {line[:40]!r}')

    def test_exports_redact_contact_details(self):
        for path in self.paths:
            text = path.read_text(encoding='utf-8')
            self.assertNotIn('jane.doe', text, path.name)
            self.assertNotIn('555-1234', text, path.name)

    def test_slack_message_escapes_mentions_and_control_characters(self):
        text = (self.out / 'tasks-slack.txt').read_text(encoding='utf-8')
        self.assertNotIn('<!channel>', text)
        self.assertIn('&lt;!channel&gt;', text)
        self.assertIn('&amp;', text)

    def test_markdown_checklist_uses_unchecked_boxes(self):
        text = (self.out / 'tasks.md').read_text(encoding='utf-8')
        boxes = re.findall(r'^- \[ \] ', text, re.M)
        self.assertEqual(len(boxes), len(build_tasks(self.doc)))

    def test_cli_rejects_unknown_format(self):
        with tempfile.TemporaryDirectory() as root:
            write_json(Path(root) / 'a.json', self.doc)
            result = subprocess.run(
                [sys.executable, str(SCRIPTS / 'export_tasks.py'), '--assessment', str(Path(root) / 'a.json'),
                 '--out', root, '--format', 'trello'],
                capture_output=True, text=True,
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn('trello', result.stderr)

    def test_all_formats_written(self):
        self.assertEqual(set(FORMATS), {'jira', 'notion', 'slack', 'markdown'})
        names = {p.name for p in self.paths}
        self.assertEqual(names, {'tasks-jira.csv', 'tasks-notion.csv', 'tasks-slack-list.csv', 'tasks-slack.txt', 'tasks.md'})


if __name__ == '__main__':
    unittest.main()
