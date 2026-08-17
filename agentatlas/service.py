from agentatlas.access import effective_access_paths
from agentatlas.delegation import evaluate_delegation
from agentatlas.drift import calculate_drift
from agentatlas.evaluation import evaluation_summary
from agentatlas.fixtures import delegation_cases, generate_agents, permission_snapshots
from agentatlas.ml import analyze_agents, ml_summary
from agentatlas.posture import posture_summary, rank_agents


def build_report() -> dict[str, object]:
    agents = generate_agents()
    ranked = rank_agents(agents)
    ml_ranked = analyze_agents(agents)
    agent_by_id = {a.agent_id: a for a in agents}
    delegation = [evaluate_delegation(*case) for case in delegation_cases()]
    drift = [calculate_drift(agent_id, prev, cur) for agent_id, (prev, cur) in permission_snapshots().items()]
    critical_paths = []
    for finding in ranked[:25]:
        for path in effective_access_paths(agent_by_id[finding.agent_id]):
            if path.risk == "critical":
                critical_paths.append(path)
    return {
        "summary": posture_summary(agents),
        "top_agents": [{"agent_id": f.agent_id, "risk": f.risk, "severity": f.severity, "reasons": list(f.reasons)} for f in ranked[:10]],
        "ml": ml_summary(agents),
        "top_ml_anomalies": [row.to_dict() for row in ml_ranked[:10]],
        "model_monitoring_and_robustness": evaluation_summary(agents),
        "delegation": [d.__dict__ for d in delegation],
        "permission_drift": [d.__dict__ for d in drift],
        "critical_effective_access_paths": [p.__dict__ for p in critical_paths[:10]],
        "scope": "Synthetic deterministic inventory; rule and ML values demonstrate governance logic and are not production compromise probabilities.",
    }
