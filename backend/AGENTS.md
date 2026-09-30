# Backend

Codex owns backend infrastructure, domain, storage, planning, routing and API. Claude owns `app/intake/` during CC-06 only. Coordinate shared contracts before changes.

Keep deterministic domain code separate from provider I/O. Validate every model/provider response. Use bounded timeouts. SQLite transactions must atomically check state versions and append decisions; reject replayed stale approvals. Test invariant failures, infeasible plans, duplicate commands, replay and disconnected providers.

CC-02 establishes Python 3.12, a lockfile and reproducible lint/type/test commands. No executable backend is present yet.
