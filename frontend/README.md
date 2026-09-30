# Frontend

React + TypeScript + Vite. Node version in `.nvmrc`; dependencies pinned exactly in `package-lock.json`.

```sh
cd frontend
npm ci                 # clean install from the lockfile
npm run gen:contracts  # regenerate src/generated/contracts.ts from contracts/schema
npm run lint
npm run typecheck
npm test               # smoke test + mocks validated against the backend schema
npm run build
npm run dev            # http://localhost:5173
```

Never edit `src/generated/`. Validate mocks with `validateContract()` from `src/contracts.ts`.
