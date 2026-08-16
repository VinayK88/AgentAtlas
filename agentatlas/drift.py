from agentatlas.models import PermissionDrift
from agentatlas.posture import PERMISSION_WEIGHTS


def calculate_drift(agent_id: str, previous: set[str], current: set[str]) -> PermissionDrift:
    added = tuple(sorted(current - previous))
    removed = tuple(sorted(previous - current))
    added_risk = sum(PERMISSION_WEIGHTS.get(p, 0.05) for p in added)
    removed_risk = sum(PERMISSION_WEIGHTS.get(p, 0.05) for p in removed)
    delta = round(added_risk - removed_risk, 4)
    severity = "critical" if delta >= 0.8 else "high" if delta >= 0.45 else "medium" if delta >= 0.2 else "low"
    return PermissionDrift(agent_id, added, removed, delta, severity)
