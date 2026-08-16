import json
import unittest
from pathlib import Path

from agentatlas.access import effective_access_paths
from agentatlas.delegation import evaluate_delegation
from agentatlas.drift import calculate_drift
from agentatlas.fixtures import generate_agents
from agentatlas.models import AgentIdentity
from agentatlas.posture import posture_summary, rank_agents
from agentatlas.service import build_report


class AgentAtlasTests(unittest.TestCase):
    def test_inventory_shape(self):
        agents = generate_agents()
        self.assertEqual(len(agents), 120)
        self.assertEqual(len({a.agent_id for a in agents}), 120)

    def test_shadow_and_orphaned_are_detected(self):
        summary = posture_summary(generate_agents())
        self.assertEqual(summary["shadow"], 9)
        self.assertEqual(summary["orphaned"], 6)
        self.assertEqual(summary["dormant"], 42)
        self.assertEqual(summary["high_or_critical"], 8)
        self.assertEqual(summary["critical"], 2)
        self.assertEqual(summary["mean_risk"], 0.2457)

    def test_ranking_is_descending_and_bounded(self):
        rows = rank_agents(generate_agents())
        self.assertTrue(all(0 <= r.risk <= 0.99 for r in rows))
        self.assertTrue(all(rows[i].risk >= rows[i + 1].risk for i in range(len(rows) - 1)))

    def test_delegation_cannot_expand_origin_authority(self):
        decision = evaluate_delegation(("human", "agent-a", "agent-b"), ("docs.read",), "payments.write")
        self.assertEqual(decision.decision, "DENY")

    def test_delegation_rejects_malformed_inputs(self):
        with self.assertRaises(ValueError):
            evaluate_delegation(("human",), ("docs.read",), "docs.read")
        with self.assertRaises(ValueError):
            evaluate_delegation(("human", "agent-a"), (), "docs.read")
        with self.assertRaises(ValueError):
            evaluate_delegation(("human", "agent-a"), ("docs.read",), "")

    def test_permission_drift_flags_privilege_growth(self):
        d = calculate_drift("agent-x", {"docs.read"}, {"docs.read", "iam.modify", "payments.write"})
        self.assertEqual(d.severity, "critical")
        self.assertGreater(d.risk_delta, 1.0)

    def test_effective_data_to_external_path(self):
        a = next(a for a in generate_agents() if a.agent_id == "agent-048")
        self.assertTrue(any(p.sink == "external-slack" and p.risk == "critical" for p in effective_access_paths(a)))

    def test_all_external_destinations_are_expanded(self):
        a = AgentIdentity(
            agent_id="agent-multi-egress",
            owner="security",
            sponsor="owner@example.test",
            environment="production",
            identity_type="workload_identity",
            autonomy_level=2,
            managed=True,
            last_active_days=1,
            permissions=("data.export",),
            tools=("objectstore.export",),
            mcp_servers=("mcp-data",),
            external_destinations=("external-slack", "external-webhook"),
        )
        sinks = {p.sink for p in effective_access_paths(a)}
        self.assertEqual(sinks, {"external-slack", "external-webhook"})

    def test_checked_in_baseline_matches_executable_report(self):
        checked_in = json.loads(Path("reports/baseline.json").read_text())
        current = json.loads(json.dumps(build_report()))
        self.assertEqual(checked_in["summary"], current["summary"])
        self.assertEqual(checked_in["top_agents"], current["top_agents"])
        self.assertEqual(checked_in["delegation"], current["delegation"])
        self.assertEqual(checked_in["permission_drift"], current["permission_drift"])


if __name__ == "__main__":
    unittest.main()
