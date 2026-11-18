---
status: done
phase: Public release v1.0
tests: unit 36/36 on Python 3.9, 3.10, 3.13 locally; CI 3.9 + 3.13 green (2026-11-18)
hosting: github:CTO-Side-com/hipaa-guardian
live: https://github.com/CTO-Side-com/hipaa-guardian
updated: 2026-11-18 19:56 +0400
---

# HIPAA Guardian: handoff

## Current state

- Public at https://github.com/CTO-Side-com/hipaa-guardian (MIT, topics set, homepage ctoside.com).
- Skill lives in `skills/hipaa-guardian/` (Agent Skills convention, discovered by `gh skill`, Claude Code plugins and Cursor).
- Client-specific material from the original draft was removed before the first commit, so it is not in public history.
- CI (`.github/workflows/tests.yml`) runs on `ubuntu-24.04`, pinned because setup-python has no 3.9 build for ubuntu-latest (26.04).

## What's working

- `render_report.py --pdf`: full PDF report via the in-house stdlib PDF writer (`pdf_writer.py`, `pdf_report.py`).
- `export_tasks.py`: Jira CSV, Notion CSV, Slack Lists CSV, Slack message, Markdown checklist. Formula-injection guarded, redacted (scrubbed before truncation), Slack `@ < >` swapped for look-alikes.
- Scanner: 13 rules, matching quoted JSON and CamelCase keys; skips the skill's own folder when vendored inside the audited repo.
- Validator: bad `verified_on` and `due_date` values, and non-string control ids, are errors, not crashes.
- Installs verified from GitHub on 2026-11-18 in isolated scratch homes: `gh skill install` (claude-code project, cursor user), the git-clone one-liner, and `claude plugin marketplace add CTO-Side-com/hipaa-guardian` + `install hipaa-guardian@ctoside`.
- Final whole-branch review done: no critical/high findings; all medium/low findings fixed with tests watched failing first; 3 planted defects all caught.

## Not verified

- Live imports into Jira, Notion and Slack Lists (file formats follow the vendors' documented import paths; not imported into a real workspace).
- `npx skills` and other third-party installers (not documented in the README).

## Decisions (2026-11-18)

- [x] Repo owner: `CTO-Side-com` org.
- [x] Client-specific section and checklist: removed entirely.
- [x] License: MIT.
- [x] Publish: create the public repo and push once tests and the final review are green.

## Needs you

(none open)

## Next steps

1. Optional: import `docs/example/tasks-*.csv` into real Jira, Notion and Slack workspaces once and fix any column mapping friction.
2. Optional: set a GitHub social preview image (Settings > General > Social preview; no API for it).

## Ideas not started

- Run the skill-creator description optimizer (trigger evals) on SKILL.md.
- More scanner rules (S3 bucket policies, Postgres `sslmode=disable`, Sentry `send_default_pii`).
