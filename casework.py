"""Two small AI-assisted October 2026 synthetic evidence/data-governance work samples."""
import argparse
import csv
import hashlib
import io
import json
import re
from collections import Counter, defaultdict
from datetime import date
from decimal import Decimal
from pathlib import Path
import lab

ROOT = Path(__file__).resolve().parent
DISCLAIMER = ("AI-assisted October 2026 independent synthetic portfolio work. No real tools, "
              "employee records or salaries were used. No hiring, eligibility or pay decisions are made. "
              "Fixture checks are not AI effectiveness tests, legal certification or operational approval.")
GENERATED = ("assessment.json", "ai-review.csv", "comp-reconciliation.csv", "readout.md", "index.html")

def read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))

def read_csv(path):
    with path.open(encoding="utf-8", newline="") as stream:
        reader = csv.DictReader(stream)
        return reader.fieldnames, list(reader)

def safe_fixture(root, relative):
    path = (root / relative).resolve()
    if not path.is_relative_to((root / "cases/fixtures").resolve()):
        raise ValueError("Fixture path outside cases/fixtures")
    return path

def require(ok, message):
    if not ok:
        raise ValueError(message)

def assess_ai(inventory, metadata, root=ROOT):
    as_of = date.fromisoformat(metadata["as_of"])
    for field in ("tool_id", "risk_id", "evidence_id"):
        require(len({r[field] for r in inventory}) == len(inventory), "Duplicate AI " + field)
    results = []
    for row in inventory:
        require(row["deployment_status"] == "proposed", "Only proposal-only synthetic tools are supported")
        require(row["gate"] in ("approval", "data_review", "citations"), "Unsupported AI evidence gate")
        require(row["owner"] and row["risk_basis"] and row["allowed_input"] and row["prohibited_input"],
                "AI scope, owner or rationale absent")
        likelihood, impact = int(row["likelihood"]), int(row["impact"])
        require(1 <= likelihood <= 5 and 1 <= impact <= 5, "AI risk components outside 1..5")
        require(int(row["max_age_days"]) > 0, "AI freshness must be positive")
        path = safe_fixture(root, row["evidence_path"])
        codes, exceptions = [], []
        age = None
        if not path.is_file():
            codes.append("MISSING")
        else:
            payload = read_json(path)
            require(payload.get("synthetic") is True, "AI artifact must declare synthetic provenance")
            start, end, collected = (date.fromisoformat(payload[k]) for k in
                                     ("period_start", "period_end", "collected_on"))
            require(start <= end <= collected <= as_of, "AI evidence chronology invalid")
            age = (as_of - end).days
            if payload.get("tool_id") != row["tool_id"] or payload.get("evidence_id") != row["evidence_id"]:
                codes.append("OUT_OF_SCOPE")
            if age > int(row["max_age_days"]):
                codes.append("STALE")
            if not codes:
                if row["gate"] == "approval":
                    reviewed = date.fromisoformat(payload["reviewed_on"])
                    require(end <= reviewed <= collected, "AI review chronology invalid")
                    if (payload.get("reviewed") is not True or payload.get("reviewer") != row["owner"]
                            or payload.get("approved_boundary") != row["allowed_input"]):
                        codes.append("EXCEPTION")
                elif row["gate"] == "data_review":
                    if (payload.get("reviewed") is not True
                            or payload.get("reviewer") != row["owner"]
                            or not isinstance(payload.get("handling_terms_declared"), str)
                            or not payload["handling_terms_declared"].strip()):
                        codes.append("INSUFFICIENT")
                    try:
                        reviewed = date.fromisoformat(payload.get("reviewed_on"))
                    except (TypeError, ValueError):
                        codes.append("INSUFFICIENT")
                    else:
                        if not end <= reviewed <= collected:
                            codes.append("INSUFFICIENT")
                else:
                    samples, allowed = payload.get("samples", []), payload.get("approved_policy_ids", [])
                    if (not samples or not allowed or len({s["sample_id"] for s in samples}) != len(samples)):
                        codes.append("INSUFFICIENT")
                    for sample in samples:
                        drafted = date.fromisoformat(sample["drafted_on"])
                        if not start <= drafted <= end:
                            codes.append("OUT_OF_SCOPE")
                        if (sample.get("expected_policy_id") not in allowed
                                or sample.get("cited_policy_id") != sample.get("expected_policy_id")):
                            exceptions.append(sample["sample_id"])
                    if exceptions:
                        codes.append("EXCEPTION")
        codes = sorted(set(codes))
        status = ("inconclusive" if any(c in codes for c in ("MISSING", "STALE", "OUT_OF_SCOPE", "INSUFFICIENT"))
                  else "fixture_exception" if codes else "fixture_complete")
        results.append({"tool_id":row["tool_id"],"risk_id":row["risk_id"],"evidence_id":row["evidence_id"],
                        "name":row["name"],"purpose":row["purpose"],"allowed_input":row["allowed_input"],
                        "prohibited_input":row["prohibited_input"],"owner":row["owner"],
                        "gate":row["gate"],"fixture_status":status,"codes":codes,"sample_exceptions":exceptions,
                        "evidence_age_days":age,"scenario_score":likelihood*impact,"scenario_band":lab.band(likelihood*impact),
                        "risk_scenario":row["risk_scenario"],"risk_basis":row["risk_basis"],
                        "deployment_status":"proposed","operational_effectiveness":"not assessed",
                        "human_decision":"required; no operational approval recorded",
                        "next_human_action":row["next_human_action"]})
    return results

def amount(value):
    require(isinstance(value, str) and re.fullmatch(r"\d+\.\d{2}", value), "Amount must use nonnegative two-decimal USD format")
    return Decimal(value)

def reconcile(manifest, source, planning):
    require(manifest["synthetic"] is True, "Compensation manifest must be synthetic")
    expected = ["record_id","period","job_code","cost_center","amount_usd","synthetic"]
    require(manifest["allowed_columns"] == expected, "Unexpected compensation schema")
    period = date.fromisoformat(manifest["period"])
    require(period <= date.fromisoformat(manifest["as_of"]), "Future compensation period")
    groups = []
    for label, rows in (("source",source),("planning",planning)):
        indexed = defaultdict(list)
        for line, row in enumerate(rows, start=2):
            require(set(row) == set(expected), "Unexpected compensation fields; no personal/protected fields supported")
            require(row["synthetic"] == "true" and re.fullmatch(r"SYN-\d{3}", row["record_id"]), "Non-synthetic compensation row")
            require(row["job_code"].startswith("DEMO-") and row["cost_center"].startswith("CC-DEMO-"), "Non-synthetic job/cost center")
            date.fromisoformat(row["period"])
            amount(row["amount_usd"])
            indexed[row["record_id"]].append((line, row))
        groups.append(indexed)
    src, plan = groups
    details = []
    for record_id in sorted(set(src) | set(plan)):
        srows, prows = src[record_id], plan[record_id]
        codes = []
        if len(srows) > 1:
            codes.append("SOURCE_DUPLICATE")
        if len(prows) > 1:
            codes.append("PLANNING_DUPLICATE")
        if not srows:
            codes.append("UNKNOWN_ID")
        if not prows:
            codes.append("MISSING_ID")
        if any(r["period"] != manifest["period"] for _,r in srows+prows):
            codes.append("PERIOD_MISMATCH")
        if len(srows) == len(prows) == 1:
            s, p = srows[0][1], prows[0][1]
            if amount(s["amount_usd"]) != amount(p["amount_usd"]):
                codes.append("AMOUNT_MISMATCH")
            if s["job_code"] != p["job_code"]:
                codes.append("JOB_CODE_MISMATCH")
            if s["cost_center"] != p["cost_center"]:
                codes.append("COST_CENTER_MISMATCH")
        details.append({"record_id":record_id,"source_lines":[n for n,_ in srows],"planning_lines":[n for n,_ in prows],
                        "source_count":len(srows),"planning_count":len(prows),
                        "source_amount_sum":str(sum((amount(r["amount_usd"]) for _,r in srows),Decimal("0.00"))),
                        "planning_amount_sum":str(sum((amount(r["amount_usd"]) for _,r in prows),Decimal("0.00"))),
                        "codes":sorted(codes),"human_action":"investigate; authorize any correction and rerun" if codes else "retain as reconciled data row",
                        "decision_scope":"data quality only; no pay recommendation"})
    source_total = sum((amount(r["amount_usd"]) for r in source),Decimal("0.00"))
    planning_total = sum((amount(r["amount_usd"]) for r in planning),Decimal("0.00"))
    return {"period":manifest["period"],"source_rows":len(source),"planning_rows":len(planning),
            "source_total":str(source_total),"planning_total":str(planning_total),"total_delta":str(planning_total-source_total),
            "totals_match":source_total==planning_total,
            "exception_records":sum(bool(r["codes"]) for r in details),
            "finding_counts":dict(sorted(Counter(c for r in details for c in r["codes"]).items())),
            "transfer_state":"hold for human review" if any(r["codes"] for r in details) else "data checks clear; human review still required",
            "reviewer":manifest["human_reviewer"],"amount_basis":manifest["amount_basis"],"details":details}

def assess(root=ROOT):
    metadata = read_json(root / "cases/fixtures/case-metadata.json")
    require(metadata["synthetic"] is True and metadata["authored_month"] == "October 2026", "Case provenance absent")
    manifest = read_json(root / "cases/fixtures/comp-manifest.json")
    require(manifest["as_of"] == metadata["as_of"], "Case dates differ")
    _, inventory = read_csv(root / "cases/fixtures/ai-inventory.csv")
    source_fields, source = read_csv(safe_fixture(root, manifest["source"]))
    planning_fields, planning = read_csv(safe_fixture(root, manifest["planning"]))
    require(source_fields == planning_fields == manifest["allowed_columns"], "Compensation columns do not match manifest")
    ai = assess_ai(inventory, metadata, root)
    comp = reconcile(manifest, source, planning)
    fixtures = sorted((root / "cases/fixtures").glob("*"))
    return {"as_of":metadata["as_of"],"disclaimer":DISCLAIMER,"provenance":metadata["provenance"],
            "ai":ai,"compensation":comp,
            "fixture_sha256":{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in fixtures if p.is_file()}}

def csv_text(rows):
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=list(rows[0]), lineterminator="\n")
    writer.writeheader()
    writer.writerows({k:"; ".join(map(str,v)) if isinstance(v,list) else v for k,v in row.items()} for row in rows)
    return stream.getvalue()

def outputs(a):
    comp = a["compensation"]
    ai_count = Counter(r["fixture_status"] for r in a["ai"])
    brief = "# Evidence and data governance - synthetic case readout\n\n" + DISCLAIMER + "\n\n"
    brief += f'Fixed assessment date: {a["as_of"]}. AI fixture counts: {dict(sorted(ai_count.items()))}.\n\n'
    brief += "All three tools remain proposed; every operational use requires a separate human decision. No model was executed. Citation checks compare manually authored source pairs, not model accuracy.\n\n"
    brief += f'Compensation reconciliation: {comp["source_rows"]} source rows, {comp["planning_rows"]} planning rows; {comp["exception_records"]} exception records. Source total {comp["source_total"]}; planning total {comp["planning_total"]}; delta {comp["total_delta"]} fictional USD.\n\n'
    brief += f'Transfer state: **{comp["transfer_state"]}**. Matching totals do not establish row-level accuracy. No suggested salary or employment decision is generated.\n\n'
    brief += "| Record | Findings | Human follow-up |\n|---|---|---|\n"
    for row in comp["details"]:
        if row["codes"]:
            brief += f'| {row["record_id"]} | {", ".join(row["codes"])} | {row["human_action"]} |\n'
    brief += "\nSee cases/README.md for the process and cases/excel-review-guide.md for a bounded Excel inspection route. Formulas are documented examples, not an executed workbook.\n"
    ai_rows = [[lab.esc(r["tool_id"]),lab.esc(r["name"]),lab.esc(r["purpose"]),
                lab.esc(f'{r["scenario_score"]} ({r["scenario_band"]})'),lab.esc(r["fixture_status"]),
                lab.esc(", ".join(r["codes"]) or "none"),lab.esc(r["next_human_action"])] for r in a["ai"]]
    comp_rows = [[lab.esc(r["record_id"]),lab.esc(r["source_count"]),lab.esc(r["planning_count"]),
                  lab.esc(r["source_amount_sum"]),lab.esc(r["planning_amount_sum"]),
                  lab.esc(", ".join(r["codes"]) or "none")] for r in comp["details"]]
    page = f'''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Evidence and data governance | Synthetic portfolio cases</title><style>
body{{margin:0;background:#f3f6f9;color:#152637;font:16px/1.6 system-ui,sans-serif}}header{{background:#10283e;color:white;padding:42px 5vw}}
main{{max-width:1200px;margin:auto;padding:28px}}h1{{font-size:clamp(2rem,5vw,3.3rem);line-height:1.15}}
.notice,.card{{padding:20px;background:white;border:1px solid #d8e2eb;border-radius:10px;margin:18px 0}}.notice{{background:#fff4d7}}
.scroll{{overflow:auto}}table{{border-collapse:collapse;width:100%;background:white;font-size:.9rem}}td,th{{padding:12px;text-align:left;vertical-align:top;border-bottom:1px solid #d8e2eb}}th{{background:#e7eef4}}a{{color:#006c70}}
</style><header><p>AI-assisted October 2026 independent synthetic work</p><h1>Evidence review meets data reconciliation.</h1>
<p>Two bounded cases for human reviewers. Fictional tools, authored output pairs and fabricated compensation-file rows.</p></header>
<main><div class="notice">{lab.esc(DISCLAIMER)}</div><p><a href="../../reports/index.html">Original GRC lab</a> | <a href="../README.md">Case methodology</a> | <a href="readout.md">Decision readout</a></p>
<h2>AI-tool inventory and scenario review</h2><p>Fixed date {a["as_of"]}. All tools remain proposed. Scoring uses the lab's illustrative 5x5 matrix; scores are assumptions, not measured likelihood or model performance.</p>
{lab.table(["Tool","Fictional name","Purpose","Scenario risk","Fixture check","Gap codes","Next human action"],ai_rows)}
<div class="card"><b>Human review boundary</b><p>Fixture counts: {lab.esc(dict(sorted(ai_count.items())))}. See the row-level gap codes and evidence requests above. No real tool or model was assessed. Restricted input rules and reviewer roles are recorded in the inventory.</p></div>
<h2>Compensation-file reconciliation</h2><p>{comp["source_rows"]} source rows / {comp["planning_rows"]} planning rows. Synthetic source total <b>{comp["source_total"]}</b>; planning total <b>{comp["planning_total"]}</b>; delta <b>{comp["total_delta"]}</b>.</p>
<div class="notice"><b>{lab.esc(comp["transfer_state"])}</b>: {comp["exception_records"]} exception records. Matching totals do not prove accurate keys, periods, amounts or job codes.</div>
{lab.table(["Synthetic slot","Source count","Planning count","Source sum","Planning sum","Findings"],comp_rows)}
<p>Review by {lab.esc(comp["reviewer"])}. Investigate source lines, authorize corrections separately, obtain a new export and rerun. This program does not edit amounts, recommend pay or evaluate people.</p>
<h2>Inspect and reproduce</h2><p><a href="../../cases/fixtures/ai-inventory.csv">AI inventory</a> | <a href="../../cases/fixtures/comp-source.csv">Synthetic source CSV</a> | <a href="../../cases/fixtures/comp-planning.csv">Synthetic planning CSV</a> | <a href="ai-review.csv">AI check rows</a> | <a href="comp-reconciliation.csv">Reconciliation detail</a> | <a href="../excel-review-guide.md">Excel review guide</a> | <a href="assessment.json">Assessment JSON</a></p>
<p>Run python casework.py check and python -m unittest discover -s tests -v. No network, model API, paid service, employee data or protected-trait inference is used. These cases demonstrate evidence and process reasoning, not professional experience or legal compliance.</p></main></html>'''
    return {"assessment.json":json.dumps(a,indent=2)+"\n","ai-review.csv":csv_text(a["ai"]),
            "comp-reconciliation.csv":csv_text(comp["details"]),"readout.md":brief,"index.html":page}

def build(root=ROOT):
    rendered = outputs(assess(root))
    folder = root / "cases/reports"
    folder.mkdir(parents=True,exist_ok=True)
    for name,text in rendered.items():
        (folder/name).write_text(text,encoding="utf-8")
    return rendered

def check(root=ROOT):
    rendered = outputs(assess(root))
    require(rendered == outputs(assess(root)), "Case outputs nondeterministic")
    errors = []
    for name,text in rendered.items():
        path = root / "cases/reports" / name
        if not path.is_file() or path.read_text(encoding="utf-8") != text:
            errors.append("Case output drift: "+name)
    return errors

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command",choices=("validate","build","check"))
    args=parser.parse_args()
    result=assess()
    if args.command=="build":
        build()
    elif args.command=="check":
        errors=check()
        if errors:
            print("\n".join(errors))
            return 2
    print("Synthetic case fixtures validated; AI operational review remains pending.")
    print(f'Compensation exception records: {result["compensation"]["exception_records"]}; {result["compensation"]["transfer_state"]}.')
    print(DISCLAIMER)
    return 0

if __name__=="__main__":
    raise SystemExit(main())
