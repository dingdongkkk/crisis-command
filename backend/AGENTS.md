# Backend

Codex owns backend infrastructure, domain, storage, planning, routing and API. Claude owns `app/intake/` during CC-06 only. Coordinate shared contracts before changes.

Keep deterministic domain code separate from provider I/O. Validate every model/provider response. Use bounded timeouts. SQLite transactions must atomically check state versions and append decisions; reject replayed stale approvals. Test invariant failures, infeasible plans, duplicate commands, replay and disconnected providers.

Layout: `app/contracts/` canonical models (CC-02), `app/domain/` pure projection and command decisions, `app/storage/` SQLite event store with receipts, `app/api/` HTTP + WebSocket (CC-03). Commands are in `backend/README.md`.
