from dataclasses import dataclass
from agentatlas.models import AgentIdentity

@dataclass(frozen=True)
class AccessPath:
    agent_id: str
    source_capability: str
    resource: str
    sink: str
    risk: str


def effective_access_paths(agent: AgentIdentity) -> list[AccessPath]:
    paths: list[AccessPath] = []
    if "customer.read" in agent.permissions:
        paths.append(AccessPath(agent.agent_id, "customer.read", "customer-pii", "agent-memory", "medium"))
    if "secrets.read" in agent.permissions:
        paths.append(AccessPath(agent.agent_id, "secrets.read", "secret-store", "agent-memory", "high"))
    if "payments.write" in agent.permissions:
        paths.append(AccessPath(agent.agent_id, "payments.write", "payment-system", "transaction", "critical"))
    if "data.export" in agent.permissions and agent.external_destinations:
        paths.append(AccessPath(agent.agent_id, "data.export", "enterprise-data", agent.external_destinations[0], "critical"))
    if "customer.read" in agent.permissions and "slack.send_external" in agent.permissions:
        paths.append(AccessPath(agent.agent_id, "customer.read + slack.send_external", "customer-pii", "external-slack", "critical"))
    return paths
