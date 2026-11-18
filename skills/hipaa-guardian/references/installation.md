# Install HIPAA Guardian

Full, copy-paste install commands for every agent live in the repository README:
https://github.com/CTO-Side-com/hipaa-guardian#install

Quick reference (the skill folder is `skills/hipaa-guardian` in the repository):

| Agent | Project scope | User scope |
|---|---|---|
| Claude Code | `.claude/skills/hipaa-guardian` | `~/.claude/skills/hipaa-guardian` |
| GitHub Copilot | `.github/skills/hipaa-guardian` | `~/.copilot/skills/hipaa-guardian` |
| Cursor | `.cursor/skills/hipaa-guardian` | `~/.cursor/skills/hipaa-guardian` |

With the GitHub CLI (2.90+): `gh skill install CTO-Side-com/hipaa-guardian hipaa-guardian --agent claude-code` (or `github-copilot`, `cursor`), adding `--scope user` for a personal install.

Before running scripts, decide where PRIVATE evidence artifacts will be stored; prefer `hipaa-output/` and add it to the repository `.gitignore`. Authorize only read-only static scans at first. Avoid real patient data, production credentials, uploading source to unfamiliar scanning services, and auto-fixing code.

Example conversation in Claude Code:

> /hipaa-guardian audit
> This is a dental-practice SaaS. Start read-only. Do not access any production data or secrets. Inspect source and deployment configuration, map ePHI data flows, run only offline metadata-only scanning, and produce a HIPAA control evidence checklist plus prioritized remediation plan. Ask before generating reports under hipaa-output/ or changing source.

For a narrow follow-up: `/hipaa-guardian triage GAP-TEC-001`.
For an approved patch plan: `/hipaa-guardian fix GAP-ENG-001` (this does not bypass the permission requirement).
For deliverables: `/hipaa-guardian report --pdf` and `/hipaa-guardian tasks jira`.

## Disabling risky practices

- Keep PHI and production secrets outside the working directory. Never ask the agent to ingest patient messages or dump unredacted logs.
- Do not run production pentests automatically. Use a written authorization and an isolated test environment.
- Record human approvals and legal review for regulations, addressable implementation decisions and BAAs.
- The agent interprets the skill; it does not independently authenticate the user's evidence or issue an accredited certification.

## Test the installation

```
python3 -m unittest discover -s <SKILL_DIR>/tests -v
python3 <SKILL_DIR>/scripts/init_assessment.py --product 'Test App' --out hipaa-output/assessment.json
python3 <SKILL_DIR>/scripts/validate_assessment.py --assessment hipaa-output/assessment.json
python3 <SKILL_DIR>/scripts/render_report.py --assessment hipaa-output/assessment.json --out hipaa-output --pdf
```

The blank assessment intentionally contains no verified controls.
