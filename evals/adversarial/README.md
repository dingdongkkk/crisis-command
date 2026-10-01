# Adversarial probes (CC-11)

`run_probes.py` attacks stated invariants through the real API, each in its own isolated database:

- approval acknowledgements, concurrent approvals, stale plans and wrong sessions;
- idempotency;
- simulated-only dispatch;
- replay equality;
- report-text and Medical ID canaries;
- override conflict reasons.

A FAIL is a finding, not a harness error.

```sh
cd backend && uv run python ../evals/adversarial/run_probes.py --json ../evals/adversarial/results.json
```
