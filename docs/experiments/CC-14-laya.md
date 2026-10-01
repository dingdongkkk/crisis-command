# CC-14: Laya and voice extensions (experiment record)

Status: **complete — negative result. Laya is not adopted**; no adapter is wired, and the core app is unchanged. The checkpoint took 1 h 51 min to download, because Hugging Face served roughly 34–100 KB/s to this machine.

## Scope decided by the user (2026-10-01)

- **Laya: evaluate.** The downloads are the isolated environment (laya 0.3.22, torch 2.14.1, transformers 5.18.0; 709 MB) and the `multilingual` checkpoint (644 MB). The source is official only: PyPI and `huggingface.co/convaiinnovations/laya`.
- **Whisper / speech: not run.** The user chose Laya only. Keyboard intake stays the only input, and browser speech was not evaluated.
- **Local LLM: not selected.** The machine has 16 GB of unified memory, and no local LLM was downloaded or measured.

## Pinned subject

| Item | Value |
| --- | --- |
| Checkpoint | `convaiinnovations/laya`, subfolder `multilingual` (mmBERT-base, 322M parameters), revision recorded in the results file |
| Licence | Apache-2.0 (upstream repository) |
| Package | `laya==0.3.22` |
| Hardware | macOS arm64, 16 GB, CPU inference |

## Method (`evals/laya/run_laya_eval.py`)

- **Cases:** the 84 labelled cases (dev 24, CC-06 held-out 30, CC-11 30). All are unseen by Laya, which is used zero-shot.
- **Questions:** each of the 9 binary critical facts is asked as a tri-state choice ("yes / no / unknown: answer only from what the caller says"). The category is asked as a choice. There is one batched forward pass per case.
- **Metrics:**
  - unsafe downgrades (must be 0);
  - missed danger;
  - false danger;
  - category accuracy;
  - fully-correct cases;
  - Brier score and ECE for P(dangerous value);
  - p50/p95 CPU latency.
- **Modes:**
  - `rules`;
  - `laya` alone;
  - `hybrid`: rules first, Laya may only raise `unknown` → dangerous at p ≥ 0.8, never lower anything (0002).

## Adoption criteria (fixed before seeing results)

Laya may be enabled as an optional adapter only if the `hybrid` mode meets all of the following:

1. 0 unsafe downgrades on every set.
2. Fewer missed dangers than `rules` on at least one set, with no increase on any set.
3. No more than 2 extra false dangers per 30 cases.
4. p95 CPU latency ≤ 500 ms per report.

Otherwise the negative result is recorded, and the adapter stays unwired. Either way it remains disabled by default. It would be wired through the existing `FactModel` interface, called outside the write lock like Gemini.

## Results (2026-10-01, `evals/laya/results-multilingual-cpu.json`)

Run: zero-shot, on CPU, on macOS arm64 (16 GB). The load took 6,685 s, almost all of it the network download.

| Set (cases) | Mode | Fully correct | Unsafe downgrades | Missed danger | False danger | Category |
| --- | --- | --- | --- | --- | --- | --- |
| dev (24) | rules | 23 | 0 | 0 | 0 | 24 |
| | Laya alone | 2 | **43** | 6 | 70 | 19 |
| | hybrid | 13 | 0 | 0 | 17 | 24 |
| held-out (30) | rules | 30 | 0 | 0 | 0 | 30 |
| | Laya alone | 3 | **74** | 5 | 70 | 19 |
| | hybrid | 18 | 0 | 0 | 18 | 30 |
| CC-11 (30) | rules | 29 | 0 | 1 | 0 | 30 |
| | Laya alone | 1 | **75** | 2 | 63 | 23 |
| | hybrid | 17 | 0 | 1 | 22 | 30 |

- **Latency:** p50 211 ms and p95 241 ms per report (10 typed questions batched) on CPU.
- **Calibration** for P(dangerous value): Brier 0.166, ECE 0.229, which is poorly calibrated.

The harness scores the rules slightly differently from `run_eval.py`. It treats a rule conflict as `unknown` and does not score `people_count`, which explains dev scoring 23/24 here against 24/24 there.

### Against the adoption criteria (hybrid mode)

| Criterion | Result | Verdict |
| --- | --- | --- |
| 0 unsafe downgrades on every set | 0, 0, 0 | pass (guaranteed by construction: the hybrid never lowers anything) |
| Fewer missed dangers than rules on at least one set | equal on all sets (0, 0, 1) | **fail** |
| At most 2 extra false dangers per 30 cases | 17 per 24, 18 per 30, 22 per 30 | **fail** |
| p95 CPU latency ≤ 500 ms | 241 ms | pass |

**Decision: reject.** Used zero-shot as a fact extractor, Laya alone marks dangerous facts "safe" without evidence in 43–75 fact slots per set. In the only mode the app would allow, it adds no recall over the rules and roughly 0.7 false alarms per call. That would flood operators and inflate demand.

What could change this, as future work and not claimed:

- fine-tuning on the triage schema with held-out human-written calls;
- per-fact thresholds above 0.8;
- using Laya only for the category.

Each would need a new pre-registered evaluation.

### Voice and local LLM

These were not run, by the user's decision; text intake remains the only input. Negative and not-run results are recorded here so they do not block the completed core demo.
