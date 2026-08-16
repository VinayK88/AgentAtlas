import unittest
from agentatlas.access import effective_access_paths
from agentatlas.delegation import evaluate_delegation
from agentatlas.drift import calculate_drift
from agentatlas.fixtures import generate_agents
from agentatlas.posture import posture_summary, rank_agents

class AgentAtlasTests(unittest.TestCase):
    def test_inventory_shape(self):
        agents = generate_agents(); self.assertEqual(len(agents), 120); self.assertEqual(len({a.agent_id for a in agents}), 120)
    def test_shadow_and_orphaned_are_detected(self):
        summary = posture_summary(generate_agents()); self.assertEqual(summary["shadow"], 9); self.assertEqual(summary["orphaned"], 6)
    def test_ranking_is_descending_and_bounded(self):
        rows = rank_agents(generate_agents()); self.assertTrue(all(0 <= r.risk <= 0.99 for r in rows)); self.assertTrue(all(rows[i].risk >= rows[i+1].risk for i in range(len(rows)-1)))
    def test_delegation_cannot_expand_origin_authority(self):
        self.assertEqual(evaluate_delegation(("human","agent-a","agent-b"), ("docs.read",), "payments.write").decision, "DENY")
    def test_permission_drift_flags_privilege_growth(self):
        d = calculate_drift("agent-x", {"docs.read"}, {"docs.read","iam.modify","payments.write"}); self.assertEqual(d.severity, "critical"); self.assertGreater(d.risk_delta, 1.0)
    def test_effective_data_to_external_path(self):
        a = next(a for a in generate_agents() if a.agent_id == "agent-048"); self.assertTrue(any(p.sink == "external-slack" and p.risk == "critical" for p in effective_access_paths(a)))

if __name__ == "__main__": unittest.main()
