# Excel inspection route - documented, not executed

The source and planning CSV files are Excel-ready text exports. No workbook was created or tested in Excel. Python/Decimal results are the verified outputs; the formulas below are illustrative review aids.

## Bounded walkthrough

Import fixtures/comp-source.csv and fixtures/comp-planning.csv as separate tables named Source and Planning. Keep record_id, period, job_code and cost_center as text; format amount_usd as a two-decimal number. Preserve the originals.

Suggested helper columns in Planning:

| Question | Illustrative formula |
|---|---|
| Duplicate key in planning? | =COUNTIF(Planning[record_id],[@record_id]) |
| Key exists in source? | =COUNTIF(Source[record_id],[@record_id]) |
| Aggregate source amount for key? | =SUMIF(Source[record_id],[@record_id],Source[amount_usd]) |

Use the COUNTIF results before interpreting sums: duplicate or absent keys make a simple amount comparison inadequate. Compare periods and job/cost-center codes against unique source records. Source-side COUNTIF catches SYN-004 missing from planning. SUM of both amount columns is 375000.00 in the authored fixtures; that equality does not resolve row exceptions.

Compare the worksheet findings with reports/comp-reconciliation.csv, which records source and planning line numbers. Reviewers should verify import types and formulas in their own Excel version before relying on a workbook.

## Decision boundary

This is data-quality investigation, not a payroll calculation or pay recommendation. All amounts and identifiers are fabricated. No formula should be used to infer a protected trait, determine eligibility, rank employees or decide compensation. Any real process would require authorized data access, suitable handling controls and a qualified human reviewer.
