import unittest

from agentatlas.fixtures import generate_agents
from agentatlas.ml import FEATURE_NAMES, MODEL_NAME, analyze_agents, feature_vector, ml_summary


class AgentAtlasMLTests(unittest.TestCase):
    def test_feature_vector_shape(self):
        agent = generate_agents()[0]
        self.assertEqual(len(feature_vector(agent)), len(FEATURE_NAMES))

    def test_ml_model_and_reference_population(self):
        summary = ml_summary(generate_agents())
        self.assertEqual(summary["model"], MODEL_NAME)
        self.assertGreaterEqual(summary["reference_population"], 20)

    def test_high_consequence_agent_is_prioritized(self):
        rows = {row.agent_id: row for row in analyze_agents(generate_agents())}
        self.assertGreaterEqual(rows["agent-120"].anomaly_percentile, 95.0)
        self.assertGreater(rows["agent-120"].hybrid_priority, rows["agent-001"].hybrid_priority)

    def test_low_risk_agent_is_not_ml_outlier(self):
        rows = {row.agent_id: row for row in analyze_agents(generate_agents())}
        self.assertFalse(rows["agent-001"].ml_outlier)
        self.assertLess(rows["agent-001"].hybrid_priority, 0.20)

    def test_results_are_deterministic(self):
        first = [row.to_dict() for row in analyze_agents(generate_agents())[:10]]
        second = [row.to_dict() for row in analyze_agents(generate_agents())[:10]]
        self.assertEqual(first, second)


if __name__ == "__main__":
    unittest.main()
