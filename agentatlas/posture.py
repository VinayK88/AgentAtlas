from agentatlas.models import AgentIdentity, PostureFinding

PERMISSION_WEIGHTS = {
    "docs.read": 0.02, "github.search": 0.03, "web.search": 0.02,
    "customer.read": 0.18, "finance.read": 0.20, "data.export": 0.38,
    "slack.send_external": 0.34, "repository.write": 0.30, "secrets.read": 0.58,
    "iam.modify": 0.72, "payments.write": 0.82, "k8s.admin": 0.70,
}


def score_agent(agent: AgentIdentity) -> PostureFinding:
    reasons: list[str] = []
    risk = 0.05
    max_perm = max((PERMISSION_WEIGHTS.get(p, 0.05) for p in agent.permissions), default=0.0)
    risk += 0.33 * max_perm
    if not agent.managed:
        risk += 0.32; reasons.append("shadow_agent")
    if agent.owner is None or agent.sponsor is None:
        risk += 0.27; reasons.append("orphaned_identity")
    if agent.last_active_days > 90:
        risk += 0.14; reasons.append("dormant_identity")
    if agent.environment == "production" and agent.autonomy_level >= 3:
        risk += 0.10; reasons.append("high_autonomy_production")
    if agent.external_destinations:
        risk += 0.12; reasons.append("external_egress_capability")
    if len(agent.permissions) >= 6:
        risk += 0.10; reasons.append("broad_permission_set")
    if any(p in agent.permissions for p in ("iam.modify", "payments.write", "k8s.admin")):
        reasons.append("privileged_scope")
    if "secrets.read" in agent.permissions:
        reasons.append("secret_access")
    if "data.export" in agent.permissions and agent.external_destinations:
        risk += 0.08; reasons.append("sensitive_data_to_external_path")
    risk = round(min(risk, 0.99), 4)
    severity = "critical" if risk >= 0.72 else "high" if risk >= 0.55 else "medium" if risk >= 0.30 else "low"
    return PostureFinding(agent.agent_id, risk, severity, tuple(reasons or ["baseline_managed_agent"]))


def rank_agents(agents: list[AgentIdentity]) -> list[PostureFinding]:
    return sorted((score_agent(a) for a in agents), key=lambda r: (r.risk, r.agent_id), reverse=True)


def posture_summary(agents: list[AgentIdentity]) -> dict[str, int | float]:
    findings = rank_agents(agents)
    return {
        "agents": len(agents), "managed": sum(a.managed for a in agents),
        "shadow": sum(not a.managed for a in agents),
        "orphaned": sum(a.owner is None or a.sponsor is None for a in agents),
        "dormant": sum(a.last_active_days > 90 for a in agents),
        "high_or_critical": sum(f.severity in {"high", "critical"} for f in findings),
        "critical": sum(f.severity == "critical" for f in findings),
    }
