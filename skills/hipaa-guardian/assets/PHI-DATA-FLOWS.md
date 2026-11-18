# PHI data flow and trust boundaries (INTERNAL / UNVERIFIED TEMPLATE)

Product: [PRODUCT]
Reviewed by: [OWNER]
Date: [DATE]
Scope: [INCLUDED SYSTEMS]
Excluded systems: [EXCLUSIONS]

| Source/channel | Data categories | Process/transform | Destination | Processor/vendor | ePHI? | Trust boundary | Evidence | Unknowns |
|---|---|---|---|---|---|---|---|---|
| [Synthetic example only] Web chat | [Unknown] | AI orchestration | [Unknown] | [Unknown] | Unverified | Public -> service | None | Verify authentication and message retention |

## Unverified data flows

[List unknown or inaccessible paths; do not fill with guesses.]

## Required review

- Identity/consent/authorization checks prior to patient-specific disclosure
- Routing of PHI and channel restrictions
- Data processors and BAAs for every applicable path
- Logs, monitoring, caches, telemetry, backups, deletion and restore paths
