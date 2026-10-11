# Methodology and assessment protocol

All policies, scores, owners and decisions below are authored synthetic assumptions for Harborlight Workspaces.

## Scope and judgment

A fictional B2B collaboration service uses identity, release, logging, recovery and incident processes plus one managed queue supplier. Excluded: real infrastructure, contracts, legal applicability, interviews, technical inspection and complete NIST baseline coverage. Test method is examination of synthetic artifacts. No operational test was performed.

Implementation status is a management assertion: **implemented** or **proposed**. Sample status is computed separately: **sample_pass**, **sample_fail**, **inconclusive**, **not_tested**. Neither is an assurance opinion.

## Risk scoring

Likelihood and impact each use integers 1–5.

| Rating | Likelihood over the fictional next year | Impact on fictional operations |
|---|---|---|
| 1 | Exceptional under scenario assumptions | Negligible, local rework |
| 2 | Unlikely but plausible | Limited disruption to one team |
| 3 | Plausible, periodic opportunity | Material disruption to one service |
| 4 | Likely, repeated opportunities | Major disruption across customer operations |
| 5 | Almost certain under assumptions | Severe confidentiality or availability consequences |

Score = likelihood × impact. Low 1–5; moderate 6–11; high 12–19; critical 20–25. Products such as 7, 11, 13 or 19 cannot arise from this integer matrix; bands may include unreachable values for readable interval definitions. Validator checks component bounds and exact products, and tests cover band boundaries and reachable scores.

Each risk includes separate likelihood and impact rationale. **Current assessed score is held equal to inherent score** because the fixtures do not support defensible residual-risk estimation. Target likelihood/impact and score describe a proposed post-remediation planning scenario. They are neither measured residual risk nor accepted exposure. No numeric percentage discount is used.

Priority: P1 for high/critical risk with an observed exception, missing required exercise or overdue current evidence; P2 for planned capability or moderate-risk supplier refresh. C01 is monitored despite a passing sample because its current risk remains critical. Priority considers urgency and dependencies; risk score alone does not dictate order.

## Evidence gates

Collected age = fixed as-of date minus collected_on. Age equal to max_age_days is fresh; age greater is stale. Authored policies: 30 days for access/log/change, 90 days for recovery, 365 days for incident/supplier. These are lab choices, not NIST-prescribed periods.

- MISSING: registered file absent.
- STALE: age exceeds the control's authored maximum.
- OUT_OF_SCOPE: control scope differs or evidence period does not cover test period.
- INSUFFICIENT: fresh, scoped evidence has an empty sample or row count differs from declared sample.
- EXCEPTION: one or more sampled rows violate the bounded criterion.
- NOT_TESTED: control proposed or test has no performed date.

Multiple evidence gate codes can coexist. NOT_TESTED takes precedence for status, then evidence gates produce inconclusive; exceptions produce sample_fail; otherwise sample_pass. Stale evidence is not used to infer current effectiveness even when historical rows would pass.

Sample populations are explicitly fictional and small. Full population sampling within a fixture gives no statistical or enterprise-wide assurance. Change dates are day-level and require approval strictly before deployment; same-day approval is conservatively an exception because ordering cannot be proven.

## Closure and governance

Every seeded finding traces to an open action. Closure requires an accepted_by reviewer role, a linked performed retest for the same control that currently passes, and current same-scope review evidence. This is a minimum demonstration gate, not a full approval workflow. A successful software test never closes an action. Reassessment remains a documented management decision after closure.

The current fixtures have no completed retests, accepted risks or closed actions. Mutation tests deliberately attempt invalid closure and confirm rejection.

## Reproducibility

JSON is authoritative. CSV files and reports are derived and must not be hand-edited. Fixed dates and stable ordering ensure repeatable output. SHA-256 hashes of available artifacts are recorded in assessment.json; E04 records null because the requested file is absent. Hashes detect changes, not authenticity or chain of custody.

Software validation checks IDs, links, scoring, periods, unsafe paths, sample declarations and closure preconditions. It is a compact fixture validator, not a general-purpose GRC platform or hardened untrusted-data ingestion service.
