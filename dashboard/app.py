import pandas as pd
import streamlit as st
from agentatlas.access import effective_access_paths
from agentatlas.delegation import evaluate_delegation
from agentatlas.drift import calculate_drift
from agentatlas.fixtures import delegation_cases, generate_agents, permission_snapshots
from agentatlas.posture import posture_summary, rank_agents

st.set_page_config(page_title="AgentAtlas", page_icon="🧭", layout="wide")
st.title("AgentAtlas — AI Agent Identity & Governance")
st.caption("Synthetic shadow-agent discovery · effective access · delegation · permission drift")

agents = generate_agents(); summary = posture_summary(agents); ranked = rank_agents(agents); by_id = {a.agent_id: a for a in agents}
cols = st.columns(6)
for col, label, value in zip(cols, ["Agents","Managed","Shadow","Orphaned","High/Critical","Critical"], [summary["agents"],summary["managed"],summary["shadow"],summary["orphaned"],summary["high_or_critical"],summary["critical"]]):
    col.metric(label, value)

t1,t2,t3,t4,t5,t6 = st.tabs(["Executive Posture","Agent Inventory","Effective Access","Delegation Chains","Permission Drift","Access Reviews"])
with t1:
    df = pd.DataFrame([f.__dict__ for f in ranked]); st.bar_chart(df.groupby("severity").size()); st.dataframe(df.head(20), use_container_width=True, hide_index=True)
with t2:
    rows=[]
    for a in agents:
        f=next(x for x in ranked if x.agent_id==a.agent_id)
        rows.append({"agent":a.agent_id,"owner":a.owner,"sponsor":a.sponsor,"managed":a.managed,"environment":a.environment,"autonomy":a.autonomy_level,"last_active_days":a.last_active_days,"risk":f.risk,"severity":f.severity})
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
with t3:
    selected=st.selectbox("Agent", [f.agent_id for f in ranked], index=0); st.write("**Permissions**", by_id[selected].permissions); st.write("**Tools**", by_id[selected].tools); st.dataframe(pd.DataFrame([p.__dict__ for p in effective_access_paths(by_id[selected])]), use_container_width=True, hide_index=True)
with t4:
    st.dataframe(pd.DataFrame([evaluate_delegation(*c).__dict__ for c in delegation_cases()]), use_container_width=True, hide_index=True)
with t5:
    st.dataframe(pd.DataFrame([calculate_drift(a,p,c).__dict__ for a,(p,c) in permission_snapshots().items()]), use_container_width=True, hide_index=True)
with t6:
    review=[{"agent":f.agent_id,"risk":f.risk,"owner":by_id[f.agent_id].owner,"recommended_review":"REVOKE/REASSIGN" if "orphaned_identity" in f.reasons else "REVIEW"} for f in ranked if f.severity in {"high","critical"}]
    st.dataframe(pd.DataFrame(review), use_container_width=True, hide_index=True)
st.caption("All identities, permissions, tools, MCP servers, destinations, and scores are synthetic. No production enforcement is performed.")
