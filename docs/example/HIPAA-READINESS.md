# HIPAA Guardian: Internal Readiness Assessment

**THIS DOCUMENT IS NOT A HIPAA CERTIFICATE OR LEGAL OPINION.**

Product: **Example Dental Cloud (synthetic)**  
Environment: staging (synthetic data)  
Assessment created: 2026-11-18  
Report generated (UTC): 2026-11-18  
Regulatory status last checked: 2026-11-18  

## Evidence coverage (not a compliance score)

- Verified: **3**
- Partially verified: **2**
- Failed: **2**
- Not applicable (human-approved): **1**
- Insufficient evidence: **67**

| Area | Verified | Partial | Failed | N/A | Evidence missing |
|---|---:|---:|---:|---:|---:|
| administrative | 0 | 1 | 0 | 1 | 27 |
| breach | 0 | 0 | 0 | 0 | 1 |
| documentation | 0 | 0 | 0 | 0 | 5 |
| engineering | 0 | 1 | 1 | 0 | 10 |
| general | 0 | 0 | 0 | 0 | 1 |
| organizational | 0 | 0 | 0 | 0 | 1 |
| physical | 0 | 0 | 0 | 0 | 12 |
| privacy | 0 | 0 | 0 | 0 | 2 |
| technical | 3 | 0 | 1 | 0 | 8 |

## Confirmed gaps

### GAP-TEC-001: Access control enforcement
- Status / urgency: **failed / critical**
- Authority: 45 CFR 164.312(a)(1) (regulatory)
- Observation: The appointment export endpoint loads records by ID without a clinic filter (src/exports/views.py:41).
- Recommendation: Scope the export query by the session's clinic_id and add a negative cross-tenant test.
- Evidence: src/exports/views.py:41

### GAP-ENG-003: Log and telemetry minimization
- Status / urgency: **failed / high**
- Authority: NIST SP 800-66 Rev. 2 (guidance; not a HIPAA mandate) (engineering)
- Observation: Booking errors log the full request payload, including patient name and insurance ID, to the APM service (src/booking/handlers.py:118).
- Recommendation: Log request IDs only, add a redaction filter, and assert in a test that no patient fields reach logs.
- Evidence: src/booking/handlers.py:118

### GAP-ENG-002: PHI-safe AI and tool invocation
- Status / urgency: **partially_verified / critical**
- Authority: NIST SP 800-66 Rev. 2 (guidance; not a HIPAA mandate) (engineering)
- Observation: Tool calls check tenant scope, but the send_reminder tool accepts any phone number the model returns.
- Recommendation: Resolve reminder recipients server-side from the verified patient record and reject model-supplied numbers.
- Evidence: tests/test_agent_tools.py:57

### GAP-ADM-023: Data backup plan
- Status / urgency: **partially_verified / high**
- Authority: 45 CFR 164.308(a)(7)(ii)(A) (regulatory)
- Observation: Nightly database snapshots exist (infra/db.tf:22), but no restore has ever been tested.
- Recommendation: Run and document a restore of a synthetic snapshot into an isolated environment.
- Evidence: infra/db.tf:22


## Unverified requirements

- **ADM-002** Risk analysis (45 CFR 164.308(a)(1)(ii)(A))
- **ADM-003** Risk management (45 CFR 164.308(a)(1)(ii)(B))
- **ADM-011** Information access management (45 CFR 164.308(a)(4)(i))
- **ADM-021** Incident response and reporting (45 CFR 164.308(a)(6)(ii))
- **ADM-029** Business associate subcontractor assurances (45 CFR 164.308(b)(2)-(3))
- **BRH-001** Business associate breach notification (45 CFR 164.410)
- **ENG-001** Cross-tenant authorization in all data planes (NIST SP 800-66 Rev. 2 (guidance; not a HIPAA mandate))
- **GEN-001** Protect ePHI confidentiality, integrity and availability (45 CFR 164.306(a))
- **ORG-001** Business associate contractual protections (45 CFR 164.314(a)(1)-(2))
- **PRV-001** Permitted PHI uses and disclosures (45 CFR 164.502(a))
- **PRV-002** Business associate agreements for PHI (45 CFR 164.504(e))
- **TEC-005** Encryption and decryption (45 CFR 164.312(a)(2)(iv))
- **TEC-009** Person or entity authentication (45 CFR 164.312(d))
- **TEC-010** Transmission security (45 CFR 164.312(e)(1))
- **ADM-001** Security management process (45 CFR 164.308(a)(1)(i))
- **ADM-005** Information system activity review (45 CFR 164.308(a)(1)(ii)(D))
- **ADM-006** Assigned security official (45 CFR 164.308(a)(2))
- **ADM-007** Workforce security (45 CFR 164.308(a)(3)(i))
- **ADM-008** Workforce authorization and supervision (45 CFR 164.308(a)(3)(ii)(A))
- **ADM-009** Workforce clearance procedure (45 CFR 164.308(a)(3)(ii)(B))
- **ADM-010** Termination procedures (45 CFR 164.308(a)(3)(ii)(C))
- **ADM-013** Access authorization (45 CFR 164.308(a)(4)(ii)(B))
- **ADM-014** Access establishment and modification (45 CFR 164.308(a)(4)(ii)(C))
- **ADM-017** Protection from malicious software (45 CFR 164.308(a)(5)(ii)(B))
- **ADM-018** Log-in monitoring (45 CFR 164.308(a)(5)(ii)(C))
- **ADM-019** Password management (45 CFR 164.308(a)(5)(ii)(D))
- **ADM-020** Security incident procedures (45 CFR 164.308(a)(6)(i))
- **ADM-022** Contingency planning (45 CFR 164.308(a)(7)(i))
- **ADM-024** Disaster recovery plan (45 CFR 164.308(a)(7)(ii)(B))
- **ADM-025** Emergency-mode operation plan (45 CFR 164.308(a)(7)(ii)(C))
- **ADM-028** Periodic technical and nontechnical evaluation (45 CFR 164.308(a)(8))
- **ENG-004** Channel-specific PHI gating (NIST SP 800-66 Rev. 2 (guidance; not a HIPAA mandate))
- **ENG-005** Credential exposure and rotation (NIST SP 800-66 Rev. 2 (guidance; not a HIPAA mandate))
- **ENG-006** Vulnerability management pipeline (NIST SP 800-66 Rev. 2 (guidance; not a HIPAA mandate))
- **ENG-007** Sensitive export and download protections (NIST SP 800-66 Rev. 2 (guidance; not a HIPAA mandate))
- **ENG-008** LLM retrieval isolation and retention (NIST SP 800-66 Rev. 2 (guidance; not a HIPAA mandate))
- **ENG-009** Secure integration/webhook processing (NIST SP 800-66 Rev. 2 (guidance; not a HIPAA mandate))
- **ENG-010** Restore and incident exercises (NIST SP 800-66 Rev. 2 (guidance; not a HIPAA mandate))
- **ENG-011** Safe AI side-effect boundaries (NIST SP 800-66 Rev. 2 (guidance; not a HIPAA mandate))
- **PHY-008** Device and media controls (45 CFR 164.310(d)(1))
- **PHY-009** Device and media disposal (45 CFR 164.310(d)(2)(i))
- **PHY-010** Media reuse (45 CFR 164.310(d)(2)(ii))
- **POL-001** Implemented security policies and procedures (45 CFR 164.316(a))
- **POL-002** Document required policies and activities (45 CFR 164.316(b)(1))
- **POL-003** Six-year security-document retention (45 CFR 164.316(b)(2)(i))
- **TEC-003** Emergency access procedure (45 CFR 164.312(a)(2)(ii))
- **TEC-006** Audit controls (45 CFR 164.312(b))
- **TEC-007** Integrity safeguards (45 CFR 164.312(c)(1))
- **TEC-008** ePHI integrity authentication mechanism (45 CFR 164.312(c)(2))
- **TEC-011** Transmission integrity controls (45 CFR 164.312(e)(2)(i))
- **ADM-004** Sanction policy (45 CFR 164.308(a)(1)(ii)(C))
- **ADM-015** Security awareness and training (45 CFR 164.308(a)(5)(i))
- **ADM-016** Security reminders (45 CFR 164.308(a)(5)(ii)(A))
- **ADM-026** Contingency plan testing and revision (45 CFR 164.308(a)(7)(ii)(D))
- **ADM-027** Application and data criticality analysis (45 CFR 164.308(a)(7)(ii)(E))
- **ENG-012** Browser storage and frontend privacy (NIST SP 800-66 Rev. 2 (guidance; not a HIPAA mandate))
- **PHY-001** Facility access controls (45 CFR 164.310(a)(1))
- **PHY-002** Facility contingency operations (45 CFR 164.310(a)(2)(i))
- **PHY-003** Facility security plan (45 CFR 164.310(a)(2)(ii))
- **PHY-004** Facility access validation (45 CFR 164.310(a)(2)(iii))
- **PHY-006** Workstation use (45 CFR 164.310(b))
- **PHY-007** Workstation security (45 CFR 164.310(c))
- **PHY-011** Device and media accountability (45 CFR 164.310(d)(2)(iii))
- **PHY-012** Data backup before device movement (45 CFR 164.310(d)(2)(iv))
- **POL-004** Availability of documentation (45 CFR 164.316(b)(2)(ii))
- **POL-005** Documentation updates (45 CFR 164.316(b)(2)(iii))
- **PHY-005** Facility maintenance records (45 CFR 164.310(a)(2)(iv))

## Outstanding scope and organizational checks

- Verify legal entity, role as a Business Associate and all contractual boundaries.
- Confirm PHI data flows, exact subprocessors, contracts and eligible features.
- Review operational logs, staff security training, facility controls and incident exercises outside the source repository.
- Complete an organization-wide HIPAA Security Risk Analysis and a human legal/regulatory review.
- Distinguish proposed rules from currently effective regulations.

## Sources

- [45 CFR 164.306](https://www.ecfr.gov/current/title-45/subtitle-A/subchapter-C/part-164/subpart-C/section-164.306)
- [45 CFR 164.308](https://www.ecfr.gov/current/title-45/subtitle-A/subchapter-C/part-164/subpart-C/section-164.308)
- [45 CFR 164.310](https://www.ecfr.gov/current/title-45/subtitle-A/subchapter-C/part-164/subpart-C/section-164.310)
- [45 CFR 164.312](https://www.ecfr.gov/current/title-45/subtitle-A/subchapter-C/part-164/subpart-C/section-164.312)
- [45 CFR 164.314](https://www.ecfr.gov/current/title-45/subtitle-A/subchapter-C/part-164/subpart-C/section-164.314)
- [45 CFR 164.316](https://www.ecfr.gov/current/title-45/subtitle-A/subchapter-C/part-164/subpart-C/section-164.316)
- [NIST SP 800-66 Rev. 2 (nonbinding guidance)](https://csrc.nist.gov/pubs/sp/800/66/r2/final)

**Before sharing this report, perform an authorized manual check for patient data and secrets.**
