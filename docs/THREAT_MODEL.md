# AgentAtlas Threat Model

## Protected assets
- Enterprise data and customer PII
- Secrets and service credentials
- Source repositories and CI/CD authority
- IAM administration
- Payment and production infrastructure

## Trust boundaries
- Human-to-agent delegation
- Agent-to-agent delegation
- Agent-to-MCP/tool invocation
- Agent-to-enterprise resource access
- Internal-to-external data movement

## Threats modeled
- Shadow/unmanaged agents
- Orphaned agent identities
- Excessive privilege
- Permission drift
- Delegated authority expansion
- Sensitive-data-to-external-destination paths
- Dormant privileged identities

## Security objectives
AgentAtlas should make agent ownership, effective authority, delegation provenance and privilege growth visible before those conditions become incidents.

All modeled identities and resources are synthetic.
