---
status: active
phase: Public release v1.0
next: Final whole-branch review, then create CTO-Side-com/hipaa-guardian and push
tests: unit 36/36 on Python 3.9, 3.10, 3.13 (2026-11-18)
hosting: github:CTO-Side-com/hipaa-guardian
updated: 2026-11-18 19:53 +0400
---

# HIPAA Guardian: handoff

## Current state

- Skill lives in `skills/hipaa-guardian/` (Agent Skills convention, discovered by `gh skill`, Claude Code plugins and Cursor).
- Client-specific material from the original draft was removed before the first commit so it never enters public history.
- Not yet pushed. Target: `https://github.com/CTO-Side-com/hipaa-guardian` (public, MIT).

## What's working

- `render_report.py --pdf`: full PDF report via the in-house stdlib PDF writer (`pdf_writer.py`, `pdf_report.py`). Checked visually with poppler and macOS Quartz.
- `export_tasks.py`: Jira CSV, Notion CSV, Slack Lists CSV, Slack message, Markdown checklist. Formula-injection guarded, redacted, Slack mentions escaped.
- Scanner: 13 rules (6 new), skips the skill's own folder when vendored inside the audited repo.
- Validator: bad or impossible `verified_on` dates are errors, not crashes.
- Install paths verified locally: Claude Code plugin (`claude plugin marketplace add` + `install hipaa-guardian@ctoside` in a scratch config), `gh skill install --from-local` for claude-code, github-copilot, cursor at project and user scope. Remote (`CTO-Side-com/...`) forms still to verify after the push.
- `docs/example/`: synthetic assessment and every output, rebuilt by `make_example.py`. README previews (`docs/images/report-preview.png`) were rendered with macOS `qlmanage` from single-page PDFs; poppler substitutes a regular face for Helvetica-Bold on this machine, Quartz renders it correctly.

## Decisions (2026-11-18)

- [x] Repo owner: `CTO-Side-com` org.
- [x] Client-specific section and checklist: removed entirely.
- [x] License: MIT.
- [x] Publish: create the public repo and push once tests and the final review are green.

## Needs you

(none open)

## Next steps

1. Done 19:49: final review returned no critical/high. Plants a/b/c all caught; worktree removed.
2. Done 19:53: all findings fixed with 8 new tests, each watched failing first (redact-before-truncate, Slack paste mentions, tall table rows, wrap() speed and negative width, validator gaps incl. due_date format, scanner CamelCase/JSON keys and xmlns, risk-register CSV formula check, installation.md paths, DEL char, SKILL.md report description).
3. `gh repo create CTO-Side-com/hipaa-guardian --public`, push `main`.
4. Verify remote installs: `/plugin marketplace add CTO-Side-com/hipaa-guardian`, `gh skill install CTO-Side-com/hipaa-guardian hipaa-guardian`, git clone one-liner; confirm the CI run is green.

## Ideas not started

- Run the skill-creator description optimizer (trigger evals) on SKILL.md.
- More scanner rules (S3 policies, Postgres `sslmode=disable`, Sentry `send_default_pii`).
