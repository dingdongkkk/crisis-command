# Triage intake evaluation (CC-06)

Labelled synthetic caller texts for the rule-based intake (`backend/app/intake/`).

| File | Cases | Languages | Use |
| --- | --- | --- | --- |
| `cases.dev.jsonl` | 24 | English, Hindi (Devanagari), Hinglish | used while writing the lexicon |
| `cases.heldout.jsonl` | 30 | English, Hindi, Hinglish | not used to tune rules; regression floor 27/30 |
| `cases.cc11.jsonl` | 30 | English, Hindi, Hinglish | CC-11 held-out set (SMS, typos, long calls, corrections). Held-out result **18/30** recorded before any fix (`docs/reviews/CC-11-review.md`); CC-12 then tuned the lexicon on it (29/30), so it is now a regression set, not held-out |
| `report.json` | — | — | latest run of all sets |

Families: cardiac, medical, accident, structural collapse, fire, gas, flood, information request, tyre/breakdown, human request, prompt injection, negation, conflict, ambiguous.

Each case lists only facts the text establishes; every other critical fact is expected `unknown`. `people_count` uses a number, `~N` for approximate, or `unknown`.

```sh
cd backend && uv run python ../evals/triage/run_eval.py --json ../evals/triage/report.json
```

Metrics: fully-correct cases; **unsafe downgrades** (a critical fact predicted at its safe value when the text does not establish it — must be 0; the runner exits non-zero otherwise); missed dangers; over-triage; category accuracy; required escalations met.

Caveats: all texts are synthetic and short. The same agent wrote the lexicon and both sets, so the held-out set is not independent; CC-11 should add an independently written set. Zero observed misses here is not evidence of safety on real calls. No model is used (rule adapter only); the optional Gemini adapter is evaluated only with fakes in unit tests.
