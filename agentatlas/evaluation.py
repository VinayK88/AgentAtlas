from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timezone

import numpy as np

from agentatlas.fixtures import generate_agents
from agentatlas.ml import FEATURE_NAMES, MODEL_NAME, RANDOM_STATE, analyze_agents, feature_vector
from agentatlas.models import AgentIdentity

MODEL_VERSION = "agentatlas-iforest-v1"
FEATURE_SCHEMA_VERSION = "agent-posture-v1"
PSI_ALERT_THRESHOLD = 0.20


def _psi(reference: np.ndarray, current: np.ndarray, bins: int = 6) -> float:
    """Population Stability Index using reference quantile bins."""
    if len(reference) == 0 or len(current) == 0:
        return 0.0
    edges = np.unique(np.quantile(reference, np.linspace(0.0, 1.0, bins + 1)))
    if len(edges) < 3:
        return 0.0
    edges[0] = -np.inf
    edges[-1] = np.inf
    ref_counts, _ = np.histogram(reference, bins=edges)
    cur_counts, _ = np.histogram(current, bins=edges)
    ref_pct = np.clip(ref_counts / max(1, ref_counts.sum()), 1e-6, None)
    cur_pct = np.clip(cur_counts / max(1, cur_counts.sum()), 1e-6, None)
    return round(float(np.sum((cur_pct - ref_pct) * np.log(cur_pct / ref_pct))), 4)


def drift_report(reference_agents: list[AgentIdentity], current_agents: list[AgentIdentity]) -> dict[str, object]:
    reference = np.vstack([feature_vector(agent) for agent in reference_agents])
    current = np.vstack([feature_vector(agent) for agent in current_agents])
    feature_psi = {
        name: _psi(reference[:, i], current[:, i])
        for i, name in enumerate(FEATURE_NAMES)
    }
    alerts = sorted(name for name, value in feature_psi.items() if value >= PSI_ALERT_THRESHOLD)
    return {
        "metric": "population_stability_index",
        "threshold": PSI_ALERT_THRESHOLD,
        "feature_psi": feature_psi,
        "drift_alert": bool(alerts),
        "alert_features": alerts,
    }


def simulate_shifted_inventory(agents: list[AgentIdentity]) -> list[AgentIdentity]:
    """Create a deterministic synthetic drift window for monitoring tests."""
    shifted: list[AgentIdentity] = []
    for index, agent in enumerate(agents):
        if index % 4 == 0:
            permissions = tuple(sorted(set((*agent.permissions, "repository.write", "data.export"))))
            destinations = tuple(sorted(set((*agent.external_destinations, "external-webhook"))))
            shifted.append(
                replace(
                    agent,
                    permissions=permissions,
                    external_destinations=destinations,
                    autonomy_level=max(agent.autonomy_level, 3),
                )
            )
        else:
            shifted.append(agent)
    return shifted


def adversarial_evaluation(agents: list[AgentIdentity]) -> dict[str, object]:
    """Evaluate deterministic evasive-style posture changes without modeling exploitation."""
    base = next(
        agent for agent in agents
        if agent.managed and agent.owner is not None and agent.sponsor is not None
    )
    cases = [
        ("low_and_slow_permission_growth", replace(
            base,
            agent_id="adv-permission-growth",
            permissions=tuple(sorted(set((*base.permissions, "repository.write", "data.export")))),
        )),
        ("external_export_path", replace(
            base,
            agent_id="adv-external-export",
            permissions=tuple(sorted(set((*base.permissions, "data.export", "slack.send_external")))),
            external_destinations=("external-webhook",),
        )),
        ("shadow_high_autonomy", replace(
            base,
            agent_id="adv-shadow-autonomy",
            managed=False,
            environment="production",
            autonomy_level=4,
        )),
    ]

    combined = [*agents, *[agent for _, agent in cases]]
    by_id = {row.agent_id: row for row in analyze_agents(combined)}
    results = []
    for name, agent in cases:
        finding = by_id[agent.agent_id]
        surfaced = (
            finding.rule_risk >= 0.30
            or finding.ml_outlier
            or finding.anomaly_percentile >= 95.0
        )
        results.append({
            "case": name,
            "rule_risk": finding.rule_risk,
            "anomaly_percentile": finding.anomaly_percentile,
            "ml_outlier": finding.ml_outlier,
            "hybrid_priority": finding.hybrid_priority,
            "surfaced_for_review": bool(surfaced),
        })

    surfaced_count = sum(row["surfaced_for_review"] for row in results)
    return {
        "cases": results,
        "surfaced": surfaced_count,
        "total": len(results),
        "synthetic_surface_rate": round(surfaced_count / len(results), 3),
        "meaning": "Defensive synthetic robustness exercise; not measured adversarial recall on production attacks.",
    }


def evaluation_summary(agents: list[AgentIdentity] | None = None) -> dict[str, object]:
    inventory = agents or generate_agents()
    shifted = simulate_shifted_inventory(inventory)
    return {
        "model_metadata": {
            "model": MODEL_NAME,
            "model_version": MODEL_VERSION,
            "feature_schema_version": FEATURE_SCHEMA_VERSION,
            "random_state": RANDOM_STATE,
            "generated_at": datetime.now(timezone.utc).isoformat(),
        },
        "steady_state_monitoring": drift_report(inventory, inventory),
        "synthetic_shift_monitoring": drift_report(inventory, shifted),
        "adversarial_evaluation": adversarial_evaluation(inventory),
    }
