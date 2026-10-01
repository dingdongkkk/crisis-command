# Combined release branch

`claude/release-combined` holds every task branch, CC-01 to CC-14, in one line of history. It is the same code as the PR stack #15 → #34. The UI is Codex's black-and-red "City command" console from #29, `codex/console-command-center` at `8c8b212`, merged at the user's request. Claude's restyle (#31) is not included.

## Verified on this branch (2026-10-01)

| Check | Result |
| --- | --- |
| Setup checks | pass |
| Backend ruff, format and mypy | clean |
| Backend `pytest` | 211 passed |
| Contracts and generated types | current |
| Scripted scenario | replay-equal |
| Triage | dev 24/24, held-out 30/30, CC-11 29/30; 0 unsafe downgrades |
| Adversarial probes | 10/10 |
| Benchmark smoke | pass |
| Frontend lint, typecheck and build | pass |
| Frontend tests | 53 passed |
| Live console end-to-end run | 17/17 (`docs/screenshots/release/`); the test now reads text content, so CSS capitalisation of labels cannot break checks |

## Open

CC-14 is in progress: the Laya results are pending a slow model download, and the adapter stays disabled by default. Run the demo with `scripts/demo.sh` (see `docs/RUN-DEMO.md` and `docs/demo/`).
