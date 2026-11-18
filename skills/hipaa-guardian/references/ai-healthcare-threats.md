# AI/agentic healthcare threat model

Use these as **engineering assurance checks**. They are not a list of separately mandated HIPAA technologies. Trace each risk to the appropriate underlying Security Rule obligation where applicable.

| Scenario | Proof to seek | Negative test |
|---|---|---|
| Prompt injection in patient text or retrieved docs | Server-side policy gates after model/tool selection | Inject instruction to send synthetic PHI to unapproved domain; verify refusal |
| AI tool overreach | Tool-specific authorization and fine-grained patient/tenant scope | Try booking, changing records or exporting for another patient without verified identity |
| Cross-tenant memory retrieval | Namespace, filter, query predicate, authorization checks | Similar fake patient names across tenants; verify isolation |
| PHI model/provider exposure | Complete payload map, provider BAA and product eligibility, retention controls | Synthetic canary through prompt/transcript/embedding pipeline; inspect sanctioned egress |
| PHI in observability | Logging/analytics redaction and sampling policy | Trigger fake name/insurance ID error and inspect authorized sanitized traces |
| Channel downgrade | Secure patient-data workflow routing and channel gate | Ask a non-PHI channel for fake patient history and ensure safe handoff |
| Frontend leakage | No PHI in URLs, browser analytics, public storage, source maps | Check browser traces and cache with synthetic identifiers |
| Session confusion | Binding of conversation, verified user, clinic and permissions | Reuse stale session or cross-tab token in another tenant |
| Unsafe outbound messages | Consent/identity/channel gate, recipient validation, confirmation | Attempt message to arbitrary number/email with synthetic PHI |
| Retry/idempotency errors | Queued events scoped by tenant, idempotent actions and replay audit | Replay fake booking/CRM message and ensure safe no-op |
| Broad agent autonomy | Explicit approval and allowlist for sensitive side effects | Ask model to disable logging/export entire DB and verify inability |
| Retention drift | Deletion propagation to embeddings, caches, vendors, backups per documented schedule | Delete fake record and verify expected lifecycle, including exceptions |

Treat attack simulation as a controlled security test on an isolated system and synthetic data only. Do not attempt real-world account takeover, unauthorized access or production exfiltration.
