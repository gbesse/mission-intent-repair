from copy import deepcopy
import itertools
import json
from pathlib import Path
import unittest

from mission_repair.solver import check_plan, contingency, legal_starts, repair

ROOT = Path(__file__).resolve().parent.parent


class MissionTests(unittest.TestCase):
    def setUp(self):
        self.case = json.loads((ROOT / "mission_repair/examples/lunar-relay.json").read_text())

    def test_original_uses_primary_and_replays(self):
        result = repair(self.case)
        self.assertEqual(result["status"], "OPTIMAL")
        self.assertEqual(result["utility"], 10)
        self.assertEqual(result["changes"], [])
        self.assertTrue(check_plan(self.case, result["plan"])["valid"])

    def test_outage_repairs_future_preserves_past(self):
        case = contingency(self.case, ["relay-primary"])
        result = repair(case)
        self.assertEqual(result["utility"], 8)
        self.assertNotIn("relay-primary", result["plan"])
        self.assertIn("relay-backup", result["plan"])
        self.assertEqual(result["plan"]["observe-south"], 2)
        self.assertEqual(result["plan"]["calibrate"], 0)
        self.assertTrue(result["repair_proven"])
        self.assertEqual({c["task"] for c in result["changes"]}, {"relay-primary", "relay-backup"})

    def test_conflicting_required_goal_has_named_core(self):
        case = contingency(self.case, ["relay-primary"])
        case["tasks"][3]["required"] = True
        result = repair(case)
        self.assertEqual(result["status"], "INFEASIBLE")
        self.assertIn("relay-primary", result["required_conflict"])
        self.assertFalse(result["conflict_is_minimal"])

    def test_frozen_past_cannot_be_rewritten_by_outage(self):
        case = contingency(self.case, ["observe-south"])
        self.assertEqual(repair(case)["status"], "INFEASIBLE")

    def test_checker_catches_bad_contact_and_frozen_edit(self):
        plan = {"calibrate": 1, "observe-south": 2, "relay-primary": 5}
        errors = {x["code"] for x in check_plan(self.case, plan)["errors"]}
        self.assertTrue({"frozen_changed", "dependency", "outside_window"} <= errors)

    def test_checker_catches_power_depletion(self):
        case = deepcopy(self.case)
        case["solar"] = [0] * 16
        result = check_plan(case, case["previous"])
        self.assertIn("battery_depleted", {e["code"] for e in result["errors"]})

    def test_capacity_drop_can_be_infeasible_without_fake_success(self):
        case = deepcopy(self.case)
        case["battery_capacity"] = 12
        case["tasks"][3]["required"] = True
        case["solar"] = [0] * 16
        self.assertEqual(repair(case)["status"], "INFEASIBLE")

    def test_solver_matches_exhaustive_oracle_on_small_cases(self):
        for capacity in (2, 3, 4, 5):
            case = {"horizon": 4, "battery_capacity": capacity, "battery_initial": capacity,
                    "storage_capacity": 2, "storage_initial": 0, "solar": [0]*4, "baseline": [0]*4,
                    "tasks": [{"id": "a", "duration": 1, "energy": 2, "value": 3, "data_delta": 1, "channels": ["x"]},
                              {"id": "b", "duration": 1, "energy": 2, "value": 4, "data_delta": 1, "channels": ["x"]},
                              {"id": "c", "duration": 1, "energy": 1, "value": 2, "data_delta": -1, "after": ["a"], "channels": ["x"]}]}
            valid = []
            for values in itertools.product([None, 0, 1, 2, 3], repeat=3):
                plan = {t["id"]: s for t, s in zip(case["tasks"], values) if s is not None}
                replay = check_plan(case, plan)
                if replay["valid"]:
                    valid.append(replay["utility"])
            result = repair(case)
            self.assertEqual(result["utility"], max(valid))
            self.assertTrue(result["utility_proven"])

    def test_digest_changes_with_assumptions(self):
        self.assertNotEqual(repair(self.case)["input_sha256"], repair(contingency(self.case, ["relay-primary"]))["input_sha256"])

    def test_invalid_inputs_fail_before_solver(self):
        for field, value in [("horizon", 1000), ("battery_initial", -1), ("solar", []), ("freeze_before", 30)]:
            case = deepcopy(self.case)
            case[field] = value
            with self.assertRaises(ValueError):
                repair(case)


if __name__ == "__main__":
    unittest.main()
