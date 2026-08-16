from agentatlas.models import AgentIdentity

BASE_PERMS = ("docs.read", "github.search", "web.search")


def generate_agents(n: int = 120) -> list[AgentIdentity]:
    """Generate deterministic synthetic enterprise agent inventory."""
    shadow = {13, 26, 39, 52, 65, 78, 91, 104, 117}
    orphaned = {17, 34, 51, 68, 85, 102}
    teams = ("ml-platform", "finance", "security", "developer-tools", "support", "data")
    agents: list[AgentIdentity] = []
    for i in range(1, n + 1):
        perms = list(BASE_PERMS)
        tools = ["docs.search", "github.search", "web.search"]
        servers = ["mcp-docs"]
        external: list[str] = []
        if i % 4 == 0:
            perms.append("customer.read"); tools.append("warehouse.query"); servers.append("mcp-data")
        if i % 6 == 0:
            perms.append("data.export"); tools.append("objectstore.export")
        if i % 8 == 0:
            perms.append("slack.send_external"); tools.append("slack.send"); servers.append("mcp-messaging"); external.append("external-slack")
        if i % 10 == 0:
            perms.append("repository.write"); tools.append("github.write")
        if i % 15 == 0:
            perms.append("secrets.read"); tools.append("vault.read"); servers.append("mcp-secrets")
        if i % 20 == 0:
            perms.append("iam.modify"); tools.append("iam.admin")
        if i % 30 == 0:
            perms.append("payments.write"); tools.append("payments.submit"); servers.append("mcp-payments")
        if i % 24 == 0:
            perms.append("k8s.admin"); tools.append("k8s.apply")
        owner = None if i in orphaned else teams[(i - 1) % len(teams)]
        sponsor = None if i in orphaned else f"sponsor-{(i % 18) + 1:02d}@example.test"
        agents.append(AgentIdentity(
            agent_id=f"agent-{i:03d}", owner=owner, sponsor=sponsor,
            environment="production" if i % 3 == 0 else "development",
            identity_type=("oauth_service_principal", "workload_identity", "api_key")[i % 3],
            autonomy_level=1 + (i % 4), managed=i not in shadow,
            last_active_days=(i * 7) % 140,
            permissions=tuple(sorted(set(perms))), tools=tuple(sorted(set(tools))),
            mcp_servers=tuple(sorted(set(servers))), external_destinations=tuple(sorted(set(external))),
        ))
    return agents


def delegation_cases() -> list[tuple[tuple[str, ...], tuple[str, ...], str]]:
    return [
        (("human:analyst", "agent-012", "agent-024"), ("docs.read", "customer.read"), "customer.read"),
        (("human:engineer", "agent-010", "agent-020"), ("github.search",), "repository.write"),
        (("human:finance", "agent-030", "agent-060"), ("finance.read",), "payments.write"),
        (("human:security", "agent-015", "agent-045"), ("secrets.read",), "secrets.read"),
    ]


def permission_snapshots() -> dict[str, tuple[set[str], set[str]]]:
    return {
        "agent-020": ({"docs.read", "github.search"}, {"docs.read", "github.search", "repository.write", "iam.modify"}),
        "agent-030": ({"finance.read", "docs.read"}, {"finance.read", "docs.read", "payments.write"}),
        "agent-048": ({"docs.read", "customer.read"}, {"docs.read", "customer.read", "data.export", "slack.send_external"}),
        "agent-075": ({"docs.read", "secrets.read"}, {"docs.read"}),
    }
