# GRC Evidence Lab â€” portfolio case study

**Type:** independent synthetic portfolio demonstration
**Repository:** https://github.com/cinfante7/grc-evidence-lab (private until visibility approval)
**Scope:** fictional Harborlight Workspaces, six controls and one critical supplier.

## Problem

An implementation assertion and a policy document are insufficient to support an assurance conclusion. The project demonstrates how an analyst links risks, controls, evidence requests, scoped test workpapers, exceptions and owned remediation.

## What I built

A reproducible standard-library Python workflow with linked JSON/CSV registers, a static executive report, content-level evidence gates, dated sample testing, append-style history consistency, a vendor decision memo and mutation tests. All organizations, records, roles and outcomes are fictional. This is an independent project; it makes no employment or client-work claim.

## What the demonstration finds

One limited access sample passes; one change sample fails; three controls are inconclusive because evidence is stale or missing; one incident control is proposed and untested. Five baseline actions remain open. Regression tests demonstrate a separate later retest and reviewer sign-off without rewriting the original exception. Current risk stays separate from hypothetical target risk.

## Review path

Start with reports/index.html, then trace R03 â†’ C03 â†’ E03 â†’ T03 â†’ M02. Read docs/methodology.md for scoring and closure gates, and docs/sources.md for illustrative NIST references.

## Limitations

No real-system inspection, operational testing, compliance opinion or complete NIST baseline assessment. Passing software tests verifies the lab, not controls. Repository access is needed while private; no deployment exists.

## Method note

This case uses an illustrative 5×5 matrix; it remains separate from any 3×3 portfolio exercise. Test history is editable JSON with consistency checks, not cryptographic immutability. The fixed decision memo is distinguished from current generated status. Verification compares all generated files without silently rebuilding them.
