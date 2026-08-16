from fastapi import FastAPI, HTTPException, Query
from agentatlas.access import effective_access_paths
from agentatlas.fixtures import generate_agents
from agentatlas.posture import posture_summary, rank_agents, score_agent

app = FastAPI(title="AgentAtlas", version="0.1.0")

@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "agentatlas"}

@app.get("/summary")
def summary() -> dict[str, int | float]:
    return posture_summary(generate_agents())

@app.get("/agents")
def agents(limit: int = Query(default=20, ge=1, le=120)) -> list[dict[str, object]]:
    inventory = generate_agents()
    by_id = {a.agent_id: a for a in inventory}
    return [{"agent_id": f.agent_id, "risk": f.risk, "severity": f.severity, "owner": by_id[f.agent_id].owner, "managed": by_id[f.agent_id].managed, "reasons": list(f.reasons)} for f in rank_agents(inventory)[:limit]]

@app.get("/agents/{agent_id}")
def agent_detail(agent_id: str) -> dict[str, object]:
    inventory = {a.agent_id: a for a in generate_agents()}
    agent = inventory.get(agent_id)
    if agent is None:
        raise HTTPException(status_code=404, detail={"error": "unknown agent"})
    posture = score_agent(agent)
    return {"agent": agent.__dict__, "posture": posture.__dict__, "effective_access_paths": [p.__dict__ for p in effective_access_paths(agent)]}
