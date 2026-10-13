# Evidence and data governance - two synthetic work samples

**AI-assisted October 2026 independent portfolio work.** Harborlight Workspaces, all tool names, records, amounts, output pairs, reviewers and decisions are fictional. This is not TJX data or work performed for TJX.

These two cases reuse the existing GRC lab's evidence-first method and 5x5 scenario scoring. They add a bounded AI-tool inventory and a compensation-file data-quality workpaper, rather than a new platform. The original six-control baseline and its event history are preserved.

## Review in three minutes

1. Open [the case report](reports/index.html) locally, or read [the decision readout](reports/readout.md).
2. Inspect [the AI inventory](fixtures/ai-inventory.csv): permitted inputs, prohibited inputs, risk scenarios, reviewer roles and evidence requests.
3. Inspect [reconciliation detail](reports/comp-reconciliation.csv): matching totals conceal six record exceptions.
4. Read [the Excel review route](excel-review-guide.md) and [the Notion/referral companion](notion-referral-case.md).

## AI governance case

Three fictional tools remain **proposed**. AIT01 has an authored, scoped reviewer sign-off fixture. AIT02 lacks requested data-handling evidence. AIT03 includes two manually authored draft/source pairs, one citing an unsupported policy ID.

The deterministic checks inspect evidence identity, dated scope, freshness, reviewer/boundary match and the declared citation criterion. A data-handling review fixture additionally requires the assigned reviewer, a nonempty handling declaration and period-end <= reviewed_on <= collected_on <= assessment date; incomplete or incoherent evidence is inconclusive. They do not run an AI tool, evaluate factual accuracy, robustness, bias, privacy/security implementation or suitability for employment decisions. A complete fixture is not tool approval or effective AI governance.

Current scenario risk = likelihood x impact on the existing 1-5 lab scale. Scores 9, 12 and 12 are authored scenario judgments, not measured probabilities or legal risk rankings. No residual score reduction is assumed. Each row records a scenario and rationale. Freshness is measured from the artifact period end; later receipt cannot refresh an old period.

A human must determine applicable requirements, evaluate real handling terms and validate real outputs before any operational use. These cases assert no legal compliance.

## Compensation data reconciliation

Source CSV has six fictional position-slot IDs, planning CSV seven rows. Both total **375000.00 fictional USD**. Equal totals mask:

- a duplicate planning key;
- a missing source key in planning;
- an unknown planning key;
- a mismatched amount;
- a mismatched job code;
- a wrong reporting period.

Amounts are invented schema fixtures, not real employee salaries, market benchmarks or compensation recommendations. No names, protected traits or demographic variables are included or inferred. The validator rejects extra fields and non-synthetic rows. It identifies file exceptions only; it never edits source amounts, ranks people or recommends hiring/pay actions.

Checks use Decimal, explicit schema, synthetic key formats, record counts, unique-key exceptions, dated period alignment, field comparison and batch totals. Results trace to original CSV line numbers. The transfer state remains **hold for human review**, even though totals match.

## Human review and proposed process improvements

A fictional Compensation Data Reviewer investigates export keys and field mapping, records the correction authority and obtains a new export. Proposed improvements are a duplicate-key export gate, explicit period validation and a two-part reconciliation checklist (batch totals plus row exceptions). None is represented as a deployed system.

Disposition sequence: preserve the original files -> investigate exceptions -> authorize source corrections separately -> obtain a new export -> rerun checks -> independent reviewer sign-off. A clean temporary regression fixture still requires human review; the software never grants transfer approval.

## Reproduce

From the repository directory, Python 3.10+ and no dependencies:

```text
python casework.py validate
python casework.py build
python casework.py check
python -m unittest discover -s tests -v
python verify.py
```

The new case date is fixed at 2026-10-13. The original GRC case remains fixed at 2026-10-11. Outputs are reproducible local artifacts; no API, deployment or model call is required. Five case outputs are checked without overwriting working files. Test success confirms seeded data checks, not AI effectiveness or legal compliance.

## What this can support in a referral

This work demonstrates evidence review, structured risk communication, data reconciliation, exception traceability and human approval boundaries. It is an independent project. It does not establish professional compensation experience, real AI audit experience, advanced Excel proficiency or success with a particular employer's systems. The CSV outputs support Excel inspection; no Excel workbook or macros were executed.
