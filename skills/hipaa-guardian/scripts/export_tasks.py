#!/usr/bin/env python3
"""Turn open findings into import-ready task lists for Jira, Notion, Slack and Markdown checklists.

Files are written locally only; nothing is sent to any service. Values are redacted, and CSV cells
are guarded against formula injection before a tracker or spreadsheet imports them.
"""
import argparse
import csv
from collections import Counter
from pathlib import Path
from common import csv_safe, load_json, output_path, redact, safe_text, today
from render_report import ORDER, summarize
from validate_assessment import validate

FORMATS = ('jira', 'notion', 'slack', 'markdown')
# Jira's default priority scheme; the importer only maps values that exist in the target site.
JIRA_PRIORITY = {'critical': 'Highest', 'high': 'High', 'medium': 'Medium', 'low': 'Low'}
FINDING = {'failed': 'Failed', 'partially_verified': 'Partially verified', 'insufficient_evidence': 'Evidence missing'}
NOT_LEGAL = 'Internal readiness item, not a legal determination.'


def task_summary(item):
    verb = 'Collect evidence' if item['status'] == 'insufficient_evidence' else 'Fix'
    return f'{verb}: {item["title"]}'


def build_tasks(assessment, gaps_only=False):
    tasks = []
    for item in summarize(assessment)['risk_items']:
        evidence_request = item['status'] == 'insufficient_evidence'
        if gaps_only and evidence_request:
            continue
        default_done = ('Evidence reviewed and recorded with a named reviewer; control status re-validated'
                        if evidence_request else 'Fix verified by a re-run test and recorded in assessment.json')
        tasks.append({
            'key': item['id'],
            'summary': task_summary(item),
            'severity': item['severity'],
            'status': item['status'],
            'control_id': item['control_id'],
            'area': item['area'],
            'authority': item['authority'],
            'source_type': item['source_type'],
            'observation': redact(item['observation'], 600),
            'recommendation': redact(item['recommendation'], 600),
            'owner': redact(item['owner'], 80),
            'due_date': redact(item['due_date'], 20),
            'done_when': redact(item['verification_test'], 400) or default_done,
            'evidence_to_collect': '; '.join(item['evidence_examples']) if evidence_request else '',
            'evidence_refs': redact(item['evidence_refs'], 400),
        })
    return tasks


def _description(task):
    lines = [
        f'HIPAA Guardian {task["key"]}: {FINDING[task["status"]]}, {task["severity"]} urgency',
        f'Control: {task["control_id"]}, {task["authority"]} ({task["source_type"]})',
        f'Observation: {task["observation"]}',
        f'Recommendation: {task["recommendation"]}',
    ]
    if task['evidence_to_collect']:
        lines.append(f'Evidence to collect: {task["evidence_to_collect"]}')
    if task['evidence_refs']:
        lines.append(f'Evidence on file: {task["evidence_refs"]}')
    lines.append(f'Done when: {task["done_when"]}')
    if task['owner']:
        lines.append(f'Owner: {task["owner"]}')
    lines.append(NOT_LEGAL)
    return '\n'.join(csv_safe(line, 900) for line in lines)


def _labels(task):
    kind = 'evidence-request' if task['status'] == 'insufficient_evidence' else 'confirmed-gap'
    return ['hipaa', f'hipaa-{task["area"]}', kind, task['control_id'].lower()]


def _write_csv(path, header, rows):
    with path.open('w', newline='', encoding='utf-8') as out:
        writer = csv.writer(out)
        writer.writerow(header)
        writer.writerows(rows)


def write_jira(tasks, path):
    header = ['Summary', 'Issue Type', 'Priority', 'Labels', 'Labels', 'Labels', 'Labels', 'Due Date', 'Description']
    rows = [[csv_safe(f'{t["key"]} {t["summary"]}'), 'Task', JIRA_PRIORITY[t['severity']], *_labels(t),
             csv_safe(t['due_date']), _description(t)] for t in tasks]
    _write_csv(path, header, rows)


def write_notion(tasks, path):
    header = ['Task', 'Status', 'Priority', 'Finding', 'Control', 'Area', 'Authority', 'Owner', 'Due',
              'Recommendation', 'Done when', 'Evidence to collect', 'Item ID']
    rows = [[csv_safe(t['summary']), 'Not started', t['severity'].capitalize(), FINDING[t['status']], t['control_id'],
             t['area'].capitalize(), csv_safe(t['authority']), csv_safe(t['owner']), csv_safe(t['due_date']),
             csv_safe(t['recommendation'], 600), csv_safe(t['done_when'], 400), csv_safe(t['evidence_to_collect'], 400),
             t['key']] for t in tasks]
    _write_csv(path, header, rows)


def write_slack_list(tasks, path):
    header = ['Task', 'Priority', 'Status', 'Owner', 'Due date', 'Control', 'Notes']
    rows = [[csv_safe(t['summary']), t['severity'].capitalize(), 'Not started', csv_safe(t['owner']),
             csv_safe(t['due_date']), t['control_id'],
             csv_safe(f'{t["key"]}. {t["recommendation"]} Done when: {t["done_when"]}', 900)] for t in tasks]
    _write_csv(path, header, rows)


def _slack_escape(value):
    # The file is pasted into the composer (which ignores &lt; entities but pings on a typed @channel)
    # or posted through a webhook (which links <...>). Look-alike characters are safe on both paths.
    return str(value).replace('<', '‹').replace('>', '›').replace('@', '＠')


def _grouped(tasks):
    for severity in ORDER:
        group = [t for t in tasks if t['severity'] == severity]
        if group:
            yield severity, group


def write_slack_message(tasks, path, product):
    kinds = Counter('ask' if t['status'] == 'insufficient_evidence' else 'gap' for t in tasks)
    lines = [
        f'*HIPAA Guardian tasks: {_slack_escape(product)}*',
        f'_{len(tasks)} open items: {kinds["gap"]} confirmed gaps, {kinds["ask"]} evidence requests. {NOT_LEGAL}_',
    ]
    for severity, group in _grouped(tasks):
        lines.extend(['', f'*{severity.capitalize()} ({len(group)})*'])
        for t in group:
            meta = ', '.join(x for x in (t['owner'], f'due {t["due_date"]}' if t['due_date'] else '') if x)
            lines.append(f'• *{t["key"]}* {_slack_escape(t["summary"])}' + (f' ({_slack_escape(meta)})' if meta else ''))
            if t['status'] != 'insufficient_evidence':
                lines.append(f'      _Next:_ {_slack_escape(t["recommendation"])}')
    path.write_text('\n'.join(lines) + '\n', encoding='utf-8')


def write_markdown(tasks, path, product):
    lines = [
        f'# HIPAA Guardian task list: {safe_text(product, 80)}', '',
        f'> {NOT_LEGAL} Generated {today()} from assessment.json. Check for patient data and secrets before sharing.',
    ]
    for severity, group in _grouped(tasks):
        lines.extend(['', f'## {severity.capitalize()} ({len(group)})', ''])
        for t in group:
            lines.append(f'- [ ] **{t["key"]}** {safe_text(t["summary"])} ({t["control_id"]}, {safe_text(t["authority"])})')
            lines.append(f'  - Recommendation: {safe_text(t["recommendation"])}')
            if t['evidence_to_collect']:
                lines.append(f'  - Evidence to collect: {safe_text(t["evidence_to_collect"])}')
            lines.append(f'  - Done when: {safe_text(t["done_when"])}')
            owner = safe_text(t['owner']) or 'Unassigned'
            lines.append(f'  - Owner: {owner} · Due: {safe_text(t["due_date"]) or "not set"}')
    path.write_text('\n'.join(lines) + '\n', encoding='utf-8')


def write_exports(assessment, out_dir, formats=FORMATS, gaps_only=False):
    tasks = build_tasks(assessment, gaps_only)
    product = redact(assessment.get('product'), 80)
    out_dir = Path(out_dir)
    plan = {
        'jira': [('tasks-jira.csv', lambda p: write_jira(tasks, p))],
        'notion': [('tasks-notion.csv', lambda p: write_notion(tasks, p))],
        'slack': [('tasks-slack-list.csv', lambda p: write_slack_list(tasks, p)),
                  ('tasks-slack.txt', lambda p: write_slack_message(tasks, p, product))],
        'markdown': [('tasks.md', lambda p: write_markdown(tasks, p, product))],
    }
    targets = [(output_path(out_dir, name), writer) for fmt in formats for name, writer in plan[fmt]]
    for path, writer in targets:
        writer(path)
    return [path for path, _ in targets]


def main():
    ap = argparse.ArgumentParser(description='Export open findings as import-ready task lists (local files only)')
    ap.add_argument('--assessment', required=True)
    ap.add_argument('--out', required=True, help='Private output directory')
    ap.add_argument('--format', default='all', help='Comma-separated: jira, notion, slack, markdown, or all (default)')
    ap.add_argument('--gaps-only', action='store_true', help='Export failed and partially verified controls only')
    args = ap.parse_args()
    requested = FORMATS if args.format.strip().lower() == 'all' else tuple(
        dict.fromkeys(f.strip().lower() for f in args.format.split(',') if f.strip()))
    unknown = [f for f in requested if f not in FORMATS]
    if unknown or not requested:
        ap.error(f'Unknown format(s): {", ".join(unknown) or "none given"}. Choose from {", ".join(FORMATS)} or all.')
    try:
        doc = load_json(args.assessment)
    except (OSError, ValueError) as exc:
        ap.error(str(exc))
    errors = validate(doc)
    if errors:
        for error in errors[:20]:
            print('ERROR:', error)
        ap.error(f'Assessment validation failed with {len(errors)} error(s)')
    target = Path(args.out).expanduser()
    if target.is_symlink():
        ap.error('Output directory must not be a symlink')
    target.mkdir(parents=True, exist_ok=True)
    try:
        paths = write_exports(doc, target, requested, args.gaps_only)
    except ValueError as exc:
        ap.error(str(exc))
    print('Wrote ' + ', '.join(str(p) for p in paths))
    print('Tasks are readiness work items, not confirmed legal violations. Review before sharing.')


if __name__ == '__main__':
    main()
