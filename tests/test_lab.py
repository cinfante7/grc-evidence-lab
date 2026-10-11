"""Tests verify the lab's reasoning and reconciliation, never real control effectiveness."""
import copy
import json
import shutil
import tempfile
import unittest
from pathlib import Path
import lab

class EvidenceLabTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        shutil.copytree(lab.ROOT / "evidence", self.root / "evidence")
        (self.root / "data").mkdir()
        self.d = copy.deepcopy(lab.load())

    def result(self, control):
        return next(r for r in lab.assess(self.d, self.root)["results"] if r["control_id"] == control)

    def write(self, name, data):
        (self.root / "evidence" / name).write_text(json.dumps(data), encoding="utf-8")

    def test_fixture_links_valid(self):
        self.assertEqual(lab.validate(self.d, self.root), [])

    def test_seeded_findings_are_visible(self):
        a = lab.assess(self.d, self.root)
        self.assertEqual(a["counts"], {"inconclusive": 3, "not_tested": 1, "sample_fail": 1, "sample_pass": 1})
        self.assertEqual({f["id"] for f in a["findings"]},
                         {"C02-STALE", "C03-EXCEPTION", "C04-MISSING", "C05-NOT_TESTED", "C06-STALE"})
        self.assertEqual(self.result("C03")["exceptions"], ["CHG-003"])

    def test_duplicate_ids_rejected(self):
        self.d["risks"].append(copy.deepcopy(self.d["risks"][0]))
        self.assertIn("Duplicate ID in risks", lab.validate(self.d, self.root))

    def test_broken_reference_rejected(self):
        self.d["controls"][0]["risk_id"] = "R99"
        self.assertTrue(any("broken risk_id" in e for e in lab.validate(self.d, self.root)))

    def test_cross_link_mismatch_rejected(self):
        self.d["tests"][0]["evidence_id"] = "E02"
        self.assertTrue(any("link mismatch" in e for e in lab.validate(self.d, self.root)))

    def test_score_and_bounds_rejected(self):
        self.d["risks"][0]["current_assessed_score"] = 7
        self.d["risks"][1]["likelihood"] = 6
        errors = lab.validate(self.d, self.root)
        self.assertTrue(any("score mismatch" in e for e in errors))
        self.assertTrue(any("outside 1..5" in e for e in errors))

    def test_scoring_bands_and_reachable_products(self):
        self.assertEqual([lab.band(x) for x in (1, 5, 6, 10, 12, 16, 20, 25)],
                         ["low", "low", "moderate", "moderate", "high", "high", "critical", "critical"])
        for r in self.d["risks"]:
            self.assertIn(r["current_assessed_score"], {l*i for l in range(1,6) for i in range(1,6)})

    def test_freshness_boundary_inclusive(self):
        self.d["evidence"][0]["collected_on"] = "2026-09-11"
        self.assertEqual(self.result("C01")["status"], "sample_pass")
        self.d["evidence"][0]["collected_on"] = "2026-09-10"
        self.assertEqual(self.result("C01")["codes"], ["STALE"])

    def test_missing_distinct_from_insufficient(self):
        (self.root / "evidence/access.json").unlink()
        self.assertEqual(self.result("C01")["codes"], ["MISSING"])
        self.write("access.json", {"synthetic": True, "rows": []})
        self.assertEqual(self.result("C01")["codes"], ["INSUFFICIENT"])

    def test_wrong_scope_and_period_distinct(self):
        self.d["evidence"][0]["scope"] = "C06"
        self.assertEqual(self.result("C01")["codes"], ["OUT_OF_SCOPE"])
        self.d["evidence"][0]["scope"] = "C01"
        self.d["evidence"][0]["period_start"] = "2026-09-15"
        self.assertEqual(self.result("C01")["codes"], ["OUT_OF_SCOPE"])

    def test_proposed_control_never_passes(self):
        self.write("incident.json", {"synthetic": True, "performed": True, "rows": [{"id":"SIM-1","owner":"Security Lead"}]})
        self.assertEqual(self.result("C05")["status"], "not_tested")

    def test_empty_sample_cannot_pass(self):
        self.d["tests"][0]["sample_count"] = 0
        self.write("access.json", {"synthetic": True, "rows":[]})
        self.assertEqual(self.result("C01")["status"], "inconclusive")

    def test_future_collection_rejected(self):
        self.d["evidence"][0]["collected_on"] = "2026-10-12"
        self.assertTrue(any("future collection" in e for e in lab.validate(self.d, self.root)))

    def test_unsafe_path_rejected(self):
        self.d["evidence"][0]["path"] = "../outside.json"
        self.assertTrue(any("unsafe evidence path" in e for e in lab.validate(self.d, self.root)))

    def test_closure_without_retest_rejected(self):
        self.d["remediation"][0]["status"] = "closed"
        self.assertTrue(any("closure requires" in e for e in lab.validate(self.d, self.root)))

    def test_closure_with_failed_retest_rejected(self):
        m = self.d["remediation"][1]
        m.update(status="closed", accepted_by="Fictional Reviewer", retest_id="T03", review_evidence_id="E03")
        self.assertTrue(any("retest must pass" in e for e in lab.validate(self.d, self.root)))

    def test_closure_without_matching_signoff_rejected(self):
        m = self.d["remediation"][1]
        m.update(status="closed", accepted_by="Fictional Reviewer", retest_id="T03", review_evidence_id="E03")
        payload = json.loads((self.root / "evidence/changes.json").read_text())
        payload["rows"][2]["approved_on"] = "2026-09-17"
        self.write("changes.json", payload)
        self.assertTrue(any("sign-off" in e for e in lab.validate(self.d, self.root)))

    def test_closure_requires_passing_retest_and_matching_review(self):
        m = self.d["remediation"][1]
        m.update(status="closed", accepted_by="Fictional Reviewer", retest_id="T03", review_evidence_id="E07")
        payload = json.loads((self.root / "evidence/changes.json").read_text())
        payload["rows"][2]["approved_on"] = "2026-09-17"
        self.write("changes.json", payload)
        review = copy.deepcopy(self.d["evidence"][2])
        review.update(id="E07", path="evidence/review.json", name="Synthetic reviewer sign-off")
        self.d["evidence"].append(review)
        self.write("review.json", {"synthetic": True, "reviewed": True,
                                  "reviewer":"Fictional Reviewer", "retest_id":"T03"})
        self.assertEqual(lab.validate(self.d, self.root), [])

    def test_artifact_provenance_required(self):
        self.write("access.json", {"synthetic": False, "rows":[]})
        with self.assertRaisesRegex(ValueError, "synthetic provenance"):
            lab.assess(self.d, self.root)

    def test_report_reconciliation_and_determinism(self):
        a = lab.build(self.d, self.root)
        first = (self.root / "reports/index.html").read_bytes()
        lab.build(self.d, self.root)
        self.assertEqual(first, (self.root / "reports/index.html").read_bytes())
        self.assertEqual(a, json.loads((self.root / "reports/assessment.json").read_text(encoding="utf-8")))
        self.assertEqual(sum(a["counts"].values()), len(self.d["controls"]))
        self.assertEqual(a["finding_count"], len(a["findings"]))
        text = first.decode("utf-8")
        for result in a["results"]:
            self.assertIn(f'id="{result["control_id"]}"', text)
        self.assertIn(lab.DISCLAIMER, text)
        self.assertEqual(len((self.root / "reports/test-results.csv").read_text().splitlines()), 7)

if __name__ == "__main__":
    unittest.main()
