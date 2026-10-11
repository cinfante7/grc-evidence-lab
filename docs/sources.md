# Primary-source register and illustrative mapping

Verified **October 11, 2026**. This bounded mapping is authored for the lab. It is partial, not equivalence, certification, baseline selection or a compliance assessment.

## Source provenance

| Source | Version / publication | Reference |
|---|---|---|
| NIST SP 800-53 | Rev. 5, September 2020, updates December 10, 2020; publication page notes release 5.2.0 August 27, 2025 | https://csrc.nist.gov/pubs/sp/800/53/r5/upd1/final |
| NIST SP 800-53A | Rev. 5, January 2022; publication page notes release 5.2.0 August 27, 2025 | https://csrc.nist.gov/pubs/sp/800/53/a/r5/final |
| NIST OSCAL catalog | Metadata version 5.2.0; last-modified 2026-05-11T16:01:09.00000-00:00 | https://github.com/usnistgov/oscal-content/blob/78650f02ad9321bb7b817846f8fbd4f2bcd620de/nist.gov/SP800-53/rev5/json/NIST_SP-800-53_rev5_catalog.json |

Control identifiers and titles were checked against the official usnistgov OSCAL catalog. The pinned commit above is the most recent file commit returned at retrieval. No full catalog is copied into this repository. Publication references support source provenance and the assessment approach; local test criteria below are authored simplifications rather than verbatim NIST assessment procedures.

## Control-by-control rationale

| Lab control | Verified NIST identifier and title | Mapping rationale | Remaining gap |
|---|---|---|---|
| C01 Access removal | AC-2 Account Management | Separation-driven removal is one account-lifecycle activity | No coverage of account creation, authorization, monitoring, all account types or organization-defined parameters |
| C02 Log review | AU-6 Audit Record Review, Analysis, and Reporting | Review disposition demonstrates a limited review/reporting activity | No actual log completeness, automated analysis, frequency tailoring or enterprise escalation assessment |
| C03 Change approval | CM-3 Configuration Change Control | Prior approval is a bounded configuration-change governance criterion | No security impact analysis, full change board process, retention or technical enforcement inspection |
| C04 Restore exercise | CP-4 Contingency Plan Testing | An observed recovery exercise is a narrow contingency-testing workpaper | No complete contingency-plan scope, coordination, evaluation or follow-up assessment |
| C05 Incident exercise | IR-3 Incident Response Testing | A planned exercise relates to incident capability testing | Plan is proposed; no exercise, capability evaluation or real procedure assessment |
| C06 Vendor review | SR-6 Supplier Assessments and Reviews | Review of a critical supplier is a bounded supplier assurance activity | No actual supplier contract, threat analysis, complete supply-chain scope or monitoring evidence |

NIST SP 800-53A supports tailoring assessment procedures and using examination, interview and testing methods. This demonstration uses **examination of synthetic records only**. Labels such as restore exercise describe the fictional requested artifact, not an operational test conducted by this project.

Freshness windows, sample sizes, scoring bands, priority rules and exact closure criteria are authored lab policy. They are not asserted as NIST requirements. NIST's publication page explicitly cautions that mappings and crosswalks do not establish equivalence.

## Verification record

The primary NIST publication pages were read through web tools. The official OSCAL JSON was retrieved read-only through PowerShell; selected control IDs/titles and metadata were printed. The official GitHub file-history API supplied commit 78650f02ad9321bb7b817846f8fbd4f2bcd620de. Source verification required public reads only; reproducible local builds do not fetch sources.
