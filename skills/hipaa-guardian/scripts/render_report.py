#!/usr/bin/env python3
"""Generate human-reviewed readiness and risk register artifacts, never a certificate."""
import argparse
import csv
from collections import Counter, defaultdict
from pathlib import Path
from common import csv_safe, load_json, load_controls, output_path, redact, safe_text, today
from validate_assessment import validate

ORDER = ['critical', 'high', 'medium', 'low']
SOURCES = [
    ('45 CFR 164.306', 'https://www.ecfr.gov/current/title-45/subtitle-A/subchapter-C/part-164/subpart-C/section-164.306'),
    ('45 CFR 164.308', 'https://www.ecfr.gov/current/title-45/subtitle-A/subchapter-C/part-164/subpart-C/section-164.308'),
    ('45 CFR 164.310', 'https://www.ecfr.gov/current/title-45/subtitle-A/subchapter-C/part-164/subpart-C/section-164.310'),
    ('45 CFR 164.312', 'https://www.ecfr.gov/current/title-45/subtitle-A/subchapter-C/part-164/subpart-C/section-164.312'),
    ('45 CFR 164.314', 'https://www.ecfr.gov/current/title-45/subtitle-A/subchapter-C/part-164/subpart-C/section-164.314'),
    ('45 CFR 164.316', 'https://www.ecfr.gov/current/title-45/subtitle-A/subchapter-C/part-164/subpart-C/section-164.316'),
    ('NIST SP 800-66 Rev. 2 (nonbinding guidance)', 'https://csrc.nist.gov/pubs/sp/800/66/r2/final'),
]
OUTSTANDING_CHECKS = [
    'Verify legal entity, role as a Business Associate and all contractual boundaries.',
    'Confirm PHI data flows, exact subprocessors, contracts and eligible features.',
    'Review operational logs, staff security training, facility controls and incident exercises outside the source repository.',
    'Complete an organization-wide HIPAA Security Risk Analysis and a human legal/regulatory review.',
    'Distinguish proposed rules from currently effective regulations.',
]


def summarize(assessment):
    """Single source for every renderer, so Markdown, CSV, PDF and task exports never disagree."""
    controls = {x['id']: x for x in load_controls()['controls']}
    actual = {x['id']: x for x in assessment['controls']}
    statuses = Counter(x['status'] for x in actual.values())
    by_area = defaultdict(Counter)
    risk_items = []
    for cid, item in actual.items():
        definition = controls[cid]
        by_area[definition['area']][item['status']] += 1
        if item['status'] not in ('verified', 'not_applicable'):
            risk = item['risk']
            risk_items.append({
                'id': 'GAP-' + cid,
                'control_id': cid,
                'area': definition['area'],
                'kind': definition['kind'],
                'source_type': definition['source_type'],
                'authority': definition['authority'],
                'title': definition['title'],
                'severity': risk.get('severity') or definition['priority_hint'],
                'status': item['status'],
                'observation': risk.get('observation') or ('Evidence required' if item['status'] == 'insufficient_evidence' else item['rationale']),
                'impact': risk.get('impact', ''),
                'recommendation': risk.get('recommendation') or ('Collect and validate required evidence' if item['status'] == 'insufficient_evidence' else ''),
                'owner': risk.get('owner', ''),
                'due_date': risk.get('due_date', ''),
                'verification_test': risk.get('verification_test', ''),
                'evidence_refs': '; '.join(redact(ev.get('ref', ''), 200) for ev in item.get('evidence', [])),
                'evidence_examples': definition.get('evidence_examples', []),
            })
    risk_items.sort(key=lambda x: (0 if x['status'] == 'failed' else 1 if x['status'] == 'partially_verified' else 2, ORDER.index(x['severity']), x['control_id']))
    return {'definitions': controls, 'controls': actual, 'statuses': statuses, 'by_area': by_area, 'risk_items': risk_items}


def render(assessment):
    summary = summarize(assessment)
    statuses, by_area, risk_items = summary['statuses'], summary['by_area'], summary['risk_items']
    lines = [
        '# HIPAA Guardian: Internal Readiness Assessment', '',
        '**THIS DOCUMENT IS NOT A HIPAA CERTIFICATE OR LEGAL OPINION.**', '',
        f"Product: **{safe_text(assessment['product'], 80)}**  ",
        f"Environment: {safe_text(assessment.get('environment'), 100)}  ",
        f"Assessment created: {safe_text(assessment['created_on'])}  ",
        f"Report generated (UTC): {today()}  ",
        f"Regulatory status last checked: {safe_text(assessment.get('regulatory_status_checked_on') or 'NOT DOCUMENTED')}  ",
        '', '## Evidence coverage (not a compliance score)', '',
        f"- Verified: **{statuses['verified']}**",
        f"- Partially verified: **{statuses['partially_verified']}**",
        f"- Failed: **{statuses['failed']}**",
        f"- Not applicable (human-approved): **{statuses['not_applicable']}**",
        f"- Insufficient evidence: **{statuses['insufficient_evidence']}**",
        '', '| Area | Verified | Partial | Failed | N/A | Evidence missing |',
        '|---|---:|---:|---:|---:|---:|'
    ]
    for area, row in sorted(by_area.items()):
        lines.append(f"| {area} | {row['verified']} | {row['partially_verified']} | {row['failed']} | {row['not_applicable']} | {row['insufficient_evidence']} |")
    lines.extend(['', '## Confirmed gaps', ''])
    confirmed = [x for x in risk_items if x['status'] in ('failed', 'partially_verified')]
    if not confirmed:
        lines.append('No confirmed gaps recorded. This **does not** mean the product is HIPAA compliant; unresolved evidence requirements may remain.')
    else:
        for item in confirmed[:50]:
            lines.extend([
                f"### {item['id']}: {safe_text(item['title'])}",
                f"- Status / urgency: **{item['status']} / {item['severity']}**",
                f"- Authority: {safe_text(item['authority'])} ({item['source_type']})",
                f"- Observation: {safe_text(item['observation'])}",
                f"- Recommendation: {safe_text(item['recommendation'])}",
                f"- Evidence: {safe_text(item['evidence_refs']) or 'None'}",
                ''
            ])
        if len(confirmed) > 50:
            lines.append(f"Plus {len(confirmed) - 50} confirmed gap records in the CSV.")
    missing = [x for x in risk_items if x['status'] == 'insufficient_evidence']
    lines.extend(['', '## Unverified requirements', ''])
    if missing:
        lines.extend([f'- **{x["control_id"]}** {safe_text(x["title"])} ({safe_text(x["authority"])})' for x in missing])
    else:
        lines.append('All controls have recorded determinations. Validate the underlying evidence and legal scope independently.')
    lines.extend(['', '## Outstanding scope and organizational checks', ''])
    lines.extend(f'- {check}' for check in OUTSTANDING_CHECKS)
    lines.extend(['', '## Sources', ''])
    lines.extend(f'- [{label}]({url})' for label, url in SOURCES)
    lines.extend(['', '**Before sharing this report, perform an authorized manual check for patient data and secrets.**', ''])
    return '\n'.join(lines), risk_items


def main():
    ap = argparse.ArgumentParser(description='Render internal HIPAA readiness report and risk register')
    ap.add_argument('--assessment', required=True)
    ap.add_argument('--out', required=True, help='Private output directory')
    ap.add_argument('--pdf', action='store_true', help='Also write HIPAA-READINESS.pdf (full report, no extra packages)')
    args = ap.parse_args()
    doc = load_json(args.assessment)
    errors = validate(doc)
    if errors:
        for error in errors[:20]:
            print('ERROR:', error)
        ap.error(f'Assessment validation failed with {len(errors)} error(s)')
    md, risks = render(doc)
    target = Path(args.out).expanduser()
    if target.is_symlink():
        ap.error('Output directory must not be a symlink')
    target.mkdir(parents=True, exist_ok=True)
    try:
        written = [output_path(target, 'HIPAA-READINESS.md'), output_path(target, 'risk-register.csv')]
        if args.pdf:
            written.append(output_path(target, 'HIPAA-READINESS.pdf'))
    except ValueError as exc:
        ap.error(str(exc))
    written[0].write_text(md, encoding='utf-8')
    fields = ['id', 'control_id', 'source_type', 'authority', 'title', 'severity', 'status', 'observation', 'impact', 'recommendation', 'owner', 'due_date', 'verification_test', 'evidence_refs']
    with written[1].open('w', newline='', encoding='utf-8') as out:
        writer = csv.DictWriter(out, fieldnames=fields)
        writer.writeheader()
        for item in risks:
            writer.writerow({key: csv_safe(item.get(key, '')) for key in fields})
    if args.pdf:
        from pdf_report import render_pdf
        written[2].write_bytes(render_pdf(doc))
    print('Wrote ' + ', '.join(str(p) for p in written))
    print('All unverified controls are evidence requests, not confirmed legal violations.')


if __name__ == '__main__':
    main()
