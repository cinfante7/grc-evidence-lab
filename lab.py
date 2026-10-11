"""Deterministic synthetic GRC workpaper validator and report generator. Python 3.10+."""
import argparse
import csv
import hashlib
import html
import json
import copy
import tempfile
import shutil
import history
from collections import Counter
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DISCLAIMER = ("Fictional organization and synthetic records. Software checks and sample results "
              "do not establish control effectiveness, regulatory compliance or production security.")
TABLES = ("risks", "controls", "evidence", "tests", "remediation", "vendors")

def load(root=ROOT):
    return json.loads((root / "data/registers.json").read_text(encoding="utf-8"))

def band(score):
    if not 1 <= score <= 25:
        raise ValueError("Score outside 1..25")
    return "critical" if score >= 20 else "high" if score >= 12 else "moderate" if score >= 6 else "low"

def validate(d, root=ROOT):
    """Reject malformed relationships and unsupported closure; gaps are assessment findings."""
    errors = []
    indexes = {}
    as_of = date.fromisoformat(d["as_of"])
    assessed_at = history.timestamp(d["assessed_at"])
    def require(condition, message):
        if not condition:
            errors.append(message)
    require(assessed_at.date() == as_of, "Assessment date/timestamp mismatch")
    for table in TABLES:
        rows = d[table]
        indexes[table] = {r["id"]: r for r in rows}
        require(len(indexes[table]) == len(rows), f"Duplicate ID in {table}")
        for r in rows:
            require(bool(r.get("owner") or r.get("custodian")), f'{r["id"]}: owner missing')
    for r in d["risks"]:
        for field in ("likelihood", "impact", "target_likelihood", "target_impact"):
            require(type(r[field]) is int and 1 <= r[field] <= 5, f'{r["id"]}: {field} outside 1..5')
        require(r["current_assessed_score"] == r["likelihood"] * r["impact"], f'{r["id"]}: current score mismatch')
        require(r["target_score"] == r["target_likelihood"] * r["target_impact"], f'{r["id"]}: target score mismatch')
        require(bool(r["likelihood_rationale"]) and bool(r["impact_rationale"]), f'{r["id"]}: scoring rationale missing')
    links = {"controls": {"risk_id": "risks", "evidence_id": "evidence", "test_id": "tests"},
             "tests": {"control_id": "controls", "evidence_id": "evidence"},
             "remediation": {"control_id": "controls", "risk_id": "risks"},
             "vendors": {"control_id": "controls", "risk_id": "risks", "evidence_id": "evidence"},
             "evidence": {"control_id": "controls"}}
    for table, fields in links.items():
        for r in d[table]:
            for field, target in fields.items():
                require(r[field] in indexes[target], f'{r["id"]}: broken {field} {r[field]}')
    if errors:
        return errors
    for c in d["controls"]:
        t = indexes["tests"][c["test_id"]]
        require(t["control_id"] == c["id"] and t["evidence_id"] == c["evidence_id"], f'{c["id"]}: test/evidence link mismatch')
        require(indexes["evidence"][c["evidence_id"]]["control_id"] == c["id"], f'{c["id"]}: evidence control mismatch')
        require(c["implementation"] in ("implemented", "proposed"), f'{c["id"]}: unknown implementation status')
    for t in d["tests"]:
        start, end = date.fromisoformat(t["period_start"]), date.fromisoformat(t["period_end"])
        require(start <= end <= as_of, f'{t["id"]}: invalid test period')
        require(type(t["sample_count"]) is int and 0 <= t["sample_count"] <= t["population_count"], f'{t["id"]}: invalid sample size')
        require(bool(t["sample_rationale"]) and bool(t["criterion"]), f'{t["id"]}: sample basis/criterion missing')
        require(t["rule"] in ("access", "logs", "changes", "restore", "incident", "vendor"), f'{t["id"]}: unsupported test rule')
        if t["performed_on"]:
            performed = history.timestamp(t["performed_at"])
            ev = indexes["evidence"][t["evidence_id"]]
            require(end <= performed.date() <= as_of, f'{t["id"]}: test chronology outside population/assessment dates')
            require(date.fromisoformat(ev["collected_on"]) <= performed.date(), f'{t["id"]}: test precedes evidence collection')
            require(performed.date().isoformat() == t["performed_on"] and performed <= assessed_at,
                    f'{t["id"]}: performed date/timestamp mismatch or future test')
        else:
            require(t["performed_at"] is None, f'{t["id"]}: unperformed test has timestamp')
    for e in d["evidence"]:
        path = (root / e["path"]).resolve()
        require(path.is_relative_to((root / "evidence").resolve()), f'{e["id"]}: unsafe evidence path')
        require(e["synthetic"] is True, f'{e["id"]}: synthetic flag missing')
        require(type(e["max_age_days"]) is int and e["max_age_days"] > 0, f'{e["id"]}: invalid freshness policy')
        require(date.fromisoformat(e["collected_on"]) <= as_of, f'{e["id"]}: future collection')
        require(date.fromisoformat(e["period_start"]) <= date.fromisoformat(e["period_end"])
                <= date.fromisoformat(e["collected_on"]), f'{e["id"]}: invalid evidence period/collection chronology')
    for m in d["remediation"]:
        c = indexes["controls"][m["control_id"]]
        require(m["risk_id"] == c["risk_id"], f'{m["id"]}: remediation risk mismatch')
        require(m["status"] in ("open", "closed"), f'{m["id"]}: unknown remediation status')
        require(m["priority"] in ("P1", "P2", "P3"), f'{m["id"]}: invalid priority')
        if m.get("completed_at"):
            require(history.timestamp(m["completed_at"]) <= assessed_at, f'{m["id"]}: future remediation completion')
        if m["status"] == "closed":
            retest = indexes["tests"].get(m.get("retest_id"))
            review = indexes["evidence"].get(m.get("review_evidence_id"))
            event = next((e for e in d.get("test_events", []) if e["id"] == m.get("retest_event_id")), None)
            required = all(m.get(k) for k in ("completed_at", "reviewed_at", "closed_at", "accepted_by"))
            require(required and bool(retest) and bool(review) and bool(event),
                    f'{m["id"]}: closure requires completion, retest event, review and closure timestamps')
            if not (required and retest and review and event):
                continue
            require(retest["control_id"] == c["id"] and retest["id"] == c["test_id"]
                    and event["control_id"] == c["id"] and event["test_id"] == retest["id"]
                    and event["evidence_id"] == retest["evidence_id"] == c["evidence_id"]
                    and event["id"] == retest["event_id"] and event["kind"] == "retest"
                    and event["remediation_id"] == m["id"], f'{m["id"]}: invalid retest scope/identity')
            require(review["scope"] == review["control_id"] == c["id"],
                    f'{m["id"]}: review control scope mismatch')
            if not retest["performed_at"]:
                errors.append(f'{m["id"]}: retest not performed')
                continue
            complete, performed, reviewed, closed = map(history.timestamp,
                (m["completed_at"], retest["performed_at"], m["reviewed_at"], m["closed_at"]))
            require(complete < performed < reviewed <= closed <= assessed_at,
                    f'{m["id"]}: closure chronology must follow completion, retest, review')
            require(history.timestamp(event["assessed_at"]) <= reviewed,
                    f'{m["id"]}: review precedes retest assessment')
            assessment = assess(d, root)
            result = next(x for x in assessment["results"] if x["control_id"] == c["id"])
            require(result["status"] == "sample_pass" and result["test_id"] == retest["id"],
                    f'{m["id"]}: retest must pass')
            review_path = (root / review["path"]).resolve()
            safe = review_path.is_relative_to((root / "evidence").resolve())
            require(safe and review_path.is_file() and review["scope"] == c["id"]
                    and review["collected_on"] == reviewed.date().isoformat()
                    and (as_of - date.fromisoformat(review["collected_on"])).days <= review["max_age_days"],
                    f'{m["id"]}: review evidence missing, stale or wrong scope/date')
            if safe and review_path.is_file():
                signoff = json.loads(review_path.read_text(encoding="utf-8"))
                require(signoff.get("synthetic") is True and signoff.get("reviewed") is True
                        and signoff.get("reviewer") == m["accepted_by"]
                        and signoff.get("retest_id") == retest["id"]
                        and signoff.get("retest_event_id") == event["id"]
                        and signoff.get("remediation_id") == m["id"]
                        and signoff.get("control_id") == c["id"]
                        and signoff.get("reviewed_at") == m["reviewed_at"],
                        f'{m["id"]}: review artifact lacks matching retest sign-off')
    for v in d["vendors"]:
        require(v["risk_id"] == indexes["controls"][v["control_id"]]["risk_id"], f'{v["id"]}: vendor risk mismatch')
    if not errors:
        errors.extend(history.validate_events(d, root, assess(d, root)))
    return errors

def artifact_gates(payload, c, e, t, d):
    """Metadata is insufficient: examine period, identity and dated population rows."""
    if payload is None:
        return []
    codes = []
    start, end = payload.get("period_start"), payload.get("period_end")
    if payload.get("scope") != c["id"] or not start or not end:
        return ["OUT_OF_SCOPE"]
    try:
        date.fromisoformat(start)
        date.fromisoformat(end)
    except (TypeError, ValueError):
        return ["OUT_OF_SCOPE"]
    if (start > end or start > t["period_start"] or end < t["period_end"]
            or start != e["period_start"] or end != e["period_end"]):
        codes.append("OUT_OF_SCOPE")
    if t["rule"] == "vendor":
        vendor_ids = {v["id"] for v in d["vendors"] if v["control_id"] == c["id"]}
        if payload.get("vendor_id") not in vendor_ids:
            codes.append("OUT_OF_SCOPE")
    field = {"access":"occurred_on", "logs":"reviewed_on", "changes":"deployed_on",
             "restore":"exercised_on", "incident":"exercised_on", "vendor":"reviewed_on"}[t["rule"]]
    for row in payload.get("rows", []):
        when = row.get(field)
        try:
            date.fromisoformat(when)
        except (TypeError, ValueError):
            codes.append("INSUFFICIENT")
            continue
        if not t["period_start"] <= when <= t["period_end"] or not start <= when <= end:
            codes.append("OUT_OF_SCOPE")
        if t["rule"] == "changes" and row.get("approved_on"):
            try:
                date.fromisoformat(row["approved_on"])
            except (TypeError, ValueError):
                codes.append("INSUFFICIENT")
    return list(dict.fromkeys(codes))

def assess(d, root=ROOT):
    as_of = date.fromisoformat(d["as_of"])
    ev = {e["id"]: e for e in d["evidence"]}
    tests = {t["id"]: t for t in d["tests"]}
    results, findings = [], []
    for c in d["controls"]:
        e, t = ev[c["evidence_id"]], tests[c["test_id"]]
        age = (as_of - date.fromisoformat(min(e["collected_on"], e["period_end"]))).days
        path = root / e["path"]
        codes, exceptions = [], []
        payload = None
        if not path.is_file():
            codes.append("MISSING")
        else:
            payload = json.loads(path.read_text(encoding="utf-8"))
            if payload.get("synthetic") is not True:
                raise ValueError(f'{e["id"]}: artifact lacks synthetic provenance')
        codes.extend(artifact_gates(payload, c, e, t, d))
        actual_end = payload.get("period_end", e["period_end"]) if payload else e["period_end"]
        try:
            date.fromisoformat(actual_end)
        except (TypeError, ValueError):
            actual_end = e["period_end"]
        age = (as_of - date.fromisoformat(min(e["collected_on"], e["period_end"], t["period_end"], actual_end))).days
        if e["scope"] != c["id"] or e["period_start"] > t["period_start"] or e["period_end"] < t["period_end"]:
            codes.append("OUT_OF_SCOPE")
        if age > e["max_age_days"]:
            codes.append("STALE")
        if c["implementation"] == "proposed" or t["performed_on"] is None:
            codes.append("NOT_TESTED")
        rows = payload.get("rows", []) if payload else []
        if not codes:
            if not rows or len(rows) != t["sample_count"]:
                codes.append("INSUFFICIENT")
            else:
                for r in rows:
                    rule = t["rule"]
                    passed = False
                    if rule == "access":
                        passed = isinstance(r.get("removal_hours"), (int, float)) and 0 <= r["removal_hours"] <= 24
                    elif rule == "logs":
                        passed = bool(r.get("disposition"))
                    elif rule == "changes":
                        approved = r.get("approved_on")
                        passed = bool(approved) and date.fromisoformat(approved) < date.fromisoformat(r["deployed_on"])
                    elif rule == "restore":
                        passed = r.get("observed_hours", 999) <= r.get("objective_hours", 0) and r.get("reviewed") is True
                    elif rule == "incident":
                        passed = payload.get("performed") is True and bool(r.get("owner"))
                    elif rule == "vendor":
                        passed = r.get("signed_off") is True and bool(r.get("exceptions"))
                    if not passed:
                        exceptions.append(r["id"])
                if exceptions:
                    codes.append("EXCEPTION")
        codes = list(dict.fromkeys(codes))
        status = ("not_tested" if "NOT_TESTED" in codes else "inconclusive"
                  if any(x in codes for x in ("MISSING", "STALE", "OUT_OF_SCOPE", "INSUFFICIENT"))
                  else "sample_fail" if exceptions else "sample_pass")
        result = {"control_id": c["id"], "test_id": t["id"], "evidence_id": e["id"],
                  "risk_id": c["risk_id"], "status": status, "age_days": age,
                  "codes": codes, "exceptions": exceptions, "sample_count": t["sample_count"],
                  "criterion": t["criterion"], "scope": t["sample_scope"]}
        results.append(result)
        for code in codes:
            findings.append({"id": f'{c["id"]}-{code}', "control_id": c["id"], "evidence_id": e["id"],
                             "risk_id": c["risk_id"], "code": code, "exceptions": exceptions})
    fingerprints = {e["id"]: hashlib.sha256((root / e["path"]).read_bytes()).hexdigest()
                    if (root / e["path"]).is_file() else None for e in d["evidence"]}
    return {"as_of": d["as_of"], "disclaimer": DISCLAIMER,
            "counts": dict(sorted(Counter(r["status"] for r in results).items())),
            "finding_count": len(findings), "results": results, "findings": findings,
            "evidence_sha256": fingerprints,
            "risk_bands": dict(sorted(Counter(band(r["current_assessed_score"]) for r in d["risks"]).items()))}

def esc(x):
    return html.escape(str(x))

def link(id_):
    return f'<a href="#{esc(id_)}">{esc(id_)}</a>'

def table(headers, rows):
    return '<div class="scroll"><table><thead><tr>' + ''.join(f'<th>{esc(h)}</th>' for h in headers) + \
           '</tr></thead><tbody>' + ''.join('<tr>' + ''.join(f'<td>{x}</td>' for x in row) + '</tr>' for row in rows) + '</tbody></table></div>'

def render(d, a):
    risks = {r["id"]: r for r in d["risks"]}
    controls = {c["id"]: c for c in d["controls"]}
    open_actions = sorted((m for m in d["remediation"] if m["status"] == "open"),
                          key=lambda m:(m["priority"],m["due_on"],m["id"]))
    closed_count = sum(m["status"] == "closed" for m in d["remediation"])
    action_brief = "<ul>" + "".join(f'<li>{link(m["id"])}  |  {esc(m["priority"])}  |  {esc(m["action"])}  |  due {esc(m["due_on"])}</li>'
                                    for m in open_actions) + "</ul>" if open_actions else "<p>No open actions recorded.</p>"
    history_rows = [[esc(event["id"]), link(event["control_id"]), esc(event["test_id"]),
                     esc(event["kind"]), esc(event["performed_at"] or "not performed"),
                     esc(event["result_snapshot"]["status"]), esc(event["remediation_id"] or "none")]
                    for event in d["test_events"]]
    vendor_rows = [[f'<span id="{v["id"]}">{esc(v["id"])}</span>', esc(v["name"]), esc(v["criticality"]),
                   link(v["risk_id"])+" / "+link(v["control_id"])+" / "+link(v["evidence_id"]),
                   esc(v["decision"]), esc(v["decision_basis"])] for v in d["vendors"]]
    sections = []
    for r in a["results"]:
        c = controls[r["control_id"]]
        t = next(t for t in d["tests"] if t["id"] == r["test_id"])
        sections.append(f'<article id="{c["id"]}"><div class="eyebrow">{c["id"]} / {link(c["risk_id"])}</div>'
                        f'<h3>{esc(c["name"])}</h3><p><span class="pill {r["status"]}">{esc(r["status"].replace("_"," "))}</span> '
                        f'Implementation: {esc(c["implementation"])}</p><p>{esc(c["criterion"])}</p>'
                        f'<p id="{t["id"]}"><b>{t["id"]}</b>  |  {esc(t["method"])}  |  {esc(t["period_start"])} to {esc(t["period_end"])}</p>'
                        f'<p>{esc(t["sample_scope"])}. Sample {t["sample_count"]}/{t["population_count"]}. {esc(t["sample_rationale"])}</p>'
                        f'<p>Procedure: {esc(t["procedure"])}</p>'
                        f'<p>Evidence {link(c["evidence_id"])}  |  age {r["age_days"]} days  |  owner {esc(c["owner"])}</p>'
                        f'<p>Finding codes: {esc(", ".join(r["codes"]) or "none")}  |  exceptions: {esc(", ".join(r["exceptions"]) or "none")}</p>'
                        f'<p>NIST illustrative reference: {esc(c["nist_id"].upper())} - {esc(c["nist_title"])}</p></article>')
    risk_rows = [[f'<span id="{r["id"]}">{r["id"]}</span>', esc(r["name"]),
                  f'{r["likelihood"]} x {r["impact"]} = <b>{r["current_assessed_score"]}</b> ({band(r["current_assessed_score"])})',
                  f'{r["target_score"]} (proposed)', esc(r["owner"])] for r in d["risks"]]
    ev_rows = [[f'<span id="{e["id"]}">{e["id"]}</span>', esc(e["name"]),
                esc(e["collected_on"]), str(e["max_age_days"]),
                f'<a href="../{esc(e["path"])}">Synthetic artifact</a>' if a["evidence_sha256"][e["id"]] else 'Missing by design',
                '<code>'+esc((a["evidence_sha256"][e["id"]] or "absent")[:16])+'</code>'] for e in d["evidence"]]
    rem_rows = [[f'<span id="{m["id"]}">{m["id"]}</span>', link(m["control_id"])+' / '+link(m["risk_id"]),
                 esc(m["priority"]), esc(m["action"]), esc(m["owner"]), esc(m["due_on"]),
                 esc(m["closure_criteria"]), esc(m["status"]), esc(m.get("completed_at") or "none"),
                 esc(m.get("retest_event_id") or "none"), esc(m.get("reviewed_at") or "none")] for m in sorted(d["remediation"], key=lambda x:(x["priority"],x["due_on"],x["id"]))]
    counts = ''.join(f'<div class="metric"><strong>{n}</strong><span>{esc(k.replace("_"," "))}</span></div>' for k,n in a["counts"].items())
    return f'''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>GRC Evidence Lab | Decision brief</title><style>
:root{{color-scheme:light;--ink:#152637;--muted:#516579;--line:#d8e2eb;--teal:#006c70}}
*{{box-sizing:border-box}}body{{margin:0;background:#f3f6f9;color:var(--ink);font:16px/1.6 system-ui,sans-serif}}
header{{background:#10283e;color:white;padding:58px max(5vw,24px)}}header p{{max-width:760px;color:#d4e3ef}}
h1{{font-size:clamp(2.2rem,5vw,3.8rem);line-height:1.1;margin:14px 0}}h2{{margin-top:42px}}h3{{margin:8px 0}}
main{{max-width:1240px;margin:auto;padding:24px}}nav{{display:flex;gap:20px;flex-wrap:wrap}}nav a{{color:#9ee8df}}
a{{color:var(--teal)}}.eyebrow{{text-transform:uppercase;letter-spacing:.12em;font-size:.78rem;font-weight:700}}
.notice{{padding:16px 20px;background:#fff4d7;border-left:4px solid #b47c13;margin:22px 0}}
.metrics,.grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:16px}}
.metric,article,.memo{{background:white;border:1px solid var(--line);border-radius:12px;padding:22px}}
.metric strong{{font-size:2.5rem;display:block}}.metric span{{color:var(--muted)}}
.pill{{padding:4px 10px;border-radius:20px;font-size:.85rem;font-weight:700;background:#e6edf3}}
.sample_pass{{background:#d9f2e8;color:#135d45}}.sample_fail{{background:#fbe2de;color:#862c26}}
.inconclusive{{background:#fff0c8;color:#725409}}.not_tested{{background:#e7e3f5;color:#514279}}
.scroll{{overflow:auto;background:white;border:1px solid var(--line);border-radius:10px}}
table{{border-collapse:collapse;width:100%;font-size:.9rem}}td,th{{padding:14px;text-align:left;border-bottom:1px solid var(--line);vertical-align:top}}
th{{background:#e7eef4}}code{{font-size:.85rem}}footer{{padding:30px;color:var(--muted)}}article p{{font-size:.9rem}}
.flow{{display:flex;gap:10px;flex-wrap:wrap;padding:18px;background:#e3f2f0;border-radius:10px}}
@media print{{header{{padding:20px}}article{{break-inside:avoid}}nav{{display:none}}}}
</style><header><div class="eyebrow">Synthetic portfolio demonstration  |  {d["as_of"]}</div>
<h1>Evidence before assurance.</h1><p>Harborlight Workspaces (fictional). A bounded review of six controls converts records into traceable findings and owner-led remediation.</p>
<nav><a href="#brief">Decision brief</a><a href="#workpapers">Workpapers</a><a href="#risks">Risks</a><a href="#evidence">Evidence</a><a href="#actions">Actions</a></nav></header>
<main><div class="notice">{DISCLAIMER}</div><section id="brief"><h2>Executive decision brief</h2><div class="metrics">{counts}</div>
<p><b>{a["finding_count"]} seeded findings.</b> Maintain current risk scores until evidence supports a reassessment. Passing samples support only their stated fictional population and criteria; they do not establish enterprise-wide effectiveness.</p>
<div class="memo"><h3>Recorded remediation decisions</h3>
<p>{len(open_actions)} open actions; {closed_count} closed actions. The queue below derives from current register status, priority and due date.</p>
{action_brief}
<p>Target scores are proposed planning scenarios. Closed actions require separate documented management reassessment before changing risk.
Read the <a href="../docs/decision-memo.md">fixed October 11 baseline decision memo</a> for the original prioritization tradeoffs; it is not a live status report.</p></div></section>
<h2>Review process</h2><div class="flow"><span>Scope &amp; score -></span><span>Map control -></span><span>Request evidence -></span><span>Check age &amp; scope -></span><span>Test sample -></span><span>Record gap -></span><span>Remediate &amp; retest -></span><span>Review &amp; reassess</span></div>
<section id="workpapers"><h2>Control workpapers</h2><div class="grid">{''.join(sections)}</div></section>
<section id="risks"><h2>Risk register</h2><p>Likelihood x impact; current assessed score remains at inherent level. No implemented-control discount is assumed.</p>
{table(["ID","Scenario","Current / inherent","Target scenario","Fictional role"],risk_rows)}</section>
<section id="evidence"><h2>Evidence register</h2><p>Maximum age is an authored lab policy, measured from the earlier of collection and population period end. SHA-256 detects fixture changes; it does not prove authenticity.</p>
{table(["ID","Artifact","Collected","Max age (days)","Record","Hash prefix"],ev_rows)}</section>
<section id="actions"><h2>Remediation queue</h2><p>{len(open_actions)} actions open; {closed_count} closed. Closure requires completion, a distinct subsequent retest, matching reviewer sign-off and chronological timestamps.</p>
{table(["ID","Trace","Priority","Action","Fictional role","Due","Closure evidence","Status","Completed","Retest event","Reviewed"],rem_rows)}</section>
<h2>Test event history</h2><p>Append-style editable JSON with a preserved initial prefix and consistency checks. This is not cryptographically immutable storage.</p>
{table(["Event","Control","Test","Kind","Performed UTC","Recorded result","Remediation"],history_rows)}
<h2>Vendor records</h2><p>Recorded scenario decisions; no real contract action or risk acceptance is performed.</p>
{table(["ID","Fictional vendor","Criticality","Trace","Proposed decision","Basis"],vendor_rows)}
<h2>Sources and limits</h2><p>Illustrative partial mappings to <a href="https://csrc.nist.gov/pubs/sp/800/53/r5/upd1/final">NIST SP 800-53 Rev. 5 / release 5.2.0</a>;
assessment approach informed by <a href="https://csrc.nist.gov/pubs/sp/800/53/a/r5/final">SP 800-53A Rev. 5 / release 5.2.0</a>.
Verified October 11, 2026. See <a href="../docs/methodology.md">methodology</a> and <a href="../docs/sources.md">mapping rationales and remaining gaps</a>.</p>
<p>No real systems were inspected, no interviews performed, and no technical controls exercised. Synthetic artifact examination is limited to the criteria shown.
This is neither a complete NIST baseline nor a compliance assessment. Figures are deterministic at the fixed as-of date.</p></main>
<footer>GRC Evidence Lab  |  Standard-library Python  |  <a href="assessment.json">Machine-readable assessment</a>  |  <a href="../README.md">Recruiter guide</a></footer></html>'''

def build(d, root=ROOT):
    errors = validate(d, root)
    if errors:
        raise ValueError("\n".join(errors))
    a = assess(d, root)
    out = root / "reports"
    out.mkdir(exist_ok=True)
    (out / "assessment.json").write_text(json.dumps(a, indent=2) + "\n", encoding="utf-8")
    (out / "index.html").write_text(render(d, a), encoding="utf-8")
    for name in TABLES:
        rows = d[name]
        fields = list(dict.fromkeys(k for row in rows for k in row))
        with (root / "data" / f"{name}.csv").open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fields)
            writer.writeheader()
            writer.writerows(rows)
    with (out / "test-results.csv").open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(a["results"][0]))
        writer.writeheader()
        writer.writerows(a["results"])
    summary = "# Executive summary - synthetic case\n\n" + DISCLAIMER + "\n\n"
    summary += f'As of {a["as_of"]}: {a["counts"]}; {a["finding_count"]} findings.\n\n'
    open_actions = sorted((m for m in d["remediation"] if m["status"] == "open"),
                          key=lambda m:(m["priority"],m["due_on"],m["id"]))
    closed_count = sum(m["status"] == "closed" for m in d["remediation"])
    summary += f"{len(open_actions)} actions open; {closed_count} closed. Current risk scores are held at inherent level; targets are proposed scenarios. Read docs/decision-memo.md as a fixed October 11 baseline memo.\n\n"
    for m in open_actions:
        summary += f'- {m["id"]} / {m["control_id"]}: {m["priority"]}, {m["action"]}; due {m["due_on"]}.\n'
    summary += "\n"
    summary += "| Finding | Trace | Gap |\n|---|---|---|\n"
    for f in a["findings"]:
        summary += f'| {f["id"]} | {f["risk_id"]} -> {f["control_id"]} -> {f["evidence_id"]} | {f["code"]} {", ".join(f["exceptions"])} |\n'
    (out / "executive-summary.md").write_text(summary, encoding="utf-8")
    return a

GENERATED = tuple(["data/" + name + ".csv" for name in TABLES] +
                  ["reports/assessment.json", "reports/index.html", "reports/test-results.csv",
                   "reports/executive-summary.md"])

def check_generated(d, root=ROOT):
    """Compare all outputs before overwriting anything, with a repeatability check."""
    with tempfile.TemporaryDirectory() as temporary:
        target = Path(temporary)
        shutil.copytree(root / "data", target / "data")
        shutil.copytree(root / "evidence", target / "evidence")
        build(d, target)
        first = {name:(target / name).read_bytes() for name in GENERATED}
        build(d, target)
        errors = []
        for name in GENERATED:
            if first[name] != (target / name).read_bytes():
                errors.append("Nondeterministic artifact: " + name)
            existing = root / name
            # Git text checkout may normalize LF/CRLF; content comparison is newline-normalized.
            expected = first[name].decode("utf-8").replace("\r\n", "\n")
            if not existing.is_file() or existing.read_text(encoding="utf-8") != expected:
                errors.append("Report drift: " + name)
        return errors

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("validate", "build", "check"))
    args = parser.parse_args()
    d = load()
    errors = validate(d)
    if errors:
        for error in errors:
            print("INVALID:", error)
        return 2
    a = assess(d)
    if args.command == "build":
        build(d)
    elif args.command == "check":
        drift = check_generated(d)
        if drift:
            for error in drift:
                print(error)
            return 2
    print("Valid register relationships. Assessment:", json.dumps(a["counts"], sort_keys=True))
    print(f'{a["finding_count"]} evidence/control findings remain intentionally open.')
    print(DISCLAIMER)
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
