"""Synthetic data checks; no real systems, models, employees or pay decisions."""
import copy
import json
import shutil
import tempfile
import unittest
from pathlib import Path
import casework

class CaseworkTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name)
        shutil.copytree(casework.ROOT/"cases/fixtures",self.root/"cases/fixtures")
        self.metadata=casework.read_json(self.root/"cases/fixtures/case-metadata.json")
        self.manifest=casework.read_json(self.root/"cases/fixtures/comp-manifest.json")
        _,self.inventory=casework.read_csv(self.root/"cases/fixtures/ai-inventory.csv")
        _,self.source=casework.read_csv(self.root/"cases/fixtures/comp-source.csv")
        _,self.planning=casework.read_csv(self.root/"cases/fixtures/comp-planning.csv")

    def write(self,name,payload):
        (self.root/"cases/fixtures"/name).write_text(json.dumps(payload),encoding="utf-8")

    def test_seeded_ai_gaps_and_review_boundary(self):
        ai=casework.assess_ai(self.inventory,self.metadata,self.root)
        self.assertEqual([r["fixture_status"] for r in ai],["fixture_complete","inconclusive","fixture_exception"])
        self.assertEqual(ai[1]["codes"],["MISSING"])
        self.assertEqual(ai[2]["sample_exceptions"],["DRAFT-002"])
        self.assertTrue(all(r["deployment_status"]=="proposed" and r["operational_effectiveness"]=="not assessed" for r in ai))

    def test_ai_wrong_scope(self):
        payload=casework.read_json(self.root/"cases/fixtures/ai-approval.json")
        payload["tool_id"]="AIT99";self.write("ai-approval.json",payload)
        self.assertEqual(casework.assess_ai(self.inventory,self.metadata,self.root)[0]["codes"],["OUT_OF_SCOPE"])

    def test_ai_wrong_reviewer_cannot_complete_fixture(self):
        payload=casework.read_json(self.root/"cases/fixtures/ai-approval.json")
        payload["reviewer"]="Unrelated Reviewer";self.write("ai-approval.json",payload)
        self.assertEqual(casework.assess_ai(self.inventory,self.metadata,self.root)[0]["fixture_status"],"fixture_exception")

    def test_ai_recent_collection_does_not_refresh_old_period(self):
        payload=casework.read_json(self.root/"cases/fixtures/ai-approval.json")
        payload.update(period_start="2026-08-01",period_end="2026-08-01",collected_on="2026-10-13",reviewed_on="2026-10-13")
        self.write("ai-approval.json",payload)
        self.assertIn("STALE",casework.assess_ai(self.inventory,self.metadata,self.root)[0]["codes"])

    def data_review_fixture(self):
        return {"synthetic":True, "tool_id":"AIT02", "evidence_id":"AIE02",
                "period_start":"2026-10-01", "period_end":"2026-10-01",
                "collected_on":"2026-10-04", "reviewed":True,
                "reviewer":"Data Steward (fictional)", "reviewed_on":"2026-10-03",
                "handling_terms_declared":"Authored schema-only handling declaration; not real vendor terms"}

    def data_review_result(self, payload):
        self.write("ai-data-review.json", payload)
        return casework.assess_ai(self.inventory,self.metadata,self.root)[1]

    def test_data_review_missing_reviewer_insufficient(self):
        payload=self.data_review_fixture();del payload["reviewer"]
        self.assertEqual(self.data_review_result(payload)["fixture_status"],"inconclusive")
        self.assertEqual(self.data_review_result(payload)["codes"],["INSUFFICIENT"])

    def test_data_review_wrong_reviewer_insufficient(self):
        payload=self.data_review_fixture();payload["reviewer"]="Unassigned Reviewer"
        self.assertEqual(self.data_review_result(payload)["codes"],["INSUFFICIENT"])

    def test_data_review_missing_review_date_insufficient(self):
        payload=self.data_review_fixture();del payload["reviewed_on"]
        self.assertEqual(self.data_review_result(payload)["codes"],["INSUFFICIENT"])

    def test_data_review_invalid_future_or_reversed_date_insufficient(self):
        for reviewed_on in ("not-a-date","2026-10-14","2026-09-30","2026-10-05"):
            with self.subTest(reviewed_on=reviewed_on):
                payload=self.data_review_fixture();payload["reviewed_on"]=reviewed_on
                self.assertEqual(self.data_review_result(payload)["codes"],["INSUFFICIENT"])

    def test_valid_documented_data_review_is_not_operational_approval(self):
        result=self.data_review_result(self.data_review_fixture())
        self.assertEqual(result["fixture_status"],"fixture_complete")
        self.assertEqual(result["codes"],[])
        self.assertEqual(result["deployment_status"],"proposed")
        self.assertEqual(result["operational_effectiveness"],"not assessed")
        self.assertEqual(result["human_decision"],"required; no operational approval recorded")

    def test_ai_future_collection_rejected(self):
        payload=casework.read_json(self.root/"cases/fixtures/ai-approval.json")
        payload["collected_on"]="2026-10-14";self.write("ai-approval.json",payload)
        with self.assertRaisesRegex(ValueError,"chronology"):
            casework.assess_ai(self.inventory,self.metadata,self.root)

    def test_ai_risk_bounds_and_duplicate_identity(self):
        bad=copy.deepcopy(self.inventory);bad[0]["impact"]="6"
        with self.assertRaisesRegex(ValueError,"outside"):
            casework.assess_ai(bad,self.metadata,self.root)
        bad=copy.deepcopy(self.inventory);bad[1]["risk_id"]=bad[0]["risk_id"]
        with self.assertRaisesRegex(ValueError,"Duplicate"):
            casework.assess_ai(bad,self.metadata,self.root)

    def test_ai_no_operational_status_supported(self):
        self.inventory[0]["deployment_status"]="approved"
        with self.assertRaisesRegex(ValueError,"proposal-only"):
            casework.assess_ai(self.inventory,self.metadata,self.root)

    def test_ai_empty_citation_sample_insufficient(self):
        payload=casework.read_json(self.root/"cases/fixtures/ai-citations.json")
        payload["samples"]=[];self.write("ai-citations.json",payload)
        self.assertIn("INSUFFICIENT",casework.assess_ai(self.inventory,self.metadata,self.root)[2]["codes"])

    def test_matching_totals_still_require_six_record_reviews(self):
        comp=casework.reconcile(self.manifest,self.source,self.planning)
        self.assertEqual((comp["source_total"],comp["planning_total"],comp["total_delta"]),("375000.00","375000.00","0.00"))
        self.assertTrue(comp["totals_match"])
        self.assertEqual(comp["exception_records"],6)
        self.assertEqual(comp["finding_counts"],{"AMOUNT_MISMATCH":1,"JOB_CODE_MISMATCH":1,"MISSING_ID":1,
                                                "PERIOD_MISMATCH":1,"PLANNING_DUPLICATE":1,"UNKNOWN_ID":1})
        self.assertEqual(comp["transfer_state"],"hold for human review")

    def test_clean_reconciliation_still_requires_human_review(self):
        comp=casework.reconcile(self.manifest,self.source,copy.deepcopy(self.source))
        self.assertEqual(comp["exception_records"],0)
        self.assertEqual(comp["transfer_state"],"data checks clear; human review still required")
        self.assertTrue(all(r["decision_scope"]=="data quality only; no pay recommendation" for r in comp["details"]))

    def test_source_duplicate_and_cost_center_mismatch_visible(self):
        source=copy.deepcopy(self.source);source.append(copy.deepcopy(source[0]))
        planning=copy.deepcopy(self.source);planning[1]["cost_center"]="CC-DEMO-X"
        comp=casework.reconcile(self.manifest,source,planning)
        self.assertIn("SOURCE_DUPLICATE",comp["finding_counts"])
        self.assertIn("COST_CENTER_MISMATCH",comp["finding_counts"])

    def test_invalid_amounts_rejected(self):
        for value in ("NaN","-1.00","1.001","1e3",""):
            planning=copy.deepcopy(self.planning);planning[0]["amount_usd"]=value
            with self.assertRaisesRegex(ValueError,"two-decimal"):
                casework.reconcile(self.manifest,self.source,planning)

    def test_personal_or_protected_columns_not_supported(self):
        planning=copy.deepcopy(self.planning);planning[0]["person_name"]="Not supported"
        with self.assertRaisesRegex(ValueError,"Unexpected"):
            casework.reconcile(self.manifest,self.source,planning)

    def test_non_synthetic_row_rejected(self):
        self.planning[0]["synthetic"]="false"
        with self.assertRaisesRegex(ValueError,"Non-synthetic"):
            casework.reconcile(self.manifest,self.source,self.planning)

    def test_unsafe_fixture_path_rejected(self):
        with self.assertRaisesRegex(ValueError,"outside"):
            casework.safe_fixture(self.root,"../unrelated.csv")

    def test_no_input_amounts_changed(self):
        original=copy.deepcopy((self.source,self.planning))
        casework.reconcile(self.manifest,self.source,self.planning)
        self.assertEqual((self.source,self.planning),original)

    def test_deterministic_outputs_and_nonmutating_drift_detection(self):
        first=casework.build(self.root)
        self.assertEqual(first,casework.build(self.root))
        self.assertEqual(casework.check(self.root),[])
        for name in casework.GENERATED:
            path=self.root/"cases/reports"/name
            original=path.read_bytes();path.write_bytes(original+b"\nTAMPER")
            altered=path.read_bytes()
            self.assertIn("Case output drift: "+name,casework.check(self.root))
            self.assertEqual(path.read_bytes(),altered)
            path.write_bytes(original)

if __name__=="__main__":
    unittest.main()
