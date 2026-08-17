import unittest

from agentatlas.evaluation import (
    adversarial_evaluation,
    drift_report,
    evaluation_summary,
    simulate_shifted_inventory,
)
from agentatlas.fixtures import generate_agents


class AgentAtlasEvaluationTests(unittest.TestCase):
    def test_steady_state_has_no_drift(self):
        agents = generate_agents()
        report = drift_report(agents, agents)
        self.assertFalse(report["drift_alert"])
        self.assertTrue(all(value == 0.0 for value in report["feature_psi"].values()))

    def test_shifted_inventory_triggers_drift(self):
        agents = generate_agents()
        shifted = simulate_shifted_inventory(agents)
        report = drift_report(agents, shifted)
        self.assertTrue(report["drift_alert"])
        self.assertGreaterEqual(len(report["alert_features"]), 1)

    def test_adversarial_cases_are_explainable_and_bounded(self):
        result = adversarial_evaluation(generate_agents())
        self.assertEqual(result["total"], 3)
        self.assertTrue(0.0 <= result["synthetic_surface_rate"] <= 1.0)
        self.assertTrue(all(0.0 <= row["rule_risk"] <= 0.99 for row in result["cases"]))
        self.assertTrue(all(0.0 <= row["hybrid_priority"] <= 0.99 for row in result["cases"]))
        external = next(row for row in result["cases"] if row["case"] == "external_export_path")
        self.assertTrue(external["surfaced_for_review"])

    def test_evaluation_summary_contains_versioned_metadata(self):
        summary = evaluation_summary(generate_agents())
        metadata = summary["model_metadata"]
        self.assertEqual(metadata["model_version"], "agentatlas-iforest-v1")
        self.assertEqual(metadata["feature_schema_version"], "agent-posture-v1")


if __name__ == "__main__":
    unittest.main()
