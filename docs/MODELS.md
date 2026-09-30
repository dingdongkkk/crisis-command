# Which model for which job

Recommendation checked 2026-09-30. These are workload assignments, not a claim that one vendor always wins. Use the models your account's picker actually exposes.

## Models that help you build

| Work | First choice | When to change |
| --- | --- | --- |
| Backend, solver, event log, replanning, difficult integration | Codex `gpt-6-astra`, medium; high for hard races/solver review | Current desktop tools expose Astra and the 5.6 family. Use `gpt-5.6-sol` for routine backend tasks; try `gpt-6.1-sol` if it appears in your picker. |
| Product specification, UX flow, architecture critique | Claude Opus 5.5 (`claude-opus-5-5`), confirmed available | Use it for CC-01 and difficult design decisions; Sonnet handles routine implementation. |
| React UI, interaction details, prompt/data authoring | Claude Sonnet 5.5 (`sonnet`) | Escalate to Opus only for unresolved complex design/debugging. |
| Independent review of Codex changes | Claude Opus 5.5 (`claude-opus-5-5`) | Reviewer supplies concrete repros and missing tests; author fixes. |
| Independent review of Claude changes | Codex Astra | UI behavior, contract compatibility and fallback tests matter more than cosmetic preference. |
| Mechanical docs, formatting, narrow fixtures | Codex 5.6 Luna already exposed locally, or Claude Haiku if available | No need for another model if switching costs more time than it saves. |

Spend most Codex usage on implementation and tests. Spend the smaller Claude budget on specification, UI and independent review. Start at moderate reasoning effort; increase it for a concrete difficult task. Do not run both agents against the same checkout concurrently.

OpenAI's current docs recommend GPT-6.1 Sol where rolled out, with Astra for the hardest work. This desktop session's callable model list is narrower; no local config is pinned to a model that is not exposed. [OpenAI model guidance](https://learn.chatgpt.com/docs/models).

Claude's current docs list Sonnet 5.5 and Opus 5.5. The user confirmed Opus 5.5 availability. Architect/reviewer roles are pinned to `claude-opus-5-5`; the frontend role keeps `sonnet`. `/model` selects the main session model independently of these role files. [Model configuration](https://support.claude.com/en/articles/11940350-claude-code-model-configuration), [usage guidance](https://support.claude.com/en/articles/14552983-models-usage-and-limits-in-claude-code).

## Models and engines inside Crisis Command

| Component | MVP choice | Fallback / later work |
| --- | --- | --- |
| Caller text conversation | Templates first; optional `gemini-3.8-flash` adapter | One targeted question at a time; local model only after hardware test. |
| Triage extraction | Same Gemini adapter, strict schema and evidence spans | Deterministic keyword/rule escalation, `unknown` on invalid/timeout output. No self-reported confidence treated as calibrated probability. |
| Incident summaries and explanations | Templates from validated facts and solver reason codes | Optional Gemini rewrites wording, but all numbers/IDs must be checked against input. |
| Duplicate candidates | Spatial/time blocking first; `intfloat/multilingual-e5-small` for similarity | Candidate review, never blindly merge distinct casualties; preserve provenance. Calibrate similarity threshold on held-out pairs. |
| Severity, escalation, consent, policy | Python rules | No LLM required. Version policy/weights. |
| Assignment | Google OR-Tools CP-SAT | Bounded solver time; validate feasible incumbent; otherwise eligible deterministic fallback or explicit no-plan state. |
| Routing | OpenRouteService Directions with avoidance and cached road fixtures | Validate geometry against closures. Matrix support must be checked, not assumed. Unknown routes are unavailable, not straight-line road ETAs. |
| Flood geometry and watchdog | Shapely + ordinary Python | Synthetic flood progression, not hydrological prediction. |
| Speech | Add only after text works; benchmark Whisper multilingual model on the actual laptop | Keyboard/transcript input always available. Browser speech support does not establish offline operation. |
| Laya | Stretch typed-decision classifier behind the existing triage interface | Pin checkpoint/license, validate language support, evaluate recall/calibration and measure CPU latency before adoption. |

For the first demo, **no runtime LLM is required**. The development subscriptions write the code. Optional app inference uses separate provider configuration; Claude Pro explicitly does not include Claude Console API usage. Do not put subscription cookies/tokens into the app or GitHub Actions. No runtime API credentials are installed here. [Claude Pro plan](https://support.claude.com/en/articles/8325606-what-is-the-pro-plan).

Gemini 3.8 Flash supports text output and structured outputs; it is not its own speech-output/Live API model. Its availability is documented, but no free quota for this account has been verified. [Google model page](https://ai.google.dev/gemini-api/docs/models/gemini-3.8-flash).

Embedding reference: [intfloat model card](https://huggingface.co/intfloat/multilingual-e5-small). Follow its input prefix guidance; similarity is not event identity. Laya reference: [upstream repository](https://github.com/NandhaKishorM/laya). These upstream capabilities are not validated emergency-triage performance.

ORS maintainers reported the Matrix API lacks polygon avoidance, with no firm delivery date in March 2026. Recheck the deployed endpoint before implementation; Directions is the planned route-building path. [Maintainer response](https://ask.openrouteservice.org/t/avoid-polygons-not-working-with-matrix-api-for-multiple-locations/7579).
