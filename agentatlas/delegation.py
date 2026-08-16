from agentatlas.models import DelegationDecision


def evaluate_delegation(chain: tuple[str, ...], origin_scopes: tuple[str, ...], requested_scope: str) -> DelegationDecision:
    allowed = requested_scope in set(origin_scopes)
    return DelegationDecision(
        chain=chain,
        origin_scopes=origin_scopes,
        requested_scope=requested_scope,
        decision="ALLOW" if allowed else "DENY",
        reason="within_originating_authority" if allowed else "delegated_scope_exceeds_origin_authority",
    )
