"""Regression cases for chronology, append-style history, content scope and output drift."""
import copy
import json
import unittest
import lab
import history
import test_lab

class RegressionTests(unittest.TestCase):
    setUp = test_lab.EvidenceLabTests.setUp
    result = test_lab.EvidenceLabTests.result
    write = test_lab.EvidenceLabTests.write

    def closed_scenario(self):
        self.d["as_of"] = "2026-10-18"
        self.d["assessed_at"] = "2026-10-18T15:00:00Z"
        c = self.d["controls"][2]
        original_t = self.d["tests"][2]
        t = copy.deepcopy(original_t)
        t.update(id="T07", evidence_id="E07", event_id="EV07",
                 period_start="2026-10-13", period_end="2026-10-14",
                 performed_on="2026-10-16", performed_at="2026-10-16T10:00:00Z",
                 population_count=2, sample_count=2,
                 sample_scope="Two new fictional deployments after remediation completion")
        self.d["tests"].append(t)
        e = copy.deepcopy(self.d["evidence"][2])
        e.update(id="E07", path="evidence/changes-followup.json",
                 collected_on="2026-10-15", period_start="2026-10-13", period_end="2026-10-14")
        self.d["evidence"].append(e)
        c.update(test_id="T07", evidence_id="E07")
        self.write("changes-followup.json", {"synthetic":True, "scope":"C03",
                   "period_start":"2026-10-13", "period_end":"2026-10-14", "rows":[
                   {"id":"CHG-004","approved_on":"2026-10-12","deployed_on":"2026-10-13"},
                   {"id":"CHG-005","approved_on":"2026-10-13","deployed_on":"2026-10-14"}]})
        m = self.d["remediation"][1]
        m.update(status="closed", completed_at="2026-10-12T09:00:00Z",
                 retest_id="T07", retest_event_id="EV07", review_evidence_id="E08",
                 accepted_by="Fictional Reviewer", reviewed_at="2026-10-17T13:00:00Z",
                 closed_at="2026-10-17T14:00:00Z")
        review = copy.deepcopy(e)
        review.update(id="E08", path="evidence/review-followup.json",
                      collected_on="2026-10-17", period_start="2026-10-17", period_end="2026-10-17")
        self.d["evidence"].append(review)
        self.write("review-followup.json", {"synthetic":True, "reviewed":True,
                   "reviewer":"Fictional Reviewer","control_id":"C03","remediation_id":"M02",
                   "retest_id":"T07","retest_event_id":"EV07","reviewed_at":m["reviewed_at"]})
        result = self.result("C03")
        assessed_at = self.d["assessed_at"]
        self.d["assessed_at"] = "2026-10-16T12:00:00Z"
        event = history.capture(self.d, self.root, result, "EV07", kind="retest", remediation_id="M02")
        self.d["test_events"].append(event)
        self.d["assessed_at"] = assessed_at
        return m

    def test_september_one_mutation_rejected(self):
        self.d["tests"][0].update(performed_on="2026-09-01", performed_at="2026-09-01T12:00:00Z")
        self.assertTrue(any("chronology" in e for e in lab.validate(self.d, self.root)))

    def test_test_before_evidence_collection_rejected(self):
        self.d["tests"][0].update(performed_on="2026-09-30", performed_at="2026-09-30T12:00:00Z")
        self.assertTrue(any("precedes evidence collection" in e for e in lab.validate(self.d, self.root)))

    def test_positive_new_retest_preserves_baseline_failure(self):
        baseline = copy.deepcopy(self.d["test_events"])
        m = self.closed_scenario()
        self.assertEqual(lab.validate(self.d, self.root), [])
        self.assertEqual(self.d["test_events"][:6], baseline)
        self.assertEqual(self.d["test_events"][2]["result_snapshot"]["exceptions"], ["CHG-003"])
        self.assertEqual(self.result("C03")["status"], "sample_pass")
        self.assertEqual(m["status"], "closed")
        original = json.loads((self.root / "evidence/changes.json").read_text())
        self.assertIsNone(original["rows"][2]["approved_on"])

    def test_failed_new_retest_cannot_close_action(self):
        self.closed_scenario()
        path = self.root / "evidence/changes-followup.json"
        payload = json.loads(path.read_text())
        payload["rows"][1]["approved_on"] = None
        self.write("changes-followup.json", payload)
        self.assertTrue(any("retest must pass" in e for e in lab.validate(self.d, self.root)))

    def test_review_timestamp_must_match_artifact(self):
        self.closed_scenario()
        path = self.root / "evidence/review-followup.json"
        payload = json.loads(path.read_text())
        payload["reviewed_at"] = "2026-10-17T12:00:00Z"
        self.write("review-followup.json", payload)
        self.assertTrue(any("sign-off" in e for e in lab.validate(self.d, self.root)))

    def test_missing_completion_rejected(self):
        self.closed_scenario()["completed_at"] = None
        self.assertTrue(any("closure requires" in e for e in lab.validate(self.d, self.root)))

    def test_retest_before_completion_rejected(self):
        self.closed_scenario()["completed_at"] = "2026-10-16T11:00:00Z"
        self.assertTrue(any("chronology" in e for e in lab.validate(self.d, self.root)))

    def test_population_before_completion_rejected(self):
        self.closed_scenario()["completed_at"] = "2026-10-14T09:00:00Z"
        self.assertTrue(any("population" in e for e in lab.validate(self.d, self.root)))

    def test_review_before_retest_rejected(self):
        self.closed_scenario()["reviewed_at"] = "2026-10-15T13:00:00Z"
        self.assertTrue(any("chronology" in e for e in lab.validate(self.d, self.root)))

    def test_closure_before_review_rejected(self):
        self.closed_scenario()["closed_at"] = "2026-10-17T12:00:00Z"
        self.assertTrue(any("chronology" in e for e in lab.validate(self.d, self.root)))

    def test_baseline_test_cannot_be_reused_for_closure(self):
        m = self.closed_scenario()
        m.update(retest_id="T03", retest_event_id="EV03")
        self.assertTrue(any("scope/identity" in e for e in lab.validate(self.d, self.root)))

    def test_wrong_review_control_rejected(self):
        self.closed_scenario()
        self.d["evidence"][-1]["control_id"] = "C02"
        self.assertTrue(any("review control scope" in e for e in lab.validate(self.d, self.root)))

    def test_wrong_reviewer_event_or_action_rejected(self):
        self.closed_scenario()
        path = self.root / "evidence/review-followup.json"
        for field,value in (("reviewer","Other Reviewer"),("retest_event_id","EV03"),("remediation_id","M01")):
            original = json.loads(path.read_text())
            changed = copy.deepcopy(original); changed[field] = value
            self.write("review-followup.json", changed)
            self.assertTrue(any("sign-off" in e for e in lab.validate(self.d, self.root)))
            self.write("review-followup.json", original)

    def test_retroactive_artifact_correction_rejected(self):
        self.closed_scenario()
        original = json.loads((self.root / "evidence/changes.json").read_text())
        original["rows"][2]["approved_on"] = "2026-09-17"
        self.write("changes.json", original)
        self.assertTrue(any("historical artifact changed" in e for e in lab.validate(self.d, self.root)))

    def test_history_deletion_mutation_and_sequence_rejected(self):
        self.d["test_events"].pop(2)
        self.assertTrue(any("history" in e for e in lab.validate(self.d, self.root)))

    def test_history_snapshot_mutation_rejected(self):
        self.d["test_events"][2]["result_snapshot"]["status"] = "sample_pass"
        self.assertTrue(any("Initial history prefix" in e for e in lab.validate(self.d, self.root)))

    def test_recent_receipt_does_not_refresh_june_logs(self):
        self.d["evidence"][1]["collected_on"] = "2026-10-11"
        self.assertEqual(self.result("C02")["status"], "inconclusive")
        self.assertIn("STALE", self.result("C02")["codes"])

    def test_register_envelope_cannot_refresh_historical_population(self):
        self.d["evidence"][1].update(collected_on="2026-10-11", period_end="2026-10-10")
        self.assertEqual(self.result("C02")["status"], "inconclusive")
        self.assertIn("STALE", self.result("C02")["codes"])
        self.assertIn("OUT_OF_SCOPE", self.result("C02")["codes"])

    def test_payload_period_cannot_be_relabelled_by_register(self):
        self.d["tests"][1].update(period_start="2026-10-01",period_end="2026-10-10")
        self.d["evidence"][1].update(period_start="2026-10-01",period_end="2026-10-10",collected_on="2026-10-11")
        self.assertIn("OUT_OF_SCOPE", self.result("C02")["codes"])

    def test_wrong_vendor_payload_rejected(self):
        original = json.loads((self.root / "evidence/vendor.json").read_text())
        original["vendor_id"] = "V99"
        self.write("vendor.json", original)
        self.assertIn("OUT_OF_SCOPE", self.result("C06")["codes"])

    def test_change_row_outside_population_rejected(self):
        original = json.loads((self.root / "evidence/changes.json").read_text())
        original["rows"][0]["deployed_on"] = "2026-08-31"
        self.write("changes.json", original)
        self.assertIn("OUT_OF_SCOPE", self.result("C03")["codes"])

    def test_undated_population_insufficient(self):
        original = json.loads((self.root / "evidence/access.json").read_text())
        del original["rows"][0]["occurred_on"]
        self.write("access.json", original)
        self.assertIn("INSUFFICIENT", self.result("C01")["codes"])

    def test_all_generated_artifacts_checked_without_overwrite(self):
        lab.build(self.d, self.root)
        self.assertEqual(lab.check_generated(self.d, self.root), [])
        for name in lab.GENERATED:
            path = self.root / name
            original = path.read_bytes()
            path.write_bytes(original + b"\nTAMPER\n")
            altered = path.read_bytes()
            self.assertIn("Report drift: "+name, lab.check_generated(self.d, self.root))
            self.assertEqual(path.read_bytes(), altered)
            path.write_bytes(original)

    def test_dynamic_narrative_after_valid_closure(self):
        self.closed_scenario()
        lab.build(self.d, self.root)
        html = (self.root / "reports/index.html").read_text(encoding="utf-8")
        summary = (self.root / "reports/executive-summary.md").read_text(encoding="utf-8")
        self.assertIn("4 open actions; 1 closed actions", html)
        self.assertIn("4 actions open; 1 closed", summary)
        self.assertNotIn("All actions are open", html)
        self.assertNotIn("- M02 /", summary)
        self.assertIn("EV03", html)
        self.assertIn("EV07", html)

if __name__ == "__main__":
    unittest.main()
