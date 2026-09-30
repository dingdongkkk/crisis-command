# CC-14: Laya and voice extensions (experiment record)

Status: **in progress.** The harness is ready and the environment is pinned. The Laya checkpoint download is running, but Hugging Face serves about 34 KB/s to this machine: 644 MB, roughly 5 hours. No results are claimed yet.

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

## Results

Pending the download. This section will record the numbers from `evals/laya/results-multilingual-cpu.json` against the criteria above.
