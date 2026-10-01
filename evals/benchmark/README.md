# Allocation benchmark (CC-11)

`run_benchmark.py` replays 100 seeded synthetic 10-minute incident streams through the real command path, twice. The first run uses the production lexicographic CP-SAT allocator. The second uses `allocate(baseline=True)`, the nearest feasible unit under identical eligibility, reachability, capacity, lock and pin constraints.

```sh
cd backend && uv run python ../evals/benchmark/run_benchmark.py --seeds 100 --json ../evals/benchmark/results.json
```

`results.json` records:

- per-seed and aggregate metrics;
- paired win/tie/loss counts and bootstrap 95 % CIs;
- metric definitions;
- metadata: commit, a dirty flag for tracked files, Python and OR-Tools versions, and machine.

Decision metrics are deterministic for a given commit; latency varies by machine. Results and interpretation are in `docs/reviews/CC-11-review.md`. Offline, with no keys and no network.
