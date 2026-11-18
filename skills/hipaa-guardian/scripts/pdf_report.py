"""Full internal HIPAA readiness report as PDF. Offline, stdlib-only, and never a certificate."""
from common import redact, today
from export_tasks import task_summary
from pdf_writer import PDF, PAGE_H, PAGE_W, text_width, wrap
from render_report import OUTSTANDING_CHECKS, SOURCES, summarize

M = 54                    # side margin
CW = PAGE_W - 2 * M       # content width
TOP = 72                  # first baseline under the running header
BOTTOM = PAGE_H - 58      # lowest usable point above the footer

BRAND = '#196b77'
INK = '#0b0b0b'
INK_2 = '#52514e'
MUTED = '#8a8984'
HAIRLINE = '#e1e0d9'
AXIS = '#c3c2b7'
PANEL = '#f4f3ef'
WHITE = '#ffffff'
NOTICE = 'Internal readiness assessment – not a HIPAA certificate or legal opinion'

# Status hues are reserved for state and always ship with a text label, never color alone.
STATUS = {
    'verified': ('Verified', 'Verified', '#0ca30c', WHITE),
    'partially_verified': ('Partially verified', 'Partial', '#fab219', INK),
    'failed': ('Failed', 'Failed', '#d03b3b', WHITE),
    'not_applicable': ('Not applicable', 'N/A', '#e1e0d9', INK),
    'insufficient_evidence': ('Insufficient evidence', 'Unverified', '#a8a79f', INK),
}
STATUS_ORDER = ['verified', 'partially_verified', 'failed', 'not_applicable', 'insufficient_evidence']
STATUS_MEANING = {
    'verified': 'Direct, recent evidence demonstrates the scoped control, with reviewer, method and artifact reference. Not a legal opinion.',
    'partially_verified': 'The control exists but coverage or operation is incomplete; the specific gap is cited.',
    'failed': 'Specific evidence shows the control is missing or inadequate; the finding and its impact are cited.',
    'not_applicable': 'Outside scope, with a documented rationale and a named human approver.',
    'insufficient_evidence': 'Untested, inaccessible or unsupported. The exact artifact needed is listed under Evidence requests.',
}
SEVERITY = {
    'critical': ('Critical', '#d03b3b', WHITE),
    'high': ('High', '#ec835a', INK),
    'medium': ('Medium', '#fab219', INK),
    'low': ('Low', '#e1e0d9', INK),
}
LIMITS = [
    'Source code shows intent; runtime and infrastructure behavior need test, configuration or operational evidence.',
    'Organizational controls need signed contractual or policy evidence confirmed by a human reviewer.',
    'Scanner results are leads, never confirmed violations, and their absence proves nothing.',
]


def _join(values):
    if isinstance(values, (list, tuple)):
        return '; '.join(redact(v, 200) for v in values) or 'None recorded'
    return redact(values, 400) or 'None recorded'


class Report:
    def __init__(self, assessment):
        self.doc = assessment
        self.summary = summarize(assessment)
        self.product = redact(assessment.get('product'), 80) or 'Unnamed product'
        self.pdf = PDF(
            title=f'HIPAA readiness assessment: {self.product}',
            author=redact(assessment.get('assessor'), 80), subject=NOTICE,
        )
        self.y = TOP
        risks = self.summary['risk_items']
        self.confirmed = [r for r in risks if r['status'] in ('failed', 'partially_verified')]
        self.missing = [r for r in risks if r['status'] == 'insufficient_evidence']

    # Layout primitives

    def new_page(self):
        self.pdf.add_page()
        self.pdf.text(M, 34, self.product, 8, True, INK_2)
        label = 'CONFIDENTIAL'
        self.pdf.text(PAGE_W - M - text_width(label, 8, True), 34, label, 8, True, MUTED)
        self.pdf.line(M, 42, PAGE_W - M, 42, HAIRLINE, 0.5)
        self.y = TOP

    def need(self, height):
        if self.y + height > BOTTOM:
            self.new_page()

    def heading(self, title, intro=None):
        self.need(80)
        if self.y > TOP:
            self.y += 18
        self.pdf.rect(M, self.y - 15, 4, 19, fill=BRAND)
        self.pdf.text(M + 12, self.y, title, 17, True, INK)
        self.y += 24
        if intro:
            self.paragraph(intro, color=INK_2)
        self.y += 4

    def subheading(self, title):
        self.need(48)
        self.y += 8
        self.pdf.text(M, self.y, title, 11.5, True, INK)
        self.y += 16

    def paragraph(self, text, size=9.5, bold=False, color=INK, indent=0, after=6):
        leading = size * 1.42
        for line in wrap(text, size, CW - indent, bold):
            self.need(leading)
            self.pdf.text(M + indent, self.y, line, size, bold, color)
            self.y += leading
        self.y += after

    def bullets(self, items, size=9.5):
        leading = size * 1.42
        for item in items:
            lines = wrap(item, size, CW - 14)
            self.need(leading * min(len(lines), 2))
            self.pdf.text(M + 2, self.y, '•', size, True, BRAND)
            for line in lines:
                self.need(leading)
                self.pdf.text(M + 14, self.y, line, size, False, INK)
                self.y += leading
            self.y += 2
        self.y += 4

    def chip(self, x, baseline, label, fill, ink, size=7.2):
        width = text_width(label, size, True) + 10
        self.pdf.rect(x, baseline - size * 0.75 - 3.2, width, size + 5, fill=fill, radius=3)
        self.pdf.text(x + 5, baseline, label, size, True, ink)
        return width

    def table(self, columns, rows, size=8.2):
        """Columns are (header, width); a cell is text or a ('chip', label, fill, ink) tuple."""
        pad, leading = 4, size * 1.35

        def header():
            height = leading + 2 * pad
            self.pdf.rect(M, self.y, CW, height, fill=PANEL)
            x = M
            for title, width in columns:
                self.pdf.text(x + pad, self.y + pad + size, title, size, True, INK_2)
                x += width
            self.y += height

        # A row is drawn whole, so a cell taller than a page is cut rather than run off the page.
        max_lines = int((BOTTOM - TOP - leading - 4 * pad) // leading)

        def fit(lines):
            return lines if len(lines) <= max_lines else lines[:max_lines - 1] + ['[continues in assessment.json]']

        self.need(3 * leading + 4 * pad)
        header()
        for row in rows:
            cells = [cell if isinstance(cell, tuple) else fit(wrap(cell, size, width - 2 * pad))
                     for (_, width), cell in zip(columns, row)]
            height = max(1 if isinstance(c, tuple) else len(c) for c in cells) * leading + 2 * pad
            if self.y + height > BOTTOM:
                self.new_page()
                header()
            x = M
            for (_, width), cell in zip(columns, cells):
                if isinstance(cell, tuple):
                    self.chip(x + pad, self.y + pad + size, *cell[1:])
                else:
                    for i, line in enumerate(cell):
                        self.pdf.text(x + pad, self.y + pad + size + i * leading, line, size, False, INK)
                x += width
            self.y += height
            self.pdf.line(M, self.y, M + CW, self.y, HAIRLINE, 0.5)
        self.y += 10

    def status_chip(self, status):
        _, short, fill, ink = STATUS[status]
        return ('chip', short, fill, ink)

    def severity_chip(self, severity):
        label, fill, ink = SEVERITY[severity]
        return ('chip', label, fill, ink)

    # Sections

    def cover(self):
        p = self.pdf
        p.add_page()
        p.rect(0, 0, PAGE_W, 318, fill=BRAND)
        p.text(M, 64, 'HIPAA GUARDIAN', 9, True, '#bfe0e4')
        p.line(M, 74, M + 36, 74, '#bfe0e4', 1)
        p.text(M, 140, 'HIPAA Readiness', 32, True, WHITE)
        p.text(M, 176, 'Assessment', 32, True, WHITE)
        p.text(M, 204, 'Internal, evidence-based review of HIPAA Security Rule controls', 11, False, '#d7ecef')
        y = 252
        for line in wrap(self.product, 16, CW, True)[:2]:
            p.text(M, y, line, 16, True, WHITE)
            y += 20
        p.text(M, y + 2, 'Environment: ' + (redact(self.doc.get('environment'), 60) or 'unknown'), 9.5, False, '#d7ecef')

        definitions = self.summary['definitions'].values()
        regulatory = sum(1 for d in definitions if d['source_type'] == 'regulatory')
        facts = [
            ('Assessor', redact(self.doc.get('assessor'), 80) or 'Unassigned'),
            ('Legal role', redact(self.doc.get('legal_role'), 80) or 'Unverified'),
            ('Assessment created', redact(self.doc.get('created_on'), 20)),
            ('Report generated', today() + ' (UTC)'),
            ('Regulatory text last checked', redact(self.doc.get('regulatory_status_checked_on'), 20) or 'Not documented'),
            ('Control library reviewed', redact(self.doc.get('control_library_reviewed_as_of'), 20) or 'Unknown'),
            ('Controls assessed', f'{len(self.summary["controls"])} ({regulatory} regulatory, {len(self.summary["controls"]) - regulatory} engineering)'),
            ('Open items', f'{len(self.confirmed)} confirmed gaps, {len(self.missing)} evidence requests'),
        ]
        column = CW / 2
        for i, (label, value) in enumerate(facts):
            x, top = M + (i % 2) * column, 360 + (i // 2) * 42
            p.text(x, top, label.upper(), 7.2, True, MUTED)
            for j, line in enumerate(wrap(value, 10.5, column - 16)[:2]):
                p.text(x, top + 15 + j * 13, line, 10.5, False, INK)

        body = ('This document records evidence for the scoped controls only. It does not certify compliance, and the share '
                'of verified controls is not a compliance score. An organization-wide HIPAA Security Risk Analysis and a '
                'legal review remain required.')
        lines = wrap(body, 9, CW - 28)
        top = 548
        height = 40 + len(lines) * 12.8
        p.rect(M, top, CW, height, fill='#fbeeee', stroke='#d03b3b', line_width=1, radius=4)
        p.text(M + 14, top + 22, 'Not a HIPAA certificate or legal opinion', 11, True, '#8f1f1f')
        for i, line in enumerate(lines):
            p.text(M + 14, top + 40 + i * 12.8, line, 9, False, INK)
        p.text(M, top + height + 24, 'Confidential. Contains security findings: check for patient data and secrets before sharing.', 8.5, False, INK_2)

        credit, site = 'Generated with HIPAA Guardian  ·  ', 'ctoside.com'
        p.text(M, PAGE_H - 70, credit, 8.5, False, MUTED)
        x = M + text_width(credit, 8.5)
        p.text(x, PAGE_H - 70, site, 8.5, True, BRAND)
        p.link(x, PAGE_H - 79, text_width(site, 8.5, True), 12, 'https://ctoside.com')

    def executive_summary(self):
        self.new_page()
        definitions = self.summary['definitions'].values()
        total = len(self.summary['controls'])
        regulatory = sum(1 for d in definitions if d['source_type'] == 'regulatory')
        self.heading('Executive summary', (
            f'{total} controls were assessed: {regulatory} mapped to 45 CFR Part 164 and {total - regulatory} engineering '
            'checks. The counts below describe evidence coverage. They are not a compliance score.'))
        self.stat_tiles()
        self.subheading('Evidence coverage by safeguard area')
        self.coverage_chart()
        self.subheading('Open items by urgency')
        rows = []
        for severity in ('critical', 'high', 'medium', 'low'):
            gaps = sum(1 for r in self.confirmed if r['severity'] == severity)
            asks = sum(1 for r in self.missing if r['severity'] == severity)
            rows.append([self.severity_chip(severity), str(gaps), str(asks), str(gaps + asks)])
        self.table([('Urgency', 120), ('Confirmed gaps', 128), ('Evidence requests', 128), ('Total', 128)], rows)
        self.subheading('Top priorities')
        top = (self.confirmed or self.summary['risk_items'])[:5]
        if top:
            self.bullets([f'{r["id"]}  {task_summary(r)} ({r["severity"]})' for r in top])
        else:
            self.paragraph('No open items are recorded.')

    def stat_tiles(self):
        gap, height = 8, 62
        width = (CW - 4 * gap) / 5
        counts = self.summary['statuses']
        for i, key in enumerate(STATUS_ORDER):
            label, _, fill, _ = STATUS[key]
            x = M + i * (width + gap)
            self.pdf.rect(x, self.y, width, height, fill=PANEL, radius=4)
            self.pdf.rect(x + 10, self.y + 12, 7, 7, fill=fill, radius=1.5)
            for j, line in enumerate(wrap(label, 7.8, width - 30)[:2]):
                self.pdf.text(x + 21, self.y + 18.5 + j * 9.5, line, 7.8, False, INK_2)
            self.pdf.text(x + 10, self.y + 52, str(counts.get(key, 0)), 22, True, INK)
        self.y += height + 14

    def coverage_chart(self):
        by_area = self.summary['by_area']
        areas = sorted(by_area, key=lambda a: (-sum(by_area[a].values()), a))
        label_w, tip_w, row_h, bar_h = 104, 26, 18, 11
        x0 = M + label_w
        span = CW - label_w - tip_w
        peak = max(sum(c.values()) for c in by_area.values())
        x = x0
        for key in STATUS_ORDER:
            label, _, fill, _ = STATUS[key]
            self.pdf.rect(x, self.y - 7, 8, 8, fill=fill, radius=1.5)
            self.pdf.text(x + 11, self.y, label, 7.8, False, INK_2)
            x += 11 + text_width(label, 7.8) + 13
        self.y += 12
        start = self.y
        for area in areas:
            counts = by_area[area]
            self.pdf.text(M, self.y + bar_h - 2, area.capitalize(), 8.5, False, INK)
            x = x0
            for key in STATUS_ORDER:
                n = counts.get(key, 0)
                if not n:
                    continue
                _, _, fill, ink = STATUS[key]
                width = span * n / peak
                self.pdf.rect(x, self.y, max(width - 2, 0.8), bar_h, fill=fill, radius=1.5)
                label = str(n)
                label_width = text_width(label, 7, True)
                if label_width + 6 <= width - 2:
                    self.pdf.text(x + (width - 2 - label_width) / 2, self.y + bar_h - 3, label, 7, True, ink)
                x += width
            self.pdf.text(x + 3, self.y + bar_h - 2, str(sum(counts.values())), 8, True, INK_2)
            self.y += row_h
        self.pdf.line(x0 - 1, start - 2, x0 - 1, self.y - (row_h - bar_h) + 2, AXIS, 0.75)
        self.y += 6

    def scope(self):
        self.new_page()
        self.heading('Scope and method', 'What was assessed, under which assumptions, and how to read each status.')
        doc = self.doc
        rows = [
            ['Product', self.product],
            ['Environment', redact(doc.get('environment'), 100) or 'unknown'],
            ['Legal role', redact(doc.get('legal_role'), 100) or 'unverified'],
            ['Assessor', redact(doc.get('assessor'), 100) or 'Unassigned'],
            ['In-scope systems', _join(doc.get('in_scope_systems', []))],
            ['Excluded systems', _join(doc.get('excluded_systems', []))],
            ['Notes', redact(doc.get('notes'), 1200) or 'None recorded'],
        ]
        self.table([('Item', 120), ('Recorded value', CW - 120)], rows, size=8.8)
        self.subheading('How to read the statuses')
        self.table([('Status', 90), ('Meaning', CW - 90)],
                   [[self.status_chip(k), STATUS_MEANING[k]] for k in STATUS_ORDER], size=8.8)
        self.subheading('What this assessment cannot show')
        self.bullets(LIMITS)

    def gaps(self):
        self.new_page()
        self.heading('Confirmed gaps', 'Failed and partially verified controls, ordered by status then urgency. '
                     'Close each one by applying the recommendation and re-running its verification test.')
        if not self.confirmed:
            self.paragraph('No confirmed gaps are recorded. This does not mean the product is HIPAA compliant: '
                           'unverified requirements may remain.')
        for item in self.confirmed:
            self.gap_card(item)

    def gap_card(self, item):
        size, leading, label_w = 9, 12.6, 96
        fields = [
            ('Authority', f'{item["authority"]} ({item["source_type"]})'),
            ('Observation', item['observation']),
            ('Impact', item['impact']),
            ('Recommendation', item['recommendation']),
            ('Owner', item['owner'] or 'Unassigned'),
            ('Due date', item['due_date'] or 'Not set'),
            ('Verification test', item['verification_test'] or 'Not defined'),
            ('Evidence', item['evidence_refs'] or 'None recorded'),
        ]
        wrapped = [(label, wrap(redact(value, 1500), size, CW - label_w)) for label, value in fields if value]
        height = 34 + sum(len(lines) * leading + 3 for _, lines in wrapped)
        self.need(min(height, BOTTOM - TOP))
        x = M
        x += self.chip(x, self.y - 1, *self.status_chip(item['status'])[1:]) + 5
        x += self.chip(x, self.y - 1, *self.severity_chip(item['severity'])[1:]) + 9
        for line in wrap(f'{item["id"]}  {item["title"]}', 11, M + CW - x, True):
            self.pdf.text(x, self.y, line, 11, True, INK)
            self.y += 15
        self.y += 5
        for label, lines in wrapped:
            self.need(leading)
            self.pdf.text(M, self.y, label, 8, True, INK_2)
            for line in lines:
                self.need(leading)
                self.pdf.text(M + label_w, self.y, line, size, False, INK)
                self.y += leading
            self.y += 3
        self.pdf.line(M, self.y, M + CW, self.y, HAIRLINE, 0.5)
        self.y += 18

    def plan(self):
        self.new_page()
        self.heading('Remediation plan', 'Every open item, ordered by status then urgency. export_tasks.py writes the same '
                     'list for Jira, Notion and Slack.')
        rows = [[str(i), r['id'], task_summary(r), self.severity_chip(r['severity']),
                 redact(r['owner'], 80) or 'Unassigned', redact(r['due_date'], 20) or '–']
                for i, r in enumerate(self.summary['risk_items'], 1)]
        if rows:
            self.table([('#', 24), ('Item', 76), ('Task', 208), ('Urgency', 60), ('Owner', 76), ('Due', 60)], rows)
        else:
            self.paragraph('No open items are recorded.')

    def evidence_requests(self):
        if not self.missing:
            return
        self.new_page()
        self.heading('Evidence requests', 'These controls have no recorded determination. Collect the listed artifact, '
                     'review it, and record the status with a named reviewer.')
        rows = [[r['control_id'], f'{r["title"]}\n{r["authority"]}', r['kind'].replace('_', ' ').capitalize(),
                 '; '.join(r['evidence_examples']) or 'Artifact demonstrating the control']
                for r in self.missing]
        self.table([('Control', 58), ('Requirement', 168), ('Kind', 62), ('Evidence to collect', CW - 288)], rows)

    def matrix(self):
        self.new_page()
        self.heading('Appendix A: control matrix', 'Every control in the library with its recorded status.')
        actual = self.summary['controls']
        rows = [[cid, d['title'], d['authority'], d['kind'].replace('_', ' ').capitalize(), self.status_chip(actual[cid]['status'])]
                for cid, d in self.summary['definitions'].items() if cid in actual]
        self.table([('ID', 52), ('Control', 198), ('Authority', 132), ('Kind', 62), ('Status', 60)], rows)

    def closing(self):
        self.new_page()
        self.heading('Appendix B: limitations and sources')
        self.subheading('Outstanding scope and organizational checks')
        self.bullets(OUTSTANDING_CHECKS)
        self.subheading('Sources')
        for label, url in SOURCES:
            self.need(28)
            self.pdf.text(M, self.y, label, 9, True, BRAND)
            self.pdf.link(M, self.y - 9, text_width(label, 9, True), 12, url)
            self.pdf.text(M, self.y + 11, url, 7.5, False, MUTED)
            self.y += 26
        self.y += 6
        self.paragraph('Recheck official texts and effective dates before relying on this report. Before sharing it, '
                       'perform an authorized manual check for patient data and secrets.', color=INK_2)

    def footers(self):
        total = len(self.pdf.pages)
        for i in range(total):
            self.pdf.line(M, PAGE_H - 44, PAGE_W - M, PAGE_H - 44, HAIRLINE, 0.5, page=i)
            self.pdf.text(M, PAGE_H - 30, 'HIPAA Guardian  ·  ' + NOTICE, 7.5, False, MUTED, page=i)
            label = f'Page {i + 1} of {total}'
            self.pdf.text(PAGE_W - M - text_width(label, 7.5), PAGE_H - 30, label, 7.5, False, MUTED, page=i)

    def build(self):
        self.cover()
        self.executive_summary()
        self.scope()
        self.gaps()
        self.plan()
        self.evidence_requests()
        self.matrix()
        self.closing()
        self.footers()
        return self.pdf.output()


def render_pdf(assessment):
    return Report(assessment).build()
