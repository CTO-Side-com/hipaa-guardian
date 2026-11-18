# Evidence-first audit methodology

## Scope interview (derive provisional answers from repo; do not require sensitive data)

1. Legal entity, US customers, role as covered entity/business associate/subcontractor, affected agreements.
2. Product versions, client/tenant boundaries, dev/stage/prod parity, regions, runtime/cloud provider and deployment administrator.
3. Categories of ePHI received/stored/transmitted, ingestion/egress channels, data retention/deletion, backups, vendor/API processors.
4. List of responsible personnel and evidence contacts for controls not in code.
5. Existing risk assessment date, operational incident history in *redacted summary form only*, last security review date and outstanding remediation.

Use `unknown` when answers are absent; do not imply the repo establishes organizational facts.

## Controlled evidence types

- `code`: local file path and line number, plus behavior confirmed by code trace or tests. Code-only evidence cannot prove infrastructure or runtime effectiveness.
- `test`: exact test file or redacted test report and run date; validate negative tests for unauthorized access and tenant boundaries.
- `configuration`: safely inspected config path and line, plus approved runtime evidence when needed; no secret values.
- `operational`: redacted system-generated screenshots/reports, restore test receipt, security monitoring reviews, access review logs or incident drill notes.
- `contract`: human confirmation of executed BAA, service eligibility, contract parties/date/version, and secure record location; never upload raw signed contracts unless allowed.
- `policy`: approved, current written policy with owner and evidence of staff execution or training.

A status `verified` requires convincing evidence for the claimed **scope**. An addressable control requires explicit assessment even where an equivalent alternative is selected. A failed control is not the same thing as a scanner hit; confirm manually.

## Threat-model prompts

- Who can call each API and whose patient data may be returned? Are tenant boundaries consistently enforced in ORM, cache, vector search, exports, websockets, background jobs and AI tool calls?
- Can any prompt injection trigger unapproved CRM/EHR operations, PHI disclosure, calls/texts, or insurance queries? Verify the policy gate *after* model suggestions and before any side effect.
- Does browser chat accept PHI from unauthenticated visitors? Where does it go, and do third parties log it?
- Can the system leak patient names through exception traces, analytics events, logs, notification subjects, queue payloads, frontend storage or model observability?
- Are model providers, STT/TTS, embeddings, search, CRM, storage, email and SMS processors contractually authorized and appropriately configured for this exact use?
- What is the restore path and how is emergency access documented and exercised?

## Report discipline

State four kinds of conclusions separately:

1. **Observed fact:** Exact evidence and test scope.
2. **Inference:** Why observed behavior probably creates a risk and what remains untested.
3. **Unknown:** Artifact or access needed to verify.
4. **Recommendation:** Risk-ranked engineering or operational action, with explicit owner.

Risk register fields: `id`, `control_id`, `severity`, `status`, `observation`, `impact`, `recommendation`, `owner`, `due_date`, `evidence_refs`, `verification_test`, `closed_on`.

Never use a percentage of controls marked verified as a HIPAA compliance score. Ensure no raw PHI or secrets appear in reports, sample prompts, fixtures or test captures.
