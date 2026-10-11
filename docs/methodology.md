# Methodology and assessment protocol

All policies, scores, owners and decisions below are authored synthetic assumptions for Harborlight Workspaces.

## Scope and judgment

A fictional B2B collaboration service uses identity, release, logging, recovery and incident processes plus one managed queue supplier. Excluded: real infrastructure, contracts, legal applicability, interviews, technical inspection and complete NIST baseline coverage. Test method is examination of synthetic artifacts. No operational test was performed.

Implementation status is a management assertion: **implemented** or **proposed**. Sample status is computed separately: **sample_pass**, **sample_fail**, **inconclusive**, **not_tested**. Neither is an assurance opinion.

## Risk scoring

Likelihood and impact each use integers 1-5.

| Rating | Likelihood over the fictional next year | Impact on fictional operations |
|---|---|---|
| 1 | Exceptional under scenario assumptions | Negligible, local rework |
| 2 | Unlikely but plausible | Limited disruption to one team |
| 3 | Plausible, periodic opportunity | Material disruption to one service |
| 4 | Likely, repeated opportunities | Major disruption across customer operations |
| 5 | Almost certain under assumptions | Severe confidentiality or availability consequences |

Score = likelihood x impact. Low 1-5; moderate 6-11; high 12-19; critical 20-25. Products such as 7, 11, 13 or 19 cannot arise from this integer matrix; bands may include unreachable values for readable interval definitions. Validator checks component bounds and exact products, and tests cover band boundaries and reachable scores.

Each risk includes separate likelihood and impact rationale. **Current assessed score is held equal to inherent score** because the fixtures do not support defensible residual-risk estimation. Target likelihood/impact and score describe a proposed post-remediation planning scenario. They are neither measured residual risk nor accepted exposure. No numeric percentage discount is used.

Priority: P1 for high/critical risk with an observed exception, missing required exercise or overdue current evidence; P2 for planned capability or moderate-risk supplier refresh. C01 is monitored despite a passing sample because its current risk remains critical. Priority considers urgency and dependencies; risk score alone does not dictate order.

## Evidence gates

Evidence age = fixed as-of date minus the earliest of collection date, registered evidence period end, actual artifact period end and tested population period end. A newly received historical worksheet cannot become current assurance. Age equal to max_age_days is fresh; age greater is stale. Authored policies: 30 days for access/log/change, 90 days for recovery, 365 days for incident/supplier. These are lab choices, not NIST-prescribed periods.

- MISSING: registered file absent.
- STALE: age exceeds the control's authored maximum.
- OUT_OF_SCOPE: control scope differs, payload period contradicts the register, period does not cover the test population, vendor identity is wrong, or dated population rows fall outside the declared period.
- INSUFFICIENT: a population date is absent/invalid, or fresh scoped evidence has an empty sample or row count differs from the declared sample.
- EXCEPTION: one or more sampled rows violate the bounded criterion.
- NOT_TESTED: control proposed or test has no performed date.

Multiple evidence gate codes can coexist. NOT_TESTED takes precedence for status, then evidence gates produce inconclusive; exceptions produce sample_fail; otherwise sample_pass. Stale evidence is not used to infer current effectiveness even when historical rows would pass.

Sample populations are explicitly fictional and small. Full population sampling within a fixture gives no statistical or enterprise-wide assurance. Change dates are day-level and require approval strictly before deployment; same-day approval is conservatively an exception because ordering cannot be proven.

## Closure and governance

Every baseline seeded finding traces to an open action. All five baseline actions remain open. Positive closure cases occur only in temporary regression fixtures.

Performed UTC timestamps must follow the population period end and evidence collection date and precede assessment. The date-only performed_on field must agree with the timestamp. Evidence collection must not predate its declared period end.

Closure requires completed_at, a **distinct new** test and evidence ID, an appended retest event tied to the same remediation/control, a passing current sample, and current same-control review evidence. The follow-up population must begin after completion. Ordering is completion < performed retest < reviewer sign-off <= closure <= assessment; the reviewer must also sign after the retest assessment. Reviewer, event, test, remediation and control IDs plus reviewed_at must match the synthetic sign-off artifact.

The regression scenario appends T07/E07/EV07 and reviewer E08 after M02 completion, leaving T03/E03/EV03 and CHG-003's original missing approval intact. Baseline tests or retroactive corrections cannot be reused as successful follow-up evidence.

## Append-style event history

registers.json includes six initial assessment events with copied workpapers, artifact payloads, fingerprints and result snapshots. data/history-baseline.json preserves the required initial prefix. Later retests append events with sequential IDs and predecessor references. Validation rejects missing/altered initial events, sequence gaps, historical workpaper or artifact rewrites, wrong identities and mismatched active results. The HTML displays both initial and later events; current results do not erase earlier exceptions.

These are **editable JSON files with bounded consistency checks**, not cryptographically immutable records, authenticated audit logs or tamper-proof storage. A person able to rewrite both baseline and registers can defeat local consistency checks. Git history is supporting provenance, not an authenticity guarantee.

## Live outputs versus fixed memo

Current counts, open/closed actions, ordered queue, dates, vendor records and event history are rendered from registers. docs/decision-memo.md is explicitly a fixed October 11 baseline decision memo; it is not an automatically refreshed management opinion. The project uses a 5x5 illustrative risk matrix. A separate portfolio example may use 3x3; scales must not be merged without a documented conversion.

## Reproducibility

JSON is authoritative. CSV files and reports are derived and must not be hand-edited. Fixed dates and stable ordering ensure repeatable output. SHA-256 hashes of available artifacts are recorded in assessment.json; E04 records null because the requested file is absent. Hashes detect changes, not authenticity or chain of custody.

Software validation checks IDs, links, scoring, content-level periods/vendor identity/row dates, chronology, unsafe paths, sample declarations, closure preconditions and append-style history consistency. It is a compact fixture validator, not a general-purpose GRC platform or hardened untrusted-data ingestion service.

check compares all six CSV registers, assessment JSON, HTML, test-results CSV and executive summary against two deterministic builds in an isolated temporary directory. It does not overwrite working outputs. verify.py runs this comparison before any writing; it never repairs report drift automatically. Run build explicitly after intentional source changes.

## C02 criterion boundary

C02 examines only nonempty disposition fields in two historical June worksheets. Weekly cadence, complete weekly coverage, escalation appropriateness and escalation closure are not assessed. Its initial workpaper and result snapshot labels were corrected to this narrower actual method; this editorial correction does not change artifacts, dates, result status or history ordering. The Git commit preserves the prior wording. Other original sample exceptions remain unchanged.
