"""Editable append-style synthetic event history; consistency checks, not tamper-proof storage."""
import copy
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

def timestamp(value):
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError("Timezone required")
    return parsed.astimezone(timezone.utc)

def fingerprint(payload):
    if payload is None:
        return None
    return hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()).hexdigest()

def capture(d, root, result, event_id, kind="initial", remediation_id=None):
    c = next(c for c in d["controls"] if c["id"] == result["control_id"])
    t = next(t for t in d["tests"] if t["id"] == c["test_id"])
    e = next(e for e in d["evidence"] if e["id"] == c["evidence_id"])
    path = root / e["path"]
    payload = json.loads(path.read_text(encoding="utf-8")) if path.is_file() else None
    previous = d.get("test_events", [])
    return {"id":event_id, "sequence":len(previous)+1,
            "previous_event_id":previous[-1]["id"] if previous else None,
            "kind":kind, "remediation_id":remediation_id,
            "control_id":c["id"], "test_id":t["id"], "evidence_id":e["id"],
            "assessed_at":d["assessed_at"], "performed_at":t["performed_at"],
            "test_snapshot":copy.deepcopy(t), "evidence_snapshot":copy.deepcopy(e),
            "result_snapshot":copy.deepcopy(result), "artifact_snapshot":payload,
            "artifact_fingerprint":fingerprint(payload)}

def validate_events(d, root, assessment):
    errors = []
    def require(ok, message):
        if not ok:
            errors.append(message)
    baseline_path = root / "data/history-baseline.json"
    if not baseline_path.is_file():
        return ["History baseline missing"]
    baseline = json.loads(baseline_path.read_text(encoding="utf-8"))
    events = d.get("test_events", [])
    require(events[:len(baseline)] == baseline, "Initial history prefix altered or removed")
    ids = {e["id"]: e for e in events}
    require(len(ids) == len(events), "Duplicate history event ID")
    controls = {c["id"]:c for c in d["controls"]}
    tests = {t["id"]:t for t in d["tests"]}
    evidence = {e["id"]:e for e in d["evidence"]}
    remediation = {m["id"]:m for m in d["remediation"]}
    assessed = timestamp(d["assessed_at"])
    previous_time = None
    for i, event in enumerate(events):
        label = event["id"]
        require(event["sequence"] == i+1, f"{label}: noncontiguous history sequence")
        require(event["previous_event_id"] == (events[i-1]["id"] if i else None), f"{label}: history predecessor mismatch")
        when = timestamp(event["assessed_at"])
        require(when <= assessed and (previous_time is None or previous_time <= when), f"{label}: history assessment chronology")
        previous_time = when
        t, e = event["test_snapshot"], event["evidence_snapshot"]
        require(event["control_id"] in controls and event["test_id"] in tests
                and event["evidence_id"] in evidence, f"{label}: broken history identity")
        require(t["control_id"] == e["control_id"] == event["control_id"]
                and t["id"] == event["test_id"] and e["id"] == t["evidence_id"] == event["evidence_id"],
                f"{label}: historical scope/identity mismatch")
        require(fingerprint(event["artifact_snapshot"]) == event["artifact_fingerprint"], f"{label}: snapshot fingerprint mismatch")
        if event["test_id"] in tests and event["evidence_id"] in evidence:
            require(t == tests[event["test_id"]] and e == evidence[event["evidence_id"]],
                    f"{label}: historical workpaper changed; append distinct IDs")
        original_path = (root / e["path"]).resolve()
        if original_path.is_relative_to((root / "evidence").resolve()):
            original = json.loads(original_path.read_text(encoding="utf-8")) if original_path.is_file() else None
            require(fingerprint(original) == event["artifact_fingerprint"],
                    f"{label}: historical artifact changed; append distinct evidence")
        require(event["performed_at"] == t["performed_at"], f"{label}: performed timestamp mismatch")
        if event["performed_at"]:
            performed = timestamp(event["performed_at"])
            require(max(t["period_end"], e["collected_on"]) <= performed.date().isoformat()
                    and performed <= when, f"{label}: historical test chronology")
        require(event["kind"] in ("initial", "retest"), f"{label}: invalid history kind")
        if event["kind"] == "retest":
            m = remediation.get(event["remediation_id"])
            require(bool(m) and m["control_id"] == event["control_id"], f"{label}: retest remediation scope mismatch")
            if m:
                complete = m.get("completed_at")
                require(bool(complete) and bool(event["performed_at"]), f"{label}: retest requires completion and performance")
                if complete and event["performed_at"]:
                    require(timestamp(complete) < timestamp(event["performed_at"])
                            and timestamp(complete).date().isoformat() < t["period_start"],
                            f"{label}: retest population and performance must follow completion")
            initial_test_ids = {x["test_id"] for x in baseline}
            initial_evidence_ids = {x["evidence_id"] for x in baseline}
            require(event["test_id"] not in initial_test_ids and event["evidence_id"] not in initial_evidence_ids,
                    f"{label}: retest requires distinct new test and evidence IDs")
    for c in d["controls"]:
        t, e = tests[c["test_id"]], evidence[c["evidence_id"]]
        event = ids.get(t.get("event_id"))
        require(bool(event), f'{t["id"]}: active history event missing')
        if not event:
            continue
        require(event["control_id"] == c["id"] and event["test_snapshot"] == t
                and event["evidence_snapshot"] == e, f'{t["id"]}: active event differs from current workpaper')
        result = next(r for r in assessment["results"] if r["control_id"] == c["id"])
        stable_fields = ("control_id", "test_id", "evidence_id", "risk_id", "status", "codes",
                         "exceptions", "sample_count", "criterion", "scope")
        require(all(event["result_snapshot"].get(k) == result.get(k) for k in stable_fields),
                f'{t["id"]}: active historical result mismatch')
        path = root / e["path"]
        payload = json.loads(path.read_text(encoding="utf-8")) if path.is_file() else None
        require(event["artifact_fingerprint"] == fingerprint(payload), f'{t["id"]}: active artifact changed without new event')
    return errors
