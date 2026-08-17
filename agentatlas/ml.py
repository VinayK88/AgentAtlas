from __future__ import annotations

import math
from dataclasses import asdict, dataclass

import numpy as np
from sklearn.ensemble import IsolationForest

from agentatlas.access import effective_access_paths
from agentatlas.models import AgentIdentity
from agentatlas.posture import PERMISSION_WEIGHTS, score_agent

MODEL_NAME = "IsolationForest"
RANDOM_STATE = 41
FEATURE_NAMES = (
    "max_permission_weight",
    "permission_count",
    "tool_count",
    "mcp_server_count",
    "external_destination_count",
    "unmanaged",
    "orphaned",
    "log_inactive_days",
    "autonomy_level",
    "production",
    "privileged_scope_count",
    "critical_access_paths",
)


@dataclass(frozen=True)
class AgentMLFinding:
    agent_id: str
    rule_risk: float
    anomaly_percentile: float
    ml_outlier: bool
    peer_distance: float
    hybrid_priority: float
    top_deviations: tuple[str, ...]

    def to_dict(self) -> dict:
        return asdict(self)


def feature_vector(agent: AgentIdentity) -> np.ndarray:
    max_permission = max((PERMISSION_WEIGHTS.get(p, 0.05) for p in agent.permissions), default=0.0)
    privileged = sum(p in {"secrets.read", "iam.modify", "payments.write", "k8s.admin"} for p in agent.permissions)
    critical_paths = sum(path.risk == "critical" for path in effective_access_paths(agent))
    return np.asarray(
        [
            max_permission,
            len(agent.permissions),
            len(agent.tools),
            len(agent.mcp_servers),
            len(agent.external_destinations),
            0 if agent.managed else 1,
            1 if agent.owner is None or agent.sponsor is None else 0,
            math.log1p(agent.last_active_days),
            agent.autonomy_level,
            1 if agent.environment == "production" else 0,
            privileged,
            critical_paths,
        ],
        dtype=float,
    )


def _reference_indices(agents: list[AgentIdentity]) -> list[int]:
    low_risk = [
        i
        for i, agent in enumerate(agents)
        if agent.managed
        and agent.owner is not None
        and agent.sponsor is not None
        and score_agent(agent).risk < 0.30
    ]
    if len(low_risk) >= 20:
        return low_risk
    return [i for i, agent in enumerate(agents) if agent.managed]


def _peer_zscore(index: int, agents: list[AgentIdentity], matrix: np.ndarray, reference: list[int]) -> np.ndarray:
    agent = agents[index]
    peer = [
        i
        for i in reference
        if agents[i].environment == agent.environment and agents[i].identity_type == agent.identity_type
    ]
    if len(peer) < 8:
        peer = reference
    peer_matrix = matrix[peer]
    mean = peer_matrix.mean(axis=0)
    std = peer_matrix.std(axis=0)
    std = np.where(std < 1e-6, 1.0, std)
    return (matrix[index] - mean) / std


def analyze_agents(agents: list[AgentIdentity]) -> list[AgentMLFinding]:
    if not agents:
        return []

    matrix = np.vstack([feature_vector(agent) for agent in agents])
    reference = _reference_indices(agents)
    reference_matrix = matrix[reference]

    model = IsolationForest(
        n_estimators=160,
        contamination=0.08,
        random_state=RANDOM_STATE,
    )
    model.fit(reference_matrix)

    raw_scores = -model.score_samples(matrix)
    reference_scores = -model.score_samples(reference_matrix)
    predictions = model.predict(matrix)

    findings: list[AgentMLFinding] = []
    for index, agent in enumerate(agents):
        percentile = round(float(100.0 * np.mean(reference_scores <= raw_scores[index])), 1)
        zscore = _peer_zscore(index, agents, matrix, reference)
        peer_distance = round(float(np.sqrt(np.mean(zscore * zscore))), 2)
        top = np.argsort(np.abs(zscore))[::-1][:3]
        deviations = tuple(FEATURE_NAMES[int(i)] for i in top if abs(zscore[int(i)]) >= 0.75)

        rule_risk = score_agent(agent).risk
        ml_adjustment = max(0.0, percentile - 80.0) / 20.0 * 0.12
        peer_adjustment = min(0.06, peer_distance * 0.015)
        hybrid = round(min(0.99, rule_risk + ml_adjustment + peer_adjustment), 4)

        findings.append(
            AgentMLFinding(
                agent_id=agent.agent_id,
                rule_risk=rule_risk,
                anomaly_percentile=percentile,
                ml_outlier=bool(predictions[index] == -1),
                peer_distance=peer_distance,
                hybrid_priority=hybrid,
                top_deviations=deviations,
            )
        )

    return sorted(findings, key=lambda row: (row.hybrid_priority, row.anomaly_percentile, row.agent_id), reverse=True)


def ml_summary(agents: list[AgentIdentity]) -> dict[str, object]:
    findings = analyze_agents(agents)
    return {
        "model": MODEL_NAME,
        "reference_population": len(_reference_indices(agents)),
        "features": list(FEATURE_NAMES),
        "outliers": sum(row.ml_outlier for row in findings),
        "mean_anomaly_percentile": round(
            sum(row.anomaly_percentile for row in findings) / len(findings), 1
        ) if findings else 0.0,
        "meaning": "ML ranks unusual agent posture and access patterns; scores are not probabilities of compromise.",
    }
