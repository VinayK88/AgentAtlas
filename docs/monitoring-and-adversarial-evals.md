# Model Monitoring & Adversarial Evaluation

AgentAtlas treats model monitoring as a separate control plane from deterministic authorization and posture rules.

## Monitoring

`agentatlas.evaluation.drift_report` computes Population Stability Index (PSI) for every feature used by the Isolation Forest / peer-deviation layer. The default alert threshold is `0.20` per feature. A steady-state self-comparison is expected to produce no alerts; a deterministic synthetic shifted window adds permission breadth, external egress, and higher autonomy to a subset of agents and is expected to trigger drift.

The report also publishes versioned metadata:

- model version: `agentatlas-iforest-v1`
- feature schema: `agent-posture-v1`
- model random seed
- report generation timestamp

PSI is used here as an engineering drift indicator, not as proof that the environment is compromised or that retraining is automatically required.

## Adversarial robustness exercises

The defensive synthetic suite evaluates three evasive-style governance changes:

1. low-and-slow permission growth;
2. an external data-export path;
3. an unmanaged high-autonomy production agent.

A case is considered surfaced for review when an explicit deterministic posture rule, the Isolation Forest outlier state, or a very high anomaly percentile raises it. This is intentionally a review-prioritization test rather than an exploitation benchmark.

The suite reports a synthetic surface rate for reproducibility, but that number is **not adversarial recall on real attacks**.

## Safety boundary

These tests use only synthetic identities, permissions, resources, and destinations. They do not create accounts, expand real privileges, call external tools, or modify production IAM.
