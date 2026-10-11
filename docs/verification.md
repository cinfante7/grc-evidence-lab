# Verification — October 11, 2026

The final release checks were executed on Windows with Python 3.13. See [actual command output](verification-output.txt).

| Check | Observed result |
|---|---|
| Register validation | Exit 0; IDs, links, scoring and declarations valid |
| Report generation | Exit 0; six control results, five seeded findings |
| Automated tests | 20 tests, all pass |
| Committed report reconciliation | Exit 0; assessment JSON and HTML match fresh computation |
| HTML local links and anchors | 41 resolve; no duplicate anchors |
| Heuristic secret/personal-data content scan | No matches in project text files |
| Staged diff whitespace check | Completed before private upload |

The mutation suite detects broken/duplicate IDs, scoring and bounds errors, stale evidence boundaries, missing versus insufficient evidence, wrong control/period scope, proposed-control status, unsafe paths, future dates, missing provenance, and unsupported closure. Closure tests cover both failed retest and missing matching reviewer sign-off. A successful closure scenario is confined to a temporary copied fixture and does not close real register actions.

Assessment reconciles to: **1 sample_pass, 1 sample_fail, 3 inconclusive, 1 not_tested**. Five findings remain open. No score is reduced because a software test passes.

The content scan is a narrow heuristic for common credential formats, private-key headers, email addresses, government-ID-like patterns and local user paths. No real datasets were imported; manual source review confirmed synthetic fixtures and fictional roles. A clean heuristic scan is not a guarantee that arbitrary sensitive data could never be present.

Browser tools returned no supported browser for rendering inspection. HTML structure, internal references, local file targets, reconciliation and responsive CSS were checked; visual appearance has not been screenshot-verified. The generated report is designed for direct local opening and uses no external scripts or assets.

No deployment, AI API, credentials extraction, security probing, new access grants, paid services or modifications to existing projects were used. NIST source retrieval was read-only. The repository starts private; public visibility requires separate owner approval.
