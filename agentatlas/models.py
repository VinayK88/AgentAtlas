from dataclasses import dataclass

@dataclass(frozen=True)
class AgentIdentity:
    agent_id: str
    owner: str | None
    sponsor: str | None
    environment: str
    identity_type: str
    autonomy_level: int
    managed: bool
    last_active_days: int
    permissions: tuple[str, ...]
    tools: tuple[str, ...]
    mcp_servers: tuple[str, ...]
    external_destinations: tuple[str, ...]

@dataclass(frozen=True)
class PostureFinding:
    agent_id: str
    risk: float
    severity: str
    reasons: tuple[str, ...]

@dataclass(frozen=True)
class DelegationDecision:
    chain: tuple[str, ...]
    origin_scopes: tuple[str, ...]
    requested_scope: str
    decision: str
    reason: str

@dataclass(frozen=True)
class PermissionDrift:
    agent_id: str
    added: tuple[str, ...]
    removed: tuple[str, ...]
    risk_delta: float
    severity: str
