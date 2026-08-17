# AgentAtlas ML methodology

AgentAtlas uses a hybrid design: deterministic governance rules remain the primary policy evidence, while an unsupervised machine-learning layer prioritizes agents whose posture and access patterns differ from a synthetic low-risk reference population.

## Model

The ML layer uses `IsolationForest` with a fixed random seed. It is trained only on managed, owned, low-posture-risk synthetic agents when enough reference records exist. This keeps the model from treating known high-risk fixtures as normal behavior.

The feature vector contains:

- maximum permission sensitivity;
- permission, tool, MCP-server, and external-destination counts;
- managed/shadow and owned/orphaned state;
- log-transformed inactivity;
- autonomy level and production environment;
- privileged-scope count;
- critical effective-access path count.

In addition to the global anomaly percentile, AgentAtlas computes a peer-distance signal against agents with the same environment and identity type. The largest feature deviations are returned as explanations.

## Hybrid priority

`hybrid_priority` starts with the transparent deterministic posture score and adds a bounded ML adjustment. The ML contribution cannot erase or replace explicit governance rules.

The anomaly percentile means *unusual relative to the synthetic reference population*. It is not a probability that an agent is malicious or compromised.

## Evaluation boundary

All data is deterministic and synthetic. The tests verify reproducibility, feature shape, stable prioritization, and separation between ordinary agents and deliberately high-consequence fixtures. They do not establish production precision, recall, calibration, or incident-prediction accuracy.

A production system should retrain on authorized enterprise telemetry, segment peers by business role, monitor feature/model drift, evaluate analyst dispositions, and calibrate thresholds against business impact.
